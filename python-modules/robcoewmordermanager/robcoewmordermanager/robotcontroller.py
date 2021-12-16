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

import logging

from cattr import structure
from kubernetes.client.rest import ApiException

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.robot import RobcoRobotCRStatus
from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class RobotController(K8sCRHandler):
    """Handle K8s Robot custom resources."""

    def __init__(self, namespace: str) -> None:
        """Construct."""
        template_cr = get_sample_cr('robco_robot')

        super().__init__(
            'registry.cloudrobotics.com',
            'v1alpha1',
            'robots',
            namespace,
            template_cr,
            {}
        )

    def get_robot_status(self, name: str, ) -> RobcoRobotCRStatus:
        """Get robot status from CR."""
        try:
            custom_res = self.get_cr(name)
        except ApiException:
            custom_res = {}

        if custom_res.get('status') is None:
            return RobcoRobotCRStatus()

        return structure(custom_res['status'], RobcoRobotCRStatus)
