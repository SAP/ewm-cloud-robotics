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

"""Helper functions for robot master."""


import logging

_LOGGER = logging.getLogger(__name__)


def retry_on_connection_error(exc: Exception):
    """Return True if there is an connection error exception."""
    try_again = isinstance(exc, (ConnectionError, TimeoutError, IOError))
    if try_again:
        _LOGGER.error('Error connecting to SAP EWM Backend: "%s" - try again later', exc)
    return try_again
