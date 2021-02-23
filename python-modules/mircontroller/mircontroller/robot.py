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

"""MiR robot controller."""

import logging
import datetime
import threading

from copy import deepcopy

from kubernetes.client.rest import ApiException

from k8scrhandler.k8scrhandler import K8sCRHandler

from .mirrobot import MiRRobot
from .helper import get_sample_cr, MainLoopController

_LOGGER = logging.getLogger(__name__)


class RobotController(K8sCRHandler):
    """MiR robot controller."""

    def __init__(self, mir_robot: MiRRobot) -> None:
        """Construct."""
        # Instance with MiR robot
        self._mir_robot = mir_robot

        # Super constructor for robot CR
        labels = {}
        labels['cloudrobotics.com/robot-name'] = self._mir_robot.robco_robot_name
        self.robot_template_cr = get_sample_cr('robco_robot')
        super().__init__(
            'registry.cloudrobotics.com',
            'v1alpha1',
            'robots',
            'default',
            self.robot_template_cr,
            labels
        )

        # Init threads
        self.robot_status_update_thread = threading.Thread(target=self._update_robot_status_loop)

    def run(self, watcher: bool = True, reprocess: bool = False,
            multiple_executor_threads: bool = False) -> None:
        """
        Start running all callbacks.

        Supporting multiple executor threads for blocking callbacks.
        """
        super().run(watcher, reprocess, multiple_executor_threads)

        # Start update thread
        self.robot_status_update_thread.start()

    def _update_robot_status_loop(self) -> None:
        """Run update robot status continiously."""
        loop_control = MainLoopController()
        _LOGGER.info('Watch robot status loop started')
        while self.thread_run:
            try:
                self.update_robot_status()
                loop_control.sleep(2)
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error('Error updating status of robot: %s', err, exc_info=True)
                # On uncovered exception in thread save the exception
                self.thread_exceptions['status_loop'] = err
                # Stop the watcher
                self.stop_watcher()

        _LOGGER.info('Watch robot status loop stopped')

    def update_robot_status(self) -> None:
        """Update status of robot CR."""
        # Update MiR robot
        self._mir_robot.update()
        # Update robot CR status
        status = deepcopy(self.robot_template_cr)['status']
        status['configuration']['trolleyAttached'] = self._mir_robot.trolley_attached
        status['robot']['batteryPercentage'] = self._mir_robot.battery_percentage
        status['robot']['lastStateChangeTime'] = self._mir_robot.last_state_change
        status['robot']['state'] = self._mir_robot.state
        status['robot']['updateTime'] = datetime.datetime.utcnow().replace(
            tzinfo=datetime.timezone.utc).isoformat()

        try:
            self.update_cr_status(self._mir_robot.robco_robot_name, status)
        except ApiException:
            _LOGGER.error(
                'Status CR of robot %s could not be updated', self._mir_robot.robco_robot_name)
