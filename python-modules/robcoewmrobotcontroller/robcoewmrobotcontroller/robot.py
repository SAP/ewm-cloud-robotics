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

"""Robot representation."""

import logging
import time

from typing import Any, Callable, Dict, Optional

from cattr import structure, unstructure
from retrying import retry

from robcoewmtypes.helper import get_robcoewmtype, create_robcoewmtype_str
from robcoewmtypes.robot import RequestFromRobot, RobotMission, RobotConfigurationStatus
from robcoewmtypes.warehouseorder import WarehouseOrder, WarehouseTask, ConfirmWarehouseTask

from .ordercontroller import OrderController
from .robot_api import RobotMissionAPI
from .robotconfigcontroller import RobotConfigurationController
from .robotrequestcontroller import RobotRequestController
from .statemachine import RobotEWMMachine, WhoIdentifier

_LOGGER = logging.getLogger(__name__)


def convert_warehouseorder(data: Any) -> WarehouseOrder:
    """Convert input to WarehouseOrder data type if neccessary."""
    if isinstance(data, WarehouseOrder) or data is None:
        return data
    else:
        return structure(data, WarehouseOrder)


class EWMRobot:
    """The EWM robot representation."""

    VALID_QUEUE_MSG_TYPES = (WarehouseOrder,)

    def __init__(self, mission_api: RobotMissionAPI, robot_config: RobotConfigurationController,
                 order_controller: OrderController, robot_request: RobotRequestController,
                 confirm_pick: Optional[Callable] = None,
                 confirm_target: Optional[Callable] = None) -> None:
        """Constructor."""
        # Robot Mission API
        self.mission_api = mission_api
        # Robot Configuration
        self.robot_config = robot_config
        # Order Controller
        self.order_controller = order_controller
        # Robot Request controller
        self.robot_request_controller = robot_request

        # Robot state machine
        state_restore = self.get_validated_state_restore()
        if state_restore:
            # Restore a previous state machine state
            # Init state machine in specific state
            self.state_machine = RobotEWMMachine(
                self.robot_config, self.mission_api, self.confirm_warehousetask, self.request_work,
                self.send_warehousetask_error, self.notify_who_completion,
                self.robot_config.save_robot_state, initial=state_restore.statemachine)
            # Restore state machine attributes
            self.state_machine.mission = RobotMission(
                name=state_restore.mission, target_name=state_restore.missiontarget)
            if state_restore.who:
                who_type = state_restore.statemachine[:state_restore.statemachine.rfind('_')]
                _LOGGER.info(
                    'Restore state machine: WarehouseOrderType %s, WarehouseOrder %s, '
                    'WarehouseTask %s, State %s, Mission %s', who_type, state_restore.who,
                    state_restore.tanum, state_restore.statemachine, state_restore.mission)
                warehouseorder = self.order_controller.get_warehouseorder(
                    state_restore.lgnum, state_restore.who)
                self.state_machine.who_type = who_type
                who_ident = WhoIdentifier(state_restore.lgnum, state_restore.who)
                self.state_machine.warehouseorders[who_ident] = warehouseorder
                self.state_machine.active_who = warehouseorder
                if state_restore.subwho:
                    sub_warehouseorder = self.order_controller.get_warehouseorder(
                        state_restore.lgnum, state_restore.subwho)
                    sub_who_ident = WhoIdentifier(
                        state_restore.lgnum, state_restore.subwho)
                    self.state_machine.sub_warehouseorders[
                        sub_who_ident] = sub_warehouseorder
                    self.state_machine.active_sub_who = sub_warehouseorder
                    for wht in sub_warehouseorder.warehousetasks:
                        if wht.tanum == state_restore.tanum:
                            self.state_machine.active_wht = wht
                            break
                else:
                    for wht in warehouseorder.warehousetasks:
                        if wht.tanum == state_restore.tanum:
                            self.state_machine.active_wht = wht
                            break
            else:
                _LOGGER.info(
                    'Restore state machine: State %s, Mission %s', state_restore.statemachine,
                    state_restore.mission)
        else:
            # Initialize a fresh state machine
            _LOGGER.info('Initialize fresh state machine')
            self.state_machine = RobotEWMMachine(
                self.robot_config, self.mission_api, self.confirm_warehousetask, self.request_work,
                self.send_warehousetask_error, self.notify_who_completion,
                self.robot_config.save_robot_state)
        # Confirmation callables for Pick, Pack and Pass
        if confirm_pick:
            self.confirm_pick = confirm_pick
        else:
            self.confirm_pick = self.confirm_false
        if confirm_target:
            self.confirm_target = confirm_target
        else:
            self.confirm_target = self.confirm_false
        # Timestamp for last time a request work was sent
        self._requested_work_time = None
        # Timestamp when robot was working for the last time
        self.last_time_working = time.time()
        self.idle_time_start = 0
        # Number of failed status updates
        self._failed_status_updates = 0
        # Robot is at staging position
        self.at_staging_position = False

    def get_validated_state_restore(self) -> Optional[RobotConfigurationStatus]:
        """Return robot state if it is valid."""
        state_restore = self.robot_config.get_robot_state()

        valid_state = True
        if state_restore:
            # If there are no CRs for warehouse order and sub warehouse order, state is invalid
            if state_restore.who:
                warehouseorder = self.order_controller.get_warehouseorder(
                    state_restore.lgnum, state_restore.who)
                if not warehouseorder:
                    _LOGGER.error(
                        'No CR for warehouse order %s in warehouse %s', state_restore.who,
                        state_restore.lgnum)
                    valid_state = False
            if state_restore.subwho:
                sub_warehouseorder = self.order_controller.get_warehouseorder(
                    state_restore.lgnum, state_restore.subwho)
                if not sub_warehouseorder:
                    _LOGGER.error(
                        'No CR for sub warehouse order %s in warehouse %s', state_restore.subwho,
                        state_restore.lgnum)
                    valid_state = False

        if valid_state:
            return state_restore
        else:
            _LOGGER.error('State from CR is not valid - ignoring it')
            return None

    def queue_callback(self, dtype: str, data: Dict) -> None:
        """Process robot order queue messages."""
        cls = self.__class__
        # Get robco ewm data classes
        try:
            robcoewmtype = get_robcoewmtype(dtype)
        except TypeError as err:
            _LOGGER.error(
                'Message type "%s" is invalid - %s - message SKIPPED: %s', dtype, err, data)
            return
        # Convert message data to robcoewmtypes data classes
        robocoewmdata = structure(data, robcoewmtype)

        # if data set is not a list yet, convert it for later processing
        if not isinstance(robocoewmdata, list):
            robocoewmdata = [robocoewmdata]

        # Check if datasets have a supported type before starting to process
        valid_robcoewmdata = []
        for dataset in robocoewmdata:
            if isinstance(dataset, cls.VALID_QUEUE_MSG_TYPES):
                valid_robcoewmdata.append(dataset)
            else:
                _LOGGER.error(
                    'Dataset includes an unsupported type: "%s". Dataset SKIPPED: %s',
                    type(dataset), dataset)

        # Process the datasets
        for dataset in valid_robcoewmdata:
            if isinstance(dataset, WarehouseOrder):
                self.state_machine.update_warehouseorder(warehouseorder=dataset)

    def robotrequest_callback(self, dtype: str, name: str, custom_res: Dict) -> None:
        """Process robotrequest messages."""
        status = custom_res.get('status', {})
        if status.get('data'):
            # Get robco ewm data classes
            try:
                robcoewmtype = get_robcoewmtype(dtype)
            except TypeError as err:
                _LOGGER.error(
                    'Message type "%s" is invalid - %s - message SKIPPED: %s',
                    dtype, err, status.get('data'))
                return
            # Convert message data to robcoewmtypes data classes
            robocoewmdata = structure(status['data'], robcoewmtype)

            if self.state_machine.state == 'MoveHU_waitingForErrorRecovery':
                who = self.state_machine.active_wht.who
                if robocoewmdata.notifywhocompletion == who:
                    _LOGGER.info(
                        'Warehouse order %s was confirmed in EWM - cancel it on the robot to '
                        'proceed', who)
                    self.state_machine.cancel_warehouseorder()

    @staticmethod
    def confirm_false(wht: WarehouseTask) -> bool:
        """Confirm Pick, Pack and Pass with False."""
        return False

    @retry(wait_fixed=100)
    def confirm_warehousetask(self, wht: WarehouseTask, enforce_first_conf: bool = False) -> None:
        """Confirm warehouse task."""
        confirmations = []
        clear_progress = False
        if wht.vlpla or enforce_first_conf:
            confirmation = ConfirmWarehouseTask(
                lgnum=wht.lgnum, tanum=wht.tanum, rsrc=self.robot_config.rsrc, who=wht.who,
                confirmationnumber=ConfirmWarehouseTask.FIRST_CONF,
                confirmationtype=ConfirmWarehouseTask.CONF_SUCCESS)
            if enforce_first_conf:
                _LOGGER.info('First confirmation enforced - confirming')
            else:
                _LOGGER.info('Source bin reached - confirming')
            confirmations.append(confirmation)
        elif wht.nlpla:
            confirmation = ConfirmWarehouseTask(
                lgnum=wht.lgnum, tanum=wht.tanum, rsrc=self.robot_config.rsrc, who=wht.who,
                confirmationnumber=ConfirmWarehouseTask.SECOND_CONF,
                confirmationtype=ConfirmWarehouseTask.CONF_SUCCESS)
            _LOGGER.info('Target bin reached - confirming')
            confirmations.append(confirmation)
            clear_progress = True

        for confirmation in confirmations:
            dtype = create_robcoewmtype_str(confirmation)
            success = self.order_controller.confirm_wht(
                dtype, unstructure(confirmation), clear_progress)

            if success is True:
                _LOGGER.info(
                    'Confirmation message for warehouse task "%s" sent to order manager',
                    wht.tanum)
            else:
                _LOGGER.error(
                    'Error sending confirmation message for warehouse task "%s" - Try again',
                    wht.tanum)
                raise ConnectionError

    @retry(wait_fixed=100)
    def send_warehousetask_error(self, wht: WarehouseTask) -> None:
        """Send warehouse task error."""
        errors = []
        if wht.vlpla:
            error = ConfirmWarehouseTask(
                lgnum=wht.lgnum, tanum=wht.tanum, rsrc=self.robot_config.rsrc, who=wht.who,
                confirmationnumber=ConfirmWarehouseTask.FIRST_CONF,
                confirmationtype=ConfirmWarehouseTask.CONF_ERROR)
            _LOGGER.info('Error before first confirmation - sending to EWM')
            errors.append(error)
        elif wht.nlpla:
            error = ConfirmWarehouseTask(
                lgnum=wht.lgnum, tanum=wht.tanum, rsrc=self.robot_config.rsrc, who=wht.who,
                confirmationnumber=ConfirmWarehouseTask.SECOND_CONF,
                confirmationtype=ConfirmWarehouseTask.CONF_ERROR)
            _LOGGER.info('Error before second confirmation - sending to EWM')
            errors.append(error)

        for error in errors:
            dtype = create_robcoewmtype_str(error)
            success = self.order_controller.confirm_wht(dtype, unstructure(error), True)

            if success is True:
                _LOGGER.info(
                    'Confirmation message for warehouse task "%s" sent to order manager',
                    wht.tanum)
            else:
                _LOGGER.error(
                    'Error sending confirmation message for warehouse task "%s" - Try again',
                    wht.tanum)
                raise ConnectionError

    @retry(wait_fixed=100)
    def request_work(self, onlynewwho: bool = False, throttle: bool = False) -> None:
        """Request work from order manager."""
        # Allow requesting work only once every 10 seconds when throttling
        if self._requested_work_time and throttle is True:
            time_elapsed = time.time() - self._requested_work_time
            if time_elapsed < 10:
                return

        self._requested_work_time = time.time()

        if onlynewwho:
            request = RequestFromRobot(
                self.robot_config.lgnum, self.robot_config.rsrc, requestnewwho=True)
        else:
            request = RequestFromRobot(
                self.robot_config.lgnum, self.robot_config.rsrc, requestwork=True)

        _LOGGER.info('Requesting work from order manager')

        dtype = create_robcoewmtype_str(request)
        success = self.robot_request_controller.send_robot_request(dtype, unstructure(request))

        if success is True:
            _LOGGER.info('Requested work from order manager')
        else:
            _LOGGER.error('Error requesting work from order manager. Try again')
            raise ConnectionError

    @retry(wait_fixed=100)
    def notify_who_completion(self, who: str) -> None:
        """
        Send a  warehouse order completion request to EWM Order Manager.

        It notifies the robot when the warehouse order was completed.
        """
        request = RequestFromRobot(
            self.robot_config.lgnum, self.robot_config.rsrc, notifywhocompletion=who)

        _LOGGER.info(
            'Requesting warehouse order completion notification for %s from order manager', who)

        dtype = create_robcoewmtype_str(request)
        success = self.robot_request_controller.send_robot_request(dtype, unstructure(request))

        if success is True:
            _LOGGER.info('Requested warehouse order completion notification from order manager')
        else:
            _LOGGER.error(
                'Error requesting warehouse order completion notification from order manager. '
                'Try again')
            raise ConnectionError

    def runner(self) -> None:
        """Run the robots state machine."""
        # Save time stamp when robot is working
        if self.state_machine.state != 'noWarehouseorder':
            self.last_time_working = time.time()

        # Save idle time start timestamp
        if self.state_machine.state != 'idling':
            self.idle_time_start = 0
        elif self.idle_time_start == 0:
            self.idle_time_start = time.time()

        # Don't run if the state machine is currently in a transition
        if self.state_machine.in_transition:
            return

        # Get current state of the state machine
        state = self.state_machine.state

        if state not in ['idling', 'atTarget']:
            self.at_staging_position = False

        # Run functions for current state
        if state == 'noWarehouseorder':
            self._run_state_nowarehouseorder()
        # "moving" subs tate of hierarchical state machine
        elif state[state.rfind('_')+1:] == 'moving':
            self._run_state_moving(state)
        # "moving" sub state of MoveHU state
        elif state in ['MoveHU_movingToSourceBin', 'MoveHU_movingToTargetBin']:
            self._run_state_movehu_goto_xyz_bin(state)
        # "loading", "unloading" sub state of MoveHU state
        elif state in ['MoveHU_loading', 'MoveHU_unloading']:
            self._run_state_movehu_loading(state)
        # "waitAtPick" sub state of PickPackPass state
        elif state == 'PickPackPass_waitingAtPick':
            self._run_state_pickpack_waitingatpick()
        # "waitAtTarget" sub state of PickPackPass state
        elif state == 'PickPackPass_waitingAtTarget':
            self._run_state_pickpack_waitingattarget()
        elif state == 'RobotError':
            self._run_state_roboterror(state)
        elif state == 'charging':
            self._run_state_charging()
        elif state == 'idling':
            self._run_state_idling()

    def _run_state_nowarehouseorder(self) -> None:
        """Run functions for robot state 'noWarehouseorder'."""
        no_work_elapsed = time.time() - self.last_time_working
        if no_work_elapsed > self.robot_config.max_idle_time:
            _LOGGER.info(
                'Robot without warehouse order for more than %s seconds, going to staging area.',
                self.robot_config.max_idle_time)
            self.state_machine.goto_target(target=self.state_machine.TARGET_STAGING)

    def _run_state_moving(self, state: str) -> None:
        """Run functions for robot 'moving' states."""
        # Go to error state, if there is no move_mission
        if self.state_machine.mission.name is None:
            _LOGGER.error(
                'Robot is in state "%s" with no move mission. Enter error state', state)
            self.state_machine.robot_error_occurred()
        else:
            # Update mission state
            self._update_mission_state(self.mission_api.api_return_move_state)

            # Generic moving is done
            if (state == 'moving' and
                    self.state_machine.mission.status == RobotMission.STATE_SUCCEEDED):
                # Robot reached staging position
                if self.state_machine.mission.target_name == self.state_machine.TARGET_STAGING:
                    self.at_staging_position = True
                # Set state target reached
                self.state_machine.target_reached()
            # EWM process related moving is done
            # Start loading / unloading when target is reached
            elif self.state_machine.mission.status == RobotMission.STATE_SUCCEEDED:
                if self.state_machine.active_wht.vlpla:
                    self.state_machine.load()
                elif self.state_machine.active_wht.nlpla:
                    self.state_machine.unload()
                else:
                    _LOGGER.error('Warehouse task neither has source nor target')
            elif self.state_machine.mission.status == (
                    RobotMission.STATE_FAILED):
                _LOGGER.error(
                    'Move mission "%s" was aborted. Entering error state',
                    self.state_machine.mission.name)
                self.state_machine.robot_error_occurred()
            elif self.state_machine.mission.status in RobotMission.STATES_CANCELED:
                _LOGGER.error(
                    'Move mission "%s" was canceled. Entering error state',
                    self.state_machine.mission.name)
                self.state_machine.robot_error_occurred()

    def _run_state_pickpack_waitingatpick(self) -> None:
        """Run functions for robot state 'PickPackPass_waitingAtPick'."""
        confirmed = self.confirm_pick(self.state_machine.active_wht)
        # Explicit confirmation
        if confirmed:
            self.state_machine.confirm()
        # Implicit confirmation when the underlying warehouse task of the human picker was
        # confirmed in SAP EWM
        else:
            self.request_work(throttle=True)

    def _run_state_pickpack_waitingattarget(self) -> None:
        """Run function for robot state 'PickPackPass_waitingAtTarget'."""
        confirmed = self.confirm_target(self.state_machine.active_wht)
        if confirmed:
            self.state_machine.confirm()

    def _run_state_movehu_goto_xyz_bin(self, state: str) -> None:
        """
        Run functions for robot state MoveHU moving states.

        'MoveHU_movingToSourceBin' and 'MoveHU_movingToTargetBin'.
        """
        # Update mission state
        self._update_mission_state(self.mission_api.api_return_load_state)
        # Start loading / unloading if target is reached
        if self.state_machine.mission.status == RobotMission.STATE_SUCCEEDED:
            if state == 'MoveHU_movingToSourceBin':
                self.state_machine.load()
            elif state == 'MoveHU_movingToTargetBin':
                self.state_machine.unload()
            else:
                _LOGGER.fatal('State "%s" is unknown - cannot proceed', state)
                raise ValueError('State "{}" is unknown - cannot proceed'.format(state))
        elif (self.state_machine.mission.status == RobotMission.STATE_RUNNING
              and self.state_machine.mission.active_action == RobotMission.ACTION_DOCKING):
            if state == 'MoveHU_movingToSourceBin':
                self.state_machine.load()
            elif state == 'MoveHU_movingToTargetBin':
                self.state_machine.unload()
            else:
                _LOGGER.fatal('State "%s" is unknown - cannot proceed', state)
                raise ValueError('State "{}" is unknown - cannot proceed'.format(state))
        elif self.state_machine.mission.status == RobotMission.STATE_FAILED:
            _LOGGER.error(
                '"%s" mission "%s" was aborted. Entering error state', state,
                self.state_machine.mission.name)
            self.state_machine.robot_error_occurred()
        elif self.state_machine.mission.status in RobotMission.STATES_CANCELED:
            _LOGGER.error(
                '"%s" mission "%s" was canceled. Entering error state', state,
                self.state_machine.mission.name)
            self.state_machine.robot_error_occurred()

    def _run_state_movehu_loading(self, state: str) -> None:
        """
        Run functions for robot loading/unloading states.

         'MoveHU_loading' and 'MoveHU_unloading'.
        """
        # Update mission state
        self._update_mission_state(self.mission_api.api_return_load_state)
        # Start loading / unloading if target is reached
        if self.state_machine.mission.status == RobotMission.STATE_SUCCEEDED:
            self.state_machine.confirm()
        elif self.state_machine.mission.status == RobotMission.STATE_FAILED:
            _LOGGER.error(
                '"%s" mission "%s" was aborted. Entering error state',
                state, self.state_machine.mission.name)
            self.state_machine.robot_error_occurred()
        elif self.state_machine.mission.status in RobotMission.STATES_CANCELED:
            _LOGGER.error(
                '"%s" mission "%s" was canceled. Entering error state',
                state, self.state_machine.mission.name)
            self.state_machine.robot_error_occurred()

    def _run_state_roboterror(self, state: str) -> None:
        """Run functions for robot state 'RobotError'."""
        # On error state reset to previous state if robot state is OK now
        # Check on_enter_RobotError method of statemachine for further
        # error handling
        if self.mission_api.api_check_state_ok():
            before_error = self.state_machine.state_before_error
            _LOGGER.info('Try to recover from robot error to state "%s"', before_error)
            # Check battery level when the robot was not working before the
            # error, that the robot does not run out of power
            process = before_error[:before_error.rfind('_')]
            if (process not in ['MoveHU', 'PickPackPass']
                    and before_error != 'charging'):
                # Go to charger if battery is low
                battery = self.state_machine.get_battery_level()
                if battery < self.state_machine.robot_config.battery_min:
                    _LOGGER.info(
                        'Battery level %s percent is too low, start charging instead', battery)
                    self.state_machine.charge_battery()
            if before_error in ['MoveHU_movingToSourceBin', 'MoveHU_loading']:
                if self.state_machine.error_count[before_error] < 3:
                    self.state_machine.restart_load()
            elif before_error in ['MoveHU_movingToTargetBin', 'MoveHU_unloading']:
                if self.state_machine.error_count[before_error] < 3:
                    self.state_machine.restart_unload()
            elif before_error == 'PickPackPass_moving':
                self.state_machine.restart_PickPackPass_move()
            elif before_error == 'moving':
                if self.state_machine.error_count[before_error] < 3:
                    self.state_machine.goto_target(
                        target=self.state_machine.mission.target_name)
                elif self.state_machine.mission.target_name == self.state_machine.TARGET_STAGING:
                    _LOGGER.info(
                        'Cannot reach position target "%s" - going to state idle anyway',
                        self.state_machine.TARGET_STAGING)
                    self.state_machine.target_reached()
                else:
                    self.state_machine.goto_target(
                        target=self.state_machine.mission.target_name)
            elif before_error == 'charging':
                self.state_machine.charge_battery()

    def _run_state_charging(self) -> None:
        """Run functions for robot state 'charging'."""
        # Update mission state
        self._update_mission_state(self.mission_api.api_return_charge_state)
        # Get battery level
        battery = self.state_machine.get_battery_level()
        if self.state_machine.mission.status == RobotMission.STATE_SUCCEEDED:
            # Set state no work
            self.state_machine.no_work()
            # Request work from SAP EWM Order Manager if robot available
            if self.mission_api.api_check_state_ok():
                self.request_work()
            else:
                _LOGGER.warning('Robot is not "AVAILABLE", not requesting work')
        elif self.state_machine.mission.status == RobotMission.STATE_FAILED:
            _LOGGER.error(
                'Charging mission "%s" was aborted. Entering error state',
                self.state_machine.mission.name)
            self.state_machine.robot_error_occurred()
        elif self.state_machine.mission.status in RobotMission.STATES_CANCELED:
            _LOGGER.info(
                'Charge mission "%s" was canceled. Requesting work',
                self.state_machine.mission.name)
            # Set state no work
            self.state_machine.no_work()
            # Request work from SAP EWM Order Manager if robot available
            if self.mission_api.api_check_state_ok():
                self.request_work()
            else:
                _LOGGER.warning('Robot is not "AVAILABLE", not requesting work')
        # If there are warehouse order start when battery is above OK level
        elif (self.state_machine.warehouseorders
              and battery >= self.state_machine.robot_config.battery_ok):
            # Start with the first order from queue
            self.state_machine.process_warehouseorder(
                warehouseorder=next(iter(self.state_machine.warehouseorders.values())))
        # Else request work when battery is almost full
        elif battery > 99.9:
            # Set state no work
            self.state_machine.no_work()
            # Request work from SAP EWM Order Manager if robot available
            if self.mission_api.api_check_state_ok():
                self.request_work()
            else:
                _LOGGER.warning('Robot is not "AVAILABLE", not requesting work')

    def _run_state_idling(self) -> None:
        """Run functions for robot state 'idling'."""
        battery = self.state_machine.get_battery_level()
        # Go to charger if battery is below idle level
        if battery < self.state_machine.robot_config.battery_idle:
            self.state_machine.charge_battery()
        # Warn when robot is idle for too long
        elif time.time() - self.idle_time_start > 600:
            if self.mission_api.api_check_state_ok():
                if self.at_staging_position is False:
                    _LOGGER.info(
                        'Robot is idling but not at staging position. Move to staging position')
                    self.state_machine.goto_target(target=self.state_machine.TARGET_STAGING)
                _LOGGER.warning('Robot is idling for 10 minutes. Requesting work')
                self.request_work()
                self.idle_time_start = time.time()

    def _update_mission_state(self, mission_updater: Callable[[Dict], None]) -> None:
        """Update the state of a mission."""
        # Update mission state explicitly if neccessary
        mission = mission_updater(self.state_machine.mission)
        # Update mission status
        if mission.status:
            self.state_machine.mission = mission
            self._failed_status_updates = 0
        # Count failed mission state updates
        else:
            self._failed_status_updates += 1

        if self._failed_status_updates > 10:
            _LOGGER.error('More that 10 failed robot status updates. Entering error state')
            self.state_machine.robot_error_occurred()
