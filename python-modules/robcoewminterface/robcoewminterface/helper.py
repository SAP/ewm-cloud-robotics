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

"""Helper functions for robcoewminterface."""


def validate_urlpath(urlpath: str) -> None:
    """Validate format of the OData URL path."""
    # To access the base path, path could be empty
    if isinstance(urlpath, str) and not urlpath:
        pass
    elif urlpath[0] != '/':
        raise ValueError('Invalid endpoint "{}". It must begin with a "/"'.format(urlpath))
    elif urlpath[-1] == '/':
        raise ValueError('Invalid endpoint "{}". It must not end with a "/"'.format(urlpath))


def val_basepath(instance, attribute, value) -> None:
    """Validate base path of the endpoint - for attr library."""
    # Validate endpoint
    validate_urlpath(value)
    # Base path must not be None
    if value is None:
        raise ValueError('Invalid endpoint "{}". It must not be "None"'.format(value))
