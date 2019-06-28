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

from robcoewmtypes.helper import get_sample_cr

from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class RobCoRobotAPI(K8sCRHandler):
    """Handle K8s custom resources."""

    def __init__(self) -> None:
        """Constructor."""
        self.init_robot_fromenv()
        template_cr = get_sample_cr('robco_robot')

        self.labels = {}
        self.labels['cloudrobotics.com/robot-name'] = self.robco_robot_name
        super().__init__(
            'registry.cloudrobotics.com',
            'v1alpha1',
            'robots',
            'default',
            template_cr,
            self.labels
        )

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
