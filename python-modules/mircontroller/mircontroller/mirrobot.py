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

"""Representation of a MiR robot in RobCo."""

import logging
import datetime
import time
import os
import math

from typing import Tuple
from requests import RequestException
from prometheus_client import Gauge, Histogram

from robcoewmtypes.robot import RobotMission

from .mirapi import MiRInterface, HTTPstatusCodeFailed

_LOGGER = logging.getLogger(__name__)


class RobcoRobotStates:
    """Robot states in RobCo."""

    STATE_UNDEFINED = 'UNDEFINED'
    STATE_UNAVAILABLE = 'UNAVAILABLE'
    STATE_AVAILABLE = 'AVAILABLE'
    STATE_EMERGENCY_STOP = 'EMERGENCY_STOP'
    STATE_ERROR = 'ERROR'

    MIR_TO_ROBCO = {
        1: STATE_UNAVAILABLE,       # MIR_STATE_STARTING
        2: STATE_UNAVAILABLE,       # MIR_STATE_SHUTTING_DOWN
        3: STATE_AVAILABLE,         # MIR_STATE_READY_FOR_MISSION
        4: STATE_UNAVAILABLE,       # MIR_STATE_PAUSE
        5: STATE_AVAILABLE,         # MIR_STATE_IN_TRANSIT
        6: STATE_UNAVAILABLE,       # MIR_STATE_ABORTED
        7: STATE_AVAILABLE,         # MIR_STATE_GOAL_REACHED
        8: STATE_AVAILABLE,         # MIR_STATE_DOCKED
        9: STATE_AVAILABLE,         # MIR_STATE_DOCKING
        10: STATE_EMERGENCY_STOP,   # MIR_STATE_EMERGENCY_STOP
        11: STATE_UNAVAILABLE,      # MIR_STATE_MANUAL_CONTROL
        12: STATE_ERROR             # MIR_STATE_ERROR
        }


class RobcoMissionStates(RobotMission):
    """Mission states in RobCo."""

    @staticmethod
    def get_robco_state(mir_state: str, message: str) -> str:
        """Get RobCo state from MiR state and message."""
        cls = __class__  # type: ignore # pylint: disable=undefined-variable
        if mir_state == 'Pending':
            return cls.STATE_ACCEPTED
        elif mir_state == 'Executing':
            return cls.STATE_RUNNING
        elif mir_state == 'Done':
            return cls.STATE_SUCCEEDED
        elif mir_state in ['Aborted', 'Abort']:
            if message == 'Aborted - User Request':
                return cls.STATE_CANCELED
            else:
                return cls.STATE_FAILED
        else:
            raise ValueError('State {} is unknown'.format(mir_state))


class MiRRobot:
    """Representation of one single MiR robot."""

    mission_mapping = {
        'moveToNamedPosition': 'mission_moveToNamedPosition',
        'charge': 'mission_charge',
        'getTrolley': 'mission_getTrolley',
        'returnTrolley': 'mission_returnTrolley'
        }

    POSTYPE_DOCK = 'dock'
    POSTYPE_CHARGER = 'charger'
    POSTYPE_POSITION = 'position'

    # Prometheus logging
    BUCKETS = (5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0, 3600.0, '+Inf')

    p_angular_speed = Gauge(
        'sap_robot_angular_speed', 'Robot\'s angular speed (rad/s)', ['robot'])
    p_linear_speed = Gauge(
        'sap_robot_linear_speed', 'Robot\'s linear speed (m/s)', ['robot'])
    p_battery_percentage = Gauge(
        'sap_robot_battery_percentage', 'Robot\'s battery percentage (%)', ['robot'])
    p_state = Histogram(
        'sap_robot_state', 'Robot\'s state', ['robot', 'state'], buckets=BUCKETS)
    p_position_x = Gauge('sap_robot_position_x', 'Robot\'s X position', ['robot'])
    p_position_y = Gauge('sap_robot_position_y', 'Robot\'s Y position', ['robot'])
    p_orientation = Gauge(
        'sap_robot_position_orientation', 'Robot\'s orientation in degree', ['robot'])
    p_theta = Gauge('sap_robot_position_theta', 'Robot\'s orientation in rad', ['robot'])

    def __init__(self, mir_api: MiRInterface) -> None:
        """Construct."""
        self._mir_api = mir_api
        self.battery_percentage = 1.0
        self.state = RobcoRobotStates.STATE_UNDEFINED
        self.last_state_change = '1970-01-01T00:00:00.000Z'
        self.last_state_change_ts = time.time()
        self.trolley_attached = False
        self.active_map = ''
        self.angular_speed = 0.0
        self.linear_speed = 0.0
        self.pos_x = 0.0
        self.pos_y = 0.0
        self.pos_orientation = 0.0
        self.pos_theta = 0.0
        # Error handling
        self.error_resetted = False
        # Init attributes from environment variables
        self.init_robot_fromenv()

    def init_robot_fromenv(self) -> None:
        """Initialize EWM Robot from environment variables."""
        # Read environment variables
        envvar = {}
        envvar['ROBCO_ROBOT_NAME'] = os.environ.get('ROBCO_ROBOT_NAME')
        envvar['PLC_TROLLEY_ATTACHED'] = os.environ.get('PLC_TROLLEY_ATTACHED')
        # Check if complete
        for var, val in envvar.items():
            if val is None:
                raise ValueError(
                    'Environment variable "{}" is not set'.format(var))

        self.robco_robot_name = envvar['ROBCO_ROBOT_NAME']
        self.trolley_attached_plc = int(envvar['PLC_TROLLEY_ATTACHED'])  # type: ignore

    def cancel_mission(self, mission: str) -> bool:
        """Cancel a mission from mission queue."""
        # POST request
        try:
            self._mir_api.http_delete('mission_queue/{qm}'.format(qm=mission))
        except HTTPstatusCodeFailed:
            return False

        return True

    def get_mission_active_action(self, mission: int) -> str:
        """Get active action of a mission."""
        # Get actions from REST interface
        http_resp_actions = self._mir_api.http_get(
            'mission_queue/{qm}/actions'.format(qm=mission))

        json_resp_actions = http_resp_actions.json()
        # Get latest action
        latest_action = 0
        for action in json_resp_actions:
            latest_action = max(latest_action, action['id'])

        if latest_action != 0:
            # Get action details from REST interface
            http_resp_action = self._mir_api.http_get(
                'mission_queue/{qm}/actions/{act}'.format(qm=mission, act=latest_action))
            # Only if HTTP request has a valid response
            if http_resp_action:
                json_resp_action = http_resp_action.json()
                if json_resp_action['action_type'] in [
                        'docking', 'pickup_shelf', 'place_shelf']:
                    return RobotMission.ACTION_DOCKING
                elif json_resp_action['action_type'] == 'move':
                    return RobotMission.ACTION_MOVING

        return ''

    def get_mission_state(self, mission: int) -> Tuple[str, str]:
        """Get the state of a mission of mission queue."""
        # Get data from REST interface
        http_resp = self._mir_api.http_get('mission_queue/{qm}'.format(qm=mission))

        json_resp = http_resp.json()
        mission_state = RobcoMissionStates.get_robco_state(
            json_resp['state'], json_resp['message'])
        return (mission_state, json_resp['message'])

    def mission_guid_by_name(self, mission: str) -> str:
        """Get the GUID of a mission by its name."""
        # Get data from REST interface
        http_resp = self._mir_api.http_get('missions')

        # Get position GUID from response
        for item in http_resp.json():
            if item['name'] == mission:
                return item['guid']

        return ''

    def position_guid_by_name(self, position: str, map_guid: str, pos_type: str) -> str:
        """Get the GUID of a position by its name."""
        cls = self.__class__

        if pos_type == cls.POSTYPE_DOCK:
            type_ids = [1, 5, 9, 11]
        elif pos_type == cls.POSTYPE_CHARGER:
            type_ids = [7]
        elif pos_type == cls.POSTYPE_POSITION:
            type_ids = [0, 42]
        else:
            raise ValueError('Position type "{}" is not known'.format(pos_type))

        # Get data from REST interface
        http_resp = self._mir_api.http_get('positions')

        # Get position GUID from response
        for item in http_resp.json():
            if (item['map'] == map_guid
                    and item['name'] == position
                    and item['type_id'] in type_ids):
                return item['guid']

        # Otherwise ERROR
        _LOGGER.error('Error getting "position guid" for "%s"', position)
        return ''

    def get_trolley(self, dock_name: str) -> int:
        """Go to the docking position and get a trolley there."""
        cls = self.__class__
        # Get relevant parameters
        pos_guid = self.position_guid_by_name(dock_name, self.active_map, cls.POSTYPE_DOCK)
        mis_guid = self.mission_guid_by_name(cls.mission_mapping['getTrolley'])

        # Prepare POST body for request
        jsonbody = {
            'mission_id': mis_guid,
            'parameters': [{'input_name': 'dock_name', 'value': pos_guid}],
            'message': 'Get trolley at {}'.format(dock_name),
            'priority': 0
            }

        http_resp = self._mir_api.http_post('mission_queue', jsonbody=jsonbody)

        resp_json = http_resp.json()
        return resp_json['id']

    def return_trolley(self, dock_name: str) -> int:
        """Go to the docking position and return robot's trolley there."""
        cls = self.__class__
        # Get relevant parameters
        pos_guid = self.position_guid_by_name(dock_name, self.active_map, cls.POSTYPE_DOCK)
        mis_guid = self.mission_guid_by_name(cls.mission_mapping['returnTrolley'])

        # Prepare POST body for request
        jsonbody = {
            'mission_id': mis_guid,
            'parameters': [{'input_name': 'dock_name', 'value': pos_guid}],
            'message': 'Return trolley to {}'.format(dock_name),
            'priority': 0
            }

        http_resp = self._mir_api.http_post('mission_queue', jsonbody=jsonbody)

        resp_json = http_resp.json()
        return resp_json['id']

    def moveto_named_position(self, target_name: str) -> int:
        """Move robot to a named position of the map."""
        cls = self.__class__
        # Get relevant parameters
        pos_guid = self.position_guid_by_name(target_name, self.active_map, cls.POSTYPE_POSITION)
        mis_guid = self.mission_guid_by_name(cls.mission_mapping['moveToNamedPosition'])

        # Prepare POST body for request
        jsonbody = {
            'mission_id': mis_guid,
            'parameters': [{'input_name': 'target_name', 'value': pos_guid}],
            'message': 'Move to position {}'.format(target_name),
            'priority': 0
            }

        http_resp = self._mir_api.http_post('mission_queue', jsonbody=jsonbody)

        resp_json = http_resp.json()
        return resp_json['id']

    def charge_robot(
            self, charger_name: str, threshold_battery: float, target_battery: float) -> int:
        """Charge robot at the charging position."""
        cls = self.__class__
        # Get relevant parameters
        pos_guid = self.position_guid_by_name(charger_name, self.active_map, cls.POSTYPE_CHARGER)
        mis_guid = self.mission_guid_by_name(cls.mission_mapping['charge'])

        # Prepare POST body for request
        jsonbody = {
            'mission_id': mis_guid,
            'parameters': [
                {'input_name': 'charger_name', 'value': pos_guid},
                {'input_name': 'threshold_battery', 'value': threshold_battery},
                {'input_name': 'target_battery', 'value': target_battery}
                ],
            'message': 'Charging robot until battery reaches {}%'.format(target_battery),
            'priority': 0
            }

        http_resp = self._mir_api.http_post('mission_queue', jsonbody=jsonbody)

        resp_json = http_resp.json()
        return resp_json['id']

    def update(self) -> None:
        """Update entire MiR robot."""
        self.update_robot_status()
        self.update_trolley_attached()

    def update_robot_status(self) -> None:
        """Update robot status."""
        # Get data from REST interface
        try:
            http_resp = self._mir_api.http_get('status')
        except RequestException:
            self.state = RobcoRobotStates.STATE_UNAVAILABLE
            _LOGGER.error('Error when updating robot status.')
        else:
            json_resp = http_resp.json()
            self.active_map = '/v2.0.0/maps/{id}'.format(id=json_resp['map_id'])
            self.battery_percentage = json_resp['battery_percentage']
            self.angular_speed = json_resp['velocity']['angular']
            self.linear_speed = json_resp['velocity']['linear']
            self.pos_x = json_resp['position']['x']
            self.pos_y = json_resp['position']['y']
            self.pos_orientation = json_resp['position']['orientation']
            self.pos_theta = math.radians(self.pos_orientation)
            if self.state != json_resp['state_id']:
                self.p_state.labels(  # pylint: disable=no-member
                    robot=self.robco_robot_name, state=self.state).observe(
                        time.time() - self.last_state_change_ts)
                self.last_state_change_ts = time.time()
                self.last_state_change = datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc).isoformat()

            self.state = RobcoRobotStates.MIR_TO_ROBCO.get(
                json_resp['state_id'], RobcoRobotStates.STATE_UNDEFINED)

            # Update prometheus metrics
            self.update_prometheus_metrics()

    def update_prometheus_metrics(self) -> None:
        """Update prometheus metrics for the robot."""
        self.p_battery_percentage.labels(  # pylint: disable=no-member
            robot=self.robco_robot_name).set(self.battery_percentage)
        self.p_angular_speed.labels(  # pylint: disable=no-member
            robot=self.robco_robot_name).set(self.angular_speed)
        self.p_linear_speed.labels(  # pylint: disable=no-member
            robot=self.robco_robot_name).set(self.linear_speed)
        self.p_position_x.labels(  # pylint: disable=no-member
            robot=self.robco_robot_name).set(self.pos_x)
        self.p_position_y.labels(  # pylint: disable=no-member
            robot=self.robco_robot_name).set(self.pos_y)
        self.p_orientation.labels(  # pylint: disable=no-member
            robot=self.robco_robot_name).set(self.pos_orientation)
        self.p_theta.labels(  # pylint: disable=no-member
            robot=self.robco_robot_name).set(self.pos_theta)

    def update_trolley_attached(self) -> None:
        """Update trolley attached attribute."""
        # Get data from REST interface
        try:
            http_resp = self._mir_api.http_get(
                'registers/{id}'.format(id=self.trolley_attached_plc))
        except RequestException:
            _LOGGER.error('Error when updating trolley attached attribute.')
        else:
            self.trolley_attached = not http_resp.json()['value'] == 0

    def unpause_robot_reset_error(self) -> None:
        """Unpause robot and reset error on MiR."""
        state_id = None

        # Get data from REST interface
        try:
            http_resp = self._mir_api.http_get('status')
        except RequestException:
            _LOGGER.error('Error when resetting error, not able to get status')
            state_id = None
        else:
            state_id = http_resp.json()['state_id']

        # Check if error raised by MiR MissionController module
        if state_id == 12:
            reset = False
            errors = http_resp.json()['errors']
            # Reset if there are only errors raised by MissionController module
            for error in errors:
                if error.get('module') == 'MissionController':
                    _LOGGER.info('Error raised by MiR MissionController module occurred.')
                    reset = True
                else:
                    reset = False
                    self.error_resetted = False
                    break

            if reset:
                ws_msg = {
                    'op': 'call_service',
                    'service': '/mirsupervisor/requestErrorReset'}
                _LOGGER.info('Reset error request sent via websocket')
                try:
                    self._mir_api.send_ws_message(ws_msg)
                except RequestException:
                    _LOGGER.error('Error state could not been reset')
                else:
                    _LOGGER.info('Error successfully reset')
                    self.error_resetted = True
                    # Assume state is "pause" after reset
                    state_id = 4

        # If mission queue is in state 4 (pause) and error was resetted
        if state_id == 4 and self.error_resetted:
            # Set robot state to 3 to continue the queued missions
            json_body = {'state_id': 3}
            try:
                self._mir_api.http_put('status', jsonbody=json_body)
            except RequestException:
                _LOGGER.error('Mission could not be continued')
            else:
                self.error_resetted = False
                _LOGGER.info('Mission continued')
