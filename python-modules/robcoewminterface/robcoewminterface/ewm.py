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

"""EWM OData provider for robcoewminterface."""

import logging
from typing import List, Optional

from robcoewmtypes.warehouse import Warehouse, WarehouseDescription, StorageBin
from robcoewmtypes.warehouseorder import (
    WarehouseOrder, WarehouseTask, WarehouseTaskConfirmation, ConfirmWarehouseTask)
from robcoewmtypes.robot import Robot

from .conversion import odata_to_attr
from .exceptions import ODataAPIException, get_exception_class
from .odata import ODataHandler

_LOGGER = logging.getLogger(__name__)

HTTP_SUCCESS = [200, 201, 202, 203, 204, 205, 206, 207, 208, 226]
HTTP_BUS_EXCEPTION = [400]

STATE_SUCCEEDED = 'SUCCEEDED'


class WarehouseOData:
    """Interaction with EWM warehouse APIs."""

    def __init__(self, odata: ODataHandler) -> None:
        """Constructor."""
        self._odata = odata

    def get_warehouse(
            self, lgnum: str, descriptions: bool = False, storagebins: bool = False) -> Warehouse:
        """
        Get data from one warehouse.

        Optionally expand descriptions and storage bins.
        """
        # define endpoint
        endpoint = '/WarehouseNumberSet'

        # create URL parameter
        params = {}
        if descriptions or storagebins:
            exvalues = []
            if descriptions:
                exvalues.append('WarehouseDescriptions')
            if storagebins:
                exvalues.append('StorageBins')
            params['$expand'] = ','.join(exvalues)

        # create IDs
        ids = {'Lgnum': lgnum}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, urlparams=params, ids=ids)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def get_warehouses(self, descriptions: bool = False,
                       storagebins: bool = False) -> Optional[List[Warehouse]]:
        """
        Get data from all warehouses.

        Optionally expand descriptions and storage bins.
        """
        # define endpoint
        endpoint = '/WarehouseNumberSet'

        # create URL parameter
        params = {}
        if descriptions or storagebins:
            exvalues = []
            if descriptions:
                exvalues.append('WarehouseDescriptions')
            if storagebins:
                exvalues.append('StorageBins')
            params['$expand'] = ','.join(exvalues)

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, urlparams=params)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint,
                result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def get_whdescription(self, lgnum: str, spras: str) -> WarehouseDescription:
        """Get description from one warehouse in a language."""
        # define endpoint
        endpoint = '/WarehouseDescriptionSet'

        # create IDs
        ids = {'Lgnum': lgnum, 'Spras': spras}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def get_whdescriptions(self, lgnum: Optional[str] = None) -> List[WarehouseDescription]:
        """
        Get descriptions from warehouses in all languages.

        Optionally filter by warehouse.
        """
        if lgnum:
            # define endpoint
            endpoint = '/WarehouseNumberSet'
            # create IDs
            ids = {'Lgnum': lgnum}
            # create navigation
            nav = '/WarehouseDescriptions'
        else:
            # define endpoint
            endpoint = '/WarehouseDescriptionSet'
            # create IDs
            ids = None
            # create navigation
            nav = None

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids, navigation=nav)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def get_storagebin(self, lgnum: str, lgpla: str) -> StorageBin:
        """Get one specific storage bin."""
        # define endpoint
        endpoint = '/StorageBinSet'

        # create IDs
        ids = {'Lgnum': lgnum, 'Lgpla': lgpla}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint,
                    result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def get_storagebins(self, lgnum: Optional[str] = None) -> List[WarehouseDescription]:
        """
        Get all storage bins from the system.

        Optionally filter by warehouse.
        """
        if lgnum:
            # define endpoint
            endpoint = '/WarehouseNumberSet'
            # create IDs
            ids = {'Lgnum': lgnum}
            # create navigation
            nav = '/StorageBins'
        else:
            # define endpoint
            endpoint = '/StorageBinSet'
            # create IDs
            ids = None
            # create navigation
            nav = None

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids, navigation=nav)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)


class WarehouseOrderOData:
    """Interaction with EWM warehouse order APIs."""

    def __init__(self, odata: ODataHandler) -> None:
        """Constructor."""
        self._odata = odata

    def get_warehouseorder(
            self, lgnum: str, who: str, openwarehousetasks: bool = False) -> WarehouseOrder:
        """
        Get data from one warehouse order.

        Optionally expand warehouse tasks.
        """
        # define endpoint
        endpoint = '/WarehouseOrderSet'

        # create URL parameter
        params = {}
        if openwarehousetasks:
            exvalues = []
            exvalues.append('OpenWarehouseTasks')
            params['$expand'] = ','.join(exvalues)

        # create IDs
        ids = {'Lgnum': lgnum, 'Who': who}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids, urlparams=params)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def get_warehouseorders(
            self, lgnum: Optional[str] = None, topwhoid: Optional[str] = None,
            openwarehousetasks: bool = False) -> List[WarehouseOrder]:
        """
        Get data from all warehouse orders.

        Optionally filter by warehouse expand warehouse tasks.
        """
        # create URL parameter
        params = {}
        if openwarehousetasks:
            exvalues = []
            exvalues.append('OpenWarehouseTasks')
            params['$expand'] = ','.join(exvalues)

        # Define endpoint IDs and navigation based on parameter selection
        if lgnum and topwhoid:
            # define endpoint
            endpoint = '/WarehouseOrderSet'
            # create IDs
            ids = None
            # create navigation
            nav = None
            # add filter URL param
            params['$filter'] = "Lgnum eq '{}' and Topwhoid eq '{}'".format(
                lgnum, topwhoid)
        elif lgnum:
            # define endpoint
            endpoint = '/WarehouseNumberSet'
            # create IDs
            ids = {'Lgnum': lgnum}
            # create navigation
            nav = '/WarehouseOrders'
        elif topwhoid:
            # define endpoint
            endpoint = '/WarehouseOrderSet'
            # create IDs
            ids = None
            # create navigation
            nav = None
            # add filter URL param
            params['$filter'] = "Topwhoid eq '{}'".format(topwhoid)
        else:
            # define endpoint
            endpoint = '/WarehouseOrderSet'
            # create IDs
            ids = None
            # create navigation
            nav = None

        # HTTP OData GET request
        http_resp = self._odata.http_get(
            endpoint, urlparams=params, ids=ids, navigation=nav)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def get_robot_warehouseorders(self, lgnum: str, rsrc: str) -> List[WarehouseOrder]:
        """Get warehouse orders assigned to the robot resource."""
        # define endpoint
        endpoint = '/GetRobotWarehouseOrders'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum), 'Rsrc': "'{}'".format(rsrc)}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, urlparams=params)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def getnew_robot_warehouseorder(self, lgnum: str, rsrc: str) -> WarehouseOrder:
        """
        Get a new warehouse order for a robot resource.

        The warehouse order will be immediately assigned to the robot
        resource in EWM.
        """
        # define endpoint
        endpoint = '/GetNewRobotWarehouseOrder'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum), 'Rsrc': "'{}'".format(rsrc)}

        # HTTP OData GET request
        http_resp = self._odata.http_patch_post('post', endpoint,
                                                urlparams=params)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def getnew_rtype_warehouseorders(
            self, lgnum: str, rsrcgrp: str, rsrctype: str, nowho: int) -> List[WarehouseOrder]:
        """
        Get #nowho new warehouse orders for a robot type.

        The warehouse order is marked as 'in process', but not assigned to a
        robot resource yet. This needs to be done by calling the method:
        assign_robot_warehouseorder.
        """
        # define endpoint
        endpoint = '/GetNewRobotTypeWarehouseOrders'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum),
                  'RsrcGrp': "'{}'".format(rsrcgrp),
                  'RsrcType': "'{}'".format(rsrctype),
                  'NoWho': int(nowho)}

        # HTTP OData GET request
        http_resp = self._odata.http_patch_post('post', endpoint, urlparams=params)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def assign_robot_warehouseorder(self, lgnum: str, rsrc: str, who: str) -> WarehouseOrder:
        """Assign a robot resource to a warehouse order."""
        # define endpoint
        endpoint = '/AssignRobotToWarehouseOrder'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum), 'Rsrc': "'{}'".format(rsrc),
                  'Who': "'{}'".format(who)}

        # HTTP OData GET request
        http_resp = self._odata.http_patch_post('post', endpoint, urlparams=params)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def get_openwarehousetask(self, lgnum: str, tanum: str) -> WarehouseTask:
        """Get data from one warehouse task."""
        # define endpoint
        endpoint = '/OpenWarehouseTaskSet'

        # create IDs
        ids = {'Lgnum': lgnum, 'Tanum': tanum}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def get_openwarehousetasks(
            self, lgnum: Optional[str] = None, who: Optional[str] = None) -> List[WarehouseTask]:
        """
        Get data from all open warehouse tasks.

        Optionally filter by warehouse and warehouse order.
        """
        # Define endpoint IDs and navigation based on parameter selection
        if lgnum and who:
            # define endpoint
            endpoint = '/WarehouseOrderSet'
            # create IDs
            ids = {'Lgnum': lgnum, 'Who': who}
            # create navigation
            nav = '/OpenWarehouseTasks'
        elif lgnum or who:
            raise AttributeError(
                'Either filter "lgnum" AND "who" or none of them ')
        else:
            # define endpoint
            endpoint = '/OpenWarehouseTaskSet'
            # create IDs
            ids = None
            # create navigation
            nav = None

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids, navigation=nav)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def confirm_warehousetask(
            self, lgnum: str, tanum: str, rsrc: str) -> WarehouseTaskConfirmation:
        """
        Confirm a warehouse task - putaway.

        TODO: Implement exceptions: partly confirmations, bin change etc.
        """
        # define endpoint
        endpoint = '/ConfirmWarehouseTask'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum), 'Tanum': "'{}'".format(tanum),
                  'Rsrc': "'{}'".format(rsrc)}

        # HTTP OData POST request
        http_resp = self._odata.http_patch_post('post', endpoint, urlparams=params)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def confirm_warehousetask_firststep(
            self, lgnum: str, tanum: str, rsrc: str) -> WarehouseTaskConfirmation:
        """
        Confirm a warehouse task - first step.

        First confirmation of a warehouse task.
        This also assigns the warehouse task to the resource.
        """
        # define endpoint
        endpoint = '/ConfirmWarehouseTaskFirstStep'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum), 'Tanum': "'{}'".format(tanum),
                  'Rsrc': "'{}'".format(rsrc)}

        # HTTP OData POST request
        http_resp = self._odata.http_patch_post('post', endpoint, urlparams=params)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint,
                    result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def send_confirmation_error(
            self, lgnum: str, rsrc: str, who: str, tanum: str, confnumber: str) -> WarehouseOrder:
        """Send error before confirmation of a warehouse task."""
        # define endpoint
        if confnumber == ConfirmWarehouseTask.FIRST_CONF:
            endpoint = '/SendFirstConfirmationError'
        elif confnumber == ConfirmWarehouseTask.SECOND_CONF:
            endpoint = '/SendSecondConfirmationError'
        else:
            raise ValueError('Could be used only for FIRST and SECOND confirmation')

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum), 'Rsrc': "'{}'".format(rsrc),
                  'Who': "'{}'".format(who), 'Tanum': "'{}'".format(tanum)}

        # HTTP OData GET request
        http_resp = self._odata.http_patch_post('post', endpoint, urlparams=params)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def unassign_robot_warehouseorder(self, lgnum: str, rsrc: str, who: str) -> WarehouseOrder:
        """Unassign a robot resource from a warehouse order."""
        # define endpoint
        endpoint = '/UnassignRobotFromWarehouseorder'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum), 'Rsrc': "'{}'".format(rsrc),
                  'Who': "'{}'".format(who)}

        # HTTP OData GET request
        http_resp = self._odata.http_patch_post('post', endpoint, urlparams=params)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)


class RobotOData:
    """Interaction with EWM warehouse robot APIs."""

    def __init__(self, odata: ODataHandler) -> None:
        """Constructor."""
        self._odata = odata

    def get_robot(self, lgnum: str, rsrc: str) -> Robot:
        """Get data from one robot."""
        # define endpoint
        endpoint = '/RobotSet'

        # create IDs
        ids = {'Lgnum': lgnum, 'Rsrc': rsrc}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint,
                    result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def get_robots(self, lgnum: Optional[str] = None) -> List[Robot]:
        """
        Get data from all open warehouse tasks.

        Optionally filter by warehouse.
        """
        # Define endpoint IDs and navigation based on parameter selection
        if lgnum:
            # define endpoint
            endpoint = '/WarehouseNumberSet'
            # create IDs
            ids = {'Lgnum': lgnum}
            # create navigation
            nav = '/Robots'
        else:
            # define endpoint
            endpoint = '/RobotSet'
            # create IDs
            ids = None
            # create navigation
            nav = None

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids, navigation=nav)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def create_robot(self, lgnum: str, rsrc: str, rsrctype: str, rsrcgrp: str) -> Robot:
        """Create a new robot resource in EWM."""
        # define endpoint
        endpoint = '/RobotSet'

        # create body
        jsonbody = {'Lgnum': lgnum, 'Rsrc': rsrc, 'RsrcType': rsrctype, 'RsrcGrp': rsrcgrp}

        # HTTP OData POST request
        http_resp = self._odata.http_patch_post('post', endpoint, jsonbody=jsonbody)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def change_robot(
            self, lgnum: str, rsrc: str, rsrctype: Optional[str] = None,
            rsrcgrp: Optional[str] = None) -> bool:
        """Change an existing robot resource in EWM."""
        # define endpoint
        endpoint = '/RobotSet'

        # create IDs
        ids = {'Lgnum': lgnum, 'Rsrc': rsrc}

        # create body
        jsonbody = {}
        if rsrctype is not None:
            jsonbody['RsrcType'] = rsrctype
        if rsrcgrp is not None:
            jsonbody['RsrcGrp'] = rsrcgrp

        # HTTP OData PATCH request
        http_resp = self._odata.http_patch_post('patch', endpoint, ids=ids, jsonbody=jsonbody)

        # No HTTP body on successfull PATCH requests
        # Body only exists in case of exceptions

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return True
        else:
            http_respjson = http_resp.json()
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)

    def set_robot_status(self, lgnum: str, rsrc: str, exccode: str) -> Robot:
        """Set exception codes for robot resources in EWM."""
        # define endpoint
        endpoint = '/SetRobotStatus'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum), 'Rsrc': "'{}'".format(rsrc),
                  'Exccode': "'{}'".format(exccode)}

        # HTTP OData POST request
        http_resp = self._odata.http_patch_post('post', endpoint, urlparams=params)

        http_respjson = http_resp.json()

        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            return odata_to_attr(http_respjson)
        else:
            # Get error code from HTTP response
            try:
                error_code = http_respjson['error']['code']
            except KeyError:
                error_code = None
            # Error handling for business exceptions raised in EWM backend
            if http_resp.status_code in HTTP_BUS_EXCEPTION:
                exception_class = get_exception_class(error_code)
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
                raise exception_class()
            # For any other error use generic exception
            else:
                self._odata.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=error_code).inc()
                raise ODataAPIException(error_code=error_code)
