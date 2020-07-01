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

"""RobCo mission API interface for robcoewm robot."""

import sys
import traceback
import logging
import time
import threading

from collections import OrderedDict
from typing import Dict, Generator, Optional

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.robot import RobotMission, RobcoRobotStates

from k8scrhandler.k8scrhandler import K8sCRHandler

from .robco_robot_api import RobCoRobotAPI
from .robotconfigcontroller import RobotConfigurationController

_LOGGER = logging.getLogger(__name__)


class RobCoMissionAPI(K8sCRHandler):
    """Send commands to RobCo robots via Kubernetes CR."""

    def __init__(self, robot_config: RobotConfigurationController,
                 robot_api: RobCoRobotAPI) -> None:
        """Construct."""
        # Robot Configuration Controller
        self.robot_config = robot_config
        # Mission status dictionary
        self.mission_status: OrderedDict[  # pylint: disable=unsubscriptable-object
            str, RobotMission] = OrderedDict()
        self.mission_status_lock = threading.RLock()

        template_cr = get_sample_cr('robco_mission')

        self.labels = {}
        self.labels['cloudrobotics.com/robot-name'] = self.robot_config.robco_robot_name
        super().__init__(
            'mission.cloudrobotics.com',
            'v1alpha1',
            'missions',
            'default',
            template_cr,
            self.labels
        )

        # RobCo Robot API
        self.robot_api = robot_api
        self.battery_percentage = 100.0
        self.robot_state = RobcoRobotStates.STATE_UNDEFINED
        self.trolley_attached = False

        # Set active charger
        self._chargers = self.robot_config.conf.chargers.copy()
        self._chargers_generator = self._iterate_chargers()
        self.charger = next(self._chargers_generator, '')
        _LOGGER.info('Using chargers: %s', self._chargers)

        # Register robot status update callback
        self.robot_api.register_callback(
            'RobCoMissionAPI', ['ADDED', 'MODIFIED'], self.update_robot_status_cb)

        # Register mission status update callback
        self.register_callback(
            'update_mission_status', ['ADDED', 'MODIFIED', 'REPROCESS'],
            self.update_mission_status_cb)
        self.register_callback('mission_deleted', ['DELETED'], self.mission_deleted_cb)

        # Thread to check for deleted mission CRs
        self.deleted_missions_thread = threading.Thread(target=self._deleted_missions_checker)

    def update_mission_status_cb(self, name: str, custom_res: Dict) -> None:
        """Update self.mission_status."""
        # OrderedDict must not be changed when iterating (self.mission_status)
        with self.mission_status_lock:
            # if status is set, update the dictionary
            if custom_res.get('status'):
                new_mstatus = self.mission_status.get(name, RobotMission(name))
                new_mstatus.status = custom_res['status'].get('status', '')
                new_mstatus.active_action = custom_res[
                    'status'].get('activeAction', {}).get('status', '')
                self.mission_status[name] = new_mstatus

            # Delete finished missions with status SUCCEEDED, CANCELED, FAILED
            # Keep maximum of 50 missions
            finished = 0
            delete_missions = []
            cleanup = 0
            cleanup_mission_dict = []
            # Start counting from the back of mission OrderedDict
            for mission, status in reversed(self.mission_status.items()):
                if status.status in [RobotMission.STATE_SUCCEEDED,
                                     RobotMission.STATE_CANCELED,
                                     RobotMission.STATE_FAILED]:
                    finished += 1
                    if finished >= 50:
                        # Save mission to be deleted
                        delete_missions.append(mission)

                # Collect missions to clean up
                if status.status == RobotMission.STATE_DELETED:
                    cleanup += 1
                    if cleanup >= 50:
                        cleanup_mission_dict.append(mission)

            # Delete mission CR and mark it as DELETED
            for mission in delete_missions:
                deleted = False
                if self.check_cr_exists(mission):
                    self.delete_cr(mission)
                    deleted = True
                    _LOGGER.info('RobCo mission CR %s was cleaned up', mission)
                else:
                    deleted = True
                if deleted:
                    # If mission was deleted mark it as deleted
                    self.mission_status[mission].status = RobotMission.STATE_DELETED

            # Clean up self.mission_status dictionary
            for mission in cleanup_mission_dict:
                self.mission_status.pop(mission, None)

    def mission_deleted_cb(self, name: str, custom_res: Dict) -> None:
        """Update self.mission_status."""
        with self.mission_status_lock:
            # If mission was deleted mark it as deleted
            if self.mission_status.get(name):
                self.mission_status[name].status = RobotMission.STATE_DELETED

    def update_robot_status_cb(self, name: str, custom_res: Dict) -> None:
        """Update robot status attributes."""
        # if status is set, update the attributes
        if custom_res.get('status'):
            try:
                self.battery_percentage = custom_res['status']['robot']['batteryPercentage']
            except KeyError:
                _LOGGER.error('No "batteryPercentage" attribute in robot CR')
            try:
                self.robot_state = custom_res['status']['robot']['state']
            except KeyError:
                _LOGGER.error('No "state" attribute in robot CR')
            self.trolley_attached = custom_res[
                'status'].get('configuration', {}).get('trolleyAttached', False)

    def check_deleted_missions(self):
        """Set self.mission_state entries with no CR to state DELETED."""
        cr_resp = self.list_all_cr()
        _LOGGER.debug('%s/%s: Check deleted CR: Got all CRs.', self.group, self.plural)
        if cr_resp:
            # Collect names of all existing CRs
            mission_crs = {}
            for obj in cr_resp['items']:
                spec = obj.get('spec')
                if not spec:
                    continue
                metadata = obj.get('metadata')
                mission_crs[metadata['name']] = True

            # Compare with self.missions_status
            delete_missions = []
            with self.mission_status_lock:
                for mission in self.mission_status.keys():
                    if mission not in mission_crs:
                        delete_missions.append(mission)

                for mission in delete_missions:
                    self.mission_status[mission].status = RobotMission.STATE_DELETED

    def run(self, watcher: bool = True, reprocess: bool = False,
            multiple_executor_threads: bool = False) -> None:
        """Start running all callbacks."""
        # Start callbacks for robot status
        self.robot_api.run(watcher=watcher)
        # If reprocessing is enabled, check for deleted mission CRs too
        if reprocess:
            self.deleted_missions_thread.start()
        # start own callbacks
        super().run(watcher=watcher, reprocess=reprocess)

    def _deleted_missions_checker(self):
        """Continously check for deleted mission CR and mark them deleted."""
        _LOGGER.info(
            'Start continiously checking for deleted mission CRs')
        while self.thread_run:
            try:
                self.check_deleted_missions()
            except Exception as exc:  # pylint: disable=broad-except
                exc_info = sys.exc_info()
                _LOGGER.error(
                    '%s/%s: Error checking for deleted missions - Exception: "%s" / "%s" - '
                    'TRACEBACK: %s', self.group, self.plural, exc_info[0], exc_info[1],
                    traceback.format_exception(*exc_info))
                # On uncovered exception in thread save the exception
                self.thread_exceptions['deleted_missions_checker'] = exc
                # Stop the watcher
                self.stop_watcher()
            finally:
                # Wait 10 seconds
                if self.thread_run:
                    time.sleep(10)

    def _create_mission(self, spec: Dict) -> str:
        # Use Unix timestamp as mission name
        mission_name = str(time.time())
        # Create CR
        self.create_cr(mission_name, self.labels, spec)
        # Return mission_name
        return mission_name

    def _iterate_chargers(self) -> Generator:
        """Iterate over self.chargers."""
        while True:
            for charger in self._chargers:
                yield charger

    def api_cancel_mission(self, name: str) -> bool:
        """Cancel a mission."""
        if self.check_cr_exists(name):
            # Mission is canceled by deleting its CR
            self.delete_cr(name)
            return True
        else:
            _LOGGER.error('Mission CR %s does not exist and cannot be deleted', name)
            return False

    def api_moveto_named_position(self, target: str) -> str:
        """Move robot to a storage bin position of the map."""
        # Get relevant parameters
        action = {'moveToNamedPosition': {'targetName': target}}
        spec = {'actions': [action]}
        # Create mission
        return self._create_mission(spec)

    def api_get_trolley(self, dock_name: str) -> str:
        """Get a trolley from a dock."""
        # Get relevant parameters
        action = {'getTrolley': {'dockName': dock_name}}
        spec = {'actions': [action]}
        # Create mission
        return self._create_mission(spec)

    def api_return_trolley(self, dock_name: str) -> str:
        """Get a trolley to a dock."""
        # Get relevant parameters
        action = {'returnTrolley': {'dockName': dock_name}}
        spec = {'actions': [action]}
        # Create mission
        return self._create_mission(spec)

    def api_moveto_staging_position(self) -> str:
        """Move robot to a staging position of the map."""
        # Get relevant parameters
        # TODO support multiple staging areas
        action = {'moveToNamedPosition': {'targetName': 'Staging'}}
        spec = {'actions': [action]}
        # Create mission
        return self._create_mission(spec)

    def api_charge_robot(self, target_battery: Optional[float] = None) -> str:
        """Charge robot at the charging position."""
        target_b = self.robot_config.conf.batteryOk
        threshold_b = self.robot_config.conf.batteryIdle
        if target_battery is not None:
            target_b = target_battery
            threshold_b = target_battery
        # Get relevant parameters
        action = {'charge': {'chargerName': self.charger,
                             'thresholdBatteryPercent': threshold_b,
                             'targetBatteryPercent': target_b}}
        spec = {'actions': [action]}
        # Create mission
        return self._create_mission(spec)

    def api_set_next_charger(self) -> None:
        """Switch to next charger of configuration."""
        # Check if chargers changed in the meantime
        if self._chargers != self.robot_config.conf.chargers:
            self._chargers = self.robot_config.conf.chargers.copy()
            self._chargers_generator = self._iterate_chargers()
            _LOGGER.info('Available chargers changed to: %s', self._chargers)
        # Get next charger from generator
        self.charger = next(self._chargers_generator, '')
        _LOGGER.info('Set charger %s', self.charger)

    def api_return_mission_activeaction(self, mission_name: str) -> str:
        """Return active_action of a mission."""
        mission = self.mission_status.get(mission_name, RobotMission(mission_name))

        return mission.active_action

    def api_return_mission_state(self, mission_name: str) -> str:
        """Return state of a mission."""
        mission = self.mission_status.get(mission_name, RobotMission(mission_name))

        return mission.status

    def api_check_state_ok(self) -> bool:
        """Check if robot is in state ok."""
        return bool(self.robot_state == RobcoRobotStates.STATE_AVAILABLE)
