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

"""Representation of a dummy robot in RobCo."""

import logging
import datetime
import os

import random

from typing import Tuple, Dict

from robcoewmtypes.robot import RobotMission

_LOGGER = logging.getLogger(__name__)


class RobcoMissionStates(RobotMission):
    """Mission states in RobCo."""

    @staticmethod
    def get_robco_state(state: str, message: str) -> str:
        """Get RobCo state from dummy state and message."""
        cls = __class__  # type: ignore  # pylint: disable=undefined-variable
        if state == 'Pending':
            return cls.STATE_ACCEPTED
        elif state == 'Executing':
            return cls.STATE_RUNNING
        elif state == 'Done':
            return cls.STATE_SUCCEEDED
        else:
            raise ValueError('State {} is unknown'.format(state))


class DummyRobot:
    """Representation of one single dummy robot."""

    mission_mapping = {
        'moveToNamedPosition': 'mission_moveToNamedPosition',
        'charge': 'mission_charge',
        'getTrolley': 'mission_getTrolley',
        'returnTrolley': 'mission_returnTrolley'
        }

    POSTYPE_DOCK = 'dock'
    POSTYPE_CHARGER = 'charger'
    POSTYPE_POSITION = 'position'

    def __init__(self) -> None:
        """Construct."""
        self.battery_percentage = 1.0
        self.state = 'UNDEFINED'
        self.last_state_change = '1970-01-01T00:00:00.000Z'
        self.trolley_attached = False
        self.active_map = None
        self.get_mission_state_counter: Dict[int, int] = {}
        self.next_mission_id = 0

        # Init remaining attributes from environment variables
        envvar = self.init_robot_fromenv()
        self.robco_robot_name = envvar['ROBCO_ROBOT_NAME']

    def init_robot_fromenv(self) -> Dict:
        """Initialize EWM Robot from environment variables."""
        # Read environment variables
        envvar = {}
        envvar['ROBCO_ROBOT_NAME'] = os.environ.get('ROBCO_ROBOT_NAME')
        # Check if complete
        for var, val in envvar.items():
            if val is None:
                raise ValueError(
                    'Environment variable "{}" is not set'.format(var))

        return envvar

    def get_mission_state(self, mission: int) -> Tuple[str, str]:
        """Get the state of a mission of mission queue."""
        if mission not in self.get_mission_state_counter:
            self.get_mission_state_counter[mission] = 0

        self.get_mission_state_counter[mission] += 1

        if self.get_mission_state_counter[mission] >= 30:
            mission_state = RobcoMissionStates.get_robco_state('Done', 'Done')
        elif self.get_mission_state_counter[mission] >= 10:
            mission_state = RobcoMissionStates.get_robco_state('Executing', 'Executing')
        else:
            mission_state = RobcoMissionStates.get_robco_state('Pending', 'Pending')

        return (mission_state, '')

    def get_trolley(self, dock_name: str) -> int:
        """Go to the docking position and get a trolley there."""
        self.next_mission_id += 1
        return self.next_mission_id

    def return_trolley(self, dock_name: str) -> int:
        """Go to the docking position and return robot's trolley there."""
        self.next_mission_id += 1
        return self.next_mission_id

    def moveto_named_position(self, target_name: str) -> int:
        """Move robot to a named position of the map."""
        self.next_mission_id += 1
        return self.next_mission_id

    def charge_robot(
            self, charger_name: str, threshold_battery: float, target_battery: float) -> int:
        """Charge robot at the charging position."""
        self.next_mission_id += 1
        return self.next_mission_id

    def update(self) -> None:
        """Update dummy robot."""
        self.battery_percentage = 90 + random.random() * 10
        self.last_state_change = datetime.datetime.utcnow().replace(
            tzinfo=datetime.timezone.utc).isoformat()
        self.state = 'AVAILABLE'
