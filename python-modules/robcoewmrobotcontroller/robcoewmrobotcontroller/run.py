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

import sys
import signal
import traceback
import logging
import time

from typing import Optional

from prometheus_client import start_http_server

from robcoewmtypes.warehouseorder import WarehouseTask
from robcoewmrobotcontroller.ordercontroller import OrderController
from robcoewmrobotcontroller.robotrequestcontroller import (
    RobotRequestController, )
from robcoewmrobotcontroller.robot import EWMRobot
from robcoewmrobotcontroller.robot_api import RobotMissionAPI
from robcoewmrobotcontroller.robco_robot_api import RobCoRobotAPI
from robcoewmrobotcontroller.robco_mission_api import RobCoMissionAPI
from robcoewmrobotcontroller.robotconfigcontroller import RobotConfigurationController

_LOGGER = logging.getLogger(__name__)


class MainLoopController:
    """Control the main loop."""

    def __init__(self):
        """Constructor."""
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


def dummy_confirm_true(wht: WarehouseTask) -> None:
    """For testing only."""
    time.sleep(5.0)
    return True


def run_robot():
    """Determine robot type and run one instance of it."""
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
    # Start main loop
    robot_main_loop(robot_config, robco_mission, robco_robot)
    # In the end stop Mission and Config CR watchers
    robco_mission.stop_watcher()
    robot_config.stop_watcher()


def robot_main_loop(robot_config: RobotConfigurationController, robot_mission_api: RobotMissionAPI,
                    robot_status_api: Optional[RobCoRobotAPI] = None) -> None:
    """Run one main loop of a EWM robot."""
    # Register handler to control main loop
    loop_control = MainLoopController()

    # Create K8S handler instances
    k8s_oc = OrderController()
    k8s_rc = RobotRequestController()

    # Create robot controller instance
    # TODO: Replace dummy confirmation method by real method
    robot = EWMRobot(
        robot_mission_api, robot_config, k8s_oc, k8s_rc, confirm_target=dummy_confirm_true)

    # K8S custom resource callbacks
    # Order controller
    k8s_oc.register_callback(
        'Robot', ['ADDED', 'MODIFIED', 'REPROCESS'], robot.queue_callback)
    # Robot request controller
    k8s_rc.register_callback(
        'Robot', ['MODIFIED', 'REPROCESS'], robot.robotrequest_callback)
    # Start
    k8s_oc.run(reprocess=True)
    k8s_rc.run(reprocess=True)
    _LOGGER.info('SAP EWM Robot "%s" started - K8S CR mode', robot.robot_config.rsrc)

    # Wait 1 seconds for initial messages being processed
    time.sleep(1.0)

    # If still no warehouse order - request work
    stateok = robot.mission_api.api_check_state_ok()
    if robot.state_machine.is_noWarehouseorder and stateok:
        robot.request_work()

    try:
        # Looping while K8S stream watchers are running
        while loop_control.shutdown is False:
            # Run state machine update
            robot.runner()

            # Check if K8S CR handler exception occured
            for k, exc in k8s_oc.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of ordercontroller. Raising it in main '
                    'thread', k)
                raise exc
            for k, exc in k8s_rc.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of robotrequestcontroller. Raising it in '
                    'main thread', k)
                raise exc
            for k, exc in robot_config.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of robotconfigurationcontroller. Raising '
                    'it in main thread', k)
                raise exc
            for k, exc in robot_mission_api.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of robot_mission_api . Raising it in '
                    'main thread', k)
                raise exc
            for k, exc in robot_status_api.thread_exceptions.items():
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
        # Stop K8S CR watcher
        _LOGGER.info('Stopping K8S CR watchers')
        k8s_oc.stop_watcher()
        k8s_rc.stop_watcher()


if __name__ == '__main__':
    # Create root logger if running as main program
    ROOT_LOGGER = logging.getLogger()
    ROOT_LOGGER.setLevel(logging.INFO)

    # Create console handler and set level to info
    CH = logging.StreamHandler()
    CH.setLevel(logging.INFO)

    # Create formatter
    FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add formatter to ch
    CH.setFormatter(FORMATTER)

    # Add ch to logger
    ROOT_LOGGER.addHandler(CH)
    # Run robot
    try:
        run_robot()
    except Exception:  # pylint: disable=broad-except
        EXC_INFO = sys.exc_info()
        _LOGGER.fatal(
            'Unexpected error "%s" - "%s" - TRACEBACK: %s', EXC_INFO[0],
            EXC_INFO[1], traceback.format_exception(*EXC_INFO))
        sys.exit('Application terminated with exception: "{}" - "{}"'.format(
            EXC_INFO[0], EXC_INFO[1]))
