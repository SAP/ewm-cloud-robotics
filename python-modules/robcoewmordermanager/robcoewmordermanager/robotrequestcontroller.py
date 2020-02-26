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

"""K8s custom resource handler for new warehouse orders."""

import logging

from typing import Dict

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.robot import RequestFromRobotStatus

from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class RobotRequestController(K8sCRHandler):
    """Handle K8s custom resources."""

    def __init__(self) -> None:
        """Construct."""
        template_cr = get_sample_cr('robotrequest')

        super().__init__(
            'sap.com',
            'v1',
            'robotrequests',
            'default',
            template_cr,
            {}
        )

    def update_status(
            self, name: str, dtype: str, status_data: Dict,
            process_complete: bool = False) -> bool:
        """Cleanup robotrequest when work when it was processed."""
        status = {}
        status['data'] = status_data
        if process_complete:
            status['status'] = RequestFromRobotStatus.STATE_PROCESSED
        else:
            status['status'] = RequestFromRobotStatus.STATE_RUNNING
        if self.check_cr_exists(name):
            self.update_cr_status(name, status)
            return True
        else:
            return False
