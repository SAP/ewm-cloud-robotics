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

from typing import Dict, Optional

from cattr import structure, unstructure

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.robot import RobotConfigurationStatus, RobotConfigurationSpec
from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class RobotConfigurationController(K8sCRHandler):
    """Handle K8s RobotConfiguration custom resources."""

    def __init__(self) -> None:
        """Construct."""
        self.init_robot_fromenv()

        # Robot configuration attributes
        self.conf = RobotConfigurationSpec()

        template_cr = get_sample_cr('robotconfiguration')

        labels = {}
        labels['cloudrobotics.com/robot-name'] = self.robco_robot_name
        super().__init__(
            'ewm.sap.com',
            'v1alpha1',
            'robotconfigurations',
            'default',
            template_cr,
            labels
        )

        # Register callbacks
        self.register_callback(
            'configUpdate', ['ADDED', 'MODIFIED', 'REPROCESS'], self.robotconfiguration_cb)

    def init_robot_fromenv(self) -> None:
        """Initialize EWM Robot from environment variables."""
        # Read environment variables
        envvar = {}
        envvar['ROBCO_ROBOT_NAME'] = os.environ.get('ROBCO_ROBOT_NAME')
        # Check if complete
        for var, val in envvar.items():
            if val is None:
                raise ValueError('Environment variable "{}" is not set'.format(var))

        self.robco_robot_name = envvar['ROBCO_ROBOT_NAME']
        self.rsrc = envvar['ROBCO_ROBOT_NAME'].upper()  # type: ignore

    def robotconfiguration_cb(self, name: str, custom_res: Dict) -> None:
        """Process robot configuration CR."""
        self.conf = structure(custom_res['spec'], RobotConfigurationSpec)

    def get_robot_state(self) -> Optional[RobotConfigurationStatus]:
        """Get current state of robot's state machine from CR."""
        custom_res = self.get_cr(self.robco_robot_name)
        if custom_res.get('status'):
            state = structure(custom_res['status'], RobotConfigurationStatus)
        else:
            state = None
        return state

    def save_robot_state(self, state: RobotConfigurationStatus) -> None:
        """Save current state of robot's state machine to CR."""
        self.update_cr_status(self.robco_robot_name, unstructure(state))
