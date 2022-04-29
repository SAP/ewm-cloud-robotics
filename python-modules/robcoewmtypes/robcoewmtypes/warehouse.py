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

"""Warehouse related data types."""

from typing import List
import attr

from .helper import strstrip, validate_annotation


# SAP OData Types are starting here

@attr.s
class WarehouseDescription:
    """SAP EWM Warehouse description type."""

    # SAP keys
    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    spras: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    # SAP values
    lnumt: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)


@attr.s
class StorageBin:
    """SAP EWM Storage bin type."""

    # SAP keys
    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    lgpla: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    # SAP values
    lgtyp: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    lgber: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    lptyp: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    aisle: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    stack: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    lvlv: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    xcord: float = attr.ib(
        default=0.0, validator=validate_annotation, converter=float)
    ycord: float = attr.ib(
        default=0.0, validator=validate_annotation, converter=float)
    zcord: float = attr.ib(
        default=0.0, validator=validate_annotation, converter=float)


@attr.s
class Warehouse:
    """SAP EWM Warehouse type."""

    # SAP keys
    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    # Lists with dependend SAP objects
    descriptions: List[WarehouseDescription] = attr.ib(
        default=attr.Factory(list), validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(WarehouseDescription),
            iterable_validator=attr.validators.instance_of(list)))
    storagebins: List[StorageBin] = attr.ib(
        default=attr.Factory(list), validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(StorageBin),
            iterable_validator=attr.validators.instance_of(list)))


# Non SAP OData Types are starting here
