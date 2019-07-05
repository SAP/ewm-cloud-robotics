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

"""FetchCore mission controller."""

import logging
import datetime
import sys
import time
import threading
import traceback

from copy import deepcopy
from collections import OrderedDict
from typing import Dict, Optional

from k8scrhandler.k8scrhandler import K8sCRHandler

from .fetchrobot import FetchRobots, RobcoMissionStates, FetchCapabilityError
from .helper import get_sample_cr, MainLoopController

_LOGGER = logging.getLogger(__name__)


class MissionController(K8sCRHandler):
    """FetchCore mission controller."""

    m_status_templ = {
        'activeAction': {},
        'taskids': [],
        'status': RobcoMissionStates.STATE_ACCEPTED,
        'timeOfActuation': datetime.datetime.utcnow().replace(
            tzinfo=datetime.timezone.utc).isoformat()}

    activeaction_templ = {'status': 'DOCKING'}

    def __init__(self, fetch_robots: FetchRobots) -> None:
        """Constructor."""
        # Instance with all FetchCore robots
        self._fetch_robots = fetch_robots

        self._active_missions = {}
        self._missions = OrderedDict()
        self._missions_lock = threading.RLock()

        # Init CR superclass
        labels = {}
        template_cr = get_sample_cr('robco_mission')
        super().__init__(
            'mission.cloudrobotics.com',
            'v1alpha1',
            'missions',
            'default',
            template_cr,
            labels
        )

        # Register CR callbacks
        self.register_callback('ADDED_MODIFIED', ['ADDED', 'MODIFIED'], self.robco_mission_cb)
        self.register_callback('DELETED', ['DELETED'], self.robco_mission_deleted_cb)

        # Mission watcher thread
        self.mission_watcher_thread = threading.Thread(target=self._watch_missions_loop)
        self._controller_upstart = True

    def run(self, watcher: bool = True, reprocess: bool = False,
            multiple_executor_threads: bool = False) -> None:
        """Start running everything."""
        self.mission_watcher_thread.start()

        super().run(
            watcher=watcher, reprocess=reprocess,
            multiple_executor_threads=multiple_executor_threads)

    def robco_mission_cb(self, name: str, custom_res: Dict) -> None:
        """Process Cloud Robotics mission CR."""
        cls = self.__class__
        robot = custom_res['metadata'].get('labels', {}).get('cloudrobotics.com/robot-name')
        # Only process missions for Fetch robots
        if robot in self._fetch_robots.robots:
            if not self._missions.get(name):
                # New mission
                with self._missions_lock:
                    self._missions[name] = custom_res
                if not custom_res.get('status'):
                    # Update status, that CR was accepted
                    status = cls.m_status_templ.copy()
                    status['status'] = RobcoMissionStates.STATE_ACCEPTED
                    status['timeOfActuation'] = datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc).isoformat()
                    self.update_cr_status(name, status)
                    _LOGGER.info('Accepted new mission %s for robot %s', name, robot)
            else:
                with self._missions_lock:
                    self._missions[name] = custom_res

    def robco_mission_deleted_cb(self, name: str, custom_res: Dict) -> None:
        """Process Cloud Robotics delete mission CR."""
        robot = custom_res['metadata'].get('labels', {}).get('cloudrobotics.com/robot-name')
        # Only process missions for Fetch robots
        if robot in self._fetch_robots.robots:
            if self._active_missions.get(robot, {}).get('metadata', {}).get('name') == name:
                _LOGGER.warning(
                    'Mission %s is active on robot %s, but CR was deleted', name, robot)
            else:
                with self._missions_lock:
                    self._missions.pop(name, None)

    def _watch_missions_loop(self) -> None:
        """Run watch missions of the robot in a loop."""
        loop_control = MainLoopController()
        _LOGGER.info('Watch missions loop started')
        while self.thread_run:
            try:
                self._watch_missions()
                loop_control.sleep(0.5)
            except Exception as exc:  # pylint: disable=broad-except
                exc_info = sys.exc_info()
                _LOGGER.error(
                    '%s/%s: Error watching missions of robot - Exception: "%s" / "%s" - '
                    'TRACEBACK: %s', self.group, self.plural, exc_info[0], exc_info[1],
                    traceback.format_exception(*exc_info))
                # On uncovered exception in thread save the exception
                self.thread_exceptions['mission_loop'] = exc
                # Stop the watcher
                self.stop_watcher()

        _LOGGER.info('Watch missions loop stopped')

    def _watch_missions(self) -> None:
        """Watch missions of the robot."""
        # Copy mission dict, it might be changed while loop is running
        with self._missions_lock:
            missions = deepcopy(self._missions)
        for mission in missions.values():
            # Check if there is an active mission for that robot
            robot = mission['metadata']['labels']['cloudrobotics.com/robot-name']
            if self._active_missions.get(robot) is None:
                # On upstart try to start RUNNING mission first
                if self._controller_upstart is True:
                    status_to_run = [
                        RobcoMissionStates.STATE_RUNNING, RobcoMissionStates.STATE_ACCEPTED]
                else:
                    status_to_run = [RobcoMissionStates.STATE_ACCEPTED]

                status = mission.get('status', {})
                if status.get('status') in status_to_run:
                    # Run mission in an own thread
                    self._active_missions[robot] = deepcopy(mission)
                    threading.Thread(
                        target=self.run_mission, args=(robot,), daemon=True).start()

        # After missions are processed for the first time, controller is not in upstart
        # mode anymore
        if missions:
            self._controller_upstart = False

    def run_mission(self, robot: str) -> None:
        """Run a mission with all its actions."""
        cls = self.__class__
        if not self._active_missions[robot]:
            _LOGGER.error('No active mission for robot %s', robot)
            return

        name = self._active_missions[robot]['metadata']['name']

        # Update status, that mission is running now
        if self._active_missions[
                robot].get('status', {}).get('status') != RobcoMissionStates.STATE_RUNNING:
            _LOGGER.info('Starting mission %s on robot %s', name, robot)
            self._active_missions[robot]['status']['status'] = RobcoMissionStates.STATE_RUNNING
            self._active_missions[robot][
                'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc).isoformat()
            self.update_cr_status(name, self._active_missions[robot]['status'])
        elif not self._active_missions[robot].get('status'):
            _LOGGER.info('Starting mission %s on robot %s', name, robot)
            self._active_missions[robot]['status'] = cls.m_status_templ.copy()
            self._active_missions[robot]['status']['status'] = RobcoMissionStates.STATE_RUNNING
            self._active_missions[robot][
                'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc).isoformat()
            self.update_cr_status(name, self._active_missions[robot]['status'])
        else:
            _LOGGER.info('Resuming mission %s on robot %s', name, robot)

        # Run all actions of mission
        try:
            actions = self._active_missions[robot]['spec']['actions']
        except KeyError:
            # Update status, that mission failed
            self._active_missions[robot]['status']['status'] = RobcoMissionStates.STATE_FAILED
            self._active_missions[robot][
                'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc).isoformat()
            self._active_missions[robot][
                'status']['message'] = 'Mission {} aborted - no actions attribute in CR'.format(
                    name)
            self.update_cr_status(name, self._active_missions[robot]['status'])
            # quit
            self._active_missions.pop(robot, None)
            return

        for i, action in enumerate(actions):
            # Get task ID from FetchCore if existing in CR
            try:
                task_id = self._active_missions[robot]['status']['taskids'][i]
            except IndexError:
                task_id = None

            if action.get('moveToNamedPosition'):
                result = self.run_action_movetonamedposition(
                    robot, action['moveToNamedPosition']['targetName'], task_id)
            elif action.get('getTrolley'):
                result = self.run_action_gettrolley(
                    robot, action['getTrolley']['dockName'], task_id)
            elif action.get('returnTrolley'):
                result = self.run_action_returntrolley(
                    robot, action['returnTrolley']['dockName'], task_id)
            else:
                # Not implemented - waiting 10 seconds
                time.sleep(10)
                result = RobcoMissionStates.STATE_SUCCEEDED

            if result in [RobcoMissionStates.STATE_FAILED, RobcoMissionStates.STATE_CANCELED]:
                # Update status, that mission failed
                self._active_missions[robot]['status']['status'] = result
                self._active_missions[robot][
                    'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc).isoformat()
                self.update_cr_status(name, self._active_missions[robot]['status'])
                # quit
                self._active_missions.pop(robot, None)
                _LOGGER.error('Mission %s on robot %s ended in state %s', name, robot, result)
                return

        # each action ran successfully
        # Update status, that mission succeeded
        self._active_missions[robot]['status']['status'] = RobcoMissionStates.STATE_SUCCEEDED
        self._active_missions[robot][
            'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                tzinfo=datetime.timezone.utc).isoformat()
        self._active_missions[robot]['status']['activeAction'] = {}
        self.update_cr_status(name, self._active_missions[robot]['status'])
        # quit
        self._active_missions.pop(robot, None)
        _LOGGER.info('Mission %s on robot %s  successfully finished', name, robot)
        return

    def run_action_movetonamedposition(
            self, robot: str, position: str, task_id: Optional[int] = None) -> bool:
        """Run mission moveToNamedPosition on the robot."""
        if not self._active_missions[robot]:
            # No active mission for robot - action failed
            _LOGGER.error('No active mission for robot %s', robot)
            self._active_missions[robot]['status']['message'] = 'Internal error. Check logs.'
            return RobcoMissionStates.STATE_FAILED
        # if there is not FetchCore task ID, create a new task
        if not task_id:
            try:
                task_id = self._fetch_robots.get_robot(robot).move_to_position(position)
            except FetchCapabilityError:
                _LOGGER.ERROR('Robot does not have a MOVE function - mission %s failed')
                return RobcoMissionStates.STATE_FAILED
            except ValueError:
                _LOGGER.ERROR('Position %s is not known - mission %s failed')
                return RobcoMissionStates.STATE_FAILED

            if task_id:
                self._active_missions[robot]['status']['taskids'].append(task_id)
                self._active_missions[robot][
                    'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc).isoformat()
                self.update_cr_status(
                    self._active_missions[robot]['metadata']['name'],
                    self._active_missions[robot]['status'])
            else:
                self._active_missions[robot]['status']['message'] = 'Mission failed'
                return RobcoMissionStates.STATE_FAILED

        status = self._fetch_robots.get_robot(robot).get_task_status(task_id)

        # Wait until movement was successfull or failed
        while status in (RobcoMissionStates.STATE_ACCEPTED, RobcoMissionStates.STATE_RUNNING):
            time.sleep(0.5)
            status = self._fetch_robots.get_robot(robot).get_task_status(task_id)
            # Update status CR when status changes to RUNNING
            if (status != self._active_missions[robot]['status']['status']
                    and status == RobcoMissionStates.STATE_RUNNING):
                self._active_missions[robot]['status']['status'] = status
                self._active_missions[robot][
                    'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc).isoformat()
                self.update_cr_status(
                    self._active_missions[robot]['metadata']['name'],
                    self._active_missions[robot]['status'])

        return status

    def run_action_gettrolley(
            self, robot: str, position: str, task_id: Optional[int] = None) -> bool:
        """Run mission getTrolley on the robot."""
        if not self._active_missions[robot]:
            # No active mission for robot - action failed
            _LOGGER.error('No active mission for robot %s', robot)
            self._active_missions[robot]['status']['message'] = 'Internal error. Check logs.'
            return RobcoMissionStates.STATE_FAILED
        # if there is not FetchCore task ID, create a new task
        if not task_id:
            try:
                task_id = self._fetch_robots.get_robot(robot).get_trolley(position)
            except FetchCapabilityError:
                # BACKUP process for robots with HMI
                _LOGGER.warning(
                    'Robot does not have a ATTACH_CART function - running backup mode NAVIGATE '
                    '+ HMI')
                try:
                    task_id = self._fetch_robots.get_robot(robot).get_return_trolley_backup(
                        position, True)
                except FetchCapabilityError:
                    _LOGGER.ERROR(
                        'Robot does not have the NAVIGATE and HMI_BUTTONS functions - mission %s '
                        'failed')
                    return RobcoMissionStates.STATE_FAILED

            except ValueError:
                _LOGGER.ERROR('Position %s is not known - mission %s failed')
                return RobcoMissionStates.STATE_FAILED

            if task_id:
                self._active_missions[robot]['status']['taskids'].append(task_id)
                self._active_missions[robot][
                    'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc).isoformat()
                self.update_cr_status(
                    self._active_missions[robot]['metadata']['name'],
                    self._active_missions[robot]['status'])
            else:
                self._active_missions[robot]['status']['message'] = 'Mission failed'
                return RobcoMissionStates.STATE_FAILED

        status = self._fetch_robots.get_robot(robot).get_task_status(task_id)

        # Wait until movement was successfull or failed
        while status in (RobcoMissionStates.STATE_ACCEPTED, RobcoMissionStates.STATE_RUNNING):
            time.sleep(0.5)
            status = self._fetch_robots.get_robot(robot).get_task_status(task_id)
            # Update status CR when status changes to RUNNING
            if (status != self._active_missions[robot]['status']['status']
                    and status == RobcoMissionStates.STATE_RUNNING):
                self._active_missions[robot]['status']['status'] = status
                self._active_missions[robot][
                    'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc).isoformat()
                self.update_cr_status(
                    self._active_missions[robot]['metadata']['name'],
                    self._active_missions[robot]['status'])

        return status

    def run_action_returntrolley(
            self, robot: str, position: str, task_id: Optional[int] = None) -> bool:
        """Run mission returnTrolley on the robot."""
        if not self._active_missions[robot]:
            # No active mission for robot - action failed
            _LOGGER.error('No active mission for robot %s', robot)
            self._active_missions[robot]['status']['message'] = 'Internal error. Check logs.'
            return RobcoMissionStates.STATE_FAILED
        # if there is not FetchCore task ID, create a new task
        if not task_id:
            try:
                task_id = self._fetch_robots.get_robot(robot).return_trolley(position)
            except FetchCapabilityError:
                # BACKUP process for robots with HMI
                _LOGGER.warning(
                    'Robot does not have a DETACH_CART function - running backup mode NAVIGATE '
                    '+ HMI')
                try:
                    task_id = self._fetch_robots.get_robot(robot).get_return_trolley_backup(
                        position, False)
                except FetchCapabilityError:
                    _LOGGER.ERROR(
                        'Robot does not have the NAVIGATE and HMI_BUTTONS functions - mission %s '
                        'failed')
                    return RobcoMissionStates.STATE_FAILED

            except ValueError:
                _LOGGER.ERROR('Position %s is not known - mission %s failed')
                return RobcoMissionStates.STATE_FAILED

            if task_id:
                self._active_missions[robot]['status']['taskids'].append(task_id)
                self._active_missions[robot][
                    'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc).isoformat()
                self.update_cr_status(
                    self._active_missions[robot]['metadata']['name'],
                    self._active_missions[robot]['status'])
            else:
                self._active_missions[robot]['status']['message'] = 'Mission failed'
                return RobcoMissionStates.STATE_FAILED

        status = self._fetch_robots.get_robot(robot).get_task_status(task_id)

        # Wait until movement was successfull or failed
        while status in (RobcoMissionStates.STATE_ACCEPTED, RobcoMissionStates.STATE_RUNNING):
            time.sleep(0.5)
            status = self._fetch_robots.get_robot(robot).get_task_status(task_id)
            # Update status CR when status changes to RUNNING
            if (status != self._active_missions[robot]['status']['status']
                    and status == RobcoMissionStates.STATE_RUNNING):
                self._active_missions[robot]['status']['status'] = status
                self._active_missions[robot][
                    'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc).isoformat()
                self.update_cr_status(
                    self._active_missions[robot]['metadata']['name'],
                    self._active_missions[robot]['status'])

        return status
