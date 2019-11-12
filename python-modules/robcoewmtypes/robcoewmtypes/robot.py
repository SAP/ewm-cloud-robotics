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


# Non SAP OData Types are starting here

@attr.s
class RequestFromRobot:
    """Robot request type."""

    # Robot identification
    lgnum: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    rsrc: str = attr.ib(
        validator=attr.validators.instance_of(str), converter=strstrip)
    # Use case specific attributes
    requestwork: bool = attr.ib(
        default=False, validator=validate_annotation, converter=bool)
    requestnewwho: bool = attr.ib(
        default=False, validator=validate_annotation, converter=bool)
    notifywhocompletion: str = attr.ib(
        default='', validator=attr.validators.instance_of(str), converter=strstrip)


@attr.s
class RequestFromRobotStatus:
    """Robot request status type."""

    STATE_PROCESSED = 'PROCESSED'
    STATE_RUNNING = 'RUNNING'
    STATE_DELETED = 'DELETED'

    # Status of request
    data: RequestFromRobot = attr.ib(validator=validate_annotation)
    # Processing status
    status: str = attr.ib()

    @status.validator
    def validate_status(self, attribute, value) -> None:
        """Validate confirmation."""
        cls = self.__class__
        if value not in [cls.STATE_PROCESSED, cls.STATE_RUNNING, cls.STATE_DELETED]:
            raise ValueError('Attribute "status" must be RUNNING, PROCESSED or DELETED')


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
    target_name: str = attr.ib(default='', validator=attr.validators.instance_of(str))


@attr.s
class RobotConfigurationStatus:
    """Current status of warehouse robots state machine."""

    statemachine: str = attr.ib(validator=validate_annotation)
    statebeforeerror: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    mission: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    missiontarget: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    lgnum: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    who: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    tanum: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
    subwho: str = attr.ib(default='', validator=validate_annotation, converter=strstrip)
