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

"""Templates for robot APIs."""

import logging

from typing import Optional

from robcoewmtypes.robot import RobotMission
from robcoewmtypes.warehouse import StorageBin
from robcoewmtypes.warehouseorder import WarehouseTask

_LOGGER = logging.getLogger(__name__)


class RobotMissionAPI:
    """Template class to define robot APIs."""

    def api_cancel_mission(self, name: str) -> bool:
        """Cancel a mission."""
        raise NotImplementedError

    def api_moveto_storagebin_position(
            self, storagebin: StorageBin) -> RobotMission:
        """Move robot to a storage bin position of the map."""
        raise NotImplementedError

    def api_charge_robot(self) -> RobotMission:
        """Charge robot at the charging position."""
        raise NotImplementedError

    def api_moveto_charging_position(self) -> RobotMission:
        """Move robot to a charging position of the map."""
        raise NotImplementedError

    def api_moveto_staging_position(self) -> RobotMission:
        """Move robot to a staging position of the map."""
        raise NotImplementedError

    def api_return_charge_state(self, mission: RobotMission) -> RobotMission:
        """Return state of a charge mission."""
        raise NotImplementedError

    def api_return_move_state(self, mission: RobotMission) -> RobotMission:
        """Return state of a move mission."""
        raise NotImplementedError

    def api_return_load_state(self, mission: RobotMission) -> RobotMission:
        """Return state of a load mission."""
        raise NotImplementedError

    def api_load_unload(self, wht: WarehouseTask) -> RobotMission:
        """Load or unload HU of a warehouse task."""
        raise NotImplementedError

    def api_check_state_ok(self) -> bool:
        """Check if robot is in state ok."""
        raise NotImplementedError

    def api_get_battery_percentage(self) -> float:
        """Get battery level from robot."""
        raise NotImplementedError

    def api_is_trolley_attached(self) -> Optional[bool]:
        """Get status if there is s a trolley attached to the robot."""
        raise NotImplementedError
