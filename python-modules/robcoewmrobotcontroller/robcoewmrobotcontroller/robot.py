#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
#
# This file is part of ewm-cloud-robotics
# (see https://github.com/SAP/ewm-cloud-robotics).
#
# This file is licensed under the Apache Software License, v. 2 except as noted
# otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
#

"""Robot representation."""

import logging

from typing import Optional

import attr

from robcoewmtypes.robot import RobotConfigurationStatus
from robcoewmtypes.statemachine_config import RobotEWMConfig
from robcoewmtypes.warehouseorder import WarehouseOrderCRDSpec

from .ordercontroller import OrderHandler
from .missioncontroller import MissionController
from .robotconfigcontroller import RobotConfigurationController
from .statemachine import RobotEWMMachine, WhoIdentifier

_LOGGER = logging.getLogger(__name__)


@attr.s
class ValidStateRestore:
    """Validated state to restore state machine."""

    state: RobotConfigurationStatus = attr.ib(
        validator=attr.validators.instance_of(RobotConfigurationStatus))
    warehouseorder: WarehouseOrderCRDSpec = attr.ib(
        default=None, validator=attr.validators.optional(
            attr.validators.instance_of(WarehouseOrderCRDSpec)))
    sub_warehouseorder: WarehouseOrderCRDSpec = attr.ib(
        default=None, validator=attr.validators.optional(
            attr.validators.instance_of(WarehouseOrderCRDSpec)))


class EWMRobot:
    """The EWM robot representation."""

    def __init__(self, robot_config: RobotConfigurationController, mission_api: MissionController,
                 order_handler: OrderHandler) -> None:
        """Construct."""
        # Robot Mission API
        self.mission_api = mission_api
        # Robot Configuration
        self.robot_config = robot_config
        # Order handler
        self.orderhandler = order_handler

        # Robot state machine
        self._init_robot_state_machine()

    def _init_robot_state_machine(self) -> None:
        """Initialize robot's state machine."""
        valid_state = self._get_validated_state_restore()
        if valid_state:
            # Restore a previous state machine state
            # Init state machine in specific state
            self.state_machine = RobotEWMMachine(
                self.robot_config, self.mission_api, self.orderhandler,
                initial=valid_state.state.statemachine)
            # Restore state machine attributes
            self.state_machine.active_mission = valid_state.state.mission
            if valid_state.state.who:
                _LOGGER.info(
                    'Restore state machine: WarehouseOrder %s, WarehouseTask %s, State %s, Mission'
                    ' %s', valid_state.state.who, valid_state.state.tanum,
                    valid_state.state.statemachine, valid_state.state.mission)
                who_ident = WhoIdentifier(valid_state.state.lgnum, valid_state.state.who)
                self.state_machine.warehouseorders[who_ident] = valid_state.warehouseorder
                self.state_machine.active_who = valid_state.warehouseorder.data
                if valid_state.state.subwho:
                    sub_who_ident = WhoIdentifier(
                        valid_state.state.lgnum, valid_state.state.subwho)
                    self.state_machine.sub_warehouseorders[
                        sub_who_ident] = valid_state.sub_warehouseorder
                    self.state_machine.active_sub_who = valid_state.sub_warehouseorder.data
                    # Availability of sub_warehouse order checked before
                    for wht in valid_state.sub_warehouseorder.data.warehousetasks:
                        if wht.tanum == valid_state.state.tanum:
                            self.state_machine.active_wht = wht
                            break

                # If no active warehouse task found yet, search in warehouse order
                if not self.state_machine.active_wht:
                    # Availability of warehouse order checked before
                    for wht in valid_state.warehouseorder.data.warehousetasks:
                        if wht.tanum == valid_state.state.tanum:
                            self.state_machine.active_wht = wht
                            break
            else:
                _LOGGER.info(
                    'Restore state machine: State %s, Mission %s', valid_state.state.statemachine,
                    valid_state.state.mission)
        else:
            # Initialize a fresh state machine
            _LOGGER.info('Initialize fresh state machine')
            self.state_machine = RobotEWMMachine(
                self.robot_config, self.mission_api, self.orderhandler)
            self.state_machine.start_fresh_machine()

        # Connect state machine to external events
        _LOGGER.info('Connect state machine to CR handler')
        self.state_machine.connect_external_events()

    def _get_validated_state_restore(self) -> Optional[ValidStateRestore]:
        """Return robot state if it is valid."""
        state_restore = self.robot_config.get_robot_state()
        if not state_restore:
            _LOGGER.info('No state to restore')
            return None
        if not state_restore.statemachine:
            _LOGGER.info('No state to restore')
            return None
        if state_restore.statemachine in RobotEWMConfig.idle_states:
            _LOGGER.info('Robot is in an idle state, which is not restored.')
            return None

        # Check if mission custom resource still exists
        if state_restore.mission:
            if self.mission_api.handler.check_cr_exists(state_restore.mission) is False:
                state_restore.mission = ''

        valid_state = ValidStateRestore(state_restore)

        is_valid = True
        if state_restore:
            # If there are no CRs for warehouse order and sub warehouse order, state is invalid
            if state_restore.who:
                warehouseorder = self.orderhandler.get_warehouseorder(
                    state_restore.lgnum, state_restore.who, self.robot_config.robot_name)
                if not warehouseorder:
                    _LOGGER.error(
                        'No CR for warehouse order %s in warehouse %s', state_restore.who,
                        state_restore.lgnum)
                    is_valid = False
                else:
                    valid_state.warehouseorder = warehouseorder
            if state_restore.subwho:
                sub_warehouseorder = self.orderhandler.get_warehouseorder(
                    state_restore.lgnum, state_restore.subwho, self.robot_config.robot_name)
                if not sub_warehouseorder:
                    _LOGGER.error(
                        'No CR for sub warehouse order %s in warehouse %s', state_restore.subwho,
                        state_restore.lgnum)
                    is_valid = False
                else:
                    valid_state.sub_warehouseorder = sub_warehouseorder
            if (state_restore.mission == ''
                    and state_restore.statemachine not in RobotEWMConfig.idle_states
                    and state_restore.statemachine not in RobotEWMConfig.error_states):
                _LOGGER.error(
                    'State machine is state %s which is not an idle or error state, but does not '
                    'have a running mission', state_restore.statemachine)
                is_valid = False
        else:
            is_valid = False

        if is_valid:
            return valid_state
        else:
            _LOGGER.error('State from CR is not valid - ignoring it')
            return None
