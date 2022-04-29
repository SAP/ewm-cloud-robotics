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

"""Run a SAP EWM robot."""

import os
import signal
import logging
import time

from typing import List

import attr

from prometheus_client import start_http_server

from robcoewmrobotcontroller.ordercontroller import OrderHandler
from robcoewmrobotcontroller.robot import EWMRobot
from robcoewmrobotcontroller.robotcontroller import RobotHandler
from robcoewmrobotcontroller.missioncontroller import MissionController, MissionHandler
from robcoewmrobotcontroller.robotconfigcontroller import (
    RobotConfigurationController, RobotConfigurationHandler)

_LOGGER = logging.getLogger(__name__)


@attr.s
class RobotController:
    """Controller for a robot."""

    robot_config: RobotConfigurationController = attr.ib(
        validator=attr.validators.instance_of(RobotConfigurationController))
    mission: MissionController = attr.ib(
        validator=attr.validators.instance_of(MissionController))


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


def create_robot_controller(
        robot_name: str,
        rc_handler: RobotConfigurationHandler,
        r_handler: RobotHandler,
        m_handler: MissionHandler) -> RobotController:
    """Create controllers for a robot."""
    # Create controller
    robot_config = RobotConfigurationController(robot_name, rc_handler)
    mission = MissionController(robot_config, m_handler, r_handler)

    return RobotController(robot_config, mission)


def run_robot(
        robot_controller: RobotController,
        o_handler: OrderHandler) -> EWMRobot:
    """Run one instance of a robot."""
    # Create instance of one robot
    robot = EWMRobot(
        robot_controller.robot_config, robot_controller.mission, o_handler)
    return robot


def run_robots():
    """Run all robot of this controller."""
    # Register handler to control main loop
    loop_control = MainLoopController()

    # Start prometheus client
    start_http_server(8000)

    # Identify namespace for custom resources
    namespace = os.environ.get('K8S_NAMESPACE', 'default')

    # Create handler
    rc_handler = RobotConfigurationHandler(namespace)
    r_handler = RobotHandler(namespace)
    m_handler = MissionHandler(namespace)
    o_handler = OrderHandler(namespace)

    # Get robots
    robots_env = os.environ.get('ROBOTS')
    if robots_env is None:
        raise ValueError('No robots in environment variable ROBOTS')
    robots_name = robots_env.split(',')

    # Create controller
    robot_controllers: List[RobotController] = []
    for robot_name in robots_name:
        if not robot_name:
            continue
        robot_controller = create_robot_controller(robot_name, rc_handler, r_handler, m_handler)
        robot_controllers.append(robot_controller)

    # Start handler
    rc_handler.run(multiple_executor_threads=True)
    r_handler.run(multiple_executor_threads=True)
    m_handler.run(multiple_executor_threads=True)
    o_handler.run(multiple_executor_threads=True)

    # Create robots
    robots: List[EWMRobot] = []
    for robot_controller in robot_controllers:
        robot = run_robot(robot_controller, o_handler)
        _LOGGER.info('SAP EWM Robot "%s" started', robot.robot_config.rsrc)
        robots.append(robot)

    _LOGGER.info('All %s robots started', len(robots))
    _LOGGER.info('Watching custom resources of namespace %s', namespace)


    # Reprocess CRs from all handler once when all robots are started
    rc_handler.process_all_crs()
    r_handler.process_all_crs()
    m_handler.process_all_crs()
    o_handler.process_all_crs()

    try:
        # Looping while K8S stream watchers are running
        while loop_control.shutdown is False:
            # Check if K8S CR handler exception occured
            for k, exc in o_handler.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of order handler. Raising it in main'
                    ' thread', k)
                raise exc
            for k, exc in rc_handler.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of robotconfiguration handler. '
                    'Raising it in main thread', k)
                raise exc
            for k, exc in m_handler.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of mission handler. Raising it in '
                    'main thread', k)
                raise exc
            for k, exc in r_handler.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of robot handler. Raising it in '
                    'main thread', k)
                raise exc

            # Sleep maximum 1.0 second
            loop_control.sleep(1.0)
    except KeyboardInterrupt:
        _LOGGER.info('Keyboard interrupt - terminating')
    except SystemExit:
        _LOGGER.info('System exit - terminating')
    finally:
        # Disconnect state machines
        for robot in robots:
            robot.state_machine.disconnect_external_events()
        # Stop K8S CR watcher
        _LOGGER.info('Stopping K8S CR watchers')
        rc_handler.stop_watcher()
        r_handler.stop_watcher()
        m_handler.stop_watcher()
        o_handler.stop_watcher()
