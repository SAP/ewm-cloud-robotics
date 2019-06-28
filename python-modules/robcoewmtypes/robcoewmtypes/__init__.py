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

"""Init file for robcoewmtypes."""

from .robot import Robot
from .warehouse import Warehouse, WarehouseDescription, StorageBin
from .warehouseorder import (
    WarehouseOrder, WarehouseTask, WarehouseTaskConfirmation)

ODATA_TYPE_MAP = {
    'ZEWM_ROBCO_SRV.WarehouseNumber': Warehouse,
    'ZEWM_ROBCO_SRV.WarehouseDescription': WarehouseDescription,
    'ZEWM_ROBCO_SRV.StorageBin': StorageBin,
    'ZEWM_ROBCO_SRV.WarehouseOrder': WarehouseOrder,
    'ZEWM_ROBCO_SRV.NewWarehouseOrder': WarehouseOrder,
    'ZEWM_ROBCO_SRV.OpenWarehouseTask': WarehouseTask,
    'ZEWM_ROBCO_SRV.WarehouseTaskConfirmation': WarehouseTaskConfirmation,
    'ZEWM_ROBCO_SRV.Robot': Robot
}
