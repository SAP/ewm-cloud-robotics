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

"""Run the MiR mission controller."""

import os
import logging

from prometheus_client import start_http_server

from mircontroller.mirapi import MiRInterface
from mircontroller.mirrobot import MiRRobot
from mircontroller.helper import MainLoopController
from mircontroller.mission import MissionController
from mircontroller.robot import RobotController

_LOGGER = logging.getLogger(__name__)


def run_missioncontroller():
    """Run one instance of the MiR controller."""
    # Start prometheus client
    start_http_server(8000)
    # Register handler to control main loop
    loop_control = MainLoopController()

    # Identify namespace for custom resources
    namespace = os.environ.get('K8S_NAMESPACE', 'default')

    # Create instance for MiR API
    mir_api = MiRInterface()

    # Create instance for MiR robot
    mir_robot = MiRRobot(mir_api)

    # Create K8S handler instances
    k8s_rc = RobotController(mir_robot, namespace)
    k8s_mc = MissionController(mir_robot, namespace)

    # Start
    k8s_rc.run(reprocess=False)
    k8s_mc.run(reprocess=False)

    _LOGGER.info('MiR controller started for robot %s', mir_robot.robco_robot_name)
    _LOGGER.info('Watching custom resources of namespace %s', namespace)

    try:
        # Looping while K8S watchers are running
        while loop_control.shutdown is False:
            # Check if K8S CR handler exception occured
            for k, exc in k8s_mc.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of mission controller. Raising it in main '
                    'thread', k)
                raise exc
            for k, exc in k8s_rc.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of robot controller. Raising it in main '
                    'thread', k)
                raise exc
            # Sleep maximum 1.0 second
            loop_control.sleep(1.0)
    except KeyboardInterrupt:
        _LOGGER.info('Keyboard interrupt - terminating')
    except SystemExit:
        _LOGGER.info('System exit - terminating')
    finally:
        # Stop K8S CRD watchers
        _LOGGER.info('Stopping K8S CR watchers')
        k8s_mc.stop_watcher()
        k8s_rc.stop_watcher()
