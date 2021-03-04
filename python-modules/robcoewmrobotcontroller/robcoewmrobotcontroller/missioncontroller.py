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

import logging
import time
import threading

from collections import OrderedDict
from typing import Dict, Generator, Optional

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.robot import RobotMission, RobcoRobotStates

from k8scrhandler.k8scrhandler import K8sCRHandler

from .robotcontroller import RobotHandler
from .robotconfigcontroller import RobotConfigurationController

_LOGGER = logging.getLogger(__name__)


class MissionHandler(K8sCRHandler):
    """Handle Mission custom resources."""

    def __init__(self) -> None:
        """Construct."""
        template_cr = get_sample_cr('robco_mission')

        labels: Dict[str, str] = {}
        super().__init__(
            'mission.cloudrobotics.com',
            'v1alpha1',
            'missions',
            'default',
            template_cr,
            labels
        )


class MissionController:
    """Send commands to RobCo robots via Kubernetes CR."""

    def __init__(self, robot_config: RobotConfigurationController, mission_handler: MissionHandler,
                 robot_handler: RobotHandler) -> None:
        """Construct."""
        # Mission handler
        self.handler = mission_handler
        # Robot Configuration Controller
        self.robot_config = robot_config
        # Mission status dictionary
        self.mission_status: OrderedDict[  # pylint: disable=unsubscriptable-object
            str, RobotMission] = OrderedDict()
        self.mission_status_lock = threading.Lock()

        # Labels used to create new missions
        self.labels = {}
        self.labels['cloudrobotics.com/robot-name'] = self.robot_config.robot_name

        # RobCo Robot API
        self.robot_handler = robot_handler
        self.battery_percentage = 100.0
        self.robot_state = RobcoRobotStates.STATE_UNDEFINED
        self.trolley_attached = False

        # Set active charger
        self._chargers = self.robot_config.conf.chargers.copy()
        self._chargers_generator = self._iterate_chargers()
        self.charger = next(self._chargers_generator, '')
        _LOGGER.info('Using chargers: %s', self._chargers)

        # Register robot status update callback
        self.robot_handler.register_callback(
            'mission_controller_{}'.format(self.robot_config.robot_name),
            ['ADDED', 'MODIFIED'], self.update_robot_status_cb, self.robot_config.robot_name)

        # Register mission status update callback
        self.handler.register_callback(
            'update_mission_status_{}'.format(self.robot_config.robot_name),
            ['ADDED', 'MODIFIED', 'REPROCESS'], self.update_mission_status_cb,
            self.robot_config.robot_name)
        self.handler.register_callback(
            'mission_deleted_{}'.format(self.robot_config.robot_name),
            ['DELETED'], self.mission_deleted_cb, self.robot_config.robot_name)

        # Register update chargers callback
        self.robot_config.handler.register_callback(
            'update_chargers_{}'.format(self.robot_config.robot_name),
            ['ADDED', 'MODIFIED'], self.update_chargers_cb, self.robot_config.robot_name)

    def update_mission_status_cb(self, name: str, custom_res: Dict) -> None:
        """Update self.mission_status."""
        # Only process custom resources labeled with own robot name
        if custom_res['metadata'].get('labels', {}).get(
                'cloudrobotics.com/robot-name') != self.robot_config.robot_name:
            return

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
            # Keep maximum of 20 missions
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
                    if finished >= 20:
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
                if self.handler.check_cr_exists(mission):
                    self.handler.delete_cr(mission)
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
        # Only process custom resources labeled with own robot name
        if custom_res['metadata'].get('labels', {}).get(
                'cloudrobotics.com/robot-name') != self.robot_config.robot_name:
            return

        with self.mission_status_lock:
            # If mission was deleted mark it as deleted
            if self.mission_status.get(name):
                self.mission_status[name].status = RobotMission.STATE_DELETED

    def update_robot_status_cb(self, name: str, custom_res: Dict) -> None:
        """Update robot status attributes."""
        # Only process custom resources labeled with own robot name
        if custom_res['metadata'].get('labels', {}).get(
                'cloudrobotics.com/robot-name') != self.robot_config.robot_name:
            return

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

    def update_chargers_cb(self, name: str, custom_res: Dict) -> None:
        """Update chargers from robotconfigurations CRD."""
        # Only process custom resources labeled with own robot name
        if custom_res['metadata'].get('labels', {}).get(
                'cloudrobotics.com/robot-name') != self.robot_config.robot_name:
            return

        # Check if chargers changed in the meantime
        if self._chargers != self.robot_config.conf.chargers:
            self._chargers = self.robot_config.conf.chargers.copy()
            self._chargers_generator = self._iterate_chargers()
            _LOGGER.info('Chargers changed to: %s', self._chargers)

    def check_deleted_missions(self):
        """Set self.mission_state entries with no CR to state DELETED."""
        cr_resp = self.handler.list_all_cr()
        _LOGGER.debug(
            '%s/%s: Check deleted CR: Got all CRs.', self.handler.group, self.handler.plural)
        # Collect names of all existing CRs
        mission_crs = {}
        for obj in cr_resp:
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

    def _create_mission(self, spec: Dict) -> str:
        # Use Unix timestamp as mission name
        mission_name = str(time.time())
        # Create CR
        self.handler.create_cr(mission_name, self.labels, spec)
        # Return mission_name
        return mission_name

    def _iterate_chargers(self) -> Generator:
        """Iterate over self.chargers."""
        if not self._chargers:
            yield ''
        while True:
            for charger in self._chargers:
                yield charger

    def api_cancel_mission(self, name: str) -> bool:
        """Cancel a mission."""
        if self.handler.check_cr_exists(name):
            # Mission is canceled by deleting its CR
            self.handler.delete_cr(name)
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
        # Get next charger from generator
        self.charger = next(self._chargers_generator, '')
        _LOGGER.info('Set charger %s', self.charger)

    def api_return_mission_activeaction(self, mission_name: str) -> str:
        """Return active_action of a mission."""
        mission = self.mission_status.get(mission_name)

        # Create mission in unknown state if it is not known
        if mission is None:
            with self.mission_status_lock:
                self.mission_status[mission_name] = RobotMission(mission_name)
            mission = self.mission_status[mission_name]

        return mission.active_action

    def api_return_mission_state(self, mission_name: str) -> str:
        """Return state of a mission."""
        mission = self.mission_status.get(mission_name)

        # Create mission in unknown state if it is not known
        if mission is None:
            with self.mission_status_lock:
                self.mission_status[mission_name] = RobotMission(mission_name)
            mission = self.mission_status[mission_name]

        return mission.status

    def api_check_state_ok(self) -> bool:
        """Check if robot is in state ok."""
        return bool(self.robot_state == RobcoRobotStates.STATE_AVAILABLE)
