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
from typing import Any, Dict, List, Optional
from requests import Response

from robcoewmtypes.warehouse import Warehouse, WarehouseDescription, StorageBin
from robcoewmtypes.warehouseorder import (
    WarehouseOrder, WarehouseTask, WarehouseTaskConfirmation, ConfirmWarehouseTask)
from robcoewmtypes.robot import (
    Robot, RobotResourceType, ResourceGroup, ResourceTypeDescription, ResourceGroupDescription)

from .conversion import odata_to_attr
from .exceptions import ODataAPIException, get_exception_class
from .odata import ODataHandler

_LOGGER = logging.getLogger(__name__)

HTTP_SUCCESS = [200, 201, 202, 203, 204, 205, 206, 207, 208, 226]
HTTP_BUS_EXCEPTION = [404, 500]

STATE_SUCCEEDED = 'SUCCEEDED'


class EWMOdata:
    """Base class for EWM OData interface."""

    def __init__(self, odata: ODataHandler) -> None:
        """Construct."""
        self._odata = odata

    def handle_http_response(self, endpoint: str, http_resp: Response) -> Any:
        """
        Handle an OData HTTP request response.

        Returns attrs data class in case of success and raises exception on error.
        For PATCH requests the body of an OData request is empty on success. Returning True then.
        """
        # Return code handling
        if http_resp.status_code in HTTP_SUCCESS:
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=STATE_SUCCEEDED).inc()
            if http_resp.text:
                return odata_to_attr(http_resp.json())
            else:
                return True

        # Determine error code
        if http_resp.status_code == 403:
            error_code = '403'
        else:
            # Get error code from HTTP response
            try:
                error_code = http_resp.json()['error']['code']
            except KeyError:
                error_code = ''

        if http_resp.status_code == 404 and not error_code:
            error_code = '404'

        # Error handling for business exceptions raised in EWM backend
        if http_resp.status_code in HTTP_BUS_EXCEPTION:
            exception_class = get_exception_class(error_code)
            self._odata.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=exception_class.ERROR_CODE).inc()
            raise exception_class()

        # For any other error use generic exception
        self._odata.odata_counter.labels(  # pylint: disable=no-member
            endpoint=endpoint, result=error_code).inc()
        raise ODataAPIException(error_code=error_code)


class WarehouseOData(EWMOdata):
    """Interaction with EWM warehouse APIs."""

    def get_warehouse(
            self, lgnum: str, descriptions: bool = False, storagebins: bool = False) -> Warehouse:
        """
        Get data of one warehouse.

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

        return self.handle_http_response(endpoint, http_resp)

    def get_warehouses(self, descriptions: bool = False,
                       storagebins: bool = False) -> Optional[List[Warehouse]]:
        """
        Get data of all warehouses.

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

        return self.handle_http_response(endpoint, http_resp)

    def get_whdescription(self, lgnum: str, spras: str) -> WarehouseDescription:
        """Get description of one warehouse in a language."""
        # define endpoint
        endpoint = '/WarehouseDescriptionSet'

        # create IDs
        ids = {'Lgnum': lgnum, 'Spras': spras}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids)

        return self.handle_http_response(endpoint, http_resp)

    def get_whdescriptions(self, lgnum: Optional[str] = None) -> List[WarehouseDescription]:
        """
        Get descriptions of warehouses in all languages.

        Optionally filter by warehouse.
        """
        ids: Optional[Dict]
        nav: Optional[str]

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

        return self.handle_http_response(endpoint, http_resp)

    def get_storagebin(self, lgnum: str, lgpla: str) -> StorageBin:
        """Get one specific storage bin."""
        # define endpoint
        endpoint = '/StorageBinSet'

        # create IDs
        ids = {'Lgnum': lgnum, 'Lgpla': lgpla}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids)

        return self.handle_http_response(endpoint, http_resp)

    def get_storagebins(self, lgnum: Optional[str] = None) -> List[WarehouseDescription]:
        """
        Get all storage bins from the system.

        Optionally filter by warehouse.
        """
        ids: Optional[Dict]
        nav: Optional[str]

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

        return self.handle_http_response(endpoint, http_resp)


class WarehouseOrderOData(EWMOdata):
    """Interaction with EWM warehouse order APIs."""

    def get_warehouseorder(
            self, lgnum: str, who: str, openwarehousetasks: bool = False) -> WarehouseOrder:
        """
        Get data of one warehouse order.

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

        return self.handle_http_response(endpoint, http_resp)

    def get_warehouseorders(
            self, lgnum: Optional[str] = None, topwhoid: Optional[str] = None,
            openwarehousetasks: bool = False) -> List[WarehouseOrder]:
        """
        Get data of all warehouse orders.

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

        return self.handle_http_response(endpoint, http_resp)

    def get_robot_warehouseorders(self, lgnum: str, rsrc: str) -> List[WarehouseOrder]:
        """Get warehouse orders assigned to the robot resource."""
        # define endpoint
        endpoint = '/GetRobotWarehouseOrders'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum), 'Rsrc': "'{}'".format(rsrc)}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, urlparams=params)

        return self.handle_http_response(endpoint, http_resp)

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

        return self.handle_http_response(endpoint, http_resp)

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

        return self.handle_http_response(endpoint, http_resp)

    def get_in_process_warehouseorders(
            self, lgnum: str, rsrcgrp: str, rsrctype: str) -> List[WarehouseOrder]:
        """Get warehouse orders in process but not assigned to a robot resource."""
        # define endpoint
        endpoint = '/GetInProcessWarehouseOrders'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum),
                  'RsrcGrp': "'{}'".format(rsrcgrp),
                  'RsrcType': "'{}'".format(rsrctype)}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, urlparams=params)

        return self.handle_http_response(endpoint, http_resp)

    def assign_robot_warehouseorder(self, lgnum: str, rsrc: str, who: str) -> WarehouseOrder:
        """Assign a robot resource to a warehouse order."""
        # define endpoint
        endpoint = '/AssignRobotToWarehouseOrder'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum), 'Rsrc': "'{}'".format(rsrc),
                  'Who': "'{}'".format(who)}

        # HTTP OData GET request
        http_resp = self._odata.http_patch_post('post', endpoint, urlparams=params)

        return self.handle_http_response(endpoint, http_resp)

    def get_openwarehousetask(self, lgnum: str, tanum: str) -> WarehouseTask:
        """Get data from one warehouse task."""
        # define endpoint
        endpoint = '/OpenWarehouseTaskSet'

        # create IDs
        ids = {'Lgnum': lgnum, 'Tanum': tanum}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids)

        return self.handle_http_response(endpoint, http_resp)

    def get_openwarehousetasks(
            self, lgnum: Optional[str] = None, who: Optional[str] = None) -> List[WarehouseTask]:
        """
        Get data of all open warehouse tasks.

        Optionally filter by warehouse and warehouse order.
        """
        # Define endpoint IDs and navigation based on parameter selection
        ids: Optional[Dict]
        nav: Optional[str]

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

        return self.handle_http_response(endpoint, http_resp)

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

        return self.handle_http_response(endpoint, http_resp)

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

        return self.handle_http_response(endpoint, http_resp)

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

        return self.handle_http_response(endpoint, http_resp)

    def unassign_robot_warehouseorder(self, lgnum: str, rsrc: str, who: str) -> WarehouseOrder:
        """Unassign a robot resource from a warehouse order."""
        # define endpoint
        endpoint = '/UnassignRobotFromWarehouseOrder'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum), 'Rsrc': "'{}'".format(rsrc),
                  'Who': "'{}'".format(who)}

        # HTTP OData GET request
        http_resp = self._odata.http_patch_post('post', endpoint, urlparams=params)

        return self.handle_http_response(endpoint, http_resp)

    def unset_warehouseorder_in_process(self, lgnum: str, who: str) -> WarehouseOrder:
        """Unset in process status of a warehouse order."""
        # define endpoint
        endpoint = '/UnsetWarehouseorderInProcessStatus'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum), 'Who': "'{}'".format(who)}

        # HTTP OData GET request
        http_resp = self._odata.http_patch_post('post', endpoint, urlparams=params)

        return self.handle_http_response(endpoint, http_resp)


class RobotOData(EWMOdata):
    """Interaction with EWM warehouse robot APIs."""

    def get_robot(self, lgnum: str, rsrc: str) -> Robot:
        """Get data of one robot."""
        # define endpoint
        endpoint = '/RobotSet'

        # create IDs
        ids = {'Lgnum': lgnum, 'Rsrc': rsrc}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids)

        return self.handle_http_response(endpoint, http_resp)

    def get_robots(self, lgnum: Optional[str] = None) -> List[Robot]:
        """
        Get data of all robots.

        Optionally filter by warehouse.
        """
        # Define endpoint IDs and navigation based on parameter selection
        ids: Optional[Dict]
        nav: Optional[str]

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

        return self.handle_http_response(endpoint, http_resp)

    def create_robot(self, lgnum: str, rsrc: str, rsrctype: str, rsrcgrp: str) -> Robot:
        """Create a new robot resource in EWM."""
        # define endpoint
        endpoint = '/RobotSet'

        # create body
        jsonbody = {'Lgnum': lgnum, 'Rsrc': rsrc, 'RsrcType': rsrctype, 'RsrcGrp': rsrcgrp}

        # HTTP OData POST request
        http_resp = self._odata.http_patch_post('post', endpoint, jsonbody=jsonbody)

        return self.handle_http_response(endpoint, http_resp)

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

        return self.handle_http_response(endpoint, http_resp)

    def set_robot_status(self, lgnum: str, rsrc: str, exccode: str) -> Robot:
        """Set exception codes for robot resources in EWM."""
        # define endpoint
        endpoint = '/SetRobotStatus'

        # create URL parameter
        params = {'Lgnum': "'{}'".format(lgnum), 'Rsrc': "'{}'".format(rsrc),
                  'Exccode': "'{}'".format(exccode)}

        # HTTP OData POST request
        http_resp = self._odata.http_patch_post('post', endpoint, urlparams=params)

        return self.handle_http_response(endpoint, http_resp)

    def get_robot_resource_type(self, lgnum: str, rsrctype: str) -> RobotResourceType:
        """Get data of one robot resource type."""
        # define endpoint
        endpoint = '/RobotResourceTypeSet'

        # create IDs
        ids = {'Lgnum': lgnum, 'RsrcType': rsrctype}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids)

        return self.handle_http_response(endpoint, http_resp)

    def get_robot_resource_types(self, lgnum: Optional[str] = None) -> List[RobotResourceType]:
        """
        Get data of all robot resource types.

        Optionally filter by warehouse.
        """
        # Define endpoint IDs and navigation based on parameter selection
        ids: Optional[Dict]
        nav: Optional[str]

        if lgnum:
            # define endpoint
            endpoint = '/WarehouseNumberSet'
            # create IDs
            ids = {'Lgnum': lgnum}
            # create navigation
            nav = '/RobotResourceTypes'
        else:
            # define endpoint
            endpoint = '/RobotResourceTypeSet'
            # create IDs
            ids = None
            # create navigation
            nav = None

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids, navigation=nav)

        return self.handle_http_response(endpoint, http_resp)

    def get_resource_type_description(
            self, lgnum: str, rsrctype: str, langu: str) -> ResourceTypeDescription:
        """Get description of one resource type in a language."""
        # define endpoint
        endpoint = '/ResourceTypeDescriptionSet'

        # create IDs
        ids = {'Lgnum': lgnum, 'RsrcType': rsrctype, 'Langu': langu}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids)

        return self.handle_http_response(endpoint, http_resp)

    def get_resource_type_descriptions(
            self, lgnum: Optional[str] = None,
            rsrctype: Optional[str] = None) -> List[ResourceTypeDescription]:
        """
        Get descriptions of resource types in all languages.

        Optionally filter by warehouse and resource type.
        """
        ids: Optional[Dict]
        nav: Optional[str]

        if lgnum or rsrctype:
            # define endpoint
            endpoint = '/RobotResourceTypeSet'
            # create IDs
            ids = {'Lgnum': lgnum, 'RsrcType': rsrctype}
            # create navigation
            nav = '/ResourceTypeDescriptions'
        else:
            # define endpoint
            endpoint = '/ResourceTypeDescriptionSet'
            # create IDs
            ids = None
            # create navigation
            nav = None

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids, navigation=nav)

        return self.handle_http_response(endpoint, http_resp)

    def get_resource_group(self, lgnum: str, rsrcgrp: str) -> ResourceGroup:
        """Get data of one robot resource group."""
        # define endpoint
        endpoint = '/ResourceGroupSet'

        # create IDs
        ids = {'Lgnum': lgnum, 'RsrcGrp': rsrcgrp}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids)

        return self.handle_http_response(endpoint, http_resp)

    def get_resource_groups(self, lgnum: Optional[str] = None) -> List[ResourceGroup]:
        """
        Get data of all resource groups.

        Optionally filter by warehouse.
        """
        # Define endpoint IDs and navigation based on parameter selection
        ids: Optional[Dict]
        nav: Optional[str]

        if lgnum:
            # define endpoint
            endpoint = '/WarehouseNumberSet'
            # create IDs
            ids = {'Lgnum': lgnum}
            # create navigation
            nav = '/ResourceGroups'
        else:
            # define endpoint
            endpoint = '/ResourceGroupSet'
            # create IDs
            ids = None
            # create navigation
            nav = None

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids, navigation=nav)

        return self.handle_http_response(endpoint, http_resp)

    def get_resource_group_description(
            self, lgnum: str, rsrcgrp: str, langu: str) -> ResourceGroupDescription:
        """Get description of one resource group in a language."""
        # define endpoint
        endpoint = '/ResourceGroupDescriptionSet'

        # create IDs
        ids = {'Lgnum': lgnum, 'RsrcGrp': rsrcgrp, 'Langu': langu}

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids)

        return self.handle_http_response(endpoint, http_resp)

    def get_resource_group_descriptions(
            self, lgnum: Optional[str] = None,
            rsrcgrp: Optional[str] = None) -> List[ResourceGroupDescription]:
        """
        Get descriptions of resource groups in all languages.

        Optionally filter by warehouse and resource group.
        """
        ids: Optional[Dict]
        nav: Optional[str]

        if lgnum or rsrcgrp:
            # define endpoint
            endpoint = '/ResourceGroupSet'
            # create IDs
            ids = {'Lgnum': lgnum, 'RsrcGrp': rsrcgrp}
            # create navigation
            nav = '/ResourceGroupDescriptions'
        else:
            # define endpoint
            endpoint = '/ResourceGroupDescriptionSet'
            # create IDs
            ids = None
            # create navigation
            nav = None

        # HTTP OData GET request
        http_resp = self._odata.http_get(endpoint, ids=ids, navigation=nav)

        return self.handle_http_response(endpoint, http_resp)
