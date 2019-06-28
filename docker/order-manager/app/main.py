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

"""Run the SAP EWM order manager."""

import sys
import traceback
import logging

from robcoewmordermanager import run as om


# According to
# https://medium.com/retailmenot-engineering/formatting-python-logs-for-stackdriver-5a5ddd80761c
class _MaxLevelFilter(object):
    def __init__(self, highest_log_level):
        self._highest_log_level = highest_log_level

    def filter(self, log_record):
        return log_record.levelno <= self._highest_log_level


# Create root logger
_LOGGER = logging.getLogger()
_LOGGER.setLevel(logging.INFO)

# Create console handler and set level to info
# Level INFO + WARNING
INFO_HANDLER = logging.StreamHandler(sys.stdout)
INFO_HANDLER.setLevel(logging.INFO)
INFO_HANDLER.addFilter(_MaxLevelFilter(logging.WARNING))
# Levels ERROR+
ERROR_HANDLER = logging.StreamHandler(sys.stderr)
ERROR_HANDLER.setLevel(logging.ERROR)

# Create formatter
FORMATTER = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - '
    '%(message)s')

# Add formatter to log handlers
INFO_HANDLER.setFormatter(FORMATTER)
ERROR_HANDLER.setFormatter(FORMATTER)

# Add log handlers to logger
_LOGGER.addHandler(INFO_HANDLER)
_LOGGER.addHandler(ERROR_HANDLER)

if __name__ == "__main__":
    # Run order manager
    try:
        om.run_ordermanager()
    except Exception:  # pylint: disable=broad-except
        EXC_INFO = sys.exc_info()
        _LOGGER.fatal(
            'Unexpected error "%s" - "%s" - TRACEBACK: \n %s', EXC_INFO[0],
            EXC_INFO[1], traceback.format_exception(*EXC_INFO))
        sys.exit('Application terminated with exception: "{}" - "{}"'.format(
            EXC_INFO[0], EXC_INFO[1]))
