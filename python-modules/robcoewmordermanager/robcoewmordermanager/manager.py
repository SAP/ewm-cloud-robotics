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

"""Order mananger for robcoewmordermanager."""

import os
import logging

from typing import Dict, Tuple, List, Union

import attr
from cattr import structure, unstructure

from prometheus_client import Counter

from robcoewmtypes.helper import get_robcoewmtype, create_robcoewmtype_str
from robcoewmtypes.robot import RequestFromRobot, RequestFromRobotStatus
from robcoewmtypes.warehouseorder import (
    ConfirmWarehouseTask, WarehouseOrder, WarehouseOrderCRDSpec)

from robcoewminterface.types import ODataConfig
from robcoewminterface.odata import ODataHandler
from robcoewminterface.ewm import WarehouseOData, WarehouseOrderOData
from robcoewminterface.exceptions import (
    ODataAPIException, NoOrderFoundError, RobotHasOrderError, WarehouseTaskAlreadyConfirmedError,
    NotFoundError)

from .helper import ProcessedMessageMemory, RobotIdentifier, WhoIdentifier
from .ordercontroller import OrderController
from .robotrequestcontroller import RobotRequestController

_LOGGER = logging.getLogger(__name__)

STATE_SUCCEEDED = 'SUCCEEDED'
STATE_FAILED = 'FAILED'

ROBOTREQUEST_TYPE = create_robcoewmtype_str(RequestFromRobot('lgnum', 'rsrc'))
WAREHOUSETASKCONF_TYPE = create_robcoewmtype_str([ConfirmWarehouseTask(
    'lgnum', 'who', ConfirmWarehouseTask.FIRST_CONF, ConfirmWarehouseTask.CONF_SUCCESS)])


class EWMOrderManager:
    """Main order manager class for EWM."""

    ROBOTREQUEST_MSG_TYPES = (RequestFromRobot, )
    CONFIRMATION_MSG_TYPES = (ConfirmWarehouseTask, )

    # Prometheus logging
    who_counter = Counter(
        'sap_ewm_warehouse_orders', 'Completed EWM Warehouse orders', ['robot', 'result'])

    def __init__(self, oc: OrderController, rc: RobotRequestController) -> None:
        """Construct."""
        self.init_odata_fromenv()

        # Memory of processed messages for order manager
        self.msg_mem = ProcessedMessageMemory()

        # SAP EWM OData handler
        self.odatahandler = ODataHandler(self.odataconfig)
        # SAP EWM OData APIs
        self.ewmwarehouse = WarehouseOData(self.odatahandler)
        self.ewmwho = WarehouseOrderOData(self.odatahandler)

        # K8s Custom Resource Controller
        self.ordercontroller = oc
        self.robotrequestcontroller = rc

        # Register callback functions
        # Warehouse order status callback
        self.ordercontroller.register_callback(
            'KubernetesWhoCR', ['MODIFIED', 'REPROCESS'], self.process_who_cr_cb)
        # Robot request controller
        self.robotrequestcontroller.register_callback(
            'RobotRequest', ['ADDED', 'MODIFIED', 'REPROCESS'], self.robotrequest_callback)

    def init_odata_fromenv(self) -> None:
        """Initialize OData interface from environment variables."""
        # Read environment variables
        envvar = {}
        envvar['EWM_HOST'] = os.environ.get('EWM_HOST')
        envvar['EWM_BASEPATH'] = os.environ.get('EWM_BASEPATH')
        envvar['EWM_AUTH'] = os.environ.get('EWM_AUTH')
        if envvar['EWM_AUTH'] == ODataConfig.AUTH_BASIC:
            envvar['EWM_USER'] = os.environ.get('EWM_USER')
            envvar['EWM_PASSWORD'] = os.environ.get('EWM_PASSWORD')
        else:
            envvar['EWM_CLIENTID'] = os.environ.get('EWM_CLIENTID')
            envvar['EWM_CLIENTSECRET'] = os.environ.get('EWM_CLIENTSECRET')
            envvar['EWM_TOKENENDPOINT'] = os.environ.get('EWM_TOKENENDPOINT')

        # Check if complete
        for var, val in envvar.items():
            if val is None:
                raise ValueError(
                    'Environment variable "{}" is not set'.format(var))

        if envvar['EWM_AUTH'] == ODataConfig.AUTH_BASIC:
            self.odataconfig = ODataConfig(
                host=envvar['EWM_HOST'],
                basepath=envvar['EWM_BASEPATH'],
                authorization=envvar['EWM_AUTH'],
                user=envvar['EWM_USER'],
                password=envvar['EWM_PASSWORD'],
                )
        else:
            self.odataconfig = ODataConfig(
                host=envvar['EWM_HOST'],
                basepath=envvar['EWM_BASEPATH'],
                authorization=envvar['EWM_AUTH'],
                clientid=envvar['EWM_CLIENTID'],
                clientsecret=envvar['EWM_CLIENTSECRET'],
                tokenendpoint=envvar['EWM_TOKENENDPOINT'],
                )

        _LOGGER.info('Connecting to OData host "%s"', self.odataconfig.host)

    def _structure_callback_data(
            self, dtype: str, data: Union[Dict, List], valid_types: Tuple) -> List:
        """Return structured attr data classes for robcoewm data types."""
        # Get robco ewm data classes
        try:
            robcoewmtype = get_robcoewmtype(dtype)
        except TypeError as err:
            _LOGGER.error(
                'Message type "%s" is invalid - %s - message SKIPPED: %s',
                dtype, err, data)
            return []
        # Convert message data to robcoewmtypes data classes
        robocoewmdata = structure(data, robcoewmtype)

        # if data set is not a list yet, convert it for later processing
        if not isinstance(robocoewmdata, list):
            robocoewmdata = [robocoewmdata]

        # Check if datasets have a supported type before starting to process
        valid_robcoewmdata = []
        for dataset in robocoewmdata:
            if isinstance(dataset, valid_types):
                valid_robcoewmdata.append(dataset)
            else:
                _LOGGER.error(
                    'Dataset includes an unsupported type: "%s". Dataset '
                    'SKIPPED: %s', type(dataset), dataset)

        return valid_robcoewmdata

    def robotrequest_callback(self, name: str, custom_res: Dict) -> None:
        """
        Handle exceptions of robotrequest CR processing.

        Used for K8S CR handler.
        """
        try:
            self.process_robotrequest_cr(name, custom_res)
        except NoOrderFoundError:
            _LOGGER.debug(
                'No warehouse order was found for robot "%s" - try again later', name)
        except RobotHasOrderError:
            _LOGGER.debug(
                'Warehouse order still assigned to robot "%s" - try again later', name)

    def process_robotrequest_cr(self, name: str, custom_res: Dict) -> None:
        """
        Process a robotrequest custom resource.

        Used for K8S CR handler.
        """
        cls = self.__class__

        if custom_res.get('status', {}).get('status') == RequestFromRobotStatus.STATE_PROCESSED:
            return

        # Structure the request data
        robcoewmdata = self._structure_callback_data(
            ROBOTREQUEST_TYPE, custom_res['spec'], cls.ROBOTREQUEST_MSG_TYPES)
        if not robcoewmdata:
            return
        # Get statusdata if available
        if custom_res.get('status', {}).get('data'):
            robcoewmstatusdata = self._structure_callback_data(
                ROBOTREQUEST_TYPE, custom_res['status']['data'], cls.ROBOTREQUEST_MSG_TYPES)
        else:
            robcoewmstatusdata = [RequestFromRobot(robcoewmdata[0].lgnum, robcoewmdata[0].rsrc), ]

        if len(robcoewmdata) > 1 or len(robcoewmstatusdata) > 1:
            raise ValueError('Robot request must include only one dataset')

        # Process the dataset
        request = robcoewmdata[0]
        status = robcoewmstatusdata[0]

        # Return if request was already processed
        if self.msg_mem.check_robotrequest_processed(name, status):
            _LOGGER.info('Robot request "%s" already processed before - skip', name)
            return

        robotident = RobotIdentifier(request.lgnum, request.rsrc)
        # Determine if it is the first request
        self.msg_mem.request_count[name] += 1
        firstrequest = bool(self.msg_mem.request_count[name] == 1)
        # Request work, when robot is asking
        if request.requestnewwho and not status.requestnewwho:
            # Get a new warehouse order for the robot
            success = self.get_and_send_robot_whos(
                robotident, firstrequest=firstrequest, newwho=True, onlynewwho=True)
            if success:
                status.requestnewwho = True
                status.requestwork = request.requestwork
        elif request.requestwork and not status.requestwork:
            # Get existing warehouse orders for the robot. If no exists, get a new warehouse order
            success = self.get_and_send_robot_whos(
                robotident, firstrequest=firstrequest, newwho=True, onlynewwho=False)
            if success:
                status.requestwork = True

        # Check if warehouse order was completed
        if request.notifywhocompletion and not status.notifywhocompletion:
            notfound = False
            try:
                who = self.ewmwho.get_warehouseorder(
                    lgnum=robotident.lgnum, who=request.notifywhocompletion)
            except NotFoundError:
                notfound = True
            else:
                if who.status not in ['D', '']:
                    notfound = True
            if notfound:
                status.notifywhocompletion = request.notifywhocompletion
                _LOGGER.info(
                    'Warehouse order %s was confirmed, notifying robot "%s"',
                    request.notifywhocompletion, robotident.rsrc)
                # Warehouse orders are completed in EWM, thus ensure that they are marked PROCESSED
                self.cleanup_who(WhoIdentifier(robotident.lgnum, request.notifywhocompletion))

        # Check if warehouse task was completed
        if request.notifywhtcompletion and not status.notifywhtcompletion:
            try:
                self.ewmwho.get_openwarehousetask(robotident.lgnum, request.notifywhtcompletion)
            except NotFoundError:
                status.notifywhtcompletion = request.notifywhtcompletion
                _LOGGER.info(
                    'Warehouse task %s was confirmed, notifying robot "%s"',
                    request.notifywhtcompletion, robotident.rsrc)

        # Raise exception if request was not complete
        if request == status:
            self.robotrequestcontroller.update_status(
                name, create_robcoewmtype_str(status), unstructure(status),
                process_complete=True)
            self.msg_mem.memorize_robotrequest(name, status)
            self.msg_mem.delete_robotrequest_from_memory(name, status)
        else:
            self.robotrequestcontroller.update_status(
                name, create_robcoewmtype_str(status), unstructure(status),
                process_complete=False)
            self.msg_mem.memorize_robotrequest(name, status)
            if request.notifywhocompletion:
                raise RobotHasOrderError
            else:
                raise NoOrderFoundError

    def confirm_warehousetask(self, whtask: ConfirmWarehouseTask) -> None:
        """Confirm the warehouse task in SAP EWM using OData service."""
        # Get warehouse order from EWM
        who = self.ewmwho.get_warehouseorder(
            whtask.lgnum, whtask.who, openwarehousetasks=True)
        # Check if warehouse task is still open
        whtopen = False
        for i, openwht in enumerate(who.warehousetasks):
            if whtask.lgnum == openwht.lgnum and whtask.tanum == openwht.tanum:
                whtopen = True
                wht_listno = i

        if whtopen is True:
            # Remove entry from warehouse order to check in the end if there are not more open
            # warehouse tasks left
            who.warehousetasks.pop(wht_listno)
        else:
            _LOGGER.warning(
                'Warehouse task "%s" of warehouse order "%s" was already '
                'confirmed - skip this confirmation', whtask.tanum, whtask.who)
            return

        # SUCCESS Messages
        if whtask.confirmationtype == ConfirmWarehouseTask.CONF_SUCCESS:
            # Perform first confirmation
            if whtask.confirmationnumber == ConfirmWarehouseTask.FIRST_CONF:
                try:
                    self.ewmwho.confirm_warehousetask_firststep(
                        whtask.lgnum, whtask.tanum, whtask.rsrc)
                except (TimeoutError, ConnectionError) as err:
                    # If not successfull. Raise to put message back in queue
                    _LOGGER.error(
                        'Connection error during first confirmation of warehouse task: %s', err)
                    raise
                except IOError as err:
                    _LOGGER.error(
                        'IOError error "%s" during first confirmation of warehouse task: %s', err,
                        attr.asdict(whtask))
                    raise
                except WarehouseTaskAlreadyConfirmedError:
                    _LOGGER.warning(
                        'Warehouse task %s has first confirmation already', attr.asdict(whtask))
                except ODataAPIException as err:
                    _LOGGER.error(
                        'Business error "%s" in SAP EWM backend during first confirmation of '
                        'warehouse task: %s', err, attr.asdict(whtask))
                    raise
                else:
                    _LOGGER.info(
                        'Warehouse task Lgnum "%s", Tanum "%s" of warehouse order "%s" got '
                        'successfull first confirmation by robot "%s"', whtask.lgnum, whtask.tanum,
                        whtask.who, whtask.rsrc)
            # Perform second confirmation
            elif whtask.confirmationnumber == ConfirmWarehouseTask.SECOND_CONF:
                try:
                    self.ewmwho.confirm_warehousetask(whtask.lgnum, whtask.tanum, whtask.rsrc)
                except (TimeoutError, ConnectionError) as err:
                    # If not successfull. Raise to put message back in queue
                    _LOGGER.error(
                        'Connection error during second confirmation of warehouse task: %s', err)
                    raise
                except IOError as err:
                    _LOGGER.error(
                        'IOError error "%s" during second confirmation of warehouse task: %s', err,
                        attr.asdict(whtask))
                    raise
                except WarehouseTaskAlreadyConfirmedError:
                    _LOGGER.warning(
                        'Warehouse task %s has first confirmation already', attr.asdict(whtask))
                except ODataAPIException as err:
                    _LOGGER.error(
                        'Business error "%s" in SAP EWM backend during second confirmation of '
                        'warehouse task: %s', err, attr.asdict(whtask))
                    raise

                _LOGGER.info(
                    'Warehouse task Lgnum "%s", Tanum "%s" of warehouse order "%s" got successfull'
                    ' second confirmation by robot "%s"', whtask.lgnum, whtask.tanum, whtask.who,
                    whtask.rsrc)
                self.who_counter.labels(  # pylint: disable=no-member
                    robot=whtask.rsrc.lower(), result=STATE_SUCCEEDED).inc()

                # Cleanup warehouse order if there are no warehouse tasks
                if not who.warehousetasks:
                    self.cleanup_who(WhoIdentifier(whtask.lgnum, whtask.who))

        # ERROR Messages
        elif whtask.confirmationtype == ConfirmWarehouseTask.CONF_ERROR:
            # Send an error to SAP EWM if an error occured on the robot before a confirmation
            try:
                self.ewmwho.send_confirmation_error(
                    whtask.lgnum, whtask.rsrc, whtask.who, whtask.tanum, whtask.confirmationnumber)
            except (TimeoutError, ConnectionError) as err:
                # If not successfull. Raise to put message back in queue
                _LOGGER.error(
                    'Connection error while sending %s confirmation error of warehouse task: %s',
                    whtask.confirmationnumber, err)
                raise
            except IOError as err:
                _LOGGER.error(
                    'IOError error "%s" while sending %s confirmation error of warehouse task: %s',
                    err, whtask.confirmationnumber, attr.asdict(whtask))
                raise
            except ODataAPIException as err:
                _LOGGER.error(
                    'Business error "%s" in SAP EWM backend while sending %s confirmation error of'
                    ' warehouse task: %s', err, whtask.confirmationnumber, attr.asdict(whtask))
                raise
            else:
                _LOGGER.info(
                    'Process error on robot "%s" before %s confirmation of Lgnum "%s", Tanum "%s" '
                    'of warehouse order "%s" successfully sent', whtask.rsrc,
                    whtask.confirmationnumber, whtask.lgnum, whtask.tanum, whtask.who)
                self.who_counter.labels(  # pylint: disable=no-member
                    robot=whtask.rsrc.lower(), result=STATE_FAILED).inc()

                # In case of an error on first confirmation processing always clean up because the
                # order is moved to a different queue and not assigned to the robot anymore
                if whtask.confirmationnumber == ConfirmWarehouseTask.FIRST_CONF:
                    self.cleanup_who(WhoIdentifier(whtask.lgnum, whtask.who))

    def get_and_send_robot_whos(
            self, robotident: RobotIdentifier, firstrequest: bool = False, newwho: bool = True,
            onlynewwho: bool = False) -> bool:
        """
        Get warehouse order from SAP EWM and send it to the robot.

        Returns True on success and False on fail.
        """
        whos = self.get_robot_whos(
            robotident, firstrequest=firstrequest, newwho=newwho, onlynewwho=onlynewwho)

        if whos:
            success = self.send_robot_whos(robotident, whos)
        else:
            success = False

        return success

    def get_robot_whos(
            self, robotident: RobotIdentifier, firstrequest: bool = False, newwho: bool = False,
            onlynewwho: bool = False) -> List[WarehouseOrder]:
        """Get warehouse order from SAP EWM."""
        # Init warehouse order list
        whos: List[WarehouseOrder] = []
        # First step - check it there are existing warehouse orders in SAP EWM
        if onlynewwho is False:
            try:
                whos.extend(self.ewmwho.get_robot_warehouseorders(
                    robotident.lgnum, robotident.rsrc))
            except NoOrderFoundError:
                # Create log entry only for the initial query to SAP EWM
                if firstrequest and newwho:
                    _LOGGER.info(
                        'No order assigned to robot "%s" in warehouse "%s" in SAP EWM yet. Try to '
                        'get a new order.', robotident.rsrc, robotident.lgnum)
                elif firstrequest:
                    _LOGGER.info(
                        'No order assigned to robot "%s" in warehouse "%s" in SAP EWM',
                        robotident.rsrc, robotident.lgnum)
            else:
                whos_who = [entry.who for entry in whos]
                _LOGGER.info(
                    'Found warehouse orders "%s" for robot "%s" in warehouse "%s" in SAP EWM',
                    whos_who, robotident.rsrc, robotident.lgnum)

        # Create log entry only for the initial query to SAP EWM
        elif firstrequest:
            _LOGGER.info(
                'Requesting a new order for robot "%s" in warehouse "%s" from SAP EWM.',
                robotident.rsrc, robotident.lgnum)

        # Second step - request a new order from SAP EWM. If no order was found send the request
        # back to robotwork topic
        # Implementation of a straight forward solution, which always gets the first order from
        # SAP EWM warehouse order queue
        if not whos and (newwho or onlynewwho):
            try:
                who = self.ewmwho.getnew_robot_warehouseorder(robotident.lgnum, robotident.rsrc)
            except NoOrderFoundError:
                # Processing of this message finished without success - return
                return whos
            except RobotHasOrderError:
                # There was already a warehouse order assigned to the robot
                _LOGGER.info(
                    'There is already a warehouse order assigned to robot "%s". Enqueue request '
                    'for new warehouse order for the next run.', robotident.rsrc)

                # Processing of this message finished without success - return
                return whos
            else:
                # Get the warehouse order again, because initially flgwho and flgto flags are not
                # set yet
                who = self.ewmwho.get_warehouseorder(who.lgnum, who.who, openwarehousetasks=True)

                whos.append(who)
                _LOGGER.info(
                    'Got new warehouse order "%s" for warehouse "%s" from SAP EWM', who.who,
                    who.lgnum)

        # Third step - if a warehouse order is a top order, get the corresponding sub warehouse
        # orders from SAP EWM
        for who in whos:
            if who.flgwho is True:
                whos.extend(self.ewmwho.get_warehouseorders(who.lgnum, topwhoid=who.who))

        # Forth step - if a warehouse order includes warehouse tasks, but they are not received
        # yet, get those tasks from SAP EWM
        for i, who in enumerate(whos):
            if not who.warehousetasks:
                whos[i] = self.ewmwho.get_warehouseorder(
                    who.lgnum, who.who, openwarehousetasks=True)

        return whos

    def cleanup_who(self, whoident: WhoIdentifier) -> None:
        """Cleanup warehouse order in Cloud Robotics when it is done."""
        try:
            who = self.ewmwho.get_warehouseorder(whoident.lgnum, whoident.who)
        except NotFoundError:
            _LOGGER.warning('Warehouse order %s not found in EWM during CR cleanup', whoident)
            who = WarehouseOrder(lgnum=whoident.lgnum, who=whoident.who)

        self.ordercontroller.cleanup_who(unstructure(who))
        self.msg_mem.delete_who_from_memory(whoident)

    def send_robot_whos(self, robotident: RobotIdentifier, whos: List[WarehouseOrder]) -> bool:
        """
        Send warehouse order from SAP EWM to the robot.

        Returns True on success and False on fail.
        """
        # Send orders to robot
        for who in whos:
            dtype = create_robcoewmtype_str(who)
            self.ordercontroller.send_who_to_robot(robotident, dtype, unstructure(who))

        # Create success log message
        whos_who = [entry.who for entry in whos]
        _LOGGER.info(
            'Warehouse orders "%s" sent to robot "%s" in warehouse "%s"',
            whos_who, robotident.rsrc, robotident.lgnum)

        return True

    def process_who_cr_cb(self, name: str, custom_res: Dict) -> None:
        """
        Handle exceptions of warehouse order CR processing.

        Used for K8S CR handler.
        """
        # Do not processed if already in order_status PROCESSED
        if custom_res.get('spec', {}).get('order_status') == WarehouseOrderCRDSpec.STATE_PROCESSED:
            return

        try:
            self.process_who_cr(name, custom_res)
        except (ConnectionError, TimeoutError, IOError) as err:
            _LOGGER.error('Error connecting to SAP EWM Backend: "%s" - try again later', err)
        else:
            # Save processed confirmations in custom resource
            self.ordercontroller.save_processed_status(name, custom_res)

    def process_who_cr(self, name: str, custom_res: Dict) -> None:
        """
        Process confirmations in warehouse order CR in sequence.

        Used for K8S CR handler.
        """
        cls = self.__class__

        # Get confirmations to be processed
        data = self._get_who_confirmations(custom_res)

        # Structure the input data
        robcoewmdata = self._structure_callback_data(
            WAREHOUSETASKCONF_TYPE, data, cls.CONFIRMATION_MSG_TYPES)

        # Process the datasets
        for dataset in robcoewmdata:
            # Check if confirmation was processed before
            if self.msg_mem.check_who_conf_processed(dataset):
                _LOGGER.info(
                    '%s confirmation of warehouse task "%s" from warehouse order "%s" already '
                    'processed - skip', dataset.confirmationnumber, dataset.tanum, dataset.who)
                continue

            # Step 1: Confirmation of warehouse task
            self.confirm_warehousetask(dataset)

            # Step 2: Send updated version of warehouse order to robot
            robotident = RobotIdentifier(dataset.lgnum, dataset.rsrc)
            # Request work after successfull first confirmations do not request work after second
            # confirmation, but wait for the robot to request more work
            if (robotident.rsrc is not None
                    and dataset.confirmationnumber == ConfirmWarehouseTask.FIRST_CONF
                    and dataset.confirmationtype == ConfirmWarehouseTask.CONF_SUCCESS):
                success = self.get_and_send_robot_whos(
                    robotident, firstrequest=True, newwho=False, onlynewwho=False)
                if success is False:
                    raise NoOrderFoundError

            # Memorize the dataset in the end
            self.msg_mem.memorize_who_conf(dataset)

        # In case order status is RUNNING and there is nothing to do, verify in EWM
        who_spec = structure(custom_res['spec'], WarehouseOrderCRDSpec)
        if not robcoewmdata and who_spec.order_status == WarehouseOrderCRDSpec.STATE_RUNNING:
            processed = False
            try:
                who = self.ewmwho.get_warehouseorder(who_spec.data.lgnum, who_spec.data.who)
            except NotFoundError:
                processed = True
                _LOGGER.warning(
                    'Warehouse order %s not found in EWM but in status RUNNING, setting to '
                    'PROCESSED', name)
            else:
                if who.status in ['D', '']:
                    processed = False
                else:
                    processed = True
                    _LOGGER.warning(
                        'Warehouse order %s in status %s in EWM but RUNNING in Cloud Robotics, '
                        'setting to PROCESSED', name, who.status)

            if processed:
                # Cleanup warehouse order CRs
                self.cleanup_who(WhoIdentifier(who_spec.data.lgnum, who_spec.data.who))

    def _get_who_confirmations(self, custom_res: Dict) -> List:
        """Get Warehouse Order confirmations to be processed."""
        # Only new confirmations are processed
        confs = custom_res.get('status', {}).get('data', [])
        processed_confs = custom_res.get('spec', {}).get('process_status', [])

        new_confs = []
        for conf in confs:
            if conf not in processed_confs:
                new_confs.append(conf)

        return new_confs
