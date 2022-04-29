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

"""K8s custom resource handler for EWM RobotConfigurations."""

import os
import logging

from typing import Dict, Optional

from cattr import structure, unstructure

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.robot import RobotConfigurationStatus, RobotConfigurationSpec
from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class RobotConfigurationHandler(K8sCRHandler):
    """Handle K8s RobotConfiguration custom resources."""

    def __init__(self, namespace: str) -> None:
        """Construct."""
        template_cr = get_sample_cr('robotconfiguration')

        labels: Dict[str, str] = {}
        super().__init__(
            'ewm.sap.com',
            'v1alpha1',
            'robotconfigurations',
            namespace,
            template_cr,
            labels
        )


class RobotConfigurationController:
    """Handle RobotConfigurations."""

    def __init__(self, robot_name: str, robot_config_handler: RobotConfigurationHandler) -> None:
        """Construct."""
        self.robot_name = robot_name
        self.rsrc = self.robot_name.upper()

        self.init_robot_fromenv()

        # Robot configuration attributes
        self.conf = RobotConfigurationSpec()

        self.handler = robot_config_handler

        # Register callbacks
        self.handler.register_callback(
            'robotconfig_update_{}'.format(self.robot_name), [
                'ADDED', 'MODIFIED', 'REPROCESS'], self.robotconfiguration_cb, self.robot_name)

    def init_robot_fromenv(self) -> None:
        """Initialize EWM Robot from environment variables."""
        # Read environment variables
        envvar = {}

        # Optional values
        self.max_retry_count = 1
        envvar['MAX_RETRY_COUNT'] = os.environ.get('MAX_RETRY_COUNT')
        if envvar['MAX_RETRY_COUNT'] is not None:
            if int(envvar['MAX_RETRY_COUNT']) > 0:
                self.max_retry_count = int(envvar['MAX_RETRY_COUNT'])

    def robotconfiguration_cb(self, name: str, custom_res: Dict) -> None:
        """Process robot configuration CR."""
        if custom_res['metadata'].get(
                'labels', {}).get('cloudrobotics.com/robot-name') == self.robot_name:
            self.conf = structure(custom_res['spec'], RobotConfigurationSpec)

    def get_robot_state(self) -> Optional[RobotConfigurationStatus]:
        """Get current state of robot's state machine from CR."""
        custom_res = self.handler.get_cr(self.robot_name)
        if custom_res.get('status'):
            state = structure(custom_res['status'], RobotConfigurationStatus)
        else:
            state = None
        return state

    def save_robot_state(self, state: RobotConfigurationStatus) -> None:
        """Save current state of robot's state machine to CR."""
        self.handler.update_cr_status(self.robot_name, unstructure(state))
