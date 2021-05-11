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

from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from typing import Dict, List

import attr
from cattr import structure, unstructure
from dateutil.parser import isoparse

from prometheus_client import Counter

from robcoewmtypes.robot import RobotConfigurationSpec, RobotConfigurationStatus, RobcoRobotStates
from robcoewmtypes.statemachine_config import RobotEWMConfig
from robcoewmtypes.warehouseorder import (
    ConfirmWarehouseTask, WarehouseOrder, WarehouseOrderCRDSpec, WarehouseOrderIdent)
from robcoewmtypes.auction import OrderReservationSpec, OrderReservationStatus, AuctioneerStatus

from robcoewminterface.types import ODataConfig
from robcoewminterface.odata import ODataHandler
from robcoewminterface.ewm import WarehouseOrderOData
from robcoewminterface.exceptions import (
    ODataAPIException, NoOrderFoundError, RobotHasOrderError, WarehouseTaskAlreadyConfirmedError,
    NotFoundError, ResourceTypeIsNoRobotError, RobotNotFoundError, WarehouseOrderAssignedError,
    WarehouseTaskAssignedError, ODATA_ERROR_CODES)

from .helper import ProcessedMessageMemory, RobotIdentifier, WhoIdentifier
from .ordercontroller import OrderController
from .robotconfigcontroller import RobotConfigurationController
from .orderreservationcontroller import OrderReservationController
from .orderauctioncontroller import OrderAuctionController
from .auctioneercontroller import AuctioneerController
from .robotcontroller import RobotController

_LOGGER = logging.getLogger(__name__)

STATE_SUCCEEDED = 'SUCCEEDED'
STATE_FAILED = 'FAILED'


class EWMOrderManager:
    """Main order manager class for EWM."""

    # Prometheus logging
    who_counter = Counter(
        'sap_ewm_warehouse_orders', 'Completed EWM Warehouse orders', ['robot', 'result'])

    def __init__(
            self, oc: OrderController, rc: RobotConfigurationController,
            orc: OrderReservationController, oac: OrderAuctionController,
            auc: AuctioneerController, roc: RobotController) -> None:
        """Construct."""
        self.init_odata_fromenv()

        # Memory of processed messages for order manager
        self.msg_mem = ProcessedMessageMemory()

        # SAP EWM OData handler
        self.odatahandler = ODataHandler(self.odataconfig)
        # SAP EWM OData APIs
        self.ewmwho = WarehouseOrderOData(self.odatahandler)

        # K8s Custom Resource Controller
        self.ordercontroller = oc
        self.robotconfigcontroller = rc
        self.orderreservationcontroller = orc
        self.orderauctioncontroller = oac
        self.auctioneercontroller = auc
        self.robotcontroller = roc

        # Register callback functions
        # Warehouse order status callback
        self.ordercontroller.register_callback(
            'KubernetesWhoCR', ['MODIFIED', 'REPROCESS'], self.process_who_cr_cb)
        # Robot request controller
        self.robotconfigcontroller.register_callback(
            'RobotConfiguration', ['ADDED', 'MODIFIED', 'REPROCESS'], self.robotconfig_cb)
        # Order reservation controller
        self.orderreservationcontroller.register_callback(
            'OrderReservation', ['ADDED', 'MODIFIED', 'REPROCESS'], self.orderreservation_cb)

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

        envvar['RESERVATION_TIMEOUT'] = os.environ.get('RESERVATION_TIMEOUT', 5.0)  # type: ignore

        # Check if complete
        for var, val in envvar.items():
            if val is None:
                raise ValueError(
                    'Environment variable "{}" is not set'.format(var))

        # OData config
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

        # Reservation Timeout for order auction
        self.reservation_timeout = float(envvar['RESERVATION_TIMEOUT'])  # type: ignore
        _LOGGER.info('Order auction reservation timeout is %s minutes', self.reservation_timeout)

    def robotconfig_cb(self, name: str, custom_res: Dict) -> None:
        """
        Handle exceptions of robotconfiguration CR processing.

        Used for K8S CR handler.
        """
        # Return if there is no status yet
        if custom_res.get('status') is None:
            return
        try:
            self.process_robotconfig_cr(name, custom_res)
        except (ConnectionError, TimeoutError, IOError) as err:
            _LOGGER.error('Error connecting to SAP EWM Backend: "%s" - try again later', err)
        except ODataAPIException as err:
            _LOGGER.error('Error in SAP EWM Backend: "%s" - try again later', err)

    def process_robotconfig_cr(self, name: str, custom_res: Dict) -> None:
        """
        Process a robotconfiguration custom resource.

        Used for K8S CR handler.
        """
        # Structure the robotconfig data
        config_spec = structure(custom_res['spec'], RobotConfigurationSpec)
        config_status = structure(custom_res['status'], RobotConfigurationStatus)

        robot = name
        robotident = RobotIdentifier(config_spec.lgnum, robot.upper())

        firstrequest = bool(config_status != self.msg_mem.robot_conf_status[robot])

        # Unassign warehouse orders if robot starts charging or enters STOP mode
        unassign = False
        if firstrequest is True:
            if config_status.statemachine == RobotEWMConfig.state_charging:
                _LOGGER.info(
                    'Robot %s starts charging, unassigning warehouse orders from queue', robot)
                unassign = True
            elif (config_spec.mode == RobotConfigurationSpec.MODE_STOP
                    and config_status.statemachine in RobotEWMConfig.idle_states):
                _LOGGER.info(
                    'Robot %s is in STOP mode, unassigning warehouse orders from queue', robot)
                unassign = True
            elif config_status.statemachine in RobotEWMConfig.error_states:
                try:
                    update_time = isoparse(config_status.updateTime)
                except ValueError:
                    unassign = True
                    _LOGGER.error(
                        'Robot %s is in error state and updateTime in CR status of '
                        'robotconfiguration is invalid. Unassigning warehouse orders from queue',
                        robot)
                else:
                    if update_time + timedelta(minutes=10) < datetime.now(timezone.utc):
                        unassign = True
                        _LOGGER.error(
                            'Robot %s is in error state for more than 10 minutes. Unassigning '
                            'warehouse orders from queue', robot)
        if unassign is True:
            whos = self.ordercontroller.get_running_whos(robot)
            for who_spec, who_status in whos:
                # Only able to unassign before first confirmation was made
                unassign_who = True
                for conf in who_status.data:
                    if (conf.confirmationnumber == ConfirmWarehouseTask.FIRST_CONF and
                            conf.validate_confirmationtype == ConfirmWarehouseTask.CONF_SUCCESS):
                        unassign_who = False

                if unassign_who is True:
                    try:
                        self.ewmwho.unassign_robot_warehouseorder(
                            who_spec.data.lgnum, who_spec.data.rsrc, who_spec.data.who)
                    except (TimeoutError, ConnectionError) as err:
                        # If not successfull. Raise to put message back in queue
                        _LOGGER.error(
                            'Connection error while requesting unassigning warehouse order %s from'
                            ' robot  %s: %s', who_spec.data.who, who_spec.data.rsrc, err)
                        raise
                    except IOError as err:
                        _LOGGER.error(
                            'IOError error while requesting unassigning warehouse order %s from '
                            'robot  %s: %s', who_spec.data.who, who_spec.data.rsrc, err)
                        raise
                    except NoOrderFoundError:
                        _LOGGER.error(
                            'Unable to unassign warehouse order %s.%s: not found',
                            who_spec.data.lgnum, who_spec.data.who)
                    except ODataAPIException as err:
                        _LOGGER.error(
                            'Business error in SAP EWM Backend while requesting unassigning '
                            'warehouse order %s from robot  %s: %s', who_spec.data.who,
                            who_spec.data.rsrc, err)
                        raise
                    else:
                        _LOGGER.info(
                            'Warehouse order %s.%s successfully unassigned from robot %s',
                            who_spec.data.lgnum, who_spec.data.who, who_spec.data.rsrc)
                    self.cleanup_who(WhoIdentifier(who_spec.data.lgnum, who_spec.data.who))
                else:
                    _LOGGER.error(
                        'Cannot unassign warehouse order %s.%s from robot %s because first '
                        'confirmation of a warehouse task is already made', who_spec.data.lgnum,
                        who_spec.data.who, who_spec.data.rsrc)

            self.msg_mem.robot_conf_status[robot] = config_status

        # Request work, when robot is running, idle, available and has no warehouse order assigned
        robot_status = self.robotcontroller.get_robot_status(robot)
        if (config_spec.mode == RobotConfigurationSpec.MODE_RUN
                and config_status.statemachine in RobotEWMConfig.idle_states
                and robot_status.robot.state == RobcoRobotStates.STATE_AVAILABLE
                and robot_status.robot.batteryPercentage >= config_spec.batteryMin):
            if self.ordercontroller.check_for_running_whos(robot) is False:
                try:
                    update_time = isoparse(robot_status.robot.updateTime)
                except ValueError:
                    if firstrequest:
                        _LOGGER.error(
                            'Warehouse order queue of robot %s is empty, but unable to determine '
                            'updateTime in CR status of the robot. Not requesting new work until '
                            'this is fixed', robot)
                else:
                    if update_time + timedelta(minutes=2) < datetime.now(timezone.utc):
                        if firstrequest:
                            _LOGGER.error(
                                'Warehouse order queue of robot %s is empty, but last status '
                                'update time of the robot is older than 2 minutes. Not requesting '
                                'new work until update arrives', robot)
                    else:
                        if firstrequest:
                            _LOGGER.info(
                                'Warehouse order queue of robot %s is empty. Start requesting a '
                                'new warehouse order', robot)
                        self.get_and_send_robot_whos(
                            robotident, firstrequest=firstrequest, newwho=False, onlynewwho=True)

                self.msg_mem.robot_conf_status[robot] = config_status

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
                        'Warehouse task %s has already first confirmation', attr.asdict(whtask))
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
                        'Warehouse task %s has already second confirmation', attr.asdict(whtask))
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
            self.send_robot_whos(robotident, whos)
            return True

        return False

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

    def send_robot_whos(self, robotident: RobotIdentifier, whos: List[WarehouseOrder]) -> None:
        """
        Send warehouse order from SAP EWM to the robot.

        Returns True on success and False on fail.
        """
        # Send orders to robot
        for who in whos:
            self.ordercontroller.send_who_to_robot(robotident, unstructure(who))

        # Create success log message
        whos_who = [entry.who for entry in whos]
        _LOGGER.info(
            'Warehouse orders "%s" sent to robot "%s" in warehouse "%s"',
            whos_who, robotident.rsrc, robotident.lgnum)

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
        except ODataAPIException as err:
            _LOGGER.error('Error in SAP EWM Backend: "%s" - try again later', err)
        else:
            # Save processed confirmations in custom resource
            self.ordercontroller.save_processed_status(name, custom_res)

    def process_who_cr(self, name: str, custom_res: Dict) -> None:
        """
        Process confirmations in warehouse order CR in sequence.

        Used for K8S CR handler.
        """
        # Get confirmations to be processed
        data = self._get_who_confirmations(custom_res)

        # Structure the input data
        confirmations = structure(data, List[ConfirmWarehouseTask])

        # Process the datasets
        for conf in confirmations:
            # Check if confirmation was processed before
            if self.msg_mem.check_who_conf_processed(conf):
                _LOGGER.info(
                    '%s confirmation of warehouse task "%s" from warehouse order "%s" already '
                    'processed - skip', conf.confirmationnumber, conf.tanum, conf.who)
                continue

            # Step 1: Confirmation of warehouse task
            self.confirm_warehousetask(conf)

            # Step 2: Send updated version of warehouse order to robot
            robotident = RobotIdentifier(conf.lgnum, conf.rsrc)
            # Request work after successfull first confirmations do not request work after second
            # confirmation, but wait for the robot to request more work
            if (robotident.rsrc is not None
                    and conf.confirmationnumber == ConfirmWarehouseTask.FIRST_CONF
                    and conf.confirmationtype == ConfirmWarehouseTask.CONF_SUCCESS):
                success = self.get_and_send_robot_whos(
                    robotident, firstrequest=True, newwho=False, onlynewwho=False)
                if success is False:
                    _LOGGER.error(
                        'Unable to update warehouse order on robot %s. Warehouse order %s in '
                        'warehouse %s not found or not running', robotident.rsrc, conf.who,
                        conf.lgnum)

            # Memorize the dataset in the end
            self.msg_mem.memorize_who_conf(conf)

        # In case order status is RUNNING and there is nothing to do, verify in EWM
        who_spec = structure(custom_res['spec'], WarehouseOrderCRDSpec)
        if not confirmations and who_spec.order_status == WarehouseOrderCRDSpec.STATE_RUNNING:
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

    def orderreservation_cb(self, name: str, custom_res: Dict) -> None:
        """Process Order requests CRs."""
        spec = structure(custom_res['spec'], OrderReservationSpec)

        status = structure(custom_res['status'], OrderReservationStatus) if custom_res.get(
            'status') else OrderReservationStatus(
                OrderReservationStatus.STATUS_NEW, self._datetime_reservation_timeout_iso())

        if status.status == OrderReservationStatus.STATUS_NEW:
            self._process_orderres_cr_new(name, spec, status)
        elif status.status == OrderReservationStatus.STATUS_ACCEPTED:
            self._process_orderres_cr_accepted(name, spec, status)
        elif status.status == OrderReservationStatus.STATUS_RESERVATIONS:
            self._process_orderres_cr_reservations(name, spec, status)

    def _datetime_reservation_timeout_iso(self) -> str:
        """Return datetime now() in ISO format."""
        timeout = datetime.now(timezone.utc) + timedelta(minutes=self.reservation_timeout)
        return timeout.isoformat(timespec='seconds')

    def _process_orderres_cr_new(
            self, name: str, spec: OrderReservationSpec, status: OrderReservationStatus) -> None:
        """Process an order reservation CR with status new."""
        # Return if wrong status
        if status.status != OrderReservationStatus.STATUS_NEW:
            return

        # Init warehouse order lists
        whos: List[WarehouseOrder] = []
        whos_exist: List[WarehouseOrder] = []

        # Get warehouse orders from EWM if not done yet
        try:
            whos_exist.extend(self.ewmwho.get_in_process_warehouseorders(
                spec.orderrequest.lgnum, spec.orderrequest.rsrcgrp, spec.orderrequest.rsrctype))
        except (ConnectionError, TimeoutError, IOError) as err:
            _LOGGER.error('Error connecting to SAP EWM Backend: "%s" - try again later', err)
            return
        except ResourceTypeIsNoRobotError:
            msg = ODATA_ERROR_CODES.get('ResourceTypeIsNoRobot')
            status.message = msg
            status.status = OrderReservationStatus.STATUS_FAILED
            self.orderreservationcontroller.update_cr_status(name, unstructure(status))
            return
        except NoOrderFoundError:
            _LOGGER.debug('No potential warehouse order reservations found, continuing')
        except ODataAPIException as err:
            _LOGGER.error('Error in SAP EWM Backend: "%s" - try again later', err)
            return

        # Check if warehouse orders are reserved for a different auction
        whos_reserved = self.orderreservationcontroller.get_reserved_warehouseorders()

        # Use non reserved warehouse orders for this auction
        for who in whos_exist:
            whoident = WarehouseOrderIdent(who.lgnum, who.who)
            if whoident not in whos_reserved:
                whos.append(who)

        if len(whos) < spec.orderrequest.quantity:
            try:
                whos.extend(self.ewmwho.getnew_rtype_warehouseorders(
                    spec.orderrequest.lgnum, spec.orderrequest.rsrcgrp, spec.orderrequest.rsrctype,
                    spec.orderrequest.quantity-len(whos)))
            except NoOrderFoundError:
                pass
            except ResourceTypeIsNoRobotError:
                msg = ODATA_ERROR_CODES.get('ResourceTypeIsNoRobot')
                status.message = msg
                status.status = OrderReservationStatus.STATUS_FAILED
                self.orderreservationcontroller.update_cr_status(name, unstructure(status))
            except (ConnectionError, TimeoutError, IOError) as err:
                _LOGGER.error('Error connecting to SAP EWM Backend: "%s" - try again later', err)
                return
            except ODataAPIException as err:
                _LOGGER.error('Error in SAP EWM Backend: "%s" - try again later', err)
                return

        if whos:
            # Attach the warehouse order list to CR status
            status.warehouseorders = whos
            status.status = OrderReservationStatus.STATUS_ACCEPTED
            self.orderreservationcontroller.update_cr_status(name, unstructure(status))
            _LOGGER.info(
                'Reserved %s warehouse orders in warehouse %s for resource type %s, group %s '
                'with order reservation %s until %s', len(whos), spec.orderrequest.lgnum,
                spec.orderrequest.rsrctype, spec.orderrequest.rsrcgrp, name, status.validuntil)
        else:
            msg = 'No warehouse orders found for order request {}. Trying again'.format(name)
            if status.message != msg:
                status.message = msg
                self.orderreservationcontroller.update_cr_status(name, unstructure(status))
                _LOGGER.info(msg)

    def _process_orderres_cr_accepted(
            self, name: str, spec: OrderReservationSpec, status: OrderReservationStatus) -> None:
        """Process an order reservation CR with status accepted."""
        # Return if wrong status
        if status.status != OrderReservationStatus.STATUS_ACCEPTED:
            return

        # Get warehouse orders with open warehouse tasks from EWM
        connection_error = False
        with ThreadPoolExecutor(max_workers=5) as executor:
            who_futures: Dict[Future, int] = {}
            for i, who in enumerate(status.warehouseorders):
                # Only get warehouse orders which do not include warehouse tasks yet
                if not who.warehousetasks:
                    who_futures[executor.submit(
                        self.ewmwho.get_warehouseorder, who.lgnum, who.who,
                        openwarehousetasks=True)] = i

            for future, i in who_futures.items():
                try:
                    status.warehouseorders[i] = future.result()
                except (ConnectionError, TimeoutError, IOError) as err:
                    _LOGGER.error(
                        'Error connecting to SAP EWM Backend: "%s" - try again later', err)
                    connection_error = True
                except ODataAPIException as err:
                    _LOGGER.error('Error in SAP EWM Backend: "%s" - try again later', err)
                    connection_error = True

        # Update CR status
        if not connection_error:
            status.status = OrderReservationStatus.STATUS_RESERVATIONS
        status.validuntil = self._datetime_reservation_timeout_iso()
        self.orderreservationcontroller.update_cr_status(name, unstructure(status))

    def _process_orderres_cr_reservations(
            self, name: str, spec: OrderReservationSpec, status: OrderReservationStatus) -> None:
        """Process an order reservation CR with status reservations."""
        # Return if wrong status
        if status.status != OrderReservationStatus.STATUS_RESERVATIONS:
            return

        # Check process of the auction once warehouse orders are reserved
        try:
            timeout = isoparse(status.validuntil)
        except ValueError:
            timeout = datetime.now(timezone.utc)

        # There are warehouse order assignments
        if spec.orderassignments:
            _LOGGER.info(
                'Found %s warehouse order assignments to robots in order request %s',
                len(spec.orderassignments), name)
            msg = 'All warehouse orders assigned to robots'
            reserved: List[WarehouseOrderIdent] = []
            for who in status.warehouseorders:
                whoident = WarehouseOrderIdent(who.lgnum, who.who)
                reserved.append(whoident)
            connection_error = False

            for ord_as in spec.orderassignments:
                whoident = WarehouseOrderIdent(ord_as.lgnum, ord_as.who)
                if whoident not in reserved:
                    _LOGGER.error(
                        'Warehouse order %s.%s is not in reservation list - skipping',
                        ord_as.lgnum, ord_as.who)
                    continue
                if ord_as in status.orderassignments:
                    _LOGGER.info(
                        'Warehouse order %s.%s already assigned before - skipping', ord_as.lgnum,
                        ord_as.who)
                    if whoident in reserved:
                        reserved.remove(whoident)
                    continue
                # Assign warehouse order to robot
                try:
                    self.ewmwho.assign_robot_warehouseorder(ord_as.lgnum, ord_as.rsrc, ord_as.who)
                except (ConnectionError, TimeoutError, IOError) as err:
                    _LOGGER.error(
                        'Error connecting to SAP EWM Backend: "%s" - try again later', err)
                    connection_error = True
                except (NoOrderFoundError, RobotNotFoundError, WarehouseOrderAssignedError,
                        WarehouseTaskAssignedError) as err:
                    _LOGGER.error(
                        'Unable to assign warehouse order %s.%s to robot %s: %s', ord_as.lgnum,
                        ord_as.who, ord_as.rsrc, err)
                except ODataAPIException as err:
                    _LOGGER.error('Error in SAP EWM Backend: "%s" - try again later', err)
                    connection_error = True
                else:
                    if whoident in reserved:
                        reserved.remove(whoident)
                    _LOGGER.info(
                        'Warehouse order %s.%s assigned to robot %s', ord_as.lgnum, ord_as.who,
                        ord_as.rsrc)
                    # Append assignment to status
                    status.orderassignments.append(ord_as)
                    # Send warehouse order to robot
                    robotident = RobotIdentifier(ord_as.lgnum, ord_as.rsrc)
                    try:
                        self.get_and_send_robot_whos(
                            robotident, firstrequest=False, newwho=False, onlynewwho=False)
                    except (ConnectionError, TimeoutError, IOError) as err:
                        _LOGGER.error(
                            'Error connecting to SAP EWM Backend: "%s" - try again later', err)
                        connection_error = True
                    except ODataAPIException as err:
                        _LOGGER.error('Error in SAP EWM Backend: "%s" - try again later', err)
                        connection_error = True

            if reserved and not connection_error:
                msg = 'Not all warehouse orders assigned to robots, cancel remaining reservations'
                _LOGGER.info(msg)
                for whoident in reserved:
                    # Unset in process status for non assigned orders to cancel reservation
                    try:
                        self.ewmwho.unset_warehouseorder_in_process(
                            whoident.lgnum, whoident.who)
                    except NoOrderFoundError:
                        _LOGGER.warning(
                            'Warehouse order %s.%s not found. Continuing anyway',
                            whoident.lgnum, whoident.who)
                    except (ConnectionError, TimeoutError, IOError) as err:
                        _LOGGER.error(
                            'Error connecting to SAP EWM Backend: "%s" - try again later', err)
                        connection_error = True
                    except ODataAPIException as err:
                        _LOGGER.error('Error in SAP EWM Backend: "%s" - try again later', err)
                        connection_error = True

            # CR is processed in this status, until there was no connection error to EWM
            if not connection_error:
                status.status = OrderReservationStatus.STATUS_SUCCEEDED
            status.message = msg
            self.orderreservationcontroller.update_cr_status(name, unstructure(status))
        # On timeout cancel the reservations
        elif timeout < datetime.now(timezone.utc):
            msg = 'Warehouse order reservations timed out, set status open in EWM again'
            _LOGGER.info(msg)
            connection_error = False

            for who in status.warehouseorders:
                try:
                    self.ewmwho.unset_warehouseorder_in_process(who.lgnum, who.who)
                except NoOrderFoundError:
                    _LOGGER.warning(
                        'Warehouse order %s.%s not found. Continuing anyway',
                        who.lgnum, who.who)
                except (ConnectionError, TimeoutError, IOError) as err:
                    _LOGGER.error(
                        'Error connecting to SAP EWM Backend: "%s" - try again later', err)
                    connection_error = True
                except ODataAPIException as err:
                    _LOGGER.error('Error in SAP EWM Backend: "%s" - try again later', err)
                    connection_error = True

            # CR is processed in this status, until there was no connection error to EWM
            if not connection_error:
                status.status = OrderReservationStatus.STATUS_TIMEOUT
            status.message = msg
            self.orderreservationcontroller.update_cr_status(name, unstructure(status))

    def is_orderauction_running(self, robot: str, firstrequest: bool = False) -> bool:
        """Check if the order auction process is setup and running on the robot."""
        # Is the robot in scope of an auctioneer
        auctioneer = self.auctioneercontroller.robots_in_scope.get(robot)
        if auctioneer is None:
            return False

        # There should be open reservations for every auctioneer not in status WATCHING
        auctioneer_status = self.auctioneercontroller.auctioneer_status[auctioneer]
        open_res = len(self.orderreservationcontroller.open_reservations[auctioneer])
        if ((auctioneer_status != AuctioneerStatus.STATUS_WATCHING
             and open_res == 0)
                or auctioneer_status == AuctioneerStatus.STATUS_ERROR):
            if firstrequest:
                _LOGGER.error(
                    'Robot %s is in scope of auctioneer %s, which seems to work not correctly. '
                    'Auctioneer status is %s with %s open reservations', robot, auctioneer,
                    auctioneer_status, open_res)
            return False

        if self.orderauctioncontroller.robot_bid_agent_working[robot] is False:
            if firstrequest:
                _LOGGER.error(
                    'Robot %s is in scope of auctioneer %s, but its bid agent seems to work not '
                    'correctly', robot, auctioneer)
            return False

        return True
