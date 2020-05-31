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

"""Warehouse order related data types."""

from typing import List
import attr

from .helper import strstrip, validate_annotation, datetime_now_iso


# SAP OData Types are starting here

@attr.s
class WarehouseTask:
    """SAP EWM Warehouse task type."""

    # SAP keys
    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    tanum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    # SAP values
    procty: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    flghuto: bool = attr.ib(
        default=False, validator=validate_annotation, converter=bool)
    tostat: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    priority: int = attr.ib(
        default=0, validator=validate_annotation, converter=int)
    weight: float = attr.ib(
        default=0.0, validator=validate_annotation, converter=float)
    unitw: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    volum: float = attr.ib(
        default=0.0, validator=validate_annotation, converter=float)
    unitv: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    vltyp: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    vlber: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    vlpla: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    vlenr: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    nltyp: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    nlber: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    nlpla: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    nlenr: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    who: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)


@attr.s
class WarehouseTaskConfirmation:
    """SAP EWM Warehouse task confirmation type."""

    # SAP complex type, no keys
    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    tanum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    tostat: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)


@attr.s
class WarehouseOrder:
    """SAP EWM Warehouse order type."""

    # SAP keys
    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    who: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    # SAP values
    status: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    areawho: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    lgtyp: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    lgpla: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    queue: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    rsrc: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    lsd: int = attr.ib(
        default=0, validator=validate_annotation, converter=int)
    topwhoid: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    refwhoid: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    flgwho: bool = attr.ib(
        default=False, validator=validate_annotation, converter=bool)
    flgto: bool = attr.ib(
        default=False, validator=validate_annotation, converter=bool)
    # Lists of dependend SAP objects
    warehousetasks: List[WarehouseTask] = attr.ib(
        default=attr.Factory(list), validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(WarehouseTask),
            iterable_validator=attr.validators.instance_of(list)))


# Non SAP OData Types are starting here

@attr.s
class ConfirmWarehouseTask:
    """Attributes to confirm a warehouse task."""

    # Warehouse task identification
    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    tanum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    # FIRST or SECOND confirmation with validator method
    confirmationnumber: str = attr.ib()
    # SUCCESS or ERROR with validator
    confirmationtype: str = attr.ib()
    # Date in ISO format when warehouse task was confirmed
    confirmationdate: str = attr.ib(
        factory=datetime_now_iso,
        validator=attr.validators.instance_of(str))
    # Related warehouse order
    who: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    # Use case specific attributes
    rsrc: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)

    # Validators
    FIRST_CONF = 'FIRST'
    SECOND_CONF = 'SECOND'

    CONF_SUCCESS = 'SUCCESS'
    CONF_ERROR = 'ERROR'
    CONF_UNASSIGN = 'UNASSIGN'

    @confirmationnumber.validator
    def validate_confirmationnumber(self, attribute, value) -> None:
        """Validate confirmation."""
        cls = self.__class__
        if value not in [cls.FIRST_CONF, cls.SECOND_CONF]:
            raise ValueError('Attribute "confirmationnumber" must be FIRST or SECOND')

    @confirmationtype.validator
    def validate_confirmationtype(self, attribute, value) -> None:
        """Validate confirmation."""
        cls = self.__class__
        if value not in [cls.CONF_SUCCESS, cls.CONF_ERROR, cls.CONF_UNASSIGN]:
            raise ValueError('Attribute "confirmationtype" must be SUCCESS, ERROR or UNASSIGN')


@attr.s
class WarehouseOrderIdent:
    """Warehouse Order identitfier."""

    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    who: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)


@attr.s
class WarehouseOrderCRDSpec:
    """Warehouse order CRD spec type."""

    STATE_RUNNING = 'RUNNING'
    STATE_PROCESSED = 'PROCESSED'

    data: WarehouseOrder = attr.ib(validator=validate_annotation)
    order_status: str = attr.ib()
    process_status: List[ConfirmWarehouseTask] = attr.ib(
        default=attr.Factory(list), validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(ConfirmWarehouseTask),
            iterable_validator=attr.validators.instance_of(list)))
    sequence: int = attr.ib(default=0, validator=validate_annotation, converter=int)

    @order_status.validator
    def validate_order_status(self, attribute, value) -> None:
        """Validate confirmation."""
        cls = self.__class__
        if value not in [cls.STATE_PROCESSED, cls.STATE_RUNNING]:
            raise ValueError('Attribute "order_status" must be RUNNING or PROCESSED')
