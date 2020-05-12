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

"""Exception classes for robcoewminterface."""

import sys
import inspect

from typing import Type

ODATA_ERROR_CODES = {
    '403': 'Authorization error',
    '404': 'Not found error',
    'ROBOT_NOT_FOUND': 'Robot resource not found.',
    'NO_ORDER_FOUND': 'No Warehouse Order found.',
    'ROBOT_STATUS_NOT_SET': 'Robot resource status could not be set.',
    'INTERNAL_ERROR': 'Internal error.',
    'INTERNAL_SERVER_ERROR': 'Internal server error. Not a SAP EWM application error.',
    'NO_RESOURCE_TYPE': 'No resource type provided.',
    'NO_RESOURCE_GROUP': 'No resource group provided.',
    'RESOURCE_EXISTING': 'Resource already existing.',
    'RESOURCE_TYPE_IS_NO_ROBOT': 'Resource type is not robot resource type.',
    'DB_UPDATE_FAILED': 'Database update failed.',
    'WAREHOUSE_ORDER_ASSIGNED': 'Warehouse Order is already assigned.',
    'WAREHOUSE_TASK_ASSIGNED': 'Warehouse Task is already assigned.',
    'WAREHOUSE_ORDER_LOCKED': 'Warehouse Order is locked.',
    'RESOURCE_GROUP_NOT_EXISTING': 'Resource Group not existing.',
    'ERROR_CREATING_PICKHU': 'Error creating Pick HU for Robot Resource.',
    'QUEUE_NOT_EXISTING': 'Queue is not existing.',
    'WAREHOUSE_TASK_NOT_CONFIRMED': 'Warehouse Task could not be confirmed.',
    'ROBOT_HAS_ORDER': 'Robot has already a Warehouse Order assigned.',
    'WAREHOUSE_ORDER_IN_PROCESS': 'Warehouse Order is in process.',
    'WAREHOUSE_ORDER_NOT_UNASSIGNED': 'Warehouse Order was not unassigned.',
    'NO_ERROR_QUEUE_FOUND': 'No Error Queue found.',
    'QUEUE_NOT_CHANGED': 'Queue not changed.',
    'WAREHOUSE_TASK_ALREADY_CONFIRMED': 'Warehouse Task is confirmed already.',
    'URL_PARAM_BODY_INCONSISTENT': 'URL parameters and POST body inconsistent.',
    'WAREHOUSE_ORDER_STATUS_NOT_UPDATED': 'Warehouse Order status not updated.',
    'FOREIGN_LOCK': 'Foreign lock.',
    'NO_AUTHORIZATION': 'No authorization in EWM backend.'
}

ODATA_ERROR_REVERSE = {v: k for k, v in ODATA_ERROR_CODES.items()}


class ODataAPIException(Exception):
    """Exceptions for OData API calls."""

    # OData error code this exception class should be used to.
    # 'ODataAPIException' is a generic code for all unmatched error codes
    ERROR_CODE = 'ODataAPIException'

    def __init__(self, *args, **kwargs) -> None:
        """Construct."""
        # Allow variable error code only for base exception class
        error_code = kwargs.pop('error_code', None)
        if error_code and self.__class__.__name__ == 'ODataAPIException':
            self.error_code = error_code
        else:
            # Get error code from class variable
            self.error_code = self.__class__.ERROR_CODE
        self.message = ODATA_ERROR_CODES.get(self.error_code, None)
        if self.message:
            error_message = 'OData API error code: {} - Message: {}'.format(
                self.error_code, self.message)
        else:
            error_message = 'OData API error code: {}'.format(self.error_code)
        super().__init__(error_message, *args, **kwargs)  # type: ignore


class NoOrderFoundError(ODataAPIException):
    """No warehouse order was found."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'NO_ORDER_FOUND'


class WarehouseOrderLockedError(ODataAPIException):
    """Warehouse Order is locked."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'WAREHOUSE_ORDER_LOCKED'


class WarehouseTaskAssignedError(ODataAPIException):
    """Warehouse Task is already assigned."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'WAREHOUSE_TASK_ASSIGNED'


class WarehouseOrderAssignedError(ODataAPIException):
    """Warehouse Order is already assigned."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'WAREHOUSE_ORDER_ASSIGNED'


class WarehouseTaskAlreadyConfirmedError(ODataAPIException):
    """Warehouse Task already confirmed."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'WAREHOUSE_TASK_ALREADY_CONFIRMED'


class RobotHasOrderError(ODataAPIException):
    """Robot has already a Warehouse Order assigned."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'ROBOT_HAS_ORDER'


class RobotNotFoundError(ODataAPIException):
    """Robot resource was not found."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'ROBOT_NOT_FOUND'


class RobotStatusNotSetError(ODataAPIException):
    """Robot status could not be set."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'ROBOT_STATUS_NOT_SET'


class ResourceTypeIsNoRobotError(ODataAPIException):
    """Resource type is not a robot type."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'RESOURCE_TYPE_IS_NO_ROBOT'


class ResourceGroupNotExistingError(ODataAPIException):
    """Resource group is not existing."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'RESOURCE_GROUP_NOT_EXISTING'


class InternalError(ODataAPIException):
    """Internal error."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'INTERNAL_ERROR'


class InternalServerError(ODataAPIException):
    """Internal server error."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'INTERNAL_SERVER_ERROR'


class ForeignLockError(ODataAPIException):
    """Foreign lock error."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'FOREIGN_LOCK'


class NoAuthorizationError(ODataAPIException):
    """NoAuthorization error."""

    # OData error code this exception class should be used to.
    ERROR_CODE = 'NO_AUTHORIZATION'


class AuthorizationError(ODataAPIException):
    """Authorization error."""

    # OData error code this exception class should be used to.
    ERROR_CODE = '403'


class NotFoundError(ODataAPIException):
    """Object not found error."""

    # OData error code this exception class should be used to.
    ERROR_CODE = '404'


def get_exception_class(error_code: str) -> Type[ODataAPIException]:
    """Get and return the exception class for a OData error code."""
    for _, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj):
            try:
                class_error_code = getattr(obj, 'ERROR_CODE')
            except AttributeError:
                # No error attribute in class -> not a valid exception class
                continue
            else:
                if class_error_code == error_code:
                    # Codes are matching -> return class
                    return obj

    # No specific exception class found -> return generic one
    return ODataAPIException
