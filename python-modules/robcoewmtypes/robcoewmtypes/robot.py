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

"""Robot related data types."""

from typing import List

import attr

from .helper import strstrip, validate_annotation


# SAP OData Types are starting here

@attr.s
class Robot:
    """SAP EWM Robot type."""

    # SAP keys
    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    rsrc: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    # SAP values
    rsrctype: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    rsrcgrp: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    actualbin: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    actqueue: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    exccodeoverall: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)


@attr.s
class RobotResourceType:
    """SAP EWM Robot Resource Type."""

    # SAP keys
    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    rsrctype: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    # SAP values
    robottype: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)
    errorqueue: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)


@attr.s
class ResourceTypeDescription:
    """SAP EWM Resource Type description type."""

    # SAP keys
    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    rsrctype: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    langu: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    # SAP values
    text: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)


@attr.s
class ResourceGroup:
    """SAP EWM Resource Group."""

    # SAP keys
    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    rsrcgrp: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    # SAP values
    zewmerrorqueue: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)


@attr.s
class ResourceGroupDescription:
    """SAP EWM Resource Group description type."""

    # SAP keys
    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    rsrcgrp: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    langu: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    # SAP values
    text: str = attr.ib(
        default='', validator=validate_annotation, converter=strstrip)


# Non SAP OData Types are starting here

@attr.s
class RobotMission:
    """Data class for robot missions."""

    ACTION_UNKNOWN = 'UNKNOWN'
    ACTION_DOCKING = 'DOCKING'
    ACTION_MOVING = 'MOVING'

    STATE_ACCEPTED = 'ACCEPTED'
    STATE_RUNNING = 'RUNNING'
    STATE_SUCCEEDED = 'SUCCEEDED'
    STATE_FAILED = 'FAILED'
    STATE_CANCELED = 'CANCELED'
    STATE_QUEUED = 'QUEUED'
    STATE_DELETED = 'DELETED'
    STATE_UNKNOWN = 'UNKNOWN'
    STATES_CANCELED = [STATE_CANCELED, STATE_DELETED]

    name: str = attr.ib(default='', validator=attr.validators.instance_of(str))
    status: str = attr.ib(default=STATE_UNKNOWN, validator=attr.validators.instance_of(str))
    active_action: str = attr.ib(
        default=ACTION_UNKNOWN, validator=attr.validators.instance_of(str))


@attr.s
class RobotConfigurationSpec:
    """Current spec of warehouse robots state machine."""

    MODE_RUN = 'RUN'
    MODE_IDLE = 'IDLE'
    MODE_CHARGE = 'CHARGE'
    MODE_STOP = 'STOP'
    VALID_MODES = [MODE_RUN, MODE_IDLE, MODE_CHARGE, MODE_STOP]

    # pylint: disable=invalid-name
    lgnum: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    rsrctype: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    rsrcgrp: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    batteryMin: float = attr.ib(default=0.0, validator=validate_annotation, converter=float)
    batteryOk: float = attr.ib(default=0.0, validator=validate_annotation, converter=float)
    batteryIdle: float = attr.ib(default=0.0, validator=validate_annotation, converter=float)
    maxIdleTime: float = attr.ib(default=0.0, validator=validate_annotation, converter=float)
    recoverFromRobotError: bool = attr.ib(default=False, validator=validate_annotation)
    mode: str = attr.ib(
        default=MODE_STOP, validator=attr.validators.in_(VALID_MODES), converter=strstrip)
    chargers: List[str] = attr.ib(
        default=attr.Factory(list), validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(str),
            iterable_validator=attr.validators.instance_of(list)))


@attr.s
class RobotConfigurationStatus:
    """Current status of warehouse robots state machine."""

    statemachine: str = attr.ib(default='', validator=validate_annotation)
    mission: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    lgnum: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    who: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    tanum: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    subwho: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    updateTime: str = attr.ib(  # pylint: disable=invalid-name
        default='1970-01-01T00:00:00.000000Z', validator=validate_annotation, converter=strstrip)


@attr.s
class RobcoRobotStates:
    """Robot states in RobCo."""

    STATE_UNDEFINED = 'UNDEFINED'
    STATE_UNAVAILABLE = 'UNAVAILABLE'
    STATE_AVAILABLE = 'AVAILABLE'
    STATE_EMERGENCY_STOP = 'EMERGENCY_STOP'
    STATE_ERROR = 'ERROR'
    VALID_STATES = [
        STATE_UNDEFINED, STATE_UNAVAILABLE, STATE_AVAILABLE, STATE_EMERGENCY_STOP, STATE_ERROR]


@attr.s
class RobcoRobotCRStatusRobot:
    """Robot attribute in status of Robco robot CR."""

    # pylint: disable=invalid-name
    batteryPercentage: float = attr.ib(default=0.0, validator=validate_annotation)
    lastStateChangeTime: str = attr.ib(
        default='1970-01-01T00:00:00.000000Z', validator=validate_annotation, converter=strstrip)
    state: str = attr.ib(
        default=RobcoRobotStates.STATE_UNDEFINED,
        validator=attr.validators.in_(RobcoRobotStates.VALID_STATES), converter=strstrip)
    updateTime: str = attr.ib(
        default='1970-01-01T00:00:00.000000Z', validator=validate_annotation, converter=strstrip)


@attr.s
class RobcoRobotCRStatus:
    """Status of Robco robot CR."""

    robot: RobcoRobotCRStatusRobot = attr.ib(
        default=attr.Factory(RobcoRobotCRStatusRobot), validator=validate_annotation)
