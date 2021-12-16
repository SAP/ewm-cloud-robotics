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

"""K8s custom resource handler for EWM RobotConfigurations."""

import logging

from typing import Dict

from robcoewmtypes.helper import get_sample_cr
from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class RobotConfigurationController(K8sCRHandler):
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
