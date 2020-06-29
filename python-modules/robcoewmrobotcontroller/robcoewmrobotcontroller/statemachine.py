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

"""Robot state machine for robcoewm robots."""

import logging
import time
from collections import namedtuple, OrderedDict, defaultdict
from typing import DefaultDict, Dict, Optional, List

from transitions.core import EventData
from transitions.extensions import LockedHierarchicalMachine as Machine
from transitions.extensions.states import add_state_features, Timeout

from prometheus_client import Counter, Histogram

import attr
from cattr import structure, unstructure

from robcoewmtypes.robot import RobotMission, RobotConfigurationStatus, RequestFromRobot
from robcoewmtypes.warehouseorder import (
    WarehouseOrder, WarehouseOrderCRDSpec, WarehouseTask, ConfirmWarehouseTask)

from .ordercontroller import OrderController
from .robco_mission_api import RobCoMissionAPI
from .robotconfigcontroller import RobotConfigurationController
from .robotrequestcontroller import RobotRequestController
from .statemachine_config import RobotEWMConfig

_LOGGER = logging.getLogger(__name__)

STATE_SUCCEEDED = 'SUCCEEDED'
STATE_FAILED = 'FAILED'

WhoIdentifier = namedtuple('WhoIdentifier', ['lgnum', 'who'])


@attr.s
class WarehouseOrderTimestamps:
    """Warehouse order processing timestamps."""

    start: float = attr.ib(factory=time.time, validator=attr.validators.instance_of(float))
    end: float = attr.ib(default=0.0, validator=attr.validators.instance_of(float))
    get_trolley: float = attr.ib(default=0.0, validator=attr.validators.instance_of(float))
    return_trolley: float = attr.ib(default=0.0, validator=attr.validators.instance_of(float))


@add_state_features(Timeout)
class RobotEWMMachine(Machine):
    """Robot state machine to handle SAP EWM warehouse orders."""

    # Disable name check because generated methods are not snake case style
    # pylint: disable=invalid-name

    # Config of the state machine
    conf = RobotEWMConfig

    buckets = (
        1.0, 5.0, 10.0, 30.0, 60.0, 90.0, 120.0, 180.0, 240.0, 300.0, 360.0, 420.0, 480.0, 540.0,
        600.0, '+Inf')

    # Prometheus logging
    who_counter = Counter(
        'sap_ewm_robot_warehouse_order_results', 'Completed EWM Warehouse orders',
        ['robot', 'order_type', 'result'])
    who_times = Histogram(
        'sap_ewm_robot_warehouse_order_times',
        'Robot\'s processing time for warehouse orders (seconds)',
        ['robot', 'order_type', 'activity'], buckets=buckets)
    state_rentention_times = Histogram(
        'sap_ewm_robot_state_retention_time', 'Robot\'s retention time in a state (seconds)',
        ['robot', 'state'], buckets=buckets)

    def __init__(
            self, robot_config: RobotConfigurationController, mission_api: RobCoMissionAPI,
            order_controller: OrderController, robotrequest_controller: RobotRequestController,
            initial: str = 'idle') -> None:
        """Construct."""
        cls = self.__class__

        # Check if all methods for transitions are implemented
        cls.conf.check_transitions_complete(cls)

        # Initialize state machine
        super().__init__(self, states=cls.conf.states, transitions=cls.conf.transitions,
                         send_event=True, queued=True,
                         before_state_change=self._run_before_state_change,
                         after_state_change=self._run_after_state_change,
                         initial=initial)

        # Controller
        # configuration of the robot
        self.robot_config = robot_config
        # mission API
        self.mission_api = mission_api
        # order controller
        self.order_controller = order_controller
        # robotrequest controller
        self.robotrequest_controller = robotrequest_controller

        # EWM
        # List of warehouse order assigned to this robot
        self.warehouseorders: OrderedDict[  # pylint: disable=unsubscriptable-object
            WhoIdentifier, WarehouseOrderCRDSpec] = OrderedDict()
        # List of sub warehouse orders of robot's warehouse orders for Pick, Pack and Pass
        # Scenario. Those are not assigned to the robot
        self.sub_warehouseorders: OrderedDict[  # pylint: disable=unsubscriptable-object
            WhoIdentifier, WarehouseOrderCRDSpec] = OrderedDict()
        # Warehouse order / warehouse task currently in process
        self.active_who: Optional[WarehouseOrder] = None
        self.active_wht: Optional[WarehouseTask] = None
        self.active_sub_who: Optional[WarehouseOrder] = None

        # Cloud Robotics mission
        self.active_mission = ''

        # Error counter for states
        self.error_count: DefaultDict[str, int] = defaultdict(int)
        # Counter for consecutive warehouse order fails
        self.failed_warehouseorders = 0

        # Timestamp when state machine entered the current state
        self.state_enter_ts = time.time()

        # Timestamps for warehouse order processing
        self.who_ts: Optional[WarehouseOrderTimestamps] = None

    def connect_external_events(self) -> None:
        """Connect state machine to external event sources of Cloud Robotics."""
        name = 'ewm-statemachine'
        self.mission_api.robot_api.register_callback(
            name, ['ADDED', 'MODIFIED'], self.robot_cb)
        self.order_controller.register_callback(
            name, ['ADDED', 'MODIFIED', 'REPROCESS'], self.warehouseorder_cb)
        self.order_controller.register_callback(
            name+'_deleted', ['DELETED'], self.warehouseorder_deleted_cb)
        self.robotrequest_controller.register_callback(
            name, ['MODIFIED', 'REPROCESS'], self.robotrequest_cb)
        self.mission_api.register_callback(
            name, ['ADDED', 'MODIFIED', 'DELETED', 'REPROCESS'], self.mission_cb)
        self.robot_config.register_callback(
            name+'_recover', ['ADDED', 'MODIFIED', 'REPROCESS'], self.cfg_recover_cb)
        self.robot_config.register_callback(
            name+'_staging_timeout', ['ADDED', 'MODIFIED'], self.cfg_idle_charge_states_cb)

    def disconnect_external_events(self) -> None:
        """Disconnect state machine from external events sources of Cloud Robotics."""
        name = 'ewm-statemachine'
        self.mission_api.robot_api.unregister_callback(name)
        self.order_controller.unregister_callback(name)
        self.order_controller.unregister_callback(name+'_deleted')
        self.robotrequest_controller.unregister_callback(name)
        self.mission_api.unregister_callback(name)
        self.robot_config.unregister_callback(name)

    def _run_before_state_change(self, event: EventData) -> None:
        """Run these methods before state changes."""
        # Log retention time in a state
        retention_time = time.time() - self.state_enter_ts
        self.state_rentention_times.labels(  # pylint: disable=no-member
            robot=self.robot_config.robco_robot_name, state=self.state).observe(retention_time)

        # Update timeout depending on max_idle_time
        if self.states.get('idle') and self.robot_config.conf.maxIdleTime > 0:
            self.states['idle'].timeout = self.robot_config.conf.maxIdleTime

    def _run_after_state_change(self, event: EventData) -> None:
        """Run these methods after state changed."""
        cls = self.__class__
        # Set enter timestmap for prometheus logging
        self.state_enter_ts = time.time()

        # On state change reset errorcount for the state which triggered the event
        if self.state != event.state.name and event.event.name != cls.conf.t_mission_failed:
            self.error_count[event.state.name] = 0

        # Save current state
        lgnum = self.active_who.lgnum if self.active_who else ''
        who = self.active_who.who if self.active_who else ''
        tanum = self.active_wht.tanum if self.active_wht else ''
        subwho = self.active_sub_who.who if self.active_sub_who else ''
        state = RobotConfigurationStatus(
            self.state, self.active_mission, lgnum, who, tanum, subwho)
        self.robot_config.save_robot_state(state)

    def mission_cb(self, name: str, custom_res: Dict) -> None:
        """Use changes of mission CRs to trigger mission status checks."""
        # Only if there is a mission running
        if self.active_mission:
            mission = self.active_mission
            mission_state = self.mission_api.api_return_mission_state(self.active_mission)
            active_action = self.mission_api.api_return_mission_activeaction(self.active_mission)

            # Trigger state machine according to mission state
            if mission_state == RobotMission.STATE_SUCCEEDED:
                _LOGGER.info('Mission %s: %s', self.active_mission, mission_state)
                self.active_mission = ''
                self.mission_succeeded(mission=mission)
            elif mission_state in [*RobotMission.STATES_CANCELED, RobotMission.STATE_FAILED]:
                _LOGGER.info('Mission %s: %s', self.active_mission, mission_state)
                self.active_mission = ''
                self.mission_failed(mission=mission)
            elif active_action == RobotMission.ACTION_DOCKING:
                self.mission_docking(mission=self.active_mission)

    def robot_cb(self, name: str, custom_res: Dict) -> None:
        """Process robot messages."""
        status = custom_res.get('status', {})
        if status.get('robot', {}):
            # Check if the robot is running out of battery when it is at staging area
            if self.state == 'atStaging':
                battery_percentage = status['robot'].get('batteryPercentage', 100.0)
                if battery_percentage < self.robot_config.conf.batteryIdle:
                    self.charge_battery()
            elif self.state == 'movingToStaging':
                battery_percentage = status['robot'].get('batteryPercentage', 100.0)
                if battery_percentage < self.robot_config.conf.batteryMin:
                    self.cancel_active_mission()
                    self.charge_battery()
            elif self.state == 'charging':
                battery_percentage = status['robot'].get('batteryPercentage', 0.0)
                if self.warehouseorders and battery_percentage > self.robot_config.conf.batteryMin:
                    _LOGGER.info(
                        'Warehouse order in queue and battery status is over minimum (%s %%) start'
                        ' processing', battery_percentage)
                    # Cancel charge mission
                    self.cancel_active_mission()
                    # Process warehouse order
                    next_who_crd = next(iter(self.warehouseorders.values()))
                    if isinstance(next_who_crd, WarehouseOrderCRDSpec):
                        self.process_warehouseorder(warehouseorder=next_who_crd.data)
                    else:
                        raise TypeError(
                            'self.warehouseorders includes an element of type "{}"'.format(
                                type(next_who_crd)))

    def cfg_recover_cb(self, name: str, custom_res: Dict) -> None:
        """Process robotconfiguration messages - recover robot."""
        cls = self.__class__
        # Check if robot should recover from robotError state
        if self.state in cls.conf.error_states:
            if custom_res['spec'].get('recoverFromRobotError'):
                _LOGGER.info('Robot recovery requested from robotconfiguration CR')
                self.recover_robot()

    def cfg_idle_charge_states_cb(self, name: str, custom_res: Dict) -> None:
        """Process robotconfiguration messages - request work."""
        if self.robot_config.conf.mode == self.robot_config.conf.MODE_RUN:
            # Request work if robot is at staging position
            if self.state == 'atStaging':
                self.staging_timeout()
            # Cancel charging mission if mode is RUN and battery is loaded
            elif self.state == 'charging':
                if self.mission_api.battery_percentage >= self.robot_config.conf.batteryOk:
                    _LOGGER.info(
                        'Battery is loaded at %s percent, cancel charge mission',
                        self.mission_api.battery_percentage)
                    self.cancel_active_mission()
                    self.charging_canceled()

    def robotrequest_cb(self, name: str, custom_res: Dict) -> None:
        """Process robotrequest messages."""
        status = custom_res.get('status', {})
        if status.get('data'):
            # Convert message data to RequestFromRobot data class
            robot_request = structure(status['data'], RequestFromRobot)

            if self.state in self.conf.awaiting_who_completion_states and self.active_who:
                if (robot_request.lgnum == self.active_who.lgnum
                        and robot_request.notifywhocompletion == self.active_who.who):
                    _LOGGER.info(
                        'Warehouse order %s was confirmed in EWM - robot is proceeding now',
                        self.active_who.who)
                    self.warehouseorder_confirmed()

            if self.state in self.conf.awaiting_wht_completion_states and self.active_wht:
                if (robot_request.lgnum == self.active_wht.lgnum
                        and robot_request.notifywhtcompletion == self.active_wht.tanum):
                    _LOGGER.info(
                        'Warehouse task %s was confirmed in EWM - robot is proceeding now',
                        self.active_wht.tanum)
                    self.warehousetask_confirmed()

    def warehouseorder_cb(self, name: str, spec: Dict) -> None:
        """Process warehouse order CRs."""
        # Convert message data to WarehouseOrderCRDSpec type
        who_crd_spec = structure(spec, WarehouseOrderCRDSpec)

        self.update_warehouseorder(warehouseorder=who_crd_spec)

    def warehouseorder_deleted_cb(self, name: str, spec: Dict) -> None:
        """Delete warehouse order from queue."""
        # Objects from EWM have upper case names
        name_split = name.upper().split('.')
        if len(name_split) == 2:
            who = WhoIdentifier(name_split[0], name_split[1])
            if who in self.warehouseorders:
                self.warehouseorders.pop(who)
                _LOGGER.info('CR of warehouse order %s deleted. Remove it from queue', who)

    def _check_who_kwarg(self, event: EventData) -> bool:
        """Check if warehouseorder is an argument of the transition."""
        obj = event.kwargs.get('warehouseorder')
        if isinstance(obj, WarehouseOrderCRDSpec):
            return True
        else:
            _LOGGER.error(
                'An keyword argument "warehouseorder" of type "WarehouseOrderCRDSpec" must be '
                'provided for the transition')
            return False

    def _sort_warehouseorders(self) -> None:
        """Sort self.warehouseorders by sequence."""
        try:
            self.warehouseorders = OrderedDict(sorted(
                self.warehouseorders.items(), key=lambda items: items[1].sequence))  # type: ignore
        except AttributeError as err:
            _LOGGER.error('Sorting self.warehouseorders failed with this AttributeError: %s', err)

    def _update_who(self, event: EventData) -> None:
        """Update a warehouse order of this state machine."""
        warehouseorder_spec = event.kwargs.get('warehouseorder')

        if (warehouseorder_spec.data.lgnum == self.robot_config.conf.lgnum
                and warehouseorder_spec.data.rsrc == self.robot_config.rsrc):
            _LOGGER.debug(
                'Start updating warehouse order "%s" directly assigned to the robot',
                warehouseorder_spec.data.who)
            self._update_robot_who(warehouseorder_spec)
        else:
            _LOGGER.debug(
                'Start updating warehouse order "%s" not directly assigned to the robot, but a sub'
                ' warehouse order', warehouseorder_spec.who)
            self._update_sub_who(warehouseorder_spec)

    def _update_robot_who(self, warehouseorder_spec: WarehouseOrderCRDSpec) -> None:
        """Update warehouse order directly assigned to this robot."""
        warehouseorder = warehouseorder_spec.data
        who = WhoIdentifier(warehouseorder.lgnum, warehouseorder.who)

        # Update queue of all warehouse order specs
        self.warehouseorders[who] = warehouseorder_spec

        # Sort warehouse order queue
        self._sort_warehouseorders()

        # Update active warehouse order
        # No warehouse order in process and received order is assigned to robot
        if self.active_who is None:
            if self.robot_config.conf.mode != self.robot_config.conf.MODE_RUN:
                _LOGGER.info(
                    'Robot is in mode %s and not active, unassign warehouse order %s',
                    self.robot_config.conf.mode, warehouseorder.who)
                self.unassign_whos()
            elif self.state == 'movingToStaging':
                _LOGGER.info(
                    'New warehouse order %s received while robot is on its way to staging area, '
                    'cancel move mission and start processing', warehouseorder.who)
                # Cancel move mission
                self.cancel_active_mission()
                # Process warehouse order
                self.process_warehouseorder(warehouseorder=warehouseorder)
            elif (self.state == 'charging'
                  and self.mission_api.battery_percentage >= self.robot_config.conf.batteryMin):
                _LOGGER.info(
                    'New warehouse order %s received while robot is charging. Battery percentage '
                    'over minimum, cancel charging and start processing', warehouseorder.who)
                # Cancel charge mission
                self.cancel_active_mission()
                # Process warehouse order
                self.process_warehouseorder(warehouseorder=warehouseorder)
            elif self.state == 'charging':
                _LOGGER.info(
                    'New warehouse order %s received, but robot battery level is too low at "%s" '
                    'percent. Continue charging', warehouseorder.who,
                    self.mission_api.battery_percentage)
                self.unassign_whos()
            elif self.state in self.conf.idle_states:
                _LOGGER.info(
                    'New warehouse order %s received, while robot is in state "%s". Start '
                    'processing', warehouseorder.who, self.state)
                self.process_warehouseorder(warehouseorder=warehouseorder)
            else:
                _LOGGER.error(
                    'New warehouse order %s received, while robot is in state "%s" with no active'
                    'warehouse order. This should not happen', warehouseorder.who, self.state)
        # An active warehouse order changed
        elif warehouseorder.who == self.active_who.who and warehouseorder != self.active_who:
            _LOGGER.info(
                'Active warehouse order %s updated, consider change on next warehouse task '
                'completion', warehouseorder.who)
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

        # Trigger event to find target in pickPackPass process if a pickPackPass order with
        # warehouse tasks arrives
        if warehouseorder == self.active_who and self.active_who.flgwho:
            if (self.state == 'pickPackPass_waitingAtPick'
                    and self.active_who.warehousetasks
                    and not self.active_wht):
                _LOGGER.info(
                    'Active warehouse order %s in pickPackPass process includes warehouse tasks',
                    warehouseorder.who)
                self.pickpackpass_who_with_tasks()

    def _update_sub_who(self, warehouseorder_spec: WarehouseOrderCRDSpec) -> None:
        """Update a sub warehouse order not directly assigned to this robot."""
        warehouseorder = warehouseorder_spec.data
        who = WhoIdentifier(warehouseorder.lgnum, warehouseorder.who)

        # Update dictionary of all warehouse orders
        self.sub_warehouseorders[who] = warehouseorder_spec

        # Update active (sub) warehouse order
        if self.active_who:
            # Sub warehouse order belongs to current active warehouse order
            if warehouseorder.topwhoid == self.active_who.who:
                # No active sub warehouse order
                if self.active_sub_who is None:
                    if self.state == 'pickPackPass_movingtoPickLocation':
                        _LOGGER.info(
                            'New sub warehouse order %s for active warehouse order %s received',
                            warehouseorder.who, self.active_who.who)
                        self.new_active_sub_who(sub_warehouseorder=warehouseorder)
                    else:
                        _LOGGER.error(
                            'Cannot start working on sub warehouse order %s while in state %s',
                            warehouseorder.who, self.state)
                # An active sub warehouse order changed
                elif (warehouseorder.who == self.active_sub_who.who
                      and warehouseorder != self.active_sub_who):
                    _LOGGER.info(
                        'Active sub warehouse order %s updated, consider change on next warehouse '
                        'task completion', warehouseorder.who)
                # A warehouse order was received, but there are no changes
                elif warehouseorder == self.active_sub_who:
                    _LOGGER.debug(
                        'Sub warehouse order received, but no changes. Active sub warehouse "%s" '
                        'order was not updated', self.active_sub_who.who)
            else:
                _LOGGER.info(
                    'Sub warehouse order %s received and enqueued. A different warehouse order is '
                    'already in process', warehouseorder.who)

    def _close_active_who(self, event: EventData) -> None:
        """Close the active warehouse order."""
        # Remove active warehouse order from warehouse order queue
        if isinstance(self.active_who, WarehouseOrder):
            _LOGGER.info('Closing active warehouse order %s', self.active_who.who)
            who = WhoIdentifier(self.active_who.lgnum, self.active_who.who)
            self.warehouseorders.pop(who, None)
            # Remove finalizer from warehouse order CR
            self.order_controller.remove_who_finalizer(self.active_who.lgnum, self.active_who.who)
        else:
            _LOGGER.error('There is no active warehouse order')

        self.active_who = None

    def _close_active_subwho(self, event: EventData) -> None:
        """Close the active sub warehouse order."""
        # Remove active sub warehouse order from warehouse order queue
        if isinstance(self.active_sub_who, WarehouseOrder):
            _LOGGER.info('Closing active sub warehouse order %s', self.active_sub_who.who)
            who = WhoIdentifier(self.active_sub_who.lgnum, self.active_sub_who.who)
            self.warehouseorders.pop(who, None)
            # Remove finalizer from warehouse order CR
            self.order_controller.remove_who_finalizer(
                self.active_sub_who.lgnum, self.active_sub_who.who)

        self.active_sub_who = None

    def _close_active_wht(self, event: EventData) -> None:
        """Close the active warehouse task."""
        if isinstance(self.active_wht, WarehouseTask):
            _LOGGER.info('Closing active warehouse task %s', self.active_wht.tanum)
            # Remove active warehouse task from active warehouse order
            if isinstance(self.active_who, WarehouseOrder):
                self.active_who.warehousetasks[:] = [
                    wht for wht in self.active_who.warehousetasks if (
                        wht.tanum != self.active_wht.tanum)]
            else:
                _LOGGER.error('There is no active warehouse order')
            # Remove active warehouse task from active sub warehouse order
            if isinstance(self.active_sub_who, WarehouseOrder):
                self.active_sub_who.warehousetasks[:] = [
                    wht for wht in self.active_sub_who.warehousetasks if (
                        wht.tanum != self.active_wht.tanum)]
            # Unset active warehouse task
            self.active_wht = None

    def _more_warehouse_tasks(self, event: EventData) -> bool:
        """Check if there are more warehouse tasks in active warehouse order."""
        if isinstance(self.active_who, WarehouseOrder):
            tanum = ''
            # More warehouse tasks than the current active one
            if isinstance(self.active_wht, WarehouseTask):
                tanum = self.active_wht.tanum
            for wht in self.active_who.warehousetasks:
                if wht.tanum != tanum:
                    return True

        return False

    def _more_sub_warehouse_tasks(self, event: EventData) -> bool:
        """Check if there are more warehouse tasks in active sub warehouse order."""
        if isinstance(self.active_sub_who, WarehouseOrder):
            tanum = ''
            # More warehouse tasks than the current active one
            if isinstance(self.active_wht, WarehouseTask):
                tanum = self.active_wht.tanum
            for wht in self.active_sub_who.warehousetasks:
                if wht.tanum != tanum:
                    return True

        return False

    def _save_active_warehouse_order(self, event: EventData) -> None:
        """Save warehouse order as active warehouse order."""
        if isinstance(event.kwargs.get('warehouseorder'), WarehouseOrder):
            if self.active_who:
                _LOGGER.error('Warehouse order %s not closed properly', self.active_who.who)
            self.active_who = event.kwargs.get('warehouseorder')
            # Add finalizer to warehouse order CR
            self.order_controller.add_who_finalizer(self.active_who.lgnum, self.active_who.who)
        else:
            _LOGGER.error('No warehouse order object in parameters.')

    def _save_active_sub_warehouse_order(self, event: EventData) -> None:
        """Save warehouse order as active sub warehouse order."""
        if isinstance(event.kwargs.get('sub_warehouseorder'), WarehouseOrder):
            if self.active_sub_who:
                _LOGGER.error(
                    'Sub warehouse order %s not closed properly', self.active_sub_who.who)
            self.active_sub_who = event.kwargs.get('sub_warehouseorder')
            # Add finalizer to warehouse order CR
            self.order_controller.add_who_finalizer(
                self.active_sub_who.lgnum, self.active_sub_who.who)
        else:
            _LOGGER.error('No warehouse order object in parameters.')

    def _send_first_wht_confirmation(self, event: EventData) -> None:
        """Send first confirmation of a warehouse task."""
        if isinstance(self.active_wht, WarehouseTask):
            confirmation = ConfirmWarehouseTask(
                lgnum=self.active_wht.lgnum, tanum=self.active_wht.tanum,
                rsrc=self.robot_config.rsrc, who=self.active_wht.who,
                confirmationnumber=ConfirmWarehouseTask.FIRST_CONF,
                confirmationtype=ConfirmWarehouseTask.CONF_SUCCESS)

            self.order_controller.confirm_wht(unstructure(confirmation))

            _LOGGER.info(
                'First confirmation for warehouse task %s of warehouse order %s sent to order '
                'manager', self.active_wht.tanum, self.active_wht.who)

            # Delete source information from warehouse task of active warehouse order
            if isinstance(self.active_who, WarehouseOrder):
                for i, wht in enumerate(self.active_who.warehousetasks):
                    if wht.tanum == self.active_wht.tanum:
                        self.active_who.warehousetasks[i].vltyp = ''
                        self.active_who.warehousetasks[i].vlber = ''
                        self.active_who.warehousetasks[i].vlpla = ''
        else:
            raise TypeError('No warehouse task assigned to self.active_wht')

    def _send_second_wht_confirmation(self, event: EventData) -> None:
        """Send second confirmation of a warehouse task."""
        if isinstance(self.active_wht, WarehouseTask):
            confirmation = ConfirmWarehouseTask(
                lgnum=self.active_wht.lgnum, tanum=self.active_wht.tanum,
                rsrc=self.robot_config.rsrc, who=self.active_wht.who,
                confirmationnumber=ConfirmWarehouseTask.SECOND_CONF,
                confirmationtype=ConfirmWarehouseTask.CONF_SUCCESS)

            self.order_controller.confirm_wht(unstructure(confirmation))

            _LOGGER.info(
                'Second confirmation for warehouse task %s of warehouse order %s sent to order '
                'manager', self.active_wht.tanum, self.active_wht.who)
        else:
            raise TypeError('No warehouse task assigned to self.active_wht')

    def _send_first_wht_confirmation_error(self, event: EventData) -> None:
        """Send first confirmation error of a warehouse task."""
        if isinstance(self.active_wht, WarehouseTask):
            confirmation = ConfirmWarehouseTask(
                lgnum=self.active_wht.lgnum, tanum=self.active_wht.tanum,
                rsrc=self.robot_config.rsrc, who=self.active_wht.who,
                confirmationnumber=ConfirmWarehouseTask.FIRST_CONF,
                confirmationtype=ConfirmWarehouseTask.CONF_ERROR)

            self.order_controller.confirm_wht(unstructure(confirmation))

            _LOGGER.info(
                'First confirmation error for warehouse task %s of warehouse order %s sent to '
                'order manager', self.active_wht.tanum, self.active_wht.who)
        else:
            raise TypeError('No warehouse task assigned to self.active_wht')

    def _send_second_wht_confirmation_error(self, event: EventData) -> None:
        """Send second confirmation of a warehouse task."""
        if isinstance(self.active_wht, WarehouseTask):
            confirmation = ConfirmWarehouseTask(
                lgnum=self.active_wht.lgnum, tanum=self.active_wht.tanum,
                rsrc=self.robot_config.rsrc, who=self.active_wht.who,
                confirmationnumber=ConfirmWarehouseTask.SECOND_CONF,
                confirmationtype=ConfirmWarehouseTask.CONF_ERROR)

            self.order_controller.confirm_wht(unstructure(confirmation))

            _LOGGER.info(
                'Second confirmation error for warehouse task %s of warehouse order %s sent to '
                'order manager', self.active_wht.tanum, self.active_wht.who)
        else:
            raise TypeError('No warehouse task assigned to self.active_wht')

    def _send_unassign_whos_request(self, event: EventData) -> None:
        """Request to unassign warehouse orders from robot."""
        who_remove: List[WhoIdentifier] = []
        for whoident, who_crd in self.warehouseorders.items():
            who = who_crd.data
            # Do not unassign the active warehouse order
            if who == self.active_who:
                continue
            # But the other warehouse orders from queue
            for wht in who.warehousetasks:
                confirmation = ConfirmWarehouseTask(
                    lgnum=wht.lgnum, tanum=wht.tanum,
                    rsrc=self.robot_config.rsrc, who=wht.who,
                    confirmationnumber=ConfirmWarehouseTask.FIRST_CONF,
                    confirmationtype=ConfirmWarehouseTask.CONF_UNASSIGN)

                self.order_controller.confirm_wht(unstructure(confirmation))
                who_remove.append(whoident)

                _LOGGER.info(
                    'Request to unassign warehouse order %s sent to order manager',
                    wht.who)
                # Needs to be sent only once per warehouse order
                break

        # Remove unassigned warehouse orders from queue
        for whoident in who_remove:
            self.warehouseorders.pop(whoident, None)

    def _request_work(self, event: EventData) -> None:
        """Request work from order manager."""
        if self.conf.is_new_work_state(event.state.name):
            _LOGGER.info('Requesting new warehouse order from order manager')
            request = RequestFromRobot(
                self.robot_config.conf.lgnum, self.robot_config.rsrc, requestnewwho=True)
        else:
            _LOGGER.info('Requesting warehouse order from order manager')
            request = RequestFromRobot(
                self.robot_config.conf.lgnum, self.robot_config.rsrc, requestwork=True)

        self.robotrequest_controller.send_robot_request(unstructure(request))

    def _cancel_request_work(self, event: EventData) -> None:
        """Cancel request work from order manager."""
        _LOGGER.info(
            'Cancel request work from order manager because of event %s', event.event.name)

        request = RequestFromRobot(
            self.robot_config.conf.lgnum, self.robot_config.rsrc, requestnewwho=True)
        self.robotrequest_controller.delete_robot_request(unstructure(request))

        request = RequestFromRobot(
            self.robot_config.conf.lgnum, self.robot_config.rsrc, requestwork=True)

        self.robotrequest_controller.delete_robot_request(unstructure(request))

    def _request_who_confirmation_notification(self, event: EventData) -> None:
        """
        Send a warehouse order completion request to EWM Order Manager.

        It notifies the robot when the warehouse order was completed.
        """
        if isinstance(self.active_who, WarehouseOrder):
            request = RequestFromRobot(
                self.robot_config.conf.lgnum, self.robot_config.rsrc,
                notifywhocompletion=self.active_who.who)

            self.robotrequest_controller.send_robot_request(unstructure(request))

            _LOGGER.info(
                'Requesting warehouse order completion notification for %s from order manager',
                self.active_who.who)
        else:
            raise TypeError('No warehouse order object in self.active_who')

    def _cancel_who_confirmation_notification(self, event: EventData) -> None:
        """Cancel a warehouse order completion request to EWM Order Manager."""
        if isinstance(self.active_who, WarehouseOrder):
            request = RequestFromRobot(
                self.robot_config.conf.lgnum, self.robot_config.rsrc,
                notifywhocompletion=self.active_who.who)

            _LOGGER.info(
                'Canceling warehouse order completion notification for %s from order manager',
                self.active_who.who)

            self.robotrequest_controller.delete_robot_request(unstructure(request))

        else:
            raise TypeError('No warehouse order object in self.active_who')

    def _request_wht_confirmation_notification(self, event: EventData) -> None:
        """
        Send a  warehouse task completion request to EWM Order Manager.

        It notifies the robot when the warehouse task was completed.
        """
        if isinstance(self.active_wht, WarehouseTask):
            request = RequestFromRobot(
                self.robot_config.conf.lgnum, self.robot_config.rsrc,
                notifywhtcompletion=self.active_wht.tanum)

            self.robotrequest_controller.send_robot_request(unstructure(request))

            _LOGGER.info(
                'Requesting warehouse task completion notification for %s from order manager',
                self.active_wht.tanum)
        else:
            raise TypeError('No warehouse task object in self.active_wht')

    def _decide_whats_next(self, event: EventData) -> None:
        """Decide what the robot should do next."""
        cls = self.__class__
        if self.robot_config.conf.mode == self.robot_config.conf.MODE_CHARGE:
            _LOGGER.info(
                'Robot is in CHARGE mode, battery percentage is %s, start charging',
                self.mission_api.battery_percentage)
            # Cancel active mission before charging if there might be one
            if event.transition.dest not in cls.conf.idle_states:
                self.cancel_active_mission()
            self.charge_battery(target_battery=90.0)
        elif self.mission_api.battery_percentage < self.robot_config.conf.batteryMin:
            _LOGGER.info(
                'Battery level %s is below minimum of %s, start charging',
                self.mission_api.battery_percentage, self.robot_config.conf.batteryMin)
            # Cancel active mission before charging if there might be one
            if event.transition.dest not in cls.conf.idle_states:
                self.cancel_active_mission()
            self.charge_battery()
        elif self.robot_config.conf.mode == self.robot_config.conf.MODE_STOP:
            _LOGGER.info('Robot is in mode STOP, unassign warehouse orders')
            self.unassign_whos()
        elif self.failed_warehouseorders > 3:
            _LOGGER.error(
                'Too many consecutive failed warehouse orders (%s). Robot enters error state',
                self.failed_warehouseorders)
            self.too_many_failed_whos()
        elif self.warehouseorders:
            _LOGGER.info('Warehouse order in queue, start processing')
            next_who_crd = next(iter(self.warehouseorders.values()))
            if isinstance(next_who_crd, WarehouseOrderCRDSpec):
                self.process_warehouseorder(warehouseorder=next_who_crd.data)
            else:
                raise TypeError(
                    'self.warehouseorders includes an element of type "{}"'.format(
                        type(next_who_crd)))
        elif self.robot_config.conf.mode == self.robot_config.conf.MODE_RUN:
            if self.mission_api.api_check_state_ok():
                self._request_work(event)
            else:
                _LOGGER.error('Robot is in a not available state, not requesting work')
        elif self.robot_config.conf.mode == self.robot_config.conf.MODE_IDLE:
            _LOGGER.info('Robot is in IDLE mode, not requesting work')

    def _increase_mission_errorcount(self, event: EventData) -> None:
        """Increase errorcount for the state which triggered the event."""
        self.error_count[event.state.name] += 1

    def _max_mission_errors_reached(self, event: EventData) -> bool:
        """Check if max errorcount is reached."""
        if self.error_count[event.state.name] >= self.robot_config.max_retry_count:
            return True
        return False

    def _is_move_trolley_order(self, event: EventData) -> bool:
        """Check if there is a moveTrolley warehouse order."""
        warehouseorder = event.kwargs.get('warehouseorder')
        if isinstance(warehouseorder, WarehouseOrder):
            # flgwho is False for moveTrolley warehouse orders
            if warehouseorder.flgwho is False:
                return True
        return False

    def _is_pickpackpass_order(self, event: EventData) -> bool:
        """Check if there is a pickPackPass warehouse order."""
        warehouseorder = event.kwargs.get('warehouseorder')
        if isinstance(warehouseorder, WarehouseOrder):
            # flgwho is True for pickPackPass warehouse orders
            if warehouseorder.flgwho is True:
                return True
        return False

    def _create_move_mission(self, event: EventData) -> None:
        """Create a RobCo move mission."""
        if self.active_mission:
            _LOGGER.error('Active mission %s overwritten', self.active_mission)
        self.active_mission = self.mission_api.api_moveto_named_position(
            event.kwargs.get('target'))
        _LOGGER.info(
            'Created move mission %s to %s', self.active_mission, event.kwargs.get('target'))

    def _create_charge_mission(self, event: EventData) -> None:
        """Create a RobCo charge mission."""
        target_battery = event.kwargs.get('target_battery')
        if self.active_mission:
            _LOGGER.error('Active mission %s overwritten', self.active_mission)
        if isinstance(target_battery, float):
            self.active_mission = self.mission_api.api_charge_robot(target_battery=target_battery)
        else:
            self.active_mission = self.mission_api.api_charge_robot()
        _LOGGER.info('Created charge mission %s', self.active_mission)

    def _create_staging_mission(self, event: EventData) -> None:
        """Create a RobCo staging mission."""
        if self.active_mission:
            _LOGGER.error('Active mission %s overwritten', self.active_mission)
        self.active_mission = self.mission_api.api_moveto_staging_position()
        _LOGGER.info('Created staging mission %s', self.active_mission)

    def _create_get_trolley_mission(self, event: EventData) -> None:
        """Create a RobCo get trolley mission."""
        if self.active_mission:
            _LOGGER.error('Active mission %s overwritten', self.active_mission)
        self.active_mission = self.mission_api.api_get_trolley(event.kwargs.get('target'))
        _LOGGER.info(
            'Created get trolley from %s mission %s', event.kwargs.get('target'),
            self.active_mission)

    def _create_return_trolley_mission(self, event: EventData) -> None:
        """Create a RobCo return trolley mission."""
        if self.active_mission:
            _LOGGER.error('Active mission %s overwritten', self.active_mission)
        self.active_mission = self.mission_api.api_return_trolley(event.kwargs.get('target'))
        _LOGGER.info(
            'Created return trolley to %s mission %s', event.kwargs.get('target'),
            self.active_mission)

    def _cancel_active_mission(self, event: EventData) -> None:
        """Cancel the active mission."""
        if self.active_mission:
            success = self.mission_api.api_cancel_mission(self.active_mission)
            if success:
                _LOGGER.info('Active mission %s canceled', self.active_mission)
            else:
                _LOGGER.error('Active mission %s did not exist', self.active_mission)
            self.active_mission = ''
        else:
            _LOGGER.info('There is no active mission which could be canceled')

    def _set_next_charger(self, event: EventData) -> None:
        """Set next charger of available chargers."""
        self.mission_api.api_set_next_charger()

    def _save_warehouse_order_start(self, event: EventData) -> None:
        """Save the start time stamp of a warehouse order."""
        if self.who_ts:
            _LOGGER.error('There is an unfinished warehouse order processing times session')
        self.who_ts = WarehouseOrderTimestamps()

    def _log_warehouse_order_completed(self, event: EventData) -> None:
        """Log warehouse order completion time."""
        if isinstance(self.who_ts, WarehouseOrderTimestamps):
            self.who_ts.end = time.time()
            time_elapsed = self.who_ts.end - self.who_ts.start
            self.who_times.labels(
                robot=self.robot_config.robco_robot_name, order_type=self.conf.get_process_type(
                    event.state.name), activity='completed').observe(time_elapsed)
        else:
            _LOGGER.error('Warehouse order processing times logging not started correctly.')
        # Unset timestamps
        self.who_ts = None

    def _log_get_trolley_completed(self, event: EventData) -> None:
        """Log time until trolley was reached."""
        if isinstance(self.who_ts, WarehouseOrderTimestamps):
            self.who_ts.get_trolley = time.time()
            # For multiple warehouse tasks per order, a return_trolley timestamp is already set
            if self.who_ts.return_trolley:
                time_elapsed = self.who_ts.get_trolley - self.who_ts.return_trolley
            else:
                time_elapsed = self.who_ts.get_trolley - self.who_ts.start
            self.who_times.labels(
                robot=self.robot_config.robco_robot_name, order_type=self.conf.get_process_type(
                    event.state.name), activity='get_trolley').observe(time_elapsed)
        else:
            _LOGGER.error('Warehouse order processing times logging not started correctly.')

    def _log_return_trolley_completed(self, event: EventData) -> None:
        """Log time until trolley was returned."""
        if isinstance(self.who_ts, WarehouseOrderTimestamps):
            self.who_ts.return_trolley = time.time()
            time_elapsed = self.who_ts.return_trolley - self.who_ts.get_trolley
            self.who_times.labels(
                robot=self.robot_config.robco_robot_name, order_type=self.conf.get_process_type(
                    event.state.name), activity='return_trolley').observe(time_elapsed)
        else:
            _LOGGER.error('Warehouse order processing times logging not started correctly.')

    def _log_warehouse_order_fail(self, event: EventData) -> None:
        """Log a failed warehouse order."""
        # Increase error counter
        self.failed_warehouseorders += 1
        # Log processing times
        self._log_warehouse_order_completed(event)
        # Log outcome
        self.who_counter.labels(
            robot=self.robot_config.robco_robot_name, order_type=self.conf.get_process_type(
                event.state.name), result=STATE_FAILED).inc()

    def _log_warehouse_order_success(self, event: EventData) -> None:
        """Log a succeeeded warehouse order."""
        # Reset error counter
        self.failed_warehouseorders = 0
        # Log processing times
        self._log_warehouse_order_completed(event)
        # Log outcome
        self.who_counter.labels(
            robot=self.robot_config.robco_robot_name, order_type=self.conf.get_process_type(
                event.state.name), result=STATE_SUCCEEDED).inc()

    def on_enter_atStaging(self, event: EventData) -> None:
        """Decide what's next when arriving at staging area."""
        self._decide_whats_next(event)

    def on_enter_idle(self, event: EventData) -> None:
        """Decide what's next when robot is not working."""
        # There is no active work
        self.active_who = None
        self.active_sub_who = None
        self.active_wht = None

        self._decide_whats_next(event)

    def on_enter_charging(self, event: EventData) -> None:
        """Create charge mission."""
        _LOGGER.info(
            'Robot starts charge mission at battery level %s %%',
            self.mission_api.battery_percentage)
        self.create_charge_mission()

    def on_enter_movingToStaging(self, event: EventData) -> None:
        """Move to staging area."""
        _LOGGER.info('Robot starts moving to staging area')
        self.create_staging_mission()

    def on_enter_robotError(self, event: EventData) -> None:
        """Print error message."""
        _LOGGER.error(
            'Too many warehouse orders failed. Please check robot and start recovery with flag in '
            'robotconfiguration CR')
        # Reset error counter
        self.failed_warehouseorders = 0
        # Wait at staging area
        self.create_staging_mission()

    def on_enter_moveTrolley_movingToSourceBin(self, event: EventData) -> None:
        """Start moving to the source bin of a warehouse task."""
        if self.active_wht:
            self.active_wht = None

        # Work on the first warehouse task from the warehouse order
        if isinstance(self.active_who, WarehouseOrder):
            if self.active_who.warehousetasks:
                self.active_wht = self.active_who.warehousetasks[0]
                # Create get trolley mission
                _LOGGER.info('Start moving to source bin of trolley %s', self.active_wht.vlenr)
                self.create_get_trolley_mission(target=self.active_wht.vlpla)
            else:
                _LOGGER.error('No warehouse task in warehouse order %s', self.active_who.who)
                self.warehouseorder_aborted()
        else:
            raise TypeError('No warehouse order object in self.active_who')

    def on_enter_moveTrolley_loadingTrolley(self, event: EventData) -> None:
        """Start loading the trolley."""
        cls = self.__class__
        if isinstance(self.active_wht, WarehouseTask):
            _LOGGER.info('Start loading trolley %s', self.active_wht.vlenr)
            if event.event.name == cls.conf.t_mission_succeeded:
                _LOGGER.info('Mission already in state SUCCEEDED')
                self.mission_succeeded(mission=self.active_mission)
        else:
            raise TypeError('No warehouse task object in self.active_wht')

    def on_enter_moveTrolley_movingToTargetBin(self, event: EventData) -> None:
        """Start moving to the target bin of a warehouse task."""
        if isinstance(self.active_wht, WarehouseTask):
            # Create return trolley mission
            _LOGGER.info('Start moving to target bin of trolley %s', self.active_wht.nlenr)
            self.create_return_trolley_mission(target=self.active_wht.nlpla)
        else:
            raise TypeError('No warehouse task object in self.active_wht')

    def on_enter_moveTrolley_unloadingTrolley(self, event: EventData) -> None:
        """Start unloading the trolley."""
        cls = self.__class__
        if isinstance(self.active_wht, WarehouseTask):
            _LOGGER.info('Start unloading trolley %s', self.active_wht.nlenr)
            if event.event.name == cls.conf.t_mission_succeeded:
                _LOGGER.info('Mission already in state SUCCEEDED')
                self.mission_succeeded(mission=self.active_mission)
        else:
            raise TypeError('No warehouse task object in self.active_wht')

    def on_enter_moveTrolley_waitingForErrorRecovery(self, event: EventData) -> None:
        """Wait for moveTrolley error recovery."""
        if isinstance(self.active_who, WarehouseOrder):
            _LOGGER.error(
                'Too many missions failed when returning trolley for moveTrolley warehouse order '
                '%s, waiting for recovery', self.active_who.who)
        else:
            _LOGGER.error(
                'Too many missions failed when returning trolley for moveTrolley warehouse order, '
                'waiting for recovery')

    def on_enter_pickPackPass_movingtoPickLocation(self, event: EventData) -> None:
        """Start moving to pick location."""
        if self.active_wht:
            self.active_wht = None

        # Work on the first warehouse task from the sub warehouse order
        if isinstance(self.active_sub_who, WarehouseOrder):
            if self.active_sub_who.warehousetasks:
                self.active_wht = self.active_sub_who.warehousetasks[0]
                # Create move mission
                _LOGGER.info('Start moving to pick location')
                self.create_move_mission(target=self.active_wht.vlpla)
            else:
                _LOGGER.error(
                    'No warehouse task in sub warehouse order %s', self.active_sub_who.who)
                self.warehouseorder_aborted()
        else:
            _LOGGER.info('No sub warehouse order available, waiting for it')

    def on_enter_pickPackPass_waitingAtPick(self, event: EventData) -> None:
        """Wait at picking position until pick completed."""
        cls = self.__class__
        if event.event.name == cls.conf.t_warehousetask_confirmed:
            _LOGGER.info('Waiting for warehouse task to target')
        elif isinstance(self.active_wht, WarehouseTask):
            _LOGGER.info('Waiting at storage bin %s for pick', self.active_wht.vlpla)
        else:
            _LOGGER.error('Waiting at pick position, but no active warehousetask')

    def on_enter_pickPackPass_movingtoTargetLocation(self, event: EventData) -> None:
        """Start moving to target location."""
        if self.active_wht:
            self.active_wht = None

        # Work on the first warehouse task from the warehouse order to go to the target location
        if isinstance(self.active_who, WarehouseOrder):
            if self.active_who.warehousetasks:
                self.active_wht = self.active_who.warehousetasks[0]
                # Create move mission
                _LOGGER.info('Start moving to target location')
                self.create_move_mission(target=self.active_wht.nlpla)
            else:
                _LOGGER.info(
                    'No warehouse task in warehouse order %s, waiting for it', self.active_who.who)
        else:
            raise TypeError('No warehouse order object in self.active_who')

    def on_enter_pickPackPass_waitingAtTarget(self, event: EventData) -> None:
        """Wait at target position until robot was unloaded."""
        if isinstance(self.active_wht, WarehouseTask):
            _LOGGER.info('Waiting at storage bin %s for unloading', self.active_wht.nlpla)
        else:
            _LOGGER.error('Waiting at target position, but no active warehousetask')

    def on_enter_pickPackPass_waitingForErrorRecovery(self, event: EventData) -> None:
        """Wait for pickPackPass error recovery."""
        if isinstance(self.active_who, WarehouseOrder):
            _LOGGER.error(
                'Too many missions failed on pickPackPass warehouse order %s, waiting '
                'for recovery', self.active_who.who)
        else:
            _LOGGER.error(
                'Too many missions failed on pickPackPass warehouse order, waiting for recovery')
