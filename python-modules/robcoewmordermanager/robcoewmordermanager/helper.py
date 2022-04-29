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

"""Helper functions for order manager."""

import time

from typing import List, DefaultDict, OrderedDict as TOrderedDict

from collections import defaultdict, namedtuple, OrderedDict

from robcoewmtypes.robot import RobotConfigurationStatus
from robcoewmtypes.warehouseorder import ConfirmWarehouseTask
from robcoewminterface.exceptions import NoOrderFoundError

RobotIdentifier = namedtuple('RobotIdentifier', ['lgnum', 'rsrc'])
WhoIdentifier = namedtuple('WhoIdentifier', ['lgnum', 'who'])


def retry_on_connection_error(exc: Exception):
    """Return True if there is an connection error exception."""
    return isinstance(exc, (ConnectionError, TimeoutError, IOError))


def retry_on_conn_noorder_error(exc: Exception):
    """Return True if there is an NoOrderFoundError exception."""
    return isinstance(exc, (ConnectionError, TimeoutError, IOError, NoOrderFoundError))


class ProcessedMessageMemory:
    """Memorize processed Order Manager messages."""

    def __init__(self) -> None:
        """Construct."""
        # Warehouse order confirmations
        self.who_confirmations: DefaultDict[WhoIdentifier, List] = defaultdict(list)
        self.deleted_whos: TOrderedDict[WhoIdentifier, float] = OrderedDict()
        # RobotConfiguration Status
        self.robot_conf_status: DefaultDict[
            str, RobotConfigurationStatus] = defaultdict(RobotConfigurationStatus)

    def memorize_who_conf(self, conf: ConfirmWarehouseTask) -> None:
        """Memorize warehouse order confirmation."""
        whoident = WhoIdentifier(conf.lgnum, conf.who)
        self.who_confirmations[whoident].append(conf)

    def check_who_conf_processed(self, conf: ConfirmWarehouseTask) -> bool:
        """Check if warehouse order confirmation was processed before."""
        whoident = WhoIdentifier(conf.lgnum, conf.who)
        return bool(conf in self.who_confirmations[whoident])

    def delete_who_from_memory(self, whoident: WhoIdentifier) -> None:
        """Delete warehouse order from memory."""
        # Save timestamp when the order was deleted
        self.deleted_whos[whoident] = time.time()

        # Keep a maximum of 500 entries in this dictionary
        to_remove = max(0, len(self.deleted_whos) - 500)
        for _ in range(to_remove):
            who, _ = self.deleted_whos.popitem(last=False)
            self.who_confirmations.pop(who, None)
