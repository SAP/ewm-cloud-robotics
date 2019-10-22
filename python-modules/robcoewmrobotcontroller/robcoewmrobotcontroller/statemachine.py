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

"""Robot state machines for robcoewm robots."""

import os
import logging
import time
from collections import OrderedDict, defaultdict, namedtuple
from typing import Callable

from transitions.extensions import LockedHierarchicalMachine as Machine
from transitions.core import EventData

from prometheus_client import Counter, Histogram

from robcoewmtypes.robot import RobotMission
from robcoewmtypes.warehouseorder import WarehouseOrder
from robcoewmtypes.warehouse import StorageBin

from .robot_api import RobotMissionAPI

_LOGGER = logging.getLogger(__name__)

STATE_SUCCEEDED = 'SUCCEEDED'
STATE_FAILED = 'FAILED'

WhoIdentifier = namedtuple('WhoIdentifier', ['lgnum', 'who'])


class RobotEWMMachine(Machine):
    """Robot state machine to handle SAP EWM warehouse orders."""

    # Disable name check because generated methods are not snake case style
    # pylint: disable=invalid-name

    states = [
        'startedWarehouseorder', 'noWarehouseorder', 'finishedWarehouseorder', 'RobotError',
        'moving', 'atTarget', 'idling', 'charging',
        {'name': 'MoveHU', 'children': [
            'findingTarget', 'movingToSourceBin', 'movingToTargetBin', 'waiting', 'loading',
            'unloading', 'waitingForErrorRecovery']},
        {'name': 'PickPackPass', 'children': [
            'findingTarget', 'moving', 'waiting', 'waitingAtPick', 'waitingAtTarget']}
        ]

    transitions = [
        # General transitions
        {'trigger': 'process_warehouseorder',
         'source': ['noWarehouseorder', 'finishedWarehouseorder', 'charging', 'idling', 'moving'],
         'dest': 'startedWarehouseorder',
         'conditions': '_check_who_arg',
         'before': '_save_active_who'},
        {'trigger': 'no_work',
         'source': ['finishedWarehouseorder', 'charging'],
         'dest': 'noWarehouseorder'},
        {'trigger': 'goto_target',
         'source': [
             'noWarehouseorder', 'finishedWarehouseorder', 'charging', 'idling', 'RobotError'],
         'dest': 'moving',
         'conditions': '_check_target_arg'},
        {'trigger': 'target_reached',
         'source': ['moving', 'RobotError'],
         'dest': 'atTarget'},
        {'trigger': 'charge_battery',
         'source': [
             'noWarehouseorder', 'finishedWarehouseorder', 'charging', 'idling', 'RobotError'],
         'dest': 'charging'},
        {'trigger': 'idle',
         'source': 'atTarget',
         'dest': 'idling'},
        {'trigger': 'update_warehouseorder',
         'source': '*',
         'dest': None,
         'after': '_update_who',
         'conditions': '_check_who_arg'},
        # Error and recovery transitions
        {'trigger': 'robot_error_occurred',
         'source': '*',
         'dest': 'RobotError',
         'before': '_save_state_before_error'},
        {'trigger': 'restart_PickPackPass_move',
         'source': 'RobotError',
         'dest': 'PickPackPass_findingTarget',
         'after': '_unset_state_before_error'},
        {'trigger': 'restart_load',
         'source': 'RobotError',
         'dest': 'MoveHU_movingToSourceBin',
         'after': '_unset_state_before_error'},
        {'trigger': 'restart_unload',
         'source': 'RobotError',
         'dest': 'MoveHU_movingToTargetBin',
         'after': '_unset_state_before_error'},
        {'trigger': 'cancel_warehouseorder',
         'source': ['RobotError', 'MoveHU_waitingForErrorRecovery'],
         'dest': 'finishedWarehouseorder',
         'after': '_unset_state_before_error'},
        {'trigger': 'wait_for_recovery',
         'source': 'RobotError',
         'dest': 'MoveHU_waitingForErrorRecovery'},
        # Transitions for Move Handling Unit scenario
        {'trigger': 'goto_sourcebin',
         'source': ['MoveHU_findingTarget', 'MoveHU_waiting'],
         'dest': 'MoveHU_movingToSourceBin'},
        {'trigger': 'goto_targetbin',
         'source': ['MoveHU_findingTarget', 'MoveHU_waiting'],
         'dest': 'MoveHU_movingToTargetBin'},
        {'trigger': 'load',
         'source': ['MoveHU_findingTarget', 'MoveHU_movingToSourceBin'],
         'dest': 'MoveHU_loading'},
        {'trigger': 'unload',
         'source': ['MoveHU_findingTarget', 'MoveHU_movingToTargetBin'],
         'dest': 'MoveHU_unloading'},
        {'trigger': 'confirm',
         'source': ['MoveHU_loading', 'MoveHU_unloading'],
         'dest': 'MoveHU_findingTarget'},
        {'trigger': 'start_MoveHU_warehouseorder',
         'source': 'startedWarehouseorder',
         'dest': 'MoveHU_findingTarget'},
        {'trigger': 'find_target_after_update',
         'source': ['MoveHU_waiting'],
         'dest': 'MoveHU_findingTarget'},
        {'trigger': 'complete_warehouseorder',
         'source': 'MoveHU_findingTarget',
         'dest': 'finishedWarehouseorder'},
        # Transitions for Pick Pack & Pass scenario
        {'trigger': 'goto_storagebin',
         'source': ['PickPackPass_findingTarget', 'PickPackPass_waiting'],
         'dest': 'PickPackPass_moving',
         'conditions': '_check_storagebin_arg'},
        {'trigger': 'load',
         'source': ['PickPackPass_findingTarget', 'PickPackPass_moving'],
         'dest': 'PickPackPass_waitingAtPick'},
        {'trigger': 'unload',
         'source': ['PickPackPass_findingTarget', 'PickPackPass_moving'],
         'dest': 'PickPackPass_waitingAtTarget'},
        {'trigger': 'confirm',
         'source': ['PickPackPass_waitingAtPick',
                    'PickPackPass_waitingAtTarget'],
         'dest': 'PickPackPass_findingTarget'},
        {'trigger': 'start_PickPackPass_warehouseorder',
         'source': 'startedWarehouseorder',
         'dest': 'PickPackPass_findingTarget'},
        {'trigger': 'find_target_after_update',
         'source': ['PickPackPass_waiting',
                    'PickPackPass_findingTarget',
                    'PickPackPass_waitingAtPick',
                    'PickPackPass_waitingAtTarget'],
         'dest': 'PickPackPass_findingTarget'},
        {'trigger': 'complete_warehouseorder',
         'source': 'PickPackPass_findingTarget',
         'dest': 'finishedWarehouseorder'},
        ]

    TARGET_CHARGING = 'charging'
    TARGET_STAGING = 'staging'
    VALID_TARGETS = [TARGET_CHARGING, TARGET_STAGING]

    BUCKETS = (
        1.0, 5.0, 10.0, 30.0, 60.0, 90.0, 120.0, 180.0, 240.0, 300.0, 360.0, 420.0, 480.0, 540.0,
        600.0, '+Inf')

    # Prometheus logging
    who_counter = Counter(
        'sap_ewm_robot_warehouse_order_results', 'Completed EWM Warehouse orders',
        ['robot', 'order_type', 'result'])
    who_times = Histogram(
        'sap_ewm_robot_warehouse_order_times',
        'Robot\'s processing time for warehouse orders (seconds)',
        ['robot', 'order_type', 'activity'], buckets=BUCKETS)
    state_rentention_times = Histogram(
        'sap_ewm_robot_state_retention_time', 'Robot\'s retention time in a state (seconds)',
        ['robot', 'state'], buckets=BUCKETS)

    def __init__(
            self, robot_mission_api: RobotMissionAPI, confirm_api: Callable,
            request_ewm_work_api: Callable, send_wht_error_api: Callable,
            notify_who_completion_api: Callable, save_wht_progress_api: Callable,
            initial: str = 'noWarehouseorder') -> None:
        """Constructor."""
        cls = self.__class__
        # Initialize state machine
        super().__init__(self, states=cls.states, transitions=cls.transitions,
                         send_event=True, queued=True,
                         prepare_event=self._set_in_transition,
                         before_state_change=self._run_before_state_change,
                         after_state_change=self._run_after_state_change,
                         finalize_event=self._unset_in_transition,
                         initial=initial)
        # Init robot identifier
        self.init_robot_fromenv()
        # List of warehouse order assigned to this robot
        self.warehouseorders = OrderedDict()
        # List of sub warehouse orders of robot's warehouse orders for Pick, Pack and Pass
        # Scenario. Those are not assigned to the robot
        self.sub_warehouseorders = OrderedDict()
        # Warehouse order / warehouse task currently in process
        self.active_who = None
        self.active_wht = None
        self.active_sub_who = None
        # State before robot error occurred
        self.state_before_error = None
        self.error_count = defaultdict(int)

        # Marks if the state machine is currently in a transition
        self.in_transition = False

        # APIs to control the robot
        self.mission_api = robot_mission_api
        self._mission = RobotMission()
        self.confirm_api = confirm_api
        self.save_wht_progress_api = save_wht_progress_api

        # APIs for EWM Ordermanager
        self.request_ewm_work = request_ewm_work_api
        self.send_wht_error = send_wht_error_api
        self.notify_who_completion = notify_who_completion_api

        # Timestamp when state machine entered the current state
        self.state_enter_ts = time.time()

        # Warehouse order type currently in process
        self.who_type = ''

        # Warehouse order timestamps
        self.who_ts = {'start': 0.0, 'load': 0.0, 'unload': 0.0, 'finish': 0.0}

    @property
    def mission(self) -> RobotMission:
        """Get self._mission."""
        return self._mission

    @mission.setter
    def mission(self, mission: RobotMission) -> None:
        """
        Set self._mission.

        Ensure self._mission.target_name is not overwritten accidently.
        """
        if self._mission.target_name:
            mission.target_name = self._mission.target_name
        self._mission = mission

    def init_robot_fromenv(self) -> None:
        """Initialize EWM Robot from environment variables."""
        # Read environment variables
        envvar = {}
        envvar['EWM_LGNUM'] = os.environ.get('EWM_LGNUM')
        envvar['ROBCO_ROBOT_NAME'] = os.environ.get('ROBCO_ROBOT_NAME')
        # Check if complete
        for var, val in envvar.items():
            if val is None:
                raise ValueError(
                    'Environment variable "{}" is not set'.format(var))

        # Optional parameters
        envvar['EWM_BATTERY_MIN'] = os.environ.get('EWM_BATTERY_MIN')
        envvar['EWM_BATTERY_OK'] = os.environ.get('EWM_BATTERY_OK')
        envvar['EWM_BATTERY_IDLE'] = os.environ.get('EWM_BATTERY_IDLE')

        # Robot identifier
        self.lgnum = envvar['EWM_LGNUM']
        # EWM rsrc must be upper case
        self.rsrc = envvar['ROBCO_ROBOT_NAME'].upper()
        # Cloud Robotics robot name
        self.robot_name = envvar['ROBCO_ROBOT_NAME']
        # Battery levels in %
        self.battery_min = float(envvar['EWM_BATTERY_MIN']) if envvar['EWM_BATTERY_MIN'] else 10
        self.battery_ok = float(envvar['EWM_BATTERY_OK']) if envvar['EWM_BATTERY_OK'] else 80
        self.battery_idle = float(envvar['EWM_BATTERY_IDLE']) if envvar['EWM_BATTERY_IDLE'] else 40

    def get_battery_level(self) -> float:
        """Get robot's battery level in percent."""
        # Try 3 times at maximum
        for _ in range(3):
            # Get battery level
            battery = self.mission_api.api_get_battery_percentage()
            if battery:
                break

        if battery is None:
            battery = 0.0
            _LOGGER.error('Did not get battery level. Assuming it is empty.')

        return battery

    def _run_before_state_change(self, event: EventData) -> None:
        """Run these methods before state changes."""
        # Reset error state
        self._reset_error_state(event)
        # Log retention time in a state
        self._log_state_rentention_time(event)

    def _run_after_state_change(self, event: EventData) -> None:
        """Run these methods after state changed."""
        # Set enter timestmap
        self._set_state_enter_ts(event)

    def _set_in_transition(self, event: EventData) -> None:
        """Set the in_transition flag of the state machine."""
        self.in_transition = True

    def _unset_in_transition(self, event: EventData) -> None:
        """Unset the in_transition flag of the state machine."""
        self.in_transition = False

    def _reset_error_state(self, event: EventData) -> None:
        """Reset error state on non error transitions."""
        if event.event.name != 'robot_error_occurred':
            self.error_count[self.state] = 0

    def _set_state_enter_ts(self, event: EventData) -> None:
        """Set time stamp when the state was entered."""
        self.state_enter_ts = time.time()

    def _log_state_rentention_time(self, event: EventData) -> None:
        """Log the retention time of this state."""
        retention_time = time.time() - self.state_enter_ts
        self.state_rentention_times.labels(  # pylint: disable=no-member
            robot=self.robot_name, state=self.state).observe(retention_time)

    def _check_target_arg(self, event: EventData) -> bool:
        """Check if target is an argument of the transition."""
        cls = self.__class__
        if event.kwargs.get('target') in cls.VALID_TARGETS:
            return True
        else:
            _LOGGER.error(
                'Keyword argument "target" for transition has invalid value "%s"',
                event.kwargs.get('target'))
            return False

    def _check_storagebin_arg(self, event: EventData) -> bool:
        """Check if storagebin is an argument of the transition."""
        if isinstance(event.kwargs.get('storagebin'), StorageBin):
            return True
        else:
            _LOGGER.error(
                'An keyword argument "storagebin" of type "StorageBin" must be'
                ' provided for the transition')
            return False

    def _check_who_arg(self, event: EventData) -> bool:
        """Check if warehouse is an argument of the transition."""
        obj = event.kwargs.get('warehouseorder')
        if isinstance(obj, WarehouseOrder):
            return True
        else:
            _LOGGER.error(
                'An keyword argument "warehouseorder" of type "WarehouseOrder"'
                ' must be provided for the transition')
            return False

    def _save_active_who(self, event: EventData) -> None:
        """Save warehouse order which is processed in this state machine."""
        self.active_who = event.kwargs.get('warehouseorder')
        self.active_wht = None

    def _save_state_before_error(self, event: EventData) -> None:
        """
        Save state before state machine went into error state.

        Use as transition.before callback.
        """
        # Count errors
        self.error_count[self.state] += 1
        self.state_before_error = self.state

    def _unset_state_before_error(self, event: EventData) -> None:
        """
        Unset state before state machine went into error state.

        Use as transition.after callback.
        """
        self.state_before_error = None

    def _update_who(self, event: EventData) -> None:
        """Update a warehouse order of this state machine."""
        warehouseorder = event.kwargs.get('warehouseorder')

        if warehouseorder.lgnum == self.lgnum and warehouseorder.rsrc == self.rsrc:
            _LOGGER.debug(
                'Start updating warehouse order "%s" directly assigned to the robot',
                warehouseorder.who)
            self._update_robot_who(warehouseorder)
        else:
            _LOGGER.debug(
                'Start updating warehouse order "%s" not directly assigned to the robot, but a sub'
                ' warehouse order', warehouseorder.who)
            self._update_sub_who(warehouseorder)

    def _update_robot_who(self, warehouseorder: WarehouseOrder):
        """Update warehouse order directly assigned to this robot."""
        who = WhoIdentifier(warehouseorder.lgnum, warehouseorder.who)

        # Update dictionary of all warehouse orders
        self.warehouseorders[who] = warehouseorder

        # Update active warehouse order
        # No warehouse order in process and received order is assigned to robot
        if self.active_who is None:
            # Get robots battery level
            battery = self.get_battery_level()
            mission_name = self._mission.name
            if self.state == 'moving':
                _LOGGER.info(
                    'New warehouse order %s received while robot is moving, cancel move mission '
                    'and start processing', warehouseorder.who)
                self.process_warehouseorder(warehouseorder=warehouseorder)
                # Cancel move mission
                self.mission_api.api_cancel_mission(mission_name)
            elif self.state == 'charging' and battery >= self.battery_ok:
                _LOGGER.info(
                    'New warehouse order %s received while robot is charging. Battery percentage '
                    'OK, cancel charging and start processing', warehouseorder.who)
                self.process_warehouseorder(warehouseorder=warehouseorder)
                # Cancel charge mission
                self.mission_api.api_cancel_mission(mission_name)
            elif self.state == 'charging':
                _LOGGER.info(
                    'New warehouse order %s received, but robot battery level is too low at "%s" '
                    'percent. Continue charging', warehouseorder.who, battery)
            elif self.state == 'idling':
                _LOGGER.info(
                    'New warehouse order %s received, while robot is idling. Start processing',
                    warehouseorder.who)
                self.process_warehouseorder(warehouseorder=warehouseorder)
            else:
                _LOGGER.error(
                    'New warehouse order %s received, while robot is in state "%s" with no active'
                    'warehouse order. This should not happen', warehouseorder.who, self.state)
        # An active warehouse order changed
        elif warehouseorder.who == self.active_who.who and warehouseorder != self.active_who:
            # Find new target if active warehouse order was updated for sub
            # state "waiting" of hierarchical state machine
            if self.state[self.state.rfind('_')+1:] in ['waiting']:
                _LOGGER.info(
                    'Active warehouse order %s updated, find new target', warehouseorder.who)
                self.active_who = warehouseorder
                self.find_target_after_update()
            else:
                _LOGGER.info('Active warehouse order %s updated', warehouseorder.who)
                self.active_who = warehouseorder
        # A warehouse order was received, but there are no changes
        elif warehouseorder == self.active_who:
            _LOGGER.debug(
                'Warehouse order received, but no changes. Active warehouse "%s" order was not '
                'updated', self.active_who.who)
        else:
            _LOGGER.info(
                'Warehouse order %s received and enqueued. A different warehouse order is already '
                'in process.', warehouseorder.who)

    def _update_sub_who(self, warehouseorder: WarehouseOrder):
        """Update a sub warehouse order not directly assigned to this robot."""
        who = WhoIdentifier(warehouseorder.lgnum, warehouseorder.who)

        # Update dictionary of all warehouse orders
        self.sub_warehouseorders[who] = warehouseorder

        # Update active (sub) warehouse order
        if self.active_who:
            # Sub warehouse order belongs to current active warehouse order
            if warehouseorder.topwhoid == self.active_who.who:
                # No active sub warehouse order and finding new target
                if self.active_sub_who is None:
                    if self.state == 'PickPackPass_findingTarget':
                        _LOGGER.info(
                            'New sub warehouse order %s received, continue working on active '
                            'warehouse order "%s"', warehouseorder.who, self.active_who.who)
                        self.find_target_after_update()
                # An active sub warehouse order changed
                elif (warehouseorder.who == self.active_sub_who.who
                      and warehouseorder != self.active_sub_who):
                    # Update active warehouse order
                    self.active_sub_who = warehouseorder
                    # Find new target if active sub warehouse order was updated for sub states
                    # "waiting" and "waitingAtPick" of hierarchical state machine
                    if self.state[self.state.rfind('_')+1:] in ['waiting']:
                        _LOGGER.info(
                            'Active sub warehouse order %s updated, find new target',
                            warehouseorder.who)
                        self.find_target_after_update()
                    elif self.state[self.state.rfind('_')+1:] in [
                            'waitingAtPick'] and self.active_wht:
                        # Init loop variables
                        wht_pick_confirmed = False
                        wht_found = False

                        # Check if active warehouse task is found in the updated sub warehouse
                        # order.
                        for task in warehouseorder.warehousetasks:
                            if (task.lgnum == self.active_wht.lgnum
                                    and task.tanum == self.active_wht.tanum):
                                wht_found = True
                                # If source bin was deleted, task is confirmed
                                if not task.vlpla:
                                    wht_pick_confirmed = True

                        # If active warehouse task was not found, it is
                        # confirmed
                        if not wht_found:
                            wht_pick_confirmed = True

                        # Change state if warehouse task confirmed
                        if wht_pick_confirmed:
                            _LOGGER.info(
                                'Active sub warehouse order %s updated, pick confirmed',
                                warehouseorder.who)
                            self.confirm()
                    else:
                        _LOGGER.info('Active sub warehouse order %s updated',
                                     warehouseorder.who)

                # A warehouse order was received, but there are no changes
                elif warehouseorder == self.active_sub_who:
                    _LOGGER.debug(
                        'Sub warehouse order received, but no changes. Active sub warehouse "%s" '
                        'order was not updated', self.active_sub_who.who)
            else:
                _LOGGER.info(
                    'Sub warehouse order %s received and enqueued. A different warehouse order is '
                    'already in process.', warehouseorder.who)

    def on_enter_charging(self, event: EventData) -> None:
        """Start charging the robot."""
        # Start charge mission
        mission = self.mission_api.api_charge_robot()

        if mission.name:
            _LOGGER.info('Started charging with mission name"%s"', mission.name)
        else:
            _LOGGER.error('Mission name of charging mission "%s" is empty')
        self._mission.name = mission.name
        self._mission.status = mission.status
        self._mission.target_name = ''

    def on_enter_idling(self, event: EventData) -> None:
        """Start idling."""
        # Check if a warehouse order arrived when moving to staging area
        if self.warehouseorders:
            # if there is a warehouse order, start processing it
            _LOGGER.info('There is a new warehouse order in queue, start processing')
            self.process_warehouseorder(warehouseorder=next(iter(self.warehouseorders.values())))
        # Request new work from SAP EWM Ordermanager if robot available
        elif self.mission_api.api_check_state_ok():
            self.request_ewm_work()
        else:
            _LOGGER.warning('Robot is not "AVAILABLE", not requesting work')

    def on_enter_RobotError(self, event: EventData) -> None:
        """Handle robot error."""
        # When retrying three times did not resolv the error, it is not recoverable
        before_error = self.state_before_error
        if self.error_count[before_error] >= 3:
            # if there is an active warehouse task in MoveHU process, notify SAP EWM
            process = before_error[:before_error.rfind('_')]
            if process == 'MoveHU' and self.active_wht:
                self.send_wht_error(self.active_wht)
                # Cancel warehouse order if warehouse task not confirmed yet
                if self.active_wht.vlpla:
                    self.cancel_warehouseorder()
                # Request warehouse order completion notification and wait
                elif self.active_wht.nlpla:
                    self.notify_who_completion(self.active_wht.who)
                    self.wait_for_recovery()

    def on_enter_moving(self, event: EventData) -> None:
        """Start moving to target staging or charging."""
        cls = self.__class__
        # Get target target
        target = event.kwargs.get('target')
        # Start move mission
        if target == cls.TARGET_CHARGING:
            mission = self.mission_api.api_moveto_charging_position()
        elif target == cls.TARGET_STAGING:
            mission = self.mission_api.api_moveto_staging_position()
        else:
            _LOGGER.error(
                'Unknown target "%s". Valid targets are %s', target,
                cls.VALID_TARGETS)
            mission = RobotMission()
        if mission.name:
            _LOGGER.info(
                'Started moving to "%s" with mission name "%s"', target, mission.name)
        else:
            _LOGGER.error(
                'Mission name of move to "%s" is empty', target)
        self._mission.name = mission.name
        self._mission.status = mission.status
        self._mission.target_name = target

    def on_exit_moving(self, event: EventData) -> None:
        """Delete goal ids when stop moving."""
        self._mission.name = ''
        self._mission.status = ''

    def on_enter_atTarget(self, event: EventData) -> None:
        """Set next state when move target is reached."""
        cls = self.__class__
        # Get last target
        target = self._mission.target_name
        self._mission.target_name = ''
        # Determine next state
        if target == cls.TARGET_CHARGING:
            self.charge_battery()
        elif target == cls.TARGET_STAGING:
            self.idle()
        else:
            _LOGGER.error('Unknown target "%s", unable to set new state', target)

    def on_enter_startedWarehouseorder(self, event: EventData) -> None:
        """Determine the type of warehouse order which was started."""
        warehouseorder = event.kwargs.get('warehouseorder')
        # Log timestamp when the order was started
        self.who_ts['start'] = time.time()
        # Start state machine according to the warehouse order type
        if warehouseorder.flgwho is True:
            _LOGGER.info(
                'Warehouse order "%s" is of type "PickPackPass". Start finding target.',
                self.active_who.who)
            self.who_type = 'PickPackPass'
            self.start_PickPackPass_warehouseorder()
        else:
            _LOGGER.info(
                'Warehouse order "%s" is of type "MoveHU". Start finding target.',
                self.active_who.who)
            self.who_type = 'MoveHU'
            self.start_MoveHU_warehouseorder()

    def on_enter_finishedWarehouseorder(self, event: EventData) -> None:
        """Clean up after finishing a warehouse order and start the next."""
        who = WhoIdentifier(self.active_who.lgnum, self.active_who.who)
        # Delete finished warehouseorder
        self.warehouseorders.pop(who, None)

        # Collect sub warehouse order for the finished warehouse order
        sub_whos = []
        for sub_who, order in self.sub_warehouseorders.items():
            if order.topwhoid == self.active_who.who:
                sub_whos.append(sub_who)
        # Delete collected sub warehouse orders
        for sub_who in sub_whos:
            self.sub_warehouseorders.pop(sub_who, None)

        # Unset active orders / tasks
        self.active_who = None
        self.active_wht = None
        self.active_sub_who = None

        # Log warehouse order completion
        self.who_ts['finish'] = time.time()
        self.who_times.labels(  # pylint: disable=no-member
            robot=self.robot_name, order_type=self.who_type,
            activity='completed').observe(
                self.who_ts['finish']-self.who_ts['start'])

        if event.event.name == 'cancel_warehouseorder':
            self.who_counter.labels(  # pylint: disable=no-member
                robot=self.robot_name,
                order_type=self.who_type,
                result=STATE_FAILED).inc()
        else:
            self.who_counter.labels(  # pylint: disable=no-member
                robot=self.robot_name,
                order_type=self.who_type,
                result=STATE_SUCCEEDED).inc()

        # Reset warehouse order type
        self.who_type = ''
        # Reset time stamps
        for key in self.who_ts:
            self.who_ts[key] = 0.0

        # Get robots battery level
        battery = self.get_battery_level()

        # If still warehouse orders in queue, start the next one
        if self.warehouseorders:
            _LOGGER.info('More warehouse orders in queue, start processing')
            # TODO: Unassign warehouse orders if below min battery level
            # Get robots battery level
            _LOGGER.info(
                'Battery level after finishing order: "%s" percent', battery)
            self.process_warehouseorder(warehouseorder=next(iter(self.warehouseorders.values())))
        else:
            _LOGGER.info('No more warehouse orders in queue')
            if battery < self.battery_min:
                _LOGGER.info(
                    'Battery level is "%s". It is below minimum of "%s". Charging robot.', battery,
                    self.battery_min)
                self.charge_battery()
            else:
                _LOGGER.info(
                    'Battery level after finishing order: "%s" percent', battery)
                # Robot has no work
                self.no_work()
                # Request new work from SAP EWM Ordermanager if robot available
                if self.mission_api.api_check_state_ok():
                    self.request_ewm_work(onlynewwho=True)
                else:
                    _LOGGER.warning('Robot is not "AVAILABLE", not requesting work')

    def on_enter_MoveHU_findingTarget(self, event: EventData) -> None:
        """Find next target from warehouse task of active warehouse order."""
        wht = None
        tosourcebin = False
        # First check if there is a warehouse task where the robot did not
        # confirm the loading of the HU yet
        for task in self.active_who.warehousetasks:
            if task.vlpla:
                wht = task
                tosourcebin = True
                _LOGGER.info(
                    'Target: source bin of warehouse task "%s", HU "%s"', task.tanum, task.vlenr)
                break
        # If no task was found, check for the first warehouse task to unload a HU
        if wht is None:
            for task in self.active_who.warehousetasks:
                if task.nlpla:
                    wht = task
                    tosourcebin = False
                    _LOGGER.info(
                        'Target: target bin of warehouse task %s, HU "%s"',
                        task.tanum, task.nlenr)
                    break

        # Start moving to the target
        if wht:
            if wht.flghuto:
                self.active_wht = wht
                if tosourcebin:
                    self.goto_sourcebin()
                else:
                    self.goto_targetbin()
            else:
                _LOGGER.error(
                    'Warehouse task "%s" is not a MoveHU warehouse task. Not supported by this '
                    'process. Cannot continue.', wht.tanum)
        else:
            _LOGGER.info(
                'No more warehouse task for warehouse order "%s" found. Finish job.',
                self.active_who.who)
            self.complete_warehouseorder()

    def on_enter_MoveHU_movingToSourceBin(self, event: EventData) -> None:
        """Start moving to the source bin of a warehouse task."""
        mission = self.mission_api.api_load_unload(self.active_wht)
        _LOGGER.info(
            'Started moving to "%s" with mission name "%s"', self.active_wht.vlpla, mission.name)
        self._mission.name = mission.name
        self._mission.status = mission.status
        self._mission.target_name = ''
        # Save state for recovery on startup
        self.save_wht_progress_api(self.active_wht, self._mission.name, self.state)

    def on_enter_MoveHU_movingToTargetBin(self, event: EventData) -> None:
        """Start moving to the target bin of a warehouse task."""
        mission = self.mission_api.api_load_unload(self.active_wht)
        _LOGGER.info(
            'Started moving to "%s" with mission name "%s"', self.active_wht.nlpla, mission.name)
        self._mission.name = mission.name
        self._mission.status = mission.status
        self._mission.target_name = ''
        # Save state for recovery on startup
        self.save_wht_progress_api(self.active_wht, self._mission.name, self.state)

    def on_enter_MoveHU_loading(self, event: EventData) -> None:
        """Load handling unit of a warehouse task on a robot."""
        _LOGGER.info('Started loading HU "%s"', self.active_wht.vlenr)

    def on_exit_MoveHU_loading(self, event: EventData) -> None:
        """Confirm and delete information about source handling unit."""
        # Confirm loading only if no error occured
        if event.event.name != 'robot_error_occurred':
            self.confirm_api(self.active_wht)
            _LOGGER.info('Loaded HU "%s"', self.active_wht.vlenr)
            # Log elapsed time from order start to HU load
            self.who_ts['load'] = time.time()
            self.who_times.labels(  # pylint: disable=no-member
                robot=self.robot_name, order_type=self.who_type,
                activity='load_hu').observe(self.who_ts['load']-self.who_ts['start'])

            for i, task in enumerate(self.active_who.warehousetasks):
                if task.tanum == self.active_wht.tanum:
                    self.active_who.warehousetasks[i].vltyp = ''
                    self.active_who.warehousetasks[i].vlber = ''
                    self.active_who.warehousetasks[i].vlpla = ''

                    self.active_wht = self.active_who.warehousetasks[i]
        else:
            _LOGGER.info('Error occurred not confirming HU load')

        self._mission.name = ''
        self._mission.status = ''

    def on_enter_MoveHU_unloading(self, event: EventData) -> None:
        """Unload handling unit of a warehouse task on a robot."""
        _LOGGER.info('Started unloading HU "%s"', self.active_wht.nlenr)

    def on_exit_MoveHU_unloading(self, event: EventData) -> None:
        """Confirm and delete information about target handling unit."""
        # Confirm loading only if no error occured
        if event.event.name != 'robot_error_occurred':
            self.confirm_api(self.active_wht)
            _LOGGER.info('Unloaded HU "%s"', self.active_wht.nlenr)
            # Log elapsed time from HU load to HU unload
            self.who_ts['unload'] = time.time()
            self.who_times.labels(  # pylint: disable=no-member
                robot=self.robot_name, order_type=self.who_type,
                activity='unload_hu').observe(self.who_ts['unload']-self.who_ts['load'])

            for i, task in enumerate(self.active_who.warehousetasks):
                if task.tanum == self.active_wht.tanum:
                    self.active_who.warehousetasks[i].nltyp = ''
                    self.active_who.warehousetasks[i].nlber = ''
                    self.active_who.warehousetasks[i].nlpla = ''

                    self.active_wht = self.active_who.warehousetasks[i]
        else:
            _LOGGER.error('Error occurred not confirming HU unload')

        self._mission.name = ''
        self._mission.status = ''

    def on_enter_MoveHU_waitingForErrorRecovery(self, event: EventData) -> None:
        """
        Robot waits until error is recovered.

        EWM confirms completion of error causing warehouse order.
        """
        return None

    def on_enter_PickPackPass_findingTarget(self, event: EventData) -> None:
        """Find next target from warehouse task of active warehouse order."""
        wht = None
        sub_who = None

        # Try to get a sub warehouse order
        for order in self.sub_warehouseorders.values():
            if order.topwhoid == self.active_who.who:
                sub_who = order
                break

        # Check if there is a warehouse task where the robot did not confirm the loading of the HU
        # yet
        if sub_who:
            for task in sub_who.warehousetasks:
                if task.vlpla:
                    wht = task
                    target = StorageBin(task.lgnum, task.vlpla)
                    _LOGGER.info(
                        'Target: source bin of warehouse task "%s"', task.tanum)
                    break
        # If no task was found, check for the first warehouse task to unload a HU
        if wht is None:
            for task in self.active_who.warehousetasks:
                if task.nlpla:
                    wht = task
                    target = StorageBin(task.lgnum, task.nlpla)
                    _LOGGER.info(
                        'Target: target bin of warehouse task %s, HU "%s", enforcing first '
                        'confirmation', task.tanum, task.nlenr)
                    # Enforce first confirmation that warehouse order is flagged "started" in EWM
                    self.confirm_api(wht, enforce_first_conf=True)
                    break

        # Start moving to the target
        if wht:
            self.active_wht = wht
            self.active_sub_who = sub_who
            _LOGGER.info('Next target is storage bin "%s"', target.lgpla)
            self.goto_storagebin(storagebin=target)
        # Check if the sub warehouse orders are already received
        elif sub_who:
            # If there are sub warehouse order, but no more warehouse tasks, everything is done.
            _LOGGER.info(
                'No more warehouse task for warehouse order "%s" found. Finish job.',
                self.active_who.who)
            self.complete_warehouseorder()
        # If no sub warehouse order for this active order found, wait until they arrive
        else:
            _LOGGER.info(
                'No warehouse task for warehouse order "%s" found. Wait.', self.active_who.who)
            # Request work from EWM in case message was lost
            self.request_ewm_work()

    def on_enter_PickPackPass_moving(self, event: EventData) -> None:
        """Start moving to a bin."""
        storagebin = event.kwargs.get('storagebin')
        mission = self.mission_api.api_moveto_storagebin_position(storagebin)
        _LOGGER.info(
            'Started moving to "%s" with mission name "%s"', storagebin.lgpla, mission.name)
        self._mission.name = mission.name
        self._mission.status = mission.status
        self._mission.target_name = storagebin
        # Save state for recovery on startup
        self.save_wht_progress_api(self.active_wht, self._mission.name, self.state)

    def on_exit_PickPackPass_moving(self, event: EventData) -> None:
        """Delete goal ids when stop moving."""
        self._mission.name = ''
        self._mission.status = ''
        self._mission.target_name = ''

    def on_exit_PickPackPass_waitingAtPick(self, event: EventData) -> None:
        """Confirm and delete information about source handling unit."""
        _LOGGER.info('Picking finished')

        for i, task in enumerate(self.active_sub_who.warehousetasks):
            if task.tanum == self.active_wht.tanum:
                self.active_sub_who.warehousetasks[i].vltyp = ''
                self.active_sub_who.warehousetasks[i].vlber = ''
                self.active_sub_who.warehousetasks[i].vlpla = ''

                self.active_wht = self.active_sub_who.warehousetasks[i]

                # Update queue of sub warehouse orders
                sub_who = WhoIdentifier(self.active_sub_who.lgnum, self.active_sub_who.who)
                self.sub_warehouseorders[sub_who] = self.active_sub_who

        # Save state for recovery on startup
        self.save_wht_progress_api(self.active_wht, '', '')

    def on_exit_PickPackPass_waitingAtTarget(
            self, event: EventData) -> None:
        """Confirm and delete information about target handling unit."""
        self.confirm_api(self.active_wht)
        _LOGGER.info('Pick HU "%s" was unloaded', self.active_wht.nlenr)

        for i, task in enumerate(self.active_who.warehousetasks):
            if task.tanum == self.active_wht.tanum:
                self.active_who.warehousetasks[i].nltyp = ''
                self.active_who.warehousetasks[i].nlber = ''
                self.active_who.warehousetasks[i].nlpla = ''

                self.active_wht = self.active_who.warehousetasks[i]
