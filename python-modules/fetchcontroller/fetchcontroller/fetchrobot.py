#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
#
# This file is part of ewm-cloud-robotics
# (see https://github.com/SAP/ewm-cloud-robotics).
#
# This file is licensed under the Apache Software License, v. 2 except as noted
# otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
#

"""Representation of a Fetch robot in RobCo."""

import logging
import threading
import time
import math

from typing import Dict, List, Set, Optional
from requests import RequestException
from prometheus_client import Gauge, Histogram

from .fetchcore import FetchInterface, HTTPstatusNotFound
from .fetchlocation import FetchMap

_LOGGER = logging.getLogger(__name__)


class RobcoRobotStates:
    """Robot states in RobCo."""

    STATE_UNDEFINED = 'UNDEFINED'
    STATE_UNAVAILABLE = 'UNAVAILABLE'
    STATE_AVAILABLE = 'AVAILABLE'
    STATE_EMERGENCY_STOP = 'EMERGENCY_STOP'
    STATE_ERROR = 'ERROR'


class RobcoMissionStates:
    """Mission states in RobCo."""

    STATE_ACCEPTED = 'ACCEPTED'
    STATE_RUNNING = 'RUNNING'
    STATE_SUCCEEDED = 'SUCCEEDED'
    STATE_FAILED = 'FAILED'
    STATE_CANCELED = 'CANCELED'

    FETCH_TO_ROBCO = {
        'NEW': STATE_ACCEPTED,
        'QUEUED': STATE_ACCEPTED,
        'WORKING': STATE_RUNNING,
        'PAUSED': STATE_RUNNING,
        'COMPLETE': STATE_SUCCEEDED,
        'FAILED': STATE_FAILED,
        'CANCELED': STATE_CANCELED,
        'PREEMPTED': STATE_CANCELED
        }


class FetchCapabilityError(BaseException):
    """Robot does not suppport this action."""


class FetchRobot:
    """Representation of one single Fetch robot."""

    # TODO: Define Charge Missions

    # Prometheus logging
    BUCKETS = (5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0, 3600.0, '+Inf')

    p_battery_percentage = Gauge(
        'sap_robot_battery_percentage', 'Robot\'s battery percentage (%)', ['robot'])
    p_state = Histogram(
        'sap_robot_state', 'Robot\'s state', ['robot', 'state'], buckets=BUCKETS)
    p_position_x = Gauge('sap_robot_position_x', 'Robot\'s X position', ['robot'])
    p_position_y = Gauge('sap_robot_position_y', 'Robot\'s Y position', ['robot'])
    p_orientation = Gauge(
        'sap_robot_position_orientation', 'Robot\'s orientation in degree', ['robot'])
    p_theta = Gauge('sap_robot_position_theta', 'Robot\'s orientation in rad', ['robot'])

    def __init__(self, name: str, fetch_api: FetchInterface) -> None:
        """Construct."""
        self.name = name
        self._fetch_api = fetch_api
        self.battery_percentage = 1.0
        self.pos_x = 0.0
        self.pos_y = 0.0
        self.pos_orientation = 0.0
        self.pos_theta = 0.0
        self.state = RobcoRobotStates.STATE_UNDEFINED
        self.last_state_change = '1970-01-01T00:00:00.000Z'
        self.last_state_change_ts = time.time()
        self.trolley_attached = False
        self.active_map: Optional[str] = None
        self.fetch_map: Optional[FetchMap] = None
        self.installed_actions: List[str] = []

    def cancel_task(self, task_id: int) -> bool:
        """Cancel a task."""
        # Check if tasks exists and is in correct state
        status = self.get_task_status(task_id)

        if status not in [RobcoMissionStates.STATE_ACCEPTED, RobcoMissionStates.STATE_RUNNING]:
            _LOGGER.info('Task %s neither running nor queued, nothing to cancel', task_id)
            return False

        # Create PATCH body
        patch_body = {'status': 'CANCELED', 'externally_paused': False}

        endpoint = '/api/v1/tasks/{}/'.format(task_id)
        try:
            self._fetch_api.http_patch(endpoint, patch_body)
        except HTTPstatusNotFound:
            _LOGGER.error('Task %s does not exist in FetchCore', task_id)
            return False
        except RequestException as err:
            _LOGGER.error('Exception %s when connecting to FetchCore endpoint %s', err, endpoint)
            return False
        else:
            return True

    def display_hmi_buttons(
            self, button_names: List, button_data: Optional[List] = None) -> Optional[int]:
        """Display buttons on robots HMI screen."""
        if 'HMI_BUTTONS' not in self.installed_actions:
            raise FetchCapabilityError(
                'Fetch {} does not support HMI_BUTTONS action'.format(self.name))

        # Create HTTP POST body
        post_body = {
            'status': 'NEW',
            'actions': [{
                'status': 'NEW',
                'preemptable': 'HARD',
                'inputs': {
                    'button_names': button_names
                    },
                'outputs': {},
                'action_definition': 'HMI_BUTTONS'
                }],
            'type': 'HMI_BUTTONS',
            'name': 'Cloud Robotics: Display Buttons {}'.format(button_names),
            'robot': self.name
            }

        if isinstance(button_data, list):
            post_body['actions'][0]['inputs']['button_data'] = button_data  # type: ignore

        endpoint = '/api/v1/tasks/'

        try:
            # Send create task for the robot in FetchCore
            resp = self._fetch_api.http_post(endpoint, post_body)
        except RequestException as err:
            _LOGGER.error(
                'Exception %s when connecting to FetchCore endpoint %s', err, endpoint)
        else:
            _LOGGER.info(
                'Display HMI buttons task started with ID %s on robot %s', resp['id'], self.name)
            return resp['id']

        return None

    def get_task_status(self, task_id: int) -> Optional[str]:
        """
        Get status of a task.

        Fetch status are: NEW, QUEUED, WORKING, COMPLETE, FAILED.
        """
        endpoint = '/api/v1/tasks/{}/'.format(task_id)
        try:
            resp = self._fetch_api.http_get(endpoint)
        except HTTPstatusNotFound:
            _LOGGER.error('Task %s does not exist in FetchCore', task_id)
        except RequestException as err:
            _LOGGER.error('Exception %s when connecting to FetchCore endpoint %s', err, endpoint)
        else:
            if resp['robot'] == self.name:
                return RobcoMissionStates.FETCH_TO_ROBCO[resp['status']]
            else:
                _LOGGER.error('Task %s is not a task of robot %s', task_id, self.name)
                raise ValueError

        return None

    def get_trolley(self, target: str) -> Optional[int]:
        """Get trolley from a target position."""
        if 'ATTACH_CART' not in self.installed_actions:
            raise FetchCapabilityError(
                'Fetch {} does not support ATTACH_CART action'.format(self.name))
        if self.fetch_map:
            # TODO: Verify that cart position exists / make cart footprint configurable
            # Create HTTP POST body
            post_body = {
                'status': 'NEW',
                'actions': [{
                    'status': 'NEW',
                    'preemptable': 'HARD',
                    'inputs': {
                        'cart_pose_id': target,
                        'cart_footprint_name': 'BLUE_FETCH_SHELF'
                        },
                    'outputs': {},
                    'action_definition': 'ATTACH_CART'
                    }],
                'type': 'ATTACH_CART',
                'name': 'Cloud Robotics: Attach cart at position {}'.format(target),
                'robot': self.name
                }

            endpoint = '/api/v1/tasks/'
            try:
                # Send create task for the robot in FetchCore
                resp = self._fetch_api.http_post(endpoint, post_body)
            except RequestException as err:
                _LOGGER.error(
                    'Exception %s when connecting to FetchCore endpoint %s', err, endpoint)
            else:
                _LOGGER.info(
                    'Attach cart task started with ID %s on robot %s', resp['id'], self.name)
                return resp['id']
        else:
            _LOGGER.error('Robot is not assigned to a map')

        return None

    def return_trolley(self, target: str) -> Optional[int]:
        """Return trolley to a target position."""
        if 'DETACH_CART' not in self.installed_actions:
            raise FetchCapabilityError(
                'Fetch {} does not support DETACH_CART action'.format(self.name))
        if self.fetch_map:
            # TODO: Verify that cart position exists
            # Create HTTP POST body
            post_body = {
                'status': 'NEW',
                'actions': [{
                    'status': 'NEW',
                    'preemptable': 'HARD',
                    'inputs': {
                        'cart_pose_id': target
                        },
                    'outputs': {},
                    'action_definition': 'DETACH_CART'
                    }],
                'type': 'DETACH_CART',
                'name': 'Cloud Robotics: Detach cart at position {}'.format(target),
                'robot': self.name
                }

            endpoint = '/api/v1/tasks/'
            try:
                # Send create task for the robot in FetchCore
                resp = self._fetch_api.http_post(endpoint, post_body)
            except RequestException as err:
                _LOGGER.error(
                    'Exception %s when connecting to FetchCore endpoint %s', err, endpoint)
                return None
            else:
                _LOGGER.info(
                    'Detach cart task started with ID %s on robot %s', resp['id'], self.name)
                return resp['id']
        else:
            _LOGGER.error('Robot is not assigned to a map')
            return None

    def get_return_trolley_backup(self, target: str, get_trolley: bool) -> Optional[int]:
        """
        Get or return trolley to a target position.

        Backup process for robots only with HMI screen.
        """
        if 'NAVIGATE' not in self.installed_actions or 'HMI_BUTTONS' not in self.installed_actions:
            raise FetchCapabilityError(
                'Fetch {} does not support NAVIGATE and HMI_BUTTONS actions'.format(self.name))

        mode_name = 'Attach' if get_trolley else 'Detach'

        if self.fetch_map:
            try:
                # Verify that position is existing
                xytheta = self.fetch_map.get_pose(target).get_xytheta()
                pose_id = self.fetch_map.get_pose(target).id
            except ValueError:
                _LOGGER.error('Target position is unknown')
            else:
                _LOGGER.debug('Target coordinates are %s', xytheta)
                # Create HTTP POST body
                if get_trolley:
                    button_names = [
                        'Please load HUs from storage bin {} to the robot and confirm'.format(
                            target)]
                else:
                    button_names = [
                        'Please unload HUs from robot to storage bin {} and confirm'.format(
                            target)]
                post_body = {
                    'status': 'NEW',
                    'actions': [
                        {
                            'status': 'NEW',
                            'preemptable': 'HARD',
                            'inputs': {
                                'pose_name': target,
                                'pose_id': pose_id,
                                'clear_costmaps': True
                                },
                            'outputs': {},
                            'action_definition': 'NAVIGATE'
                        }, {
                            'status': 'NEW',
                            'preemptable': 'HARD',
                            'inputs': {
                                'button_names': button_names
                                },
                            'outputs': {},
                            'action_definition': 'HMI_BUTTONS'}
                        ],
                    'type': 'NAVIGATE',
                    'name': 'Cloud Robotics: {} cart at position {}'.format(mode_name, target),
                    'robot': self.name
                    }

                endpoint = '/api/v1/tasks/'
                try:
                    # Send create task for the robot in FetchCore
                    resp = self._fetch_api.http_post(endpoint, post_body)
                except RequestException as err:
                    _LOGGER.error(
                        'Exception %s when connecting to FetchCore endpoint %s', err, endpoint)
                else:
                    _LOGGER.info(
                        '%s cart backup task started with ID %s on robot %s',
                        mode_name, resp['id'], self.name)
                    return resp['id']
        else:
            _LOGGER.error('Robot is not assigned to a map')

        return None

    def move_to_position(self, target: str) -> Optional[int]:
        """Move robot to a named position."""
        if 'NAVIGATE' not in self.installed_actions:
            raise FetchCapabilityError(
                'Fetch {} does not support NAVIGATE action'.format(self.name))
        if self.fetch_map:
            try:
                # Verify that position is existing
                xytheta = self.fetch_map.get_pose(target).get_xytheta()
                pose_id = self.fetch_map.get_pose(target).id
            except ValueError:
                _LOGGER.error('Target position is unknown')
            else:
                _LOGGER.debug('Target coordinates are %s', xytheta)
                # Create HTTP POST body
                post_body = {
                    'status': 'NEW',
                    'actions': [{
                        'status': 'NEW',
                        'preemptable': 'HARD',
                        'inputs': {
                            'pose_name': target,
                            'pose_id': pose_id,
                            'clear_costmaps': True
                            },
                        'outputs': {},
                        'action_definition': 'NAVIGATE'
                        }],
                    'type': 'NAVIGATE',
                    'name': 'Cloud Robotics: Go to position {}'.format(target),
                    'robot': self.name
                    }

                endpoint = '/api/v1/tasks/'
                try:
                    # Send create task for the robot in FetchCore
                    resp = self._fetch_api.http_post(endpoint, post_body)
                except RequestException as err:
                    _LOGGER.error(
                        'Exception %s when connecting to FetchCore endpoint %s', err, endpoint)
                else:
                    _LOGGER.info(
                        'Move to position task started with ID %s on robot %s',
                        resp['id'], self.name)
                    return resp['id']
        else:
            _LOGGER.error('Robot is not assigned to a map')

        return None

    def update_robot_state(self, robots: Dict) -> None:
        """
        Update the robot's state.

        robots: one line of "results" from /api/v1/robots/.
        """
        if robots.get('name') != self.name:
            _LOGGER.error('Wrong robot name %s, this is robot %s', robots.get('name'), self.name)
            return

        self.last_state_change = robots.get('last_status_change', self.last_state_change)

        state_old = self.state

        if robots.get('error_status'):
            self.state = RobcoRobotStates.STATE_ERROR
        elif robots.get('status') == 'IDLE':
            if robots.get('localized') is False:
                self.state = RobcoRobotStates.STATE_ERROR
            else:
                self.state = RobcoRobotStates.STATE_AVAILABLE
        elif robots.get('status') == 'WORKING':
            if robots.get('localized') is False:
                self.state = RobcoRobotStates.STATE_ERROR
            else:
                self.state = RobcoRobotStates.STATE_AVAILABLE
        elif robots.get('status') == 'RUNSTOP':
            self.state = RobcoRobotStates.STATE_EMERGENCY_STOP
        elif robots.get('status') == 'OFFLINE':
            self.state = RobcoRobotStates.STATE_UNAVAILABLE
        else:
            self.state = RobcoRobotStates.STATE_UNDEFINED

        if self.state != state_old:
            self.p_state.labels(  # pylint: disable=no-member
                robot=self.name, state=state_old).observe(
                    time.time() - self.last_state_change_ts)
            self.last_state_change_ts = time.time()

    def update_trolley_attached(self, robots: Dict) -> None:
        """
        Update the robot's trolley_attached attribut.

        robots: one line of "results" from /api/v1/robots/.
        """
        if robots.get('name') != self.name:
            _LOGGER.error('Wrong robot name %s, this is robot %s', robots.get('name'), self.name)
            return

        self.trolley_attached = bool(robots.get('cart_footprint') is not None)

    def update_active_map(self, robots: Dict) -> None:
        """
        Update the robot's map attribute.

        robots: one line of "results" from /api/v1/robots/.
        """
        if robots.get('name') != self.name:
            _LOGGER.error('Wrong robot name %s, this is robot %s', robots.get('name'), self.name)
            return

        self.active_map = robots.get('map')

    def update_installed_actions(self, robots: Dict) -> None:
        """
        Update the robot's installed actions (capabilities) list.

        robots: one line of "results" from /api/v1/robots/.
        """
        if robots.get('name') != self.name:
            _LOGGER.error('Wrong robot name %s, this is robot %s', robots.get('name'), self.name)
            return

        installed_actions = []

        for action in robots.get('installed_actions', []):
            installed_actions.append(action['action_definition'])

        self.installed_actions = installed_actions

    def update_status_attributes(self, states: Dict) -> None:
        """
        Update the robot's status attributes.

        states: one line of "results" from /api/v1/robots/states/.
        """
        if states.get('robot') != self.name:
            _LOGGER.error('Wrong robot name %s, this is robot %s', states.get('robot'), self.name)
            return

        self.battery_percentage = states.get('battery_level', self.battery_percentage / 100) * 100
        self.pos_x = states.get('current_pose', {}).get('x', self.pos_x)
        self.pos_y = states.get('current_pose', {}).get('y', self.pos_y)
        self.pos_theta = states.get('current_pose', {}).get('theta', self.pos_theta)
        self.pos_orientation = math.degrees(self.pos_theta)

        # Update prometheus metrics
        self.p_battery_percentage.labels(  # pylint: disable=no-member
            robot=self.name).set(self.battery_percentage)
        self.p_position_x.labels(  # pylint: disable=no-member
            robot=self.name).set(self.pos_x)
        self.p_position_y.labels(  # pylint: disable=no-member
            robot=self.name).set(self.pos_y)
        self.p_orientation.labels(  # pylint: disable=no-member
            robot=self.name).set(self.pos_orientation)
        self.p_theta.labels(  # pylint: disable=no-member
            robot=self.name).set(self.pos_theta)


class FetchRobots:
    """All RobCo relevant FetchCore robots."""

    def __init__(self, fetch_api: FetchInterface) -> None:
        """Construct."""
        self._robots: Dict[str, FetchRobot] = {}
        self._active_maps: Dict[str, FetchMap] = {}
        self._fetch_api = fetch_api

    @property
    def robots(self) -> Dict:
        """Get robots."""
        return self._robots

    def get_robot(self, name: str) -> FetchRobot:
        """Get the instance of one robot."""
        try:
            robot = self._robots[name]
        except KeyError:
            raise ValueError('Robot {} is unknown'.format(name))

        return robot

    def get_active_maps(self) -> Set:
        """Get a set of maps where at least one robot is active."""
        active_maps: Set[str] = set()

        for robot in self._robots.values():
            if robot.active_map:
                active_maps.add(robot.active_map)

        return active_maps

    def add_robot(self, name: str) -> None:
        """Add a robot to robot list."""
        if name not in self._robots:
            self._robots[name] = FetchRobot(name, self._fetch_api)
            _LOGGER.info('Robot %s added to robot list', name)

    def remove_robot(self, name: str) -> None:
        """Remove a robot from robot list."""
        if name in self._robots:
            self._robots.pop(name)
            _LOGGER.info('Robot %s removed from robot list', name)
        else:
            _LOGGER.warning('Robot %s is not in robot list', name)

    def update(self) -> None:
        """Update all robots, their states and maps in parallel."""
        # Create threads
        ur_thread = threading.Thread(target=self.update_robots, name='update_robots')
        urs_thread = threading.Thread(target=self.update_robots_states, name='update_robot_states')
        uam_thread = threading.Thread(target=self.update_active_maps, name='update_active_maps')
        # Start threads
        ur_thread.start()
        urs_thread.start()
        uam_thread.start()
        # Wait for threads to finish
        ur_thread.join()
        urs_thread.join()
        uam_thread.join()

    def update_robots(self) -> None:
        """Update all robots in list."""
        # Call FetchcCore API
        endpoint = '/api/v1/robots/'
        try:
            results = self._fetch_api.http_get(endpoint).get('results', [])
        except RequestException as err:
            _LOGGER.error('Exception %s when connecting to FetchCore endpoint %s', err, endpoint)
        else:
            # Update robots
            for result in results:
                robot = self._robots.get(result.get('name'))
                if robot:
                    robot.update_active_map(result)
                    robot.update_robot_state(result)
                    robot.update_trolley_attached(result)
                    robot.update_installed_actions(result)

    def update_robots_states(self) -> None:
        """Update states of all robots in list."""
        # Call FetchCore API
        endpoint = '/api/v1/robots/states/'
        try:
            results = self._fetch_api.http_get(endpoint).get('results', [])
        except RequestException as err:
            _LOGGER.error('Exception %s when connecting to FetchCore endpoint %s', err, endpoint)
        else:
            # Update robots
            for result in results:
                robot = self._robots.get(result.get('robot'))
                if robot:
                    robot.update_status_attributes(result)

    def update_active_maps(self) -> None:
        """Update maps and their poses."""
        # Get active maps from robots
        active_maps = self.get_active_maps()

        # Remember active maps
        for active_map in active_maps:
            if active_map not in self._active_maps:
                self._active_maps[active_map] = FetchMap(active_map, self._fetch_api)

        # Update maps and their poses from FetchCore
        for fetchmap in self._active_maps.values():
            if fetchmap.name == '':
                fetchmap.update_map()
            fetchmap.update_poses()

        # Ensure the right FetchCore maps are assigned to the robots
        for robot in self._robots.values():
            if robot.active_map:
                robot.fetch_map = self._active_maps[robot.active_map]
