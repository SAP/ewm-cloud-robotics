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

"""MiR mission controller."""

import logging
import datetime
import time
import threading

from copy import deepcopy
from collections import OrderedDict
from typing import Dict, Optional, OrderedDict as TOrderedDict
from requests import RequestException
from prometheus_client import Counter

from k8scrhandler.k8scrhandler import K8sCRHandler

from .mirrobot import MiRRobot, RobcoMissionStates
from .helper import get_sample_cr, MainLoopController

_LOGGER = logging.getLogger(__name__)


class MissionController(K8sCRHandler):
    """MiR mission controller."""

    m_status_templ = {
        'activeAction': {},
        'missionQueueIds': [],
        'status': RobcoMissionStates.STATE_ACCEPTED,
        'timeOfActuation': datetime.datetime.utcnow().replace(
            tzinfo=datetime.timezone.utc).isoformat()}

    activeaction_templ = {'status': 'DOCKING'}

    # Prometheus logging
    mission_counter = Counter(
        'sap_robot_mission_results', 'Completed Cloud Robotics missions',
        ['robot', 'action', 'target', 'status'])

    action_to_target_mapping = {
        'moveToNamedPosition': 'targetName',
        'charge': 'chargerName',
        'getTrolley': 'dockName',
        'returnTrolley': 'dockName'
        }

    def __init__(self, mir_robot: MiRRobot) -> None:
        """Construct."""
        # Instance of MiR robot
        self._mir_robot = mir_robot

        self._active_mission: Dict[str, Dict] = {}
        self._missions: TOrderedDict[str, Dict] = OrderedDict()
        self._missions_lock = threading.RLock()

        # Init CR superclass
        labels = {}
        labels['cloudrobotics.com/robot-name'] = self._mir_robot.robco_robot_name
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
        self.mission_watcher_thread = threading.Thread(
            target=self._watch_missions_loop, daemon=True)
        self._controller_upstart = True

        # Robot error reset thread
        self.robot_error_reset_thread = threading.Thread(target=self._reset_robot_error_loop)

    def run(self, reprocess: bool = False, multiple_executor_threads: bool = False) -> None:
        """Start running everything."""
        self.mission_watcher_thread.start()
        _LOGGER.info('Automatically resetting errors from MissionController module on MiR robot')
        self.robot_error_reset_thread.start()

        super().run(reprocess=reprocess, multiple_executor_threads=multiple_executor_threads)

    def robco_mission_cb(self, name: str, custom_res: Dict) -> None:
        """Process Cloud Robotics mission CR."""
        cls = self.__class__
        robot = custom_res['metadata'].get('labels', {}).get('cloudrobotics.com/robot-name')
        # Only process missions for this MiR robots
        if robot == self._mir_robot.robco_robot_name:
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
        # Only process missions for this MiR robot
        if robot == self._mir_robot.robco_robot_name:
            if self._active_mission.get('metadata', {}).get('name') == name:
                # Wait a maximum of 10 seconds for a missionQueueId
                mission_queue_id: Optional[str] = None
                for _ in range(20):
                    if self._active_mission.get('metadata', {}).get('name') != name:
                        break
                    if self._active_mission['status']['missionQueueIds']:
                        mission_queue_id = self._active_mission['status']['missionQueueIds'][-1]
                        break
                    time.sleep(0.5)

                if mission_queue_id is not None:
                    if self._mir_robot.cancel_mission(mission_queue_id):
                        _LOGGER.info(
                            'CR of active mission %s deleted. Mission canceled on robot %s', name,
                            robot)
                    else:
                        _LOGGER.error(
                            'CR of active mission %s deleted. Canceling mission on robot %s '
                            'failed', name, robot)
                else:
                    _LOGGER.error(
                        'CR of active mission %s deleted. No missionQueueIds found. Unable to '
                        'cancel mission on robot %s', name, robot)

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
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error('Error watching missions of robot: %s', err, exc_info=True)
                # On uncovered exception in thread save the exception
                self.thread_exceptions['mission_loop'] = err
                # Stop the watcher
                self.stop_watcher()

        _LOGGER.info('Watch missions loop stopped')

    def _watch_missions(self) -> None:
        """Watch missions of the robot."""
        cls = self.__class__
        # Copy mission dict, it might be changed while loop is running
        with self._missions_lock:
            missions = deepcopy(self._missions)
        for mission in missions.values():
            # When active mission was found break the loop
            if self._active_mission:
                break
            # On upstart try to start RUNNING mission first
            if self._controller_upstart is True:
                status_to_run = [
                    RobcoMissionStates.STATE_RUNNING, RobcoMissionStates.STATE_ACCEPTED]
            else:
                status_to_run = [RobcoMissionStates.STATE_ACCEPTED]

            status = mission.get('status', {})
            if status.get('status') in status_to_run:
                # Run mission
                self._active_mission = deepcopy(mission)
                result = self.run_mission()
                # Log mission status in prometheus
                for action in self._active_mission['spec']['actions']:
                    for action_key, action_value in action.items():
                        if action_key in self._mir_robot.mission_mapping:
                            target = action_value.get(
                                cls.action_to_target_mapping.get(action_key), 'UNKNOWN')
                            self.mission_counter.labels(  # pylint: disable=no-member
                                robot=self._mir_robot.robco_robot_name, action=action_key,
                                target=target, status=result).inc()
                self._active_mission.clear()

        # After missions are processed for the first time, controller is not in upstart
        # mode anymore
        if missions:
            self._controller_upstart = False

    def _reset_robot_error_loop(self) -> None:
        """Check and reset robot errors in a loop."""
        loop_control = MainLoopController()
        _LOGGER.info('Reset robot errors loop started')
        while self.thread_run:
            try:
                # Reset potential MiR error
                self._mir_robot.unpause_robot_reset_error()
                loop_control.sleep(2.0)
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error('Error resetting robot errors of robot: %s', err, exc_info=True)
                # On uncovered exception in thread save the exception
                self.thread_exceptions['robot_error_loop'] = err
                # Stop the watcher
                self.stop_watcher()

        _LOGGER.info('Watch robot status loop stopped')

    def run_mission(self) -> str:
        """Run a mission with all its actions."""
        cls = self.__class__
        if not self._active_mission:
            _LOGGER.error('No active mission for robot %s', self._mir_robot.robco_robot_name)
            return RobcoMissionStates.STATE_FAILED

        name = self._active_mission['metadata']['name']

        # Update status, that mission is running now
        if self._active_mission.get('status', {}).get(
                'status') != RobcoMissionStates.STATE_RUNNING:
            _LOGGER.info('Starting mission %s on robot %s', name, self._mir_robot.robco_robot_name)
            self._active_mission['status']['status'] = RobcoMissionStates.STATE_RUNNING
            self._active_mission[
                'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc).isoformat()
            if self.check_cr_exists(name):
                self.update_cr_status(name, self._active_mission['status'])
            else:
                _LOGGER.info('CR of mission %s deleted, canceling mission', name)
                return RobcoMissionStates.STATES_CANCELED
        elif not self._active_mission.get('status'):
            _LOGGER.info('Starting mission %s on robot %s', name, self._mir_robot.robco_robot_name)
            self._active_mission['status'] = cls.m_status_templ.copy()
            self._active_mission['status']['status'] = RobcoMissionStates.STATE_RUNNING
            self._active_mission[
                'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc).isoformat()
            if self.check_cr_exists(name):
                self.update_cr_status(name, self._active_mission['status'])
            else:
                _LOGGER.info('CR of mission %s deleted, canceling mission', name)
                return RobcoMissionStates.STATES_CANCELED
        else:
            _LOGGER.info('Resuming mission %s on robot %s', name, self._mir_robot.robco_robot_name)

        # Run all actions of mission
        try:
            actions = self._active_mission['spec']['actions']
        except KeyError:
            # Update status, that mission failed
            self._active_mission['status']['status'] = RobcoMissionStates.STATE_FAILED
            self._active_mission[
                'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc).isoformat()
            self._active_mission[
                'status']['message'] = 'Mission {} aborted - no actions attribute in CR'.format(
                    name)
            if self.check_cr_exists(name):
                self.update_cr_status(name, self._active_mission['status'])
            else:
                _LOGGER.error('CR of mission %s deleted, cannot update status', name)
            return RobcoMissionStates.STATE_FAILED

        for i, action in enumerate(actions):
            # Get mission queue id from MiR if existing in CR
            try:
                mission_queue_id = self._active_mission['status']['missionQueueIds'][i]
            except IndexError:
                mission_queue_id = None

            if action.get('moveToNamedPosition'):
                result = self.run_action_movetonamedposition(
                    action['moveToNamedPosition']['targetName'], mission_queue_id)
            elif action.get('getTrolley'):
                result = self.run_action_gettrolley(
                    action['getTrolley']['dockName'], mission_queue_id)
            elif action.get('returnTrolley'):
                result = self.run_action_returntrolley(
                    action['returnTrolley']['dockName'], mission_queue_id)
            elif action.get('charge'):
                result = self.run_action_charge(
                    action['charge']['chargerName'], action['charge']['thresholdBatteryPercent'],
                    action['charge']['targetBatteryPercent'], mission_queue_id)
            else:
                self._active_mission['status']['message'] = 'Unknown action'
                result = RobcoMissionStates.STATE_FAILED

            if result in [RobcoMissionStates.STATE_FAILED, RobcoMissionStates.STATE_CANCELED]:
                # Update status, that mission failed
                self._active_mission['status']['status'] = result
                self._active_mission[
                    'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc).isoformat()
                if self.check_cr_exists(name):
                    self.update_cr_status(name, self._active_mission['status'])
                else:
                    _LOGGER.warning('CR of mission %s deleted, cannot update status', name)
                _LOGGER.error(
                    'Mission %s on robot %s ended in state %s with message: %s', name,
                    self._mir_robot.robco_robot_name, result,
                    self._active_mission['status'].get('message'))
                return result

        # each action ran successfully
        # Update status, that mission succeeded
        self._active_mission['status']['status'] = RobcoMissionStates.STATE_SUCCEEDED
        self._active_mission[
            'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                tzinfo=datetime.timezone.utc).isoformat()
        self._active_mission['status']['activeAction'] = {}
        if self.check_cr_exists(name):
            self.update_cr_status(name, self._active_mission['status'])
        else:
            _LOGGER.warning('CR of mission %s deleted, cannot update status', name)
        _LOGGER.info(
            'Mission %s on robot %s  successfully finished', name,
            self._mir_robot.robco_robot_name)
        # Reset localization reset counter
        self._mir_robot.reset_localization_failed_reset_counter()

        return RobcoMissionStates.STATE_SUCCEEDED

    def run_action_charge(
            self, charger_name: str, threshold_battery: float, target_battery: float,
            mission_queue_id: Optional[str] = None) -> str:
        """Run mission charge on the robot."""
        if not self._active_mission:
            # No active mission for robot - action failed
            _LOGGER.error('No active mission for robot %s', self._mir_robot.robco_robot_name)
            self._active_mission['status']['message'] = 'Internal error. Check logs.'
            return RobcoMissionStates.STATE_FAILED
        # if there is no mission queue id, create a new mission
        if mission_queue_id is None:
            try:
                mission_queue_id = self._mir_robot.charge_robot(
                    charger_name, threshold_battery, target_battery)
            except RequestException:
                self._active_mission['status']['message'] = 'Mission failed during creation'
                return RobcoMissionStates.STATE_FAILED

            self._active_mission['status']['missionQueueIds'].append(mission_queue_id)
            self._active_mission[
                'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc).isoformat()
            if self.check_cr_exists(self._active_mission['metadata']['name']):
                self.update_cr_status(
                    self._active_mission['metadata']['name'],
                    self._active_mission['status'])
            else:
                _LOGGER.info(
                    'CR of mission %s deleted, mission was canceled',
                    self._active_mission['metadata']['name'])
                return RobcoMissionStates.STATE_CANCELED

        return self.watch_running_mission(mission_queue_id, False)

    def run_action_movetonamedposition(
            self, target: str, mission_queue_id: Optional[str] = None) -> str:
        """Run mission moveToNamedPosition on the robot."""
        if not self._active_mission:
            # No active mission for robot - action failed
            _LOGGER.error('No active mission for robot %s', self._mir_robot.robco_robot_name)
            self._active_mission['status']['message'] = 'Internal error. Check logs.'
            return RobcoMissionStates.STATE_FAILED
        # if there is no mission queue id, create a new mission
        if mission_queue_id is None:
            try:
                mission_queue_id = self._mir_robot.moveto_named_position(target)
            except RequestException:
                self._active_mission['status']['message'] = 'Mission failed during creation'
                return RobcoMissionStates.STATE_FAILED

            self._active_mission['status']['missionQueueIds'].append(mission_queue_id)
            self._active_mission[
                'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc).isoformat()
            if self.check_cr_exists(self._active_mission['metadata']['name']):
                self.update_cr_status(
                    self._active_mission['metadata']['name'],
                    self._active_mission['status'])
            else:
                _LOGGER.info(
                    'CR of mission %s deleted, mission was canceled',
                    self._active_mission['metadata']['name'])
                return RobcoMissionStates.STATE_CANCELED

        return self.watch_running_mission(mission_queue_id, False)

    def run_action_gettrolley(
            self, dock_name: str, mission_queue_id: Optional[str] = None) -> str:
        """Run mission getTrolley on the robot."""
        if not self._active_mission:
            # No active mission for robot - action failed
            _LOGGER.error('No active mission for robot %s', self._mir_robot.robco_robot_name)
            self._active_mission['status']['message'] = 'Internal error. Check logs.'
            return RobcoMissionStates.STATE_FAILED
        # if there is no mission queue id, create a new mission
        if mission_queue_id is None:
            try:
                mission_queue_id = self._mir_robot.get_trolley(dock_name)
            except RequestException:
                self._active_mission['status']['message'] = 'Mission failed during creation'
                return RobcoMissionStates.STATE_FAILED

            self._active_mission['status']['missionQueueIds'].append(mission_queue_id)
            self._active_mission[
                'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc).isoformat()
            if self.check_cr_exists(self._active_mission['metadata']['name']):
                self.update_cr_status(
                    self._active_mission['metadata']['name'],
                    self._active_mission['status'])
            else:
                _LOGGER.info(
                    'CR of mission %s deleted, mission was canceled',
                    self._active_mission['metadata']['name'])
                return RobcoMissionStates.STATE_CANCELED

        return self.watch_running_mission(mission_queue_id, True)

    def run_action_returntrolley(
            self, dock_name: str, mission_queue_id: Optional[str] = None) -> str:
        """Run mission returnTrolley on the robot."""
        if not self._active_mission:
            # No active mission for robot - action failed
            _LOGGER.error('No active mission for robot %s', self._mir_robot.robco_robot_name)
            self._active_mission['status']['message'] = 'Internal error. Check logs.'
            return RobcoMissionStates.STATE_FAILED
        # if there is no mission queue id, create a new mission
        if mission_queue_id is None:
            try:
                mission_queue_id = self._mir_robot.return_trolley(dock_name)
            except RequestException:
                self._active_mission['status']['message'] = 'Mission failed during creation'
                return RobcoMissionStates.STATE_FAILED

            self._active_mission['status']['missionQueueIds'].append(mission_queue_id)
            self._active_mission[
                'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc).isoformat()
            if self.check_cr_exists(self._active_mission['metadata']['name']):
                self.update_cr_status(
                    self._active_mission['metadata']['name'],
                    self._active_mission['status'])
            else:
                _LOGGER.info(
                    'CR of mission %s deleted, mission was canceled',
                    self._active_mission['metadata']['name'])
                return RobcoMissionStates.STATE_CANCELED

        return self.watch_running_mission(mission_queue_id, True)

    def watch_running_mission(self, mission_queue_id: str, with_active_action: bool) -> str:
        """Watch a running mission and return its result when finished."""
        try:
            state_resp = self._mir_robot.get_mission_state(mission_queue_id)
        except RequestException:
            self._active_mission['status']['message'] = 'Mission state could not be determined'
            return RobcoMissionStates.STATE_FAILED

        status = state_resp[0]
        message = state_resp[1]

        # Wait until movement was successfull or failed
        loop_control = MainLoopController()
        while status in (RobcoMissionStates.STATE_ACCEPTED, RobcoMissionStates.STATE_RUNNING):
            loop_control.sleep(1.0)
            try:
                state_resp = self._mir_robot.get_mission_state(mission_queue_id)
            except RequestException:
                self._active_mission['status']['message'] = 'Mission state could not be determined'
                return RobcoMissionStates.STATE_FAILED

            status = state_resp[0]
            message = state_resp[1]

            # Get active action of robot
            try:
                active_action = {
                    'status': self._mir_robot.get_mission_active_action(mission_queue_id)}
            except RequestException:
                _LOGGER.error('Error getting activeAction')
                active_action = {}

            # Update status CR when status changes to RUNNING
            if ((status != self._active_mission['status']['status']
                 or (active_action != self._active_mission['status'].get('activeAction')
                     and with_active_action is True))
                    and status == RobcoMissionStates.STATE_RUNNING):
                self._active_mission['status']['status'] = status
                if with_active_action is True:
                    self._active_mission['status']['activeAction'] = deepcopy(active_action)
                self._active_mission[
                    'status']['timeOfActuation'] = datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc).isoformat()
                if self.check_cr_exists(self._active_mission['metadata']['name']):
                    self.update_cr_status(
                        self._active_mission['metadata']['name'],
                        self._active_mission['status'])
                else:
                    _LOGGER.info(
                        'CR of mission %s deleted, mission was canceled',
                        self._active_mission['metadata']['name'])
                    return RobcoMissionStates.STATE_CANCELED

        # Save last status message before quitting
        self._active_mission['status']['message'] = message
        return status
