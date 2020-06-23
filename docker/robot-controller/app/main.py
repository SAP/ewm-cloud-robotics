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

"""Run the SAP EWM robot controller."""

import sys
import traceback
import logging

from robcoewmrobotcontroller import run as robot_controller


# According to
# https://medium.com/retailmenot-engineering/formatting-python-logs-for-stackdriver-5a5ddd80761c
class _MaxLevelFilter(logging.Filter):
    """MaxLevelFilter filters log entry by their log level."""

    def __init__(self, highest_log_level: int) -> None:
        """Initialize."""
        super().__init__()
        self._highest_log_level = highest_log_level

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter if log record by log level."""
        return record.levelno <= self._highest_log_level


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
FORMATTER = logging.Formatter('- %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

# Add formatter to log handlers
INFO_HANDLER.setFormatter(FORMATTER)
ERROR_HANDLER.setFormatter(FORMATTER)

# Add log handlers to logger
_LOGGER.addHandler(INFO_HANDLER)
_LOGGER.addHandler(ERROR_HANDLER)


def main() -> None:
    """Run main program."""
    try:
        # Run robot controller
        robot_controller.run_robot()
    except Exception:  # pylint: disable=broad-except
        exc_info = sys.exc_info()
        _LOGGER.critical(
            'Unexpected error "%s" - "%s" - TRACEBACK: \n %s', exc_info[0],
            exc_info[1], traceback.format_exception(*exc_info))
        sys.exit('Application terminated with exception: "{}" - "{}"'.format(
            exc_info[0], exc_info[1]))


if __name__ == '__main__':
    # Run main program
    main()
