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

"""Run the SAP EWM robot configurator."""

import os
import sys
import logging

from pythonjsonlogger import jsonlogger

from robcoewmrobotconfigurator import run as robotconfigurator


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """CustomJsonFormatter with extra fields for log level."""

    def add_fields(self, log_record, record, message_dict):
        """Add fields for level and severity."""
        super().add_fields(log_record, record, message_dict)

        # Ensure level field is propagated
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        # Add field for severity
        log_record['severity'] = log_record['level']


# According to
# https://medium.com/retailmenot-engineering/formatting-python-logs-for-stackdriver-5a5ddd80761c
class MaxLevelFilter(logging.Filter):
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

# Determine log level
LOG_LEVEL = str(os.environ.get('LOG_LEVEL')).upper()
# Default level is INFO
if LOG_LEVEL == 'NONE':
    LOG_LEVEL = 'INFO'
LEVEL = logging.INFO
if LOG_LEVEL == 'DEBUG':
    LEVEL = logging.DEBUG
elif LOG_LEVEL == 'WARNING' or LOG_LEVEL.lower() == 'WARN':
    LEVEL = logging.WARNING
elif LOG_LEVEL == 'ERROR':
    LEVEL = logging.ERROR

_LOGGER.setLevel(LEVEL)

# Determine log format
if str(os.environ.get('LOG_FORMAT')).lower() == 'json':
    # JSON log handler
    JSON_HANDLER = logging.StreamHandler()
    # Create formatter
    LOG_KEYS = [
        'exc_info',
        'exc_text',
        'filename',
        'funcName',
        'levelname',
        'lineno',
        'message',
        'name',
        'pathname',
        'threadName']
    JSON_FORMAT = ' '.join(['%({0:s})s'.format(i) for i in LOG_KEYS])
    JSON_FORMATTER = CustomJsonFormatter(
        JSON_FORMAT, rename_fields={'levelname': 'level', 'name': 'logger'}, timestamp=True)
    JSON_HANDLER.setFormatter(JSON_FORMATTER)
    _LOGGER.addHandler(JSON_HANDLER)

    _LOGGER.info('Using JSON log format')
else:
    # Create console handler and set level to info
    # Level INFO + WARNING
    INFO_HANDLER = logging.StreamHandler(sys.stdout)
    INFO_HANDLER.setLevel(LEVEL)
    INFO_HANDLER.addFilter(MaxLevelFilter(logging.WARNING))
    # Levels ERROR+
    ERROR_HANDLER = logging.StreamHandler(sys.stderr)
    ERROR_HANDLER.setLevel(logging.ERROR)

    # Create formatter
    LOG_FORMATTER = logging.Formatter('- %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

    # Add formatter to log handlers
    INFO_HANDLER.setFormatter(LOG_FORMATTER)
    ERROR_HANDLER.setFormatter(LOG_FORMATTER)

    # Add log handlers to logger
    _LOGGER.addHandler(INFO_HANDLER)
    _LOGGER.addHandler(ERROR_HANDLER)

    _LOGGER.info('Using CONSOLE log format')

_LOGGER.info('Log level is %s', LOG_LEVEL)


def main() -> None:
    """Run main program."""
    try:
        # Run robot configurator
        robotconfigurator.run_robotconfigurator()
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.critical('Unexpected error in main program: %s', err, exc_info=True)
        sys.exit('Application terminated with error')


if __name__ == '__main__':
    # Run main program
    main()
