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

import sys
import traceback
import logging

from typing import Dict

from retrying import retry

from robcoewmtypes.helper import get_sample_cr
from k8scrhandler.k8scrhandler import K8sCRHandler, k8s_cr_callback

from .helper import retry_on_connection_error

_LOGGER = logging.getLogger(__name__)


class RobCoRobotAPI(K8sCRHandler):
    """Handle K8s custom resources."""

    def __init__(self) -> None:
        """Constructor."""
        template_cr = get_sample_cr('robco_robot')

        self.labels = {}
        super().__init__(
            'registry.cloudrobotics.com',
            'v1alpha1',
            'robots',
            'default',
            template_cr,
            self.labels
        )

    @retry(wait_fixed=10000, retry_on_exception=retry_on_connection_error)
    @k8s_cr_callback
    def _callback(self, name: str, labels: Dict, operation: str, custom_res: Dict) -> None:
        """Process custom resource operation."""
        # Run all registered callback functions
        try:
            for callback in self.callbacks[operation].values():
                callback(name, custom_res)
        except (ConnectionError, TimeoutError, IOError) as err:
            _LOGGER.error(
                'Error connecting to SAP EWM Backend: "%s" - try again in 10 seconds', err)
            if self.thread_run:
                # Raise again that retrying can restart the callback
                raise
        except Exception:  # pylint: disable=broad-except
            _LOGGER.error(
                '%s/%s: Error while processing custom resource %s', self.group, self.plural, name)
            exc_info = sys.exc_info()
            _LOGGER.error(
                '%s/%s: Error in callback - Exception: "%s" / "%s" - TRACEBACK: %s', self.group,
                self.plural, exc_info[0], exc_info[1], traceback.format_exception(*exc_info))
        else:
            _LOGGER.debug(
                '%s/%s: Successfully processed custom resource %s', self.group, self.plural, name)
