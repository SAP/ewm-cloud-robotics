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

"""K8s custom resource handler for new warehouse orders."""

import os
import sys
import traceback
import logging

from typing import Dict, Optional

from cattr import structure

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.warehouseorder import (
    WarehouseOrder, ConfirmWarehouseTask, WarehouseOrderCRDSpec)

from k8scrhandler.k8scrhandler import K8sCRHandler, k8s_cr_callback

_LOGGER = logging.getLogger(__name__)


class OrderController(K8sCRHandler):
    """Handle K8s custom resources."""

    def __init__(self) -> None:
        """Construct."""
        self.init_robot_fromenv()
        # Last successfully processed spec of warehouse order
        self.processed_order_spec: Dict[str, Dict] = {}

        template_cr = get_sample_cr('warehouseorder')

        labels = {}
        labels['cloudrobotics.com/robot-name'] = self.robco_robot_name
        super().__init__(
            'sap.com',
            'v1',
            'warehouseorders',
            'default',
            template_cr,
            labels
        )

    @k8s_cr_callback
    def _callback(self, name: str, labels: Dict, operation: str, custom_res: Dict) -> None:
        """Process custom resource operation."""
        _LOGGER.debug('Handling %s on %s', operation, name)
        # Run all registered callback functions
        try:
            # Check if warehouse order has to be processed in callback.
            process_cr = self._warehouse_order_precheck(name, custom_res)
            # If pre check was successfull set iterate over all callbacks
            if process_cr:
                for callback in self.callbacks[operation].values():
                    callback(name, custom_res['spec']['data'])
        except Exception:  # pylint: disable=broad-except
            _LOGGER.error(
                'Error while processing custom resource %s', name)
            exc_info = sys.exc_info()
            _LOGGER.error(
                '%s/%s: Error in callback - Exception: "%s" / "%s" - TRACEBACK: %s', self.group,
                self.plural, exc_info[0], exc_info[1], traceback.format_exception(*exc_info))
        else:
            if operation == 'DELETED':
                # Cleanup when CR was deleted
                self.processed_order_spec.pop(name, None)
            elif process_cr:
                # When CR was processed successfully, save its spec
                self.processed_order_spec[name] = custom_res['spec']
        _LOGGER.debug('Successfully processed custom resource %s', name)

    def _warehouse_order_precheck(self, name: str, custom_res: Dict) -> bool:
        """Check if warehouse order has to be processed in callback."""
        # Skip warehouse orders with specs already processed before
        if self.processed_order_spec.get(name) == custom_res['spec']:
            _LOGGER.debug('Spec for "%s" already processed before - skip', name)
            return False
        cr_status = custom_res.get('status', {})
        status_data = cr_status.get('data', {})
        process_status = custom_res['spec'].get('process_status', {})
        order_status = custom_res['spec'].get('order_status')
        # Skip warehouse order which is not RUNNING
        if order_status != WarehouseOrderCRDSpec.STATE_RUNNING:
            _LOGGER.debug(
                'Skip "%s" because warehouse order is not %s but in order_status "%s"', name,
                WarehouseOrderCRDSpec.STATE_RUNNING, order_status)
            return False
        # Skip warehouse order if process status from order manager is not
        # equal to status of the warehouse order
        if status_data != process_status:
            _LOGGER.info(
                'Skip "%s" because order manager process status is not equal to warehouse order '
                'status', name)
            return False

        # Check if a warehouse task is already confirmed
        if status_data:
            for wht in custom_res['spec']['data']['warehousetasks']:
                for conf in status_data:
                    if wht['tanum'] == conf['tanum'] and wht['lgnum'] == conf['lgnum']:
                        if (conf['confirmationnumber'] == ConfirmWarehouseTask.FIRST_CONF
                                and conf['confirmationtype'] == ConfirmWarehouseTask.CONF_SUCCESS
                                and wht['vlpla'] != ''):
                            _LOGGER.error(
                                'Skip "%s" because warehouse task "%s" already got first '
                                'confirmation but includes a source bin', name, wht['tanum'])
                            return False
                        if conf['confirmationnumber'] == ConfirmWarehouseTask.SECOND_CONF:
                            _LOGGER.error(
                                'Skip "%s" because warehouse task "%s" already got second '
                                'confirmation', name, wht['tanum'])
                            return False

        return True

    def init_robot_fromenv(self) -> None:
        """Initialize EWM Robot from environment variables."""
        # Read environment variables
        envvar = {}
        envvar['ROBCO_ROBOT_NAME'] = os.environ.get('ROBCO_ROBOT_NAME')
        # Check if complete
        for var, val in envvar.items():
            if val is None:
                raise ValueError('Environment variable "{}" is not set'.format(var))

        # Robot identifier
        self.robco_robot_name = envvar['ROBCO_ROBOT_NAME']

    def confirm_wht(self, dtype: str, wht: Dict) -> None:
        """Notify order manager about current status of who + tasks."""
        name = '{lgnum}.{who}'.format(lgnum=wht['lgnum'], who=wht['who'])
        # Get current status from custom resource of the warehouse order
        custom_res = self.get_cr(name)
        status = custom_res.get('status') if isinstance(custom_res.get('status'), dict) else {}
        # Append current wht confirmation to status
        if not status.get('data'):
            status['data'] = []
        # Check if confirmation was already sent
        for conf in status['data']:
            if conf == wht:
                _LOGGER.error('Confirmation already sent. Not doing anything.')
                return
        status['data'].append(wht)
        self.update_cr_status(name, status)

    def get_warehouseorder(
            self, lgnum: str, who: str) -> Optional[WarehouseOrder]:
        """Get a warehouse order from CR."""
        name = '{}.{}'.format(lgnum, who)

        if self.check_cr_exists(name):
            custom_res = self.get_cr(name)
            if self._warehouse_order_precheck(name, custom_res):
                return structure(custom_res['spec']['data'], WarehouseOrder)
            else:
                return None
        else:
            return None
