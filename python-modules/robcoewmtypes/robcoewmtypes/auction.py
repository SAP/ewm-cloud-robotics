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

"""Order auction related data types."""

from typing import List
import attr

from .helper import strstrip, validate_annotation, datetime_now_iso
from .warehouseorder import WarehouseOrder


@attr.s
class OrderRequest:
    """Order request from auctioneer."""

    lgnum: str = attr.ib(validator=validate_annotation, converter=strstrip)
    rsrctype: str = attr.ib(validator=validate_annotation, converter=strstrip)
    rsrcgrp: str = attr.ib(validator=validate_annotation, converter=strstrip)
    quantity: int = attr.ib(validator=validate_annotation, converter=int)


@attr.s
class OrderAssignment:
    """Order assignment to robot resource from auctioneer."""

    lgnum: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    who: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    rsrc: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)


@attr.s
class OrderReservationSpec:
    """SAP orderreservation CR spec."""

    orderrequest: OrderRequest = attr.ib(validator=validate_annotation)
    orderassignments: List[OrderAssignment] = attr.ib(
        default=attr.Factory(list), validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(OrderAssignment),
            iterable_validator=attr.validators.instance_of(list)))


@attr.s
class OrderReservationStatus:
    """SAP orderreservation CR status."""

    STATUS_NEW = 'NEW'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_RESERVATIONS = 'RESERVATIONS'
    STATUS_FAILED = 'FAILED'
    STATUS_SUCCEEDED = 'SUCCEEDED'
    STATUS_TIMEOUT = 'TIMEOUT'
    VALID_STATUS = [
        STATUS_NEW, STATUS_ACCEPTED, STATUS_RESERVATIONS, STATUS_FAILED, STATUS_SUCCEEDED,
        STATUS_TIMEOUT]
    IN_PROCESS_STATUS = [STATUS_NEW, STATUS_ACCEPTED, STATUS_RESERVATIONS]

    status: str = attr.ib(
        default=STATUS_NEW, validator=attr.validators.in_(VALID_STATUS), converter=strstrip)
    validuntil: str = attr.ib(
        factory=datetime_now_iso, validator=validate_annotation, converter=strstrip)
    message: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    warehouseorders: List[WarehouseOrder] = attr.ib(
        default=attr.Factory(list), validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(WarehouseOrder),
            iterable_validator=attr.validators.instance_of(list)))
    orderassignments: List[OrderAssignment] = attr.ib(
        default=attr.Factory(list), validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(OrderAssignment),
            iterable_validator=attr.validators.instance_of(list)))
