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

"""Run the SAP EWM robot configurator."""

import signal
import logging
import time

from robcoewmrobotconfigurator.ewm_robot_sync import EWMRobotSync
from robcoewmrobotconfigurator.robotconfigcontroller import RobotConfigurationController
from robcoewmrobotconfigurator.robco_robot_api import RobCoRobotAPI

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


def run_robotconfigurator():
    """Run one instance of the robot configurator."""
    # Register handler to control main loop
    loop_control = MainLoopController()

    # Create CR watcher instances
    k8s_rb = RobCoRobotAPI()
    k8s_rc = RobotConfigurationController()

    # Create EWM robot syncer instance
    robotsync = EWMRobotSync(k8s_rc)

    # Register callback functions
    k8s_rb.register_callback('ConfigurationController', ['ADDED'], k8s_rc.robco_robot_cb)
    k8s_rc.register_callback(
        'EWMRobotSync', ['ADDED', 'MODIFIED', 'REPROCESS'], robotsync.robotconfiguration_cb)
    # Start
    k8s_rb.run()
    k8s_rc.run(reprocess=True)

    _LOGGER.info('SAP EWM Robot Configurator started')

    try:
        # Looping while K8S watchers are running
        while loop_control.shutdown is False:
            # Refresh bearer token when using OAuth
            if robotsync.odataconfig.authorization == robotsync.odataconfig.AUTH_OAUTH:
                robotsync.odatahandler.refresh_access_token()
            # Check if K8S CR handler exception occured
            for k, exc in k8s_rb.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of RobCoRobotAPI. Raising it in main '
                    'thread', k)
                raise exc
            for k, exc in k8s_rc.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of RobotConfigurationController. Raising '
                    'it in main thread', k)
                raise exc
            # Sleep maximum 1.0 second
            loop_control.sleep(1.0)
    except KeyboardInterrupt:
        _LOGGER.info('Keyboard interrupt - terminating')
    except SystemExit:
        _LOGGER.info('System exit - terminating')
    finally:
        # Stop K8S CR watchers
        _LOGGER.info('Stopping K8S CR watchers')
        k8s_rb.stop_watcher()
        k8s_rc.stop_watcher()
        # Shutdown threadpool executor
        robotsync.executor.shutdown()
