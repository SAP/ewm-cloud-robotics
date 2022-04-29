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

"""Run the SAP EWM order manager."""

import os
import signal
import logging
import time

from prometheus_client import start_http_server

from robcoewmordermanager.ordercontroller import OrderController
from robcoewmordermanager.robotconfigcontroller import RobotConfigurationController
from robcoewmordermanager.orderreservationcontroller import OrderReservationController
from robcoewmordermanager.orderauctioncontroller import OrderAuctionController
from robcoewmordermanager.auctioneercontroller import AuctioneerController
from robcoewmordermanager.manager import EWMOrderManager
from robcoewmordermanager.robotcontroller import RobotController

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


def run_ordermanager():
    """Run one instance of the order manager."""
    # Register handler to control main loop
    loop_control = MainLoopController()

    # Start prometheus client
    start_http_server(8000)

    # Identify namespace for custom resources
    namespace = os.environ.get('K8S_NAMESPACE', 'default')

    # Create K8S handler instances
    k8s_oc = OrderController(namespace)
    k8s_rc = RobotConfigurationController(namespace)
    k8s_orc = OrderReservationController(namespace)
    k8s_oac = OrderAuctionController(namespace)
    k8s_auc = AuctioneerController(namespace)
    k8s_roc = RobotController(namespace)

    # Create order manager instance
    manager = EWMOrderManager(k8s_oc, k8s_rc, k8s_orc, k8s_oac, k8s_auc, k8s_roc)

    # Start
    manager.robotcontroller.run(reprocess=False, multiple_executor_threads=False)
    manager.auctioneercontroller.run(reprocess=False, multiple_executor_threads=False)
    manager.orderauctioncontroller.run(reprocess=False, multiple_executor_threads=False)
    manager.ordercontroller.run(reprocess=True, multiple_executor_threads=True)
    manager.orderreservationcontroller.run(reprocess=True, multiple_executor_threads=True)
    manager.robotconfigcontroller.run(reprocess=True, multiple_executor_threads=True)

    _LOGGER.info('SAP EWM Order Manager started')
    _LOGGER.info('Watching custom resources of namespace %s', namespace)

    try:
        # Looping while K8S watchers are running
        while loop_control.shutdown is False:
            # Refresh bearer token when using OAuth
            if manager.odataconfig.authorization == manager.odataconfig.AUTH_OAUTH:
                manager.odatahandler.refresh_access_token()
            # Check if K8S CR handler exception occured
            for k, exc in manager.ordercontroller.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of ordercontroller. Raising it in main '
                    'thread', k)
                raise exc
            for k, exc in manager.robotconfigcontroller.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of robotconfigcontroller. Raising it in '
                    'main thread', k)
                raise exc
            for k, exc in manager.orderreservationcontroller.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of orderreservationcontroller. Raising it'
                    ' in main thread', k)
                raise exc
            for k, exc in manager.orderauctioncontroller.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of orderauctioncontroller. Raising it'
                    ' in main thread', k)
                raise exc
            for k, exc in manager.auctioneercontroller.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of auctioneercontroller. Raising it'
                    ' in main thread', k)
                raise exc
            for k, exc in manager.robotcontroller.thread_exceptions.items():
                _LOGGER.error(
                    'Uncovered exception in "%s" thread of robotcontroller. Raising it'
                    ' in main thread', k)
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
        manager.ordercontroller.stop_watcher()
        manager.robotconfigcontroller.stop_watcher()
        manager.orderreservationcontroller.stop_watcher()
        manager.orderauctioncontroller.stop_watcher()
        manager.auctioneercontroller.stop_watcher()
        manager.robotcontroller.stop_watcher()
