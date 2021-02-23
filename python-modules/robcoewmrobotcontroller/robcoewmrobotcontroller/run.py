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

"""Run a SAP EWM robot."""

import signal
import logging
import time

from prometheus_client import start_http_server

from robcoewmrobotcontroller.ordercontroller import OrderController
from robcoewmrobotcontroller.robotrequestcontroller import (
    RobotRequestController, )
from robcoewmrobotcontroller.robot import EWMRobot
from robcoewmrobotcontroller.robco_robot_api import RobCoRobotAPI
from robcoewmrobotcontroller.robco_mission_api import RobCoMissionAPI
from robcoewmrobotcontroller.robotconfigcontroller import RobotConfigurationController

_LOGGER = logging.getLogger(__name__)


class MainLoopController:
    """Control the main loop."""

    def __init__(self):
        """Construct."""
        # Shutdown Handler
        self.shutdown = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        # Sleep handler
        self.last_time = time.time()

    def exit_gracefully(self, signum, frame):
        """Set shutdown flag on SIGTERM and SIGINT."""
        self.shutdown = True
        _LOGGER.info('Closing application because signal %s received', signum)

    def sleep(self, seconds: float):
        """Sleep maximum n seconds after the last call."""
        timediff = time.time() - self.last_time

        if timediff < seconds:
            time.sleep(seconds-timediff)

        self.last_time = time.time()


def run_robot():
    """Run one instance of a robot."""
    # Register handler to control main loop
    loop_control = MainLoopController()

    # Start prometheus client
    start_http_server(8000)

    # Create Robot configuration interface
    robot_config = RobotConfigurationController()
    # Start robot configuration interface
    robot_config.run(reprocess=True)
    # Wait 1 seconds for initial messages being processed
    time.sleep(1.0)
    # Create RobCo robot interface
    robco_robot = RobCoRobotAPI()
    # Create RobCo mission interface
    robco_mission = RobCoMissionAPI(robot_config, robco_robot)
    # Start RobCo interface
    robco_mission.run(reprocess=True)
    # Wait 1 seconds for initial messages being processed
    time.sleep(1.0)

    # Create K8S handler instances
    k8s_oc = OrderController()
    k8s_rc = RobotRequestController()

    # Create robot controller instance
    robot = EWMRobot(robco_mission, robot_config, k8s_oc, k8s_rc)

    # Start
    robot.ordercontroller.run(reprocess=True)
    robot.robotrequestcontroller.run(reprocess=True)
    _LOGGER.info('SAP EWM Robot "%s" started', robot.robot_config.rsrc)

    try:
        # Looping while K8S stream watchers are running
        while loop_control.shutdown is False:
            # Check if K8S CR handler exception occured
            for k, exc in robot.ordercontroller.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of ordercontroller. Raising it in main '
                    'thread', k)
                raise exc
            for k, exc in robot.robotrequestcontroller.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of robotrequestcontroller. Raising it in '
                    'main thread', k)
                raise exc
            for k, exc in robot.robot_config.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of robotconfigurationcontroller. Raising '
                    'it in main thread', k)
                raise exc
            for k, exc in robot.mission_api.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of robot_mission_api . Raising it in '
                    'main thread', k)
                raise exc
            for k, exc in robot.mission_api.robot_api.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of robot_status_api. Raising it in '
                    'main thread', k)
                raise exc

            # Sleep maximum 1.0 second
            loop_control.sleep(1.0)
    except KeyboardInterrupt:
        _LOGGER.info('Keyboard interrupt - terminating')
    except SystemExit:
        _LOGGER.info('System exit - terminating')
    finally:
        # Disconnect state machine
        robot.state_machine.disconnect_external_events()
        # Stop K8S CR watcher
        _LOGGER.info('Stopping K8S CR watchers')
        robot.ordercontroller.stop_watcher()
        robot.robotrequestcontroller.stop_watcher()
        robot.mission_api.stop_watcher()
        robot.robot_config.stop_watcher()
