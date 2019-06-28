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

"""Run the SAP EWM order manager."""

import sys
import signal
import traceback
import logging
import time

from prometheus_client import start_http_server

from robcoewmordermanager.ewm_robot_sync import EWMRobotSync
from robcoewmordermanager.ordercontroller import OrderController
from robcoewmordermanager.robotrequestcontroller import RobotRequestController
from robcoewmordermanager.robco_robot_api import RobCoRobotAPI
from robcoewmordermanager.manager import EWMOrderManager

_LOGGER = logging.getLogger(__name__)

K8S_CR_HANDLER = 'K8S_CR'


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


def run_ordermanager():
    """Run one instance of the order manager."""
    # Register handler to control main loop
    loop_control = MainLoopController()

    # Start prometheus client
    start_http_server(8000)

    # Create EWM robot syncer instance
    robotsync = EWMRobotSync()
    # Register callback functions
    k8s_rb = RobCoRobotAPI()
    k8s_rb.register_callback('EWMRobotSync', ['ADDED'], robotsync.robco_robot_cb)
    # Start
    k8s_rb.run()

    # Create order manager instance
    manager = EWMOrderManager()

    # Register callback functions
    # Create K8S handler instances
    k8s_oc = OrderController()
    k8s_rc = RobotRequestController()
    # K8S custom resource callbacks
    # Warehouse order status callback
    k8s_oc.register_callback(
        'KubernetesWhoCR', ['MODIFIED', 'REPROCESS'], manager.process_who_cr_cb)
    # Robot request controller
    k8s_rc.register_callback(
        'RobotRequest', ['ADDED', 'MODIFIED', 'REPROCESS'], manager.robotrequest_callback)
    # Warehouse order publisher
    manager.send_who_to_robot = k8s_oc.send_who_to_robot
    # Warehouse order cleanup
    manager.cleanup_who = k8s_oc.cleanup_who
    # Robot request cleanup
    manager.update_robotrequest_status = k8s_rc.update_request

    # Start
    k8s_oc.run(reprocess=True, multiple_executor_threads=True)
    k8s_rc.run(reprocess=True, multiple_executor_threads=True)

    _LOGGER.info('SAP EWM Order Manager started - K8S CR mode')

    try:
        # Looping while Pub/Sub subscriber is running
        while loop_control.shutdown is False:
            # Check if K8S CR handler exception occured
            for k, exc in k8s_rb.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of RobCoRobotAPI. Raising it in main '
                    'thread', k)
                raise exc
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
            # Sleep maximum 1.0 second
            loop_control.sleep(1.0)
    except KeyboardInterrupt:
        _LOGGER.info('Keyboard interrupt - terminating')
    except SystemExit:
        _LOGGER.info('System exit - terminating')
    finally:
        # Stop K8S CR watchers
        _LOGGER.info('Stopping K8S CR watchers')
        k8s_oc.stop_watcher()
        k8s_rc.stop_watcher()
        k8s_rb.stop_watcher()


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
    # Run order manager
    try:
        run_ordermanager()
    except Exception:  # pylint: disable=broad-except
        EXC_INFO = sys.exc_info()
        _LOGGER.fatal(
            'Unexpected error "%s" - "%s" - TRACEBACK: %s', EXC_INFO[0], EXC_INFO[1],
            traceback.format_exception(*EXC_INFO))
        sys.exit('Application terminated with exception: "{}" - "{}"'.format(
            EXC_INFO[0], EXC_INFO[1]))
