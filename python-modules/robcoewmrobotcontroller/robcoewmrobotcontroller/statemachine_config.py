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

"""Config for robot state machine of robcoewm robots."""

from typing import Dict, List


class RobotEWMConfig:
    """Configuration for robot state machine to handle SAP EWM warehouse orders."""

    # trigger
    t_start_fresh_machine = 'start_fresh_machine'
    t_process_warehouseorder = 'process_warehouseorder'
    t_update_warehouseorder = 'update_warehouseorder'
    t_create_move_mission = 'create_move_mission'
    t_create_charge_mission = 'create_charge_mission'
    t_create_staging_mission = 'create_staging_mission'
    t_create_get_trolley_mission = 'create_get_trolley_mission'
    t_create_return_trolley_mission = 'create_return_trolley_mission'
    t_cancel_active_mission = 'cancel_active_mission'
    t_mission_docking = 'mission_docking'
    t_mission_succeeded = 'mission_succeeded'
    t_mission_failed = 'mission_failed'
    t_warehouseorder_aborted = 'warehouseorder_aborted'
    t_warehouseorder_confirmed = 'warehouseorder_confirmed'
    t_warehousetask_confirmed = 'warehousetask_confirmed'
    t_pickpackpass_who_with_tasks = 'pickpackpass_who_with_tasks'
    t_new_active_sub_who = 'new_active_sub_who'
    t_charge_battery = 'charge_battery'
    t_go_staging = 'go_staging'
    t_too_many_failed_whos = 'too_many_failed_whos'
    t_request_work = 'request_work'
    t_recover_robot = 'recover_robot'

    # processes
    p_moveTrolley = 'moveTrolley'
    p_pickPackPass = 'pickPackPass'
    processes = [p_moveTrolley, p_pickPackPass]

    @classmethod
    def get_process_type(cls, state: str) -> str:
        """Get process type for the state."""
        process = state[:state.rfind('_')]
        if process in cls.processes:
            return process
        return ''

    # states for state machine
    states = [
        'robotError', 'movingToStaging', 'charging',
        {'name': 'atStaging', 'timeout': 300, 'on_timeout': t_request_work},
        {'name': 'noWork', 'timeout': 15, 'on_timeout': t_go_staging},
        {'name': p_moveTrolley, 'children': [
            'movingToSourceBin', 'movingToTargetBin', 'loadingTrolley', 'unloadingTrolley',
            'waitingForErrorRecovery']},
        {'name': p_pickPackPass, 'children': [
            'movingtoPickLocation', 'movingtoTargetLocation', 'waitingAtPick', 'waitingAtTarget',
            'waitingForErrorRecovery']}
        ]

    idle_states = ['atStaging', 'noWork']
    awaiting_who_completion_states = [
        'moveTrolley_waitingForErrorRecovery', 'pickPackPass_waitingForErrorRecovery',
        'pickPackPass_waitingAtTarget']
    awaiting_wht_completion_states = ['pickPackPass_waitingAtPick']
    error_states = [
        'moveTrolley_waitingForErrorRecovery', 'pickPackPass_waitingForErrorRecovery',
        'robotError']

    @classmethod
    def is_new_work_state(cls, state: str) -> bool:
        """Identify if request for work has to be created with requestnewwho parameter set."""
        if state[:state.rfind('_')] in cls.processes or state == 'noWork':
            return True
        return False

    # transitions for state machine
    transitions: List[Dict] = [
        # Start fresh state machine
        {'trigger': t_start_fresh_machine,
         'source': 'noWork',
         'dest': 'noWork'},
        # Order Manager input
        {'trigger': t_update_warehouseorder,
         'source': '*',
         'dest': None,
         'conditions': '_check_who_kwarg',
         'after': '_update_who'},
        # RobCo Missions
        {'trigger': t_create_move_mission,
         'source': '*',
         'dest': None,
         'after': '_create_move_mission'},
        {'trigger': t_create_charge_mission,
         'source': '*',
         'dest': None,
         'after': '_create_charge_mission'},
        {'trigger': t_create_staging_mission,
         'source': '*',
         'dest': None,
         'after': '_create_staging_mission'},
        {'trigger': t_create_get_trolley_mission,
         'source': '*',
         'dest': None,
         'after': '_create_get_trolley_mission'},
        {'trigger': t_create_return_trolley_mission,
         'source': '*',
         'dest': None,
         'after': '_create_return_trolley_mission'},
        {'trigger': t_cancel_active_mission,
         'source': '*',
         'dest': None,
         'after': '_cancel_active_mission'},
        # general transitions
        {'trigger': t_go_staging,
         'source': 'noWork',
         'dest': 'movingToStaging'},
        {'trigger': t_too_many_failed_whos,
         'source': idle_states,
         'dest': 'robotError'},
        {'trigger': t_mission_succeeded,
         'source': 'movingToStaging',
         'dest': 'atStaging'},
        {'trigger': t_mission_failed,
         'source': 'movingToStaging',
         'dest': '=',
         'unless': '_max_mission_errors_reached',
         'before': '_increase_mission_errorcount'},
        {'trigger': t_mission_failed,
         'source': 'movingToStaging',
         'dest': 'noWork',
         'conditions': '_max_mission_errors_reached'},
        {'trigger': t_request_work,
         'source': 'atStaging',
         'dest': 'atStaging'},
        {'trigger': t_charge_battery,
         'source': [*idle_states, 'movingToStaging'],
         'dest': 'charging'},
        {'trigger': t_mission_succeeded,
         'source': 'charging',
         'dest': 'noWork'},
        {'trigger': t_mission_failed,
         'source': 'charging',
         'dest': '=',
         'unless': '_max_mission_errors_reached',
         'before': ['_set_next_charger', '_increase_mission_errorcount']},
        {'trigger': t_mission_failed,
         'source': 'charging',
         'dest': 'noWork',
         'conditions': '_max_mission_errors_reached',
         'before': '_set_next_charger'},
        {'trigger': t_recover_robot,
         'source': 'robotError',
         'dest': 'noWork'},
        # Start EWM processes transitions
        {'trigger': t_process_warehouseorder,
         'source': [
             'noWork', 'charging', 'atStaging', 'movingToStaging',
             'moveTrolley_unloadingTrolley', 'pickPackPass_waitingAtTarget'],
         'dest': 'moveTrolley_movingToSourceBin',
         'conditions': '_is_move_trolley_order',
         'before': '_save_active_warehouse_order',
         'after': '_save_warehouse_order_start'},
        {'trigger': t_process_warehouseorder,
         'source': [
             'noWork', 'charging', 'atStaging', 'movingToStaging',
             'moveTrolley_unloadingTrolley', 'pickPackPass_waitingAtTarget'],
         'dest': 'pickPackPass_movingtoPickLocation',
         'conditions': '_is_pickpackpass_order',
         'before': '_save_active_warehouse_order',
         'after': '_save_warehouse_order_start'},
        # moveTrolley transitions
        {'trigger': t_warehouseorder_aborted,
         'source': 'moveTrolley_movingToSourceBin',
         'dest': 'noWork',
         'before': ['_log_warehouse_order_fail', '_close_active_who']},
        {'trigger': t_mission_failed,
         'source': [
             'moveTrolley_movingToSourceBin', 'moveTrolley_loadingTrolley'],
         'dest': 'moveTrolley_movingToSourceBin',
         'unless': '_max_mission_errors_reached',
         'before': '_increase_mission_errorcount'},
        {'trigger': t_mission_failed,
         'source': [
             'moveTrolley_movingToTargetBin', 'moveTrolley_unloadingTrolley'],
         'dest': 'moveTrolley_movingToTargetBin',
         'unless': '_max_mission_errors_reached',
         'before': '_increase_mission_errorcount'},
        {'trigger': t_mission_failed,
         'source': [
             'moveTrolley_movingToSourceBin', 'moveTrolley_loadingTrolley'],
         'dest': 'noWork',
         'conditions': '_max_mission_errors_reached',
         'before': [
             '_send_first_wht_confirmation_error', '_log_get_trolley_completed',
             '_log_warehouse_order_fail', '_close_active_who']},
        {'trigger': t_mission_failed,
         'source': [
             'moveTrolley_movingToTargetBin', 'moveTrolley_unloadingTrolley'],
         'dest': 'moveTrolley_waitingForErrorRecovery',
         'conditions': '_max_mission_errors_reached',
         'before': [
             '_send_second_wht_confirmation_error', '_log_return_trolley_completed',
             '_log_warehouse_order_fail'],
         'after': '_request_who_confirmation_notification'},
        {'trigger': t_mission_docking,
         'source': 'moveTrolley_movingToSourceBin',
         'dest': 'moveTrolley_loadingTrolley'},
        {'trigger': t_mission_docking,
         'source': 'moveTrolley_loadingTrolley',
         'dest': None},
        {'trigger': t_mission_succeeded,
         'source': 'moveTrolley_movingToSourceBin',
         'dest': 'moveTrolley_loadingTrolley'},
        {'trigger': t_mission_succeeded,
         'source': 'moveTrolley_loadingTrolley',
         'dest': 'moveTrolley_movingToTargetBin',
         'before': ['_send_first_wht_confirmation', '_log_get_trolley_completed']},
        {'trigger': t_mission_docking,
         'source': 'moveTrolley_movingToTargetBin',
         'dest': 'moveTrolley_unloadingTrolley'},
        {'trigger': t_mission_docking,
         'source': 'moveTrolley_unloadingTrolley',
         'dest': None},
        {'trigger': t_mission_succeeded,
         'source': 'moveTrolley_movingToTargetBin',
         'dest': 'moveTrolley_unloadingTrolley'},
        {'trigger': t_mission_succeeded,
         'source': 'moveTrolley_unloadingTrolley',
         'dest': 'moveTrolley_movingToSourceBin',
         'conditions': '_more_warehouse_tasks',
         'before': '_send_second_wht_confirmation'},
        {'trigger': t_mission_succeeded,
         'source': 'moveTrolley_unloadingTrolley',
         'dest': 'noWork',
         'unless': '_more_warehouse_tasks',
         'before': [
             '_send_second_wht_confirmation', '_log_return_trolley_completed',
             '_log_warehouse_order_success', '_close_active_who']},
        {'trigger': t_warehouseorder_confirmed,
         'source': 'moveTrolley_waitingForErrorRecovery',
         'dest': 'noWork',
         'before': '_close_active_who'},
        # pickPackPass transitions
        {'trigger': t_new_active_sub_who,
         'source': 'pickPackPass_movingtoPickLocation',
         'dest': '=',
         'before': '_save_active_sub_warehouse_order'},
        {'trigger': t_warehouseorder_aborted,
         'source': 'pickPackPass_movingtoPickLocation',
         'dest': 'pickPackPass_waitingForErrorRecovery',
         'before': '_log_warehouse_order_fail'},
        {'trigger': t_mission_failed,
         'source': ['pickPackPass_movingtoPickLocation', 'pickPackPass_movingtoTargetLocation'],
         'dest': '=',
         'unless': '_max_mission_errors_reached',
         'before': '_increase_mission_errorcount'},
        {'trigger': t_mission_failed,
         'source': 'pickPackPass_movingtoPickLocation',
         'dest': 'pickPackPass_waitingForErrorRecovery',
         'conditions': '_max_mission_errors_reached',
         'before': '_log_warehouse_order_fail'},
        {'trigger': t_mission_failed,
         'source': 'pickPackPass_movingtoTargetLocation',
         'dest': 'pickPackPass_waitingForErrorRecovery',
         'conditions': '_max_mission_errors_reached',
         'before': [
             '_send_second_wht_confirmation_error', '_log_warehouse_order_fail'],
         'after': '_request_who_confirmation_notification'},
        {'trigger': t_mission_succeeded,
         'source': 'pickPackPass_movingtoPickLocation',
         'dest': 'pickPackPass_waitingAtPick',
         'after': '_request_wht_confirmation_notification'},
        {'trigger': t_warehousetask_confirmed,
         'source': 'pickPackPass_waitingAtPick',
         'dest': 'pickPackPass_movingtoPickLocation',
         'conditions': '_more_sub_warehouse_tasks',
         'before': '_close_active_wht'},
        {'trigger': t_warehousetask_confirmed,
         'source': 'pickPackPass_waitingAtPick',
         'dest': '=',
         'unless': ['_more_sub_warehouse_tasks', '_more_warehouse_tasks'],
         'before': ['_request_work', '_close_active_wht']},
        {'trigger': t_pickpackpass_who_with_tasks,
         'source': 'pickPackPass_waitingAtPick',
         'dest': 'pickPackPass_movingtoTargetLocation',
         'conditions': '_more_warehouse_tasks',
         'unless': '_more_sub_warehouse_tasks',
         'before': '_close_active_wht',
         'after': '_send_first_wht_confirmation'},
        {'trigger': t_mission_succeeded,
         'source': 'pickPackPass_movingtoTargetLocation',
         'dest': 'pickPackPass_waitingAtTarget',
         'after': '_request_who_confirmation_notification'},
        {'trigger': t_warehouseorder_confirmed,
         'source': 'pickPackPass_waitingAtTarget',
         'dest': 'noWork',
         'before': [
             '_close_active_wht', '_log_warehouse_order_success', '_close_active_who',
             '_close_active_subwho']},
        {'trigger': t_warehouseorder_confirmed,
         'source': 'pickPackPass_waitingForErrorRecovery',
         'dest': 'noWork',
         'before': ['_close_active_wht', '_close_active_who', '_close_active_subwho']}
        ]

    @classmethod
    def check_transitions_complete(cls, obj: object) -> None:
        """Check if class contains all methods for transitions."""
        object_methods = [
            method_name for method_name in dir(obj) if callable(getattr(obj, method_name))]

        categories = ['prepare', 'conditions', 'unless', 'before', 'after']

        for transition in cls.transitions:
            for cat in categories:
                callbacks = transition.get(cat, [])
                if not isinstance(callbacks, list):
                    callbacks = [callbacks]
                for callb in callbacks:
                    if callb not in object_methods:
                        raise AttributeError(
                            'Callback method {} for trigger {} does not exist'.format(
                                callb, transition.get('trigger')))
