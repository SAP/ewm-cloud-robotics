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

import logging

from typing import Dict, Optional

from cattr import structure

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.warehouseorder import (
    ConfirmWarehouseTask, WarehouseOrderCRDSpec)

from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class OrderHandler(K8sCRHandler):
    """Handle K8s custom resources."""

    def __init__(self) -> None:
        """Construct."""
        template_cr = get_sample_cr('warehouseorder')

        labels: Dict[str, str] = {}
        super().__init__(
            'ewm.sap.com',
            'v1alpha1',
            'warehouseorders',
            'default',
            template_cr,
            labels
        )

    @staticmethod
    def warehouse_order_precheck(
            name: str, custom_res: Dict, robot_name: Optional[str] = None) -> bool:
        """Check if warehouse order has to be processed in callback."""
        # Check if the order belongs to the right robot
        if robot_name is not None:
            if custom_res['metadata'].get('labels', {}).get(
                    'cloudrobotics.com/robot-name') != robot_name:
                _LOGGER.info(
                    'Skip "%s" because warehouse order is assigned to a different robot', name)
                return False
        # Skip warehouse order if process status from order manager is not
        # equal to status of the warehouse order. Consider entries for own robot resource only
        process_status = [s for s in custom_res['spec'].get(
            'process_status', []) if s['rsrc'].lower() == custom_res['metadata'].get(
                'labels', {}).get('cloudrobotics.com/robot-name')]
        status_data = custom_res.get('status', {}).get('data', [])
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
                        if (conf['confirmationnumber'] == ConfirmWarehouseTask.SECOND_CONF
                                and conf['confirmationtype'] == ConfirmWarehouseTask.CONF_SUCCESS):
                            _LOGGER.info(
                                'Skip "%s" because warehouse task "%s" already got second '
                                'successful confirmation', name, wht['tanum'])
                            return False

        return True

    def confirm_wht(self, wht: Dict) -> None:
        """Notify order manager about current status of who + tasks."""
        # Warehouse order CR name must be lower case
        name = '{lgnum}.{who}'.format(lgnum=wht['lgnum'], who=wht['who']).lower()
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
            self, lgnum: str, who: str,
            robot_name: Optional[str] = None) -> Optional[WarehouseOrderCRDSpec]:
        """Get a warehouse order from CR."""
        # Warehouse order CR name must be lower case
        name = '{}.{}'.format(lgnum, who).lower()

        if self.check_cr_exists(name):
            custom_res = self.get_cr(name)
            if self.warehouse_order_precheck(name, custom_res, robot_name):
                return structure(custom_res['spec'], WarehouseOrderCRDSpec)
            else:
                return None
        else:
            return None

    def add_who_finalizer(self, lgnum: str, who: str, robot: str) -> None:
        """Add a finalizer to warehouse order CR."""
        # Warehouse order CR name must be lower case
        name = '{}.{}'.format(lgnum, who).lower()

        finalizer = '{}.ewm-robot-controller.sap.com'.format(robot)

        if self.add_finalizer(name, finalizer):
            _LOGGER.info('Added finalizer %s to warehouse order CR %s', finalizer, name)

    def remove_who_finalizer(self, lgnum: str, who: str, robot: str) -> None:
        """Add a finalizer from warehouse order CR."""
        # Warehouse order CR name must be lower case
        name = '{}.{}'.format(lgnum, who).lower()

        finalizer = '{}.ewm-robot-controller.sap.com'.format(robot)

        if self.remove_finalizer(name, finalizer):
            _LOGGER.info('Removed finalizer %s from warehouse order CR %s', finalizer, name)
