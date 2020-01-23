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

"""Fetchcontroller helper."""

import os
import json
import time
import signal
import logging
import threading

from typing import Dict

_LOGGER = logging.getLogger(__name__)


def get_sample_cr(crd: str) -> Dict:
    """Get a dictionary with a sample of a CRD."""
    valid_crd = ['robco_mission', 'robco_robot', 'robco_robottype']
    if crd not in valid_crd:
        raise ValueError('There is no sample for CRD "{}"'.format(crd))
    path = os.path.dirname(__file__)
    with open('{}/k8s-files/sample_{}.json'.format(path, crd)) as file:
        template_cr = json.load(file)

    return template_cr


class MainLoopController:
    """Control the main loop."""

    def __init__(self):
        """Construct."""
        # Shutdown Handler
        self.shutdown = False
        # Signaling only works in main thread
        if threading.current_thread() is threading.main_thread():
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
