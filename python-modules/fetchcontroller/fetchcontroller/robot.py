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

"""FetchCore robot controller."""

import logging
import datetime
import threading

from copy import deepcopy
from typing import Dict

from kubernetes.client.rest import ApiException

from k8scrhandler.k8scrhandler import K8sCRHandler

from .fetchrobot import FetchRobots
from .helper import get_sample_cr, MainLoopController

_LOGGER = logging.getLogger(__name__)


class RobotController(K8sCRHandler):
    """FetchCore robot controller."""

    def __init__(self, fetch_robots: FetchRobots, namespace: str) -> None:
        """Construct."""
        # Instance with all FetchCore robots
        self._fetch_robots = fetch_robots

        self.robottypes: Dict[str, bool] = {}

        # Super constructor for robot CR
        self.robot_template_cr = get_sample_cr('robco_robot')
        super().__init__(
            'registry.cloudrobotics.com',
            'v1alpha1',
            'robots',
            namespace,
            self.robot_template_cr,
            {}
        )

        # Create instance for robottypes CR
        template_robottype_cr = get_sample_cr('robco_robottype')
        self.robottype_controller = K8sCRHandler(
            'registry.cloudrobotics.com',
            'v1alpha1',
            'robottypes',
            namespace,
            template_robottype_cr,
            {}
        )

        # Init threads
        self.robot_status_update_thread = threading.Thread(target=self._update_robot_status_loop)

        # register callbacks
        self.robottype_controller.register_callback(
            'robot', ['ADDED', 'MODIFIED', 'REPROCESS'], self.robottype_cb)
        self.register_callback(
            'robot', ['ADDED', 'REPROCESS'], self.robot_cb)
        self.register_callback(
            'robot_deleted', ['DELETED'], self.robot_deleted_cb)

    def robot_cb(self, name: str, custom_res: Dict) -> None:
        """Process robot CR callback data."""
        # Check if robot is a Fetch robot
        robottype = custom_res.get('spec', {}).get('type')
        is_fetch = self.robottypes.get(robottype, False)
        if is_fetch:
            # Fetch robot is not in FetchCore watch list, add it
            try:
                self._fetch_robots.get_robot(name)
            except ValueError:
                self._fetch_robots.add_robot(name)
                _LOGGER.info('Added robot %s to FetchCore watch list', name)

    def robot_deleted_cb(self, name: str, custom_res: Dict) -> None:
        """Process robot delete CR callback data."""
        # Check if robot is a Fetch robot
        robottype = custom_res.get('spec', {}).get('type')
        is_fetch = self.robottypes.get(robottype, False)
        if is_fetch:
            # Remove robot from FetchCore watch list
            self._fetch_robots.remove_robot(name)
            _LOGGER.info('Removed robot %s from FetchCore watch list', name)

    def robottype_cb(self, name: str, custom_res: Dict) -> None:
        """Process robottype CR callback data."""
        self.robottypes[name] = bool(custom_res.get('spec', {}).get('make') == 'fetch')

    def run(self, reprocess: bool = False, multiple_executor_threads: bool = False) -> None:
        """
        Start running all callbacks.

        Supporting multiple executor threads for blocking callbacks.
        """
        # Initial load of robot types
        robot_type_crs = self.robottype_controller.list_all_cr(use_cache=False)
        for custom_res in robot_type_crs:
            name = custom_res.get('metadata', {}).get('name')
            spec = custom_res.get('spec')
            if name and spec:
                self.robottype_cb(name, custom_res)

        # Initial load of robots
        robot_crs = self.list_all_cr(use_cache=False)
        for custom_res in robot_crs:
            name = custom_res.get('metadata', {}).get('name')
            spec = custom_res.get('spec')
            if name and spec:
                self.robot_cb(name, custom_res)

        # Initial load from FetchCore
        self._fetch_robots.update()

        # Start watcher threads
        self.robottype_controller.run(reprocess, multiple_executor_threads)
        super().run(reprocess, multiple_executor_threads)

        # Start update thread
        self.robot_status_update_thread.start()

    def stop_watcher(self) -> None:
        """Stop watching CR stream."""
        # Stop robottype and robot watchers
        self.robottype_controller.stop_watcher()
        super().stop_watcher()

    def _update_robot_status_loop(self) -> None:
        """Run update robot status continiously."""
        loop_control = MainLoopController()
        _LOGGER.info('Watch robot status loop started')
        while self.thread_run:
            try:
                self.update_robot_status()
                loop_control.sleep(2)
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error('Error updating status of robots: %s', err, exc_info=True)
                # On uncovered exception in thread save the exception
                self.thread_exceptions['status_loop'] = err
                # Stop the watcher
                self.stop_watcher()

        _LOGGER.info('Watch robot status loop stopped')

    def update_robot_status(self) -> None:
        """Continously update status of robot CR."""
        status = deepcopy(self.robot_template_cr)['status']
        # Get updated robot states from FetchCore
        self._fetch_robots.update()
        # Update robot CR status
        for name, robot in self._fetch_robots.robots.items():
            status['configuration']['trolleyAttached'] = robot.trolley_attached
            status['robot']['batteryPercentage'] = robot.battery_percentage
            status['robot']['lastStateChangeTime'] = robot.last_state_change
            status['robot']['state'] = robot.state
            status['robot']['updateTime'] = datetime.datetime.utcnow().replace(
                tzinfo=datetime.timezone.utc).isoformat()

            try:
                self.update_cr_status(name, status)
            except ApiException:
                _LOGGER.error('Status CR of robot %s could not be updated', name)
