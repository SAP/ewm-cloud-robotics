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

"""OData related data types."""

import attr

from .helper import val_basepath


@attr.s(frozen=True)
class ODataConfig:
    """OData config type."""

    # Constants
    AUTH_BASIC = 'Basic'
    AUTH_ODATA = 'OData'
    AUTH_TYPES = [AUTH_BASIC]

    host = attr.ib(validator=attr.validators.instance_of(str), converter=str)
    basepath = attr.ib(validator=val_basepath, converter=str)
    authorization = attr.ib(converter=str)
    user = attr.ib(validator=attr.validators.instance_of(str), converter=str)
    password = attr.ib(validator=attr.validators.instance_of(str), converter=str)

    @authorization.validator
    def _check_auth(self, attribute, value):
        if value not in ODataConfig.AUTH_TYPES:
            raise ValueError(
                'Config error: Invalid authorization type "{}". '
                'Valid values are {}'.format(value, ODataConfig.AUTH_TYPES))
