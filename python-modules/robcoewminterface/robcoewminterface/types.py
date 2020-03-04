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
    AUTH_OAUTH = 'OAuth'
    AUTH_TYPES = [AUTH_BASIC, AUTH_OAUTH]

    host = attr.ib(validator=attr.validators.instance_of(str), converter=str)
    basepath = attr.ib(validator=val_basepath, converter=str)
    authorization = attr.ib(converter=str)
    user = attr.ib(validator=attr.validators.instance_of(str), converter=str, default='')
    password = attr.ib(validator=attr.validators.instance_of(str), converter=str, default='')
    clientid = attr.ib(validator=attr.validators.instance_of(str), converter=str, default='')
    clientsecret = attr.ib(validator=attr.validators.instance_of(str), converter=str, default='')
    tokenendpoint = attr.ib(validator=attr.validators.instance_of(str), converter=str, default='')

    @authorization.validator
    def _check_auth(self, attribute, value):
        if value not in self.AUTH_TYPES:
            raise ValueError(
                'Config error: Invalid authorization type "{}". '
                'Valid values are {}'.format(value, ODataConfig.AUTH_TYPES))

    @tokenendpoint.validator
    def _check_token(self, attribute, value):
        if not value and self.authorization == self.AUTH_OAUTH:
            raise ValueError('Using OAuth with no token endpoint set')

    @clientid.validator
    def _check_clientid(self, attribute, value):
        if not value and self.authorization == self.AUTH_OAUTH:
            raise ValueError('Using OAuth with no client id set')

    @clientsecret.validator
    def _check_clientsecret(self, attribute, value):
        if not value and self.authorization == self.AUTH_OAUTH:
            raise ValueError('Using OAuth with client secret set')

    @user.validator
    def _check_user(self, attribute, value):
        if not value and self.authorization == self.AUTH_BASIC:
            raise ValueError('Using Basic authentication with no user set')

    @password.validator
    def _check_password(self, attribute, value):
        if not value and self.authorization == self.AUTH_BASIC:
            raise ValueError('Using Basic authentication with no password set')
