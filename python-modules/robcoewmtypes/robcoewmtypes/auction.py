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
class Scope:
    """Scope of an auctioneer."""

    lgnum: str = attr.ib(validator=validate_annotation, converter=strstrip)
    rsrctype: str = attr.ib(validator=validate_annotation, converter=strstrip)
    rsrcgrp: str = attr.ib(validator=validate_annotation, converter=strstrip)


@attr.s
class Configuration:
    """Configuration of an auctioneer."""

    # pylint: disable=invalid-name
    maxOrdersPerRobot: int = attr.ib(validator=validate_annotation, converter=int)
    minOrdersPerRobot: int = attr.ib(validator=validate_annotation, converter=int)
    minOrdersPerAuction: int = attr.ib(validator=validate_annotation, converter=int)


@attr.s
class AuctioneerSpec:
    """Auctioneer specification."""

    scope: Scope = attr.ib(validator=validate_annotation)
    configuration: Configuration = attr.ib(validator=validate_annotation)


@attr.s
class AuctioneerStatus:
    """Auctioneer status."""

    STATUS_WATCHING = 'WATCHING'
    STATUS_WAITING = 'WAITING'
    STATUS_AUCTION = 'AUCTION'
    STATUS_ERROR = 'ERROR'
    VALID_STATUS = [STATUS_WATCHING, STATUS_WAITING, STATUS_AUCTION, STATUS_ERROR]

    # pylint: disable=invalid-name
    availableRobots: List[str] = attr.ib(
        default=attr.Factory(list), validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(str),
            iterable_validator=attr.validators.instance_of(list)))
    robotsInScope: List[str] = attr.ib(
        default=attr.Factory(list), validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(str),
            iterable_validator=attr.validators.instance_of(list)))
    warehouseOrdersInProcess: int = attr.ib(
        default=0, validator=validate_annotation, converter=int)
    runningAuctions: int = attr.ib(default=0, validator=validate_annotation, converter=int)
    status: str = attr.ib(
        default=STATUS_ERROR, validator=attr.validators.in_(VALID_STATUS), converter=strstrip)
    message: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    lastStatusChangeTime: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    updateTime: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)


@attr.s
class OrderAuctionSpec:
    """SAP orderauction CR spec."""

    STATUS_OPEN = 'OPEN'
    STATUS_CLOSED = 'CLOSED'
    STATUS_COMPLETED = 'COMPLETED'
    VALID_STATUS = [STATUS_OPEN, STATUS_CLOSED, STATUS_COMPLETED]

    validuntil: str = attr.ib(validator=validate_annotation, converter=strstrip)
    auctionstatus: str = attr.ib(
        default=STATUS_OPEN, validator=attr.validators.in_(VALID_STATUS), converter=strstrip)
    warehouseorders: List[WarehouseOrder] = attr.ib(
        default=attr.Factory(list), validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(WarehouseOrder),
            iterable_validator=attr.validators.instance_of(list)))


@attr.s
class WarehouseOrderBidding:
    """Bidding for an orderauction."""

    lgnum: str = attr.ib(validator=validate_annotation, converter=strstrip)
    who: str = attr.ib(validator=validate_annotation, converter=strstrip)
    bidding: float = attr.ib(validator=validate_annotation, converter=float)


@attr.s
class OrderAuctionStatus:
    """SAP orderauction CR status."""

    STATUS_RUNNING = 'RUNNING'
    STATUS_COMPLETED = 'COMPLETED'
    VALID_STATUS = [STATUS_RUNNING, STATUS_COMPLETED]

    bidstatus: str = attr.ib(
        default=STATUS_RUNNING, validator=attr.validators.in_(VALID_STATUS), converter=strstrip)
    biddings: List[WarehouseOrderBidding] = attr.ib(
        default=attr.Factory(list), validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(WarehouseOrderBidding),
            iterable_validator=attr.validators.instance_of(list)))


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
