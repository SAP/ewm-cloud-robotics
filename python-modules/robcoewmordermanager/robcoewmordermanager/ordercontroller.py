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

"""K8s custom resource handler for EWM warehouse orders."""

import sys
import traceback
import logging
import threading
import time

from collections import OrderedDict
from typing import Dict

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.warehouseorder import WarehouseOrderCRDSpec

from k8scrhandler.k8scrhandler import K8sCRHandler

from .helper import RobotIdentifier

_LOGGER = logging.getLogger(__name__)


class OrderController(K8sCRHandler):
    """Handle K8s custom resources."""

    def __init__(self) -> None:
        """Construct."""
        # Processed warehouse order CRs dictionary
        self._processed_orders = OrderedDict()
        self._processed_orders_lock = threading.RLock()
        self._deleted_orders = OrderedDict()

        template_cr = get_sample_cr('warehouseorder')

        labels = {}
        super().__init__(
            'sap.com',
            'v1',
            'warehouseorders',
            'default',
            template_cr,
            labels
        )

        # Thread to check for deleted warehouse order CRs
        self.deleted_warehouse_orders_thread = threading.Thread(
            target=self._deleted_orders_checker)

        # Register callbacks
        self.register_callback(
            'CleanupOrders', ['ADDED', 'MODIFIED', 'REPROCESS'], self._cleanup_orders_cb)
        self.register_callback('DeletedOrders', ['DELETED'], self._order_deleted_cb)

    def _cleanup_orders_cb(self, name: str, custom_res: Dict) -> None:
        """Cleanup processed warehouse order CRs."""
        # If CR already deleted, there is no need for a cleanup
        if (custom_res['spec'].get('order_status') != WarehouseOrderCRDSpec.STATE_RUNNING
                and name in self._deleted_orders):
            return
        elif (custom_res['spec'].get('order_status') == WarehouseOrderCRDSpec.STATE_RUNNING
              and name in self._deleted_orders):
            self._deleted_orders.pop(name, None)

        # Clean up warehouse orders with order_status PROCESSED
        if custom_res['spec'].get('order_status') == WarehouseOrderCRDSpec.STATE_PROCESSED:
            # Already in order_status PROCESSED no need for cleanup
            if self._processed_orders.get(name) == WarehouseOrderCRDSpec.STATE_PROCESSED:
                return
        elif custom_res['spec'].get('order_status') == WarehouseOrderCRDSpec.STATE_RUNNING:
            # order_status RUNNING, no reason for cleanup
            if self._processed_orders.get(name):
                with self._processed_orders_lock:
                    self._processed_orders.pop(name, None)
            return
        else:
            _LOGGER.warning('Unknown order_status "%s"', custom_res['spec'].get('order_status'))
            return

        with self._processed_orders_lock:
            # New in order_status PROCESSED
            self._processed_orders[name] = WarehouseOrderCRDSpec.STATE_PROCESSED

            # Delete warehouse orders with status PROCESSED
            # Keep maximum of 50 warehouse_orders
            processed = 0
            delete_warehouse_orders = []
            # Start counting from the back of warehouse order OrderedDict
            for warehouse_order in reversed(self._processed_orders.keys()):
                processed += 1
                if processed > 50:
                    # Save warehouse_order to be deleted
                    delete_warehouse_orders.append(warehouse_order)

            # Delete warehouse order CR
            for warehouse_order in delete_warehouse_orders:
                if self.check_cr_exists(warehouse_order):
                    success = self.delete_cr(warehouse_order)
                    if success:
                        self._deleted_orders[warehouse_order] = True
                        self._processed_orders.pop(warehouse_order, None)
                        _LOGGER.info(
                            'RobCo warehouse_order CR %s was cleaned up', warehouse_order)
                    else:
                        _LOGGER.error(
                            'Deleting RobCo warehouse_order CR %s failed', warehouse_order)
                else:
                    self._deleted_orders[warehouse_order] = True
                    self._processed_orders.pop(warehouse_order, None)

            # Keep a maximum of 500 entries in deleted orders OrderedDict
            to_remove = max(0, len(self._deleted_orders) - 500)
            for _ in range(to_remove):
                self._deleted_orders.popitem(last=False)

    def _deleted_orders_checker(self) -> None:
        """Continously check for deleted warehouse_order CR and remove them from ordered dict."""
        _LOGGER.info(
            'Start continiously checking for deleted warehouse_order CRs')
        while self.thread_run:
            try:
                self._check_deleted_orders()
            except Exception as exc:  # pylint: disable=broad-except
                exc_info = sys.exc_info()
                _LOGGER.error(
                    '%s/%s: Error checking for deleted warehouse_orders - Exception: "%s" / "%s" -'
                    ' TRACEBACK: %s', self.group, self.plural, exc_info[0], exc_info[1],
                    traceback.format_exception(*exc_info))
                # On uncovered exception in thread save the exception
                self.thread_exceptions['deleted_warehouse_orders_checker'] = exc
                # Stop the watcher
                self.stop_watcher()
            finally:
                # Wait 10 seconds
                if self.thread_run:
                    time.sleep(10)

    def _check_deleted_orders(self) -> None:
        """Remove self._processed_orders entries with no CR from ordered dictionary."""
        cr_resp = self.list_all_cr()
        _LOGGER.debug('%s/%s: Check deleted CR: Got all CRs.', self.group, self.plural)
        if cr_resp:
            # Collect names of all existing CRs
            warehouse_order_crs = {}
            for obj in cr_resp['items']:
                spec = obj.get('spec')
                if not spec:
                    continue
                metadata = obj.get('metadata')
                warehouse_order_crs[metadata['name']] = True

            # Compare with self._processed_orders
            deleted_warehouse_orders = []
            with self._processed_orders_lock:
                for warehouse_order in self._processed_orders.keys():
                    if warehouse_order not in warehouse_order_crs:
                        deleted_warehouse_orders.append(warehouse_order)

                for warehouse_order in deleted_warehouse_orders:
                    self._deleted_orders[warehouse_order] = True
                    self._processed_orders.pop(warehouse_order, None)

    def run(self, watcher: bool = True, reprocess: bool = False,
            multiple_executor_threads: bool = False) -> None:
        """Start running all callbacks."""
        # If reprocessing is enabled, check for deleted warehouse order CRs too
        if reprocess:
            self.deleted_warehouse_orders_thread.start()
        # start own callbacks
        super().run(watcher=watcher, reprocess=reprocess,
                    multiple_executor_threads=multiple_executor_threads)

    def send_who_to_robot(
            self, robotident: RobotIdentifier, dtype: str, who: Dict) -> bool:
        """Send the warehouse order to a robot."""
        labels = {}
        # Robot name must be lower case
        labels['cloudrobotics.com/robot-name'] = robotident.rsrc.lower()
        name = '{lgnum}.{who}'.format(lgnum=who['lgnum'], who=who['who'])
        spec = {'data': who, 'order_status': WarehouseOrderCRDSpec.STATE_RUNNING}
        if self.check_cr_exists(name):
            _LOGGER.debug('Warehouse order CR "%s" exists. Update it', name)
            success = self.update_cr_spec(name, spec, labels)
        else:
            _LOGGER.debug('Warehouse order CR "%s" not existing. Create it', name)
            success = self.create_cr(name, labels, spec)

            return success

    def cleanup_who(self, who: Dict) -> bool:
        """Cleanup warehouse order when it was finished."""
        # Warehouse orders to be deleted
        to_be_closed = []
        # Delete warehouse order
        name = '{lgnum}.{who}'.format(lgnum=who['lgnum'], who=who['who'])
        to_be_closed.append(name)
        spec_order_processed = {'order_status': WarehouseOrderCRDSpec.STATE_PROCESSED}

        success = self.update_cr_spec(name, spec_order_processed)
        if success:
            _LOGGER.info(
                'Cleanup successfull, warehouse order CR "%s" in order_status %s', name,
                WarehouseOrderCRDSpec.STATE_PROCESSED)

            # Delete sub warehouse orders if existing
            crs = self.list_all_cr()
            if crs:
                for obj in crs['items']:
                    spec = obj.get('spec')
                    if not spec:
                        continue
                    # Delete warehouse order if its top warehouse order
                    # was deleted in this step
                    if (spec['data']['topwhoid'] == who['who']
                            and spec['data']['lgnum'] == who['lgnum']):
                        name = '{lgnum}.{who}'.format(
                            lgnum=spec['data']['lgnum'], who=spec['data']['who'])
                        to_be_closed.append(name)
                        success_sub = success = self.update_cr_spec(name, spec_order_processed)
                        if success_sub is True:
                            _LOGGER.info(
                                'Cleanup successfull, warehouse order CR "%s" in order_status %s',
                                name, WarehouseOrderCRDSpec.STATE_PROCESSED)
                        else:
                            _LOGGER.error('Error updating warehouse order CR "%s"', name)
                            success = False

        return success

    def _order_deleted_cb(self, name: str, custom_res: Dict) -> None:
        """Remove deleted CR from self._processed_orders."""
        self._deleted_orders[name] = True
        if self._processed_orders.get(name):
            with self._processed_orders_lock:
                # When warehouse order cr was deleted remove it from ordered dictionary
                self._processed_orders.pop(name, None)

    def save_processed_status(self, name: str, custom_res: Dict) -> None:
        """Save processed custom resource status in spec.process_status."""
        if self.check_cr_exists(name):
            # Only if changed
            if custom_res['spec'].get('process_status') != custom_res[
                    'status'].get('data'):
                data_processed = {'process_status': custom_res['status']['data']}
                self.update_cr_spec(name, data_processed)
