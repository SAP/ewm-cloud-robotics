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

"""K8s custom resource handler for RobCo Robots."""

import os
import logging

from typing import Dict

from robcoewmtypes.helper import get_sample_cr
from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class RobotConfigurationController(K8sCRHandler):
    """Handle K8s RobotConfiguration custom resources."""

    def __init__(self) -> None:
        """Constructor."""
        self.init_default_values_fromenv()

        template_cr = get_sample_cr('robotconfiguration')

        labels = {}
        super().__init__(
            'sap.com',
            'v1',
            'robotconfigurations',
            'default',
            template_cr,
            labels
        )

    def init_default_values_fromenv(self) -> None:
        """Initialize robot configuration controller from environment variables."""
        # Read environment variables
        envvar = {}
        envvar['EWM_LGNUM'] = os.environ.get('EWM_LGNUM')
        envvar['EWM_RSRC_TYPE'] = os.environ.get('EWM_RSRC_TYPE')
        envvar['EWM_RSRC_GRP'] = os.environ.get('EWM_RSRC_GRP')
        envvar['CHARGER_LIST'] = os.environ.get('CHARGER_LIST', 'Charger')
        # Check if complete
        for var, val in envvar.items():
            if val is None:
                raise ValueError(
                    'Environment variable "{}" is not set'.format(var))

        # Optional parameters
        envvar['EWM_BATTERY_MIN'] = os.environ.get('EWM_BATTERY_MIN')
        envvar['EWM_BATTERY_OK'] = os.environ.get('EWM_BATTERY_OK')
        envvar['EWM_BATTERY_IDLE'] = os.environ.get('EWM_BATTERY_IDLE')
        envvar['MAX_IDLE_TIME'] = os.environ.get('MAX_IDLE_TIME')

        self.lgnum = envvar['EWM_LGNUM']
        self.rsrc_type = envvar['EWM_RSRC_TYPE']
        self.rsrc_grp = envvar['EWM_RSRC_GRP']

        # List of chargers
        self.chargers = [x.strip() for x in envvar['CHARGER_LIST'].split(',')]

        # Battery levels in %
        self.battery_min = float(envvar['EWM_BATTERY_MIN']) if envvar['EWM_BATTERY_MIN'] else 10
        self.battery_ok = float(envvar['EWM_BATTERY_OK']) if envvar['EWM_BATTERY_OK'] else 80
        self.battery_idle = float(envvar['EWM_BATTERY_IDLE']) if envvar['EWM_BATTERY_IDLE'] else 40

        # Max idle time until robot moves to staging area
        self.max_idle_time = float(envvar['MAX_IDLE_TIME']) if envvar['MAX_IDLE_TIME'] else 30

    def robco_robot_cb(self, name: str, custom_res: Dict) -> None:
        """Process Cloud Robotics robot CR."""
        # If no robot configuration for this robot already exists, create a new one
        if not self.check_cr_exists(name):
            labels = {}
            labels['cloudrobotics.com/robot-name'] = name
            spec = {
                'batteryIdle': self.battery_idle,
                'batteryMin': self.battery_min,
                'batteryOk': self.battery_ok,
                'lgnum': self.lgnum,
                'rsrcgrp': self.rsrc_grp,
                'rsrctype': self.rsrc_type,
                'maxIdleTime': self.max_idle_time,
                'chargers': self.chargers
                }

            # Create CR
            self.create_cr(name, labels, spec)
