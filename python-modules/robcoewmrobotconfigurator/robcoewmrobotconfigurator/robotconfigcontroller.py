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

"""K8s custom resource handler for RobCo Robots."""

import os
import logging

from typing import Dict

from cattr import unstructure

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.robot import RobotConfigurationSpec
from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class RobotConfigurationController(K8sCRHandler):
    """Handle K8s RobotConfiguration custom resources."""

    error_states = [
        'moveTrolley_waitingForErrorRecovery', 'pickPackPass_waitingForErrorRecovery',
        'robotError']

    def __init__(self, namespace: str) -> None:
        """Construct."""
        self.init_default_values_fromenv()

        template_cr = get_sample_cr('robotconfiguration')

        super().__init__(
            'ewm.sap.com',
            'v1alpha1',
            'robotconfigurations',
            namespace,
            template_cr,
            {}
        )

        # Register callbacks
        self.register_callback(
            'robotconfiguration', ['ADDED', 'MODIFIED', 'REPROCESS'], self.reset_recovery_flag_cb)

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

        self.config_spec = RobotConfigurationSpec()

        self.config_spec.lgnum = envvar['EWM_LGNUM']
        self.config_spec.rsrctype = envvar['EWM_RSRC_TYPE']
        self.config_spec.rsrcgrp = envvar['EWM_RSRC_GRP']

        # List of chargers
        self.config_spec.chargers = [
            x.strip() for x in envvar['CHARGER_LIST'].split(',')]  # type: ignore

        # Battery levels in %
        self.config_spec.batteryMin = float(
            envvar['EWM_BATTERY_MIN']) if envvar['EWM_BATTERY_MIN'] else 10.0  # type: ignore
        self.config_spec.batteryOk = float(
            envvar['EWM_BATTERY_OK']) if envvar['EWM_BATTERY_OK'] else 80.0  # type: ignore
        self.config_spec.batteryIdle = float(
            envvar['EWM_BATTERY_IDLE']) if envvar['EWM_BATTERY_IDLE'] else 40.0  # type: ignore

        # Max idle time until robot moves to staging area
        self.config_spec.maxIdleTime = float(
            envvar['MAX_IDLE_TIME']) if envvar['MAX_IDLE_TIME'] else 30.0  # type: ignore

    def robco_robot_cb(self, name: str, custom_res: Dict) -> None:
        """Process Cloud Robotics robot CR."""
        # If no robot configuration for this robot already exists, create a new one
        if not self.check_cr_exists(name):
            labels = {}
            labels['cloudrobotics.com/robot-name'] = name

            # Create CR
            self.create_cr(name, labels, unstructure(self.config_spec), owner_cr=custom_res)

    def reset_recovery_flag_cb(self, name: str, custom_res: Dict) -> None:
        """Reset recovery flag of robots if they are not in robotError state anymore."""
        if custom_res['spec'].get('recoverFromRobotError'):
            statemachine = custom_res.get('status', {}).get('statemachine')
            if statemachine not in self.error_states:
                spec = {'recoverFromRobotError': False}
                # Update CR spec
                self.update_cr_spec(name, spec)
                _LOGGER.info(
                    'Robot %s recovered to state %s. recoverFromRobotError flag to false',
                    name, statemachine)
