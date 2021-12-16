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

"""K8s custom resource handler for reservations from order auctioneer."""

import logging

from collections import defaultdict
from threading import RLock
from typing import DefaultDict, Dict, List

from cattr import structure

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.auction import OrderReservationStatus
from robcoewmtypes.warehouseorder import WarehouseOrderIdent

from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class OrderReservationController(K8sCRHandler):
    """Handle K8s custom resources."""

    def __init__(self, namespace: str) -> None:
        """Construct."""
        template_cr = get_sample_cr('orderreservation')

        super().__init__(
            'ewm.sap.com',
            'v1alpha1',
            'orderreservations',
            namespace,
            template_cr,
            {}
        )

        # Open reservations per auctioneer
        self._open_reservations: DefaultDict[str, Dict] = defaultdict(dict)
        self._open_reservations_lock = RLock()

        # Register callbacks
        self.register_callback(
            'GetOpenReservations', ['ADDED', 'MODIFIED', 'REPROCESS'],
            self._get_open_reservations_cb)
        self.register_callback(
            'DeleteOpenReservations', ['DELETED'], self._delete_open_reservations_cb)

    def get_reserved_warehouseorders(self) -> List[WarehouseOrderIdent]:
        """Get reserved warehouse orders of reservations which are in process."""
        reserved_whos: List[WarehouseOrderIdent] = []
        # Get all CRs
        cr_resp = self.list_all_cr()
        for custom_res in cr_resp:
            # Continue if CR has no status
            if not custom_res.get('status'):
                continue
            # Continue if CR is not in process
            status = structure(custom_res.get('status'), OrderReservationStatus)
            if status.status not in OrderReservationStatus.IN_PROCESS_STATUS:
                continue
            # Append warehouse order idents to list
            for who in status.warehouseorders:
                who_ident = WarehouseOrderIdent(lgnum=who.lgnum, who=who.who)
                reserved_whos.append(who_ident)

        return reserved_whos

    def _delete_open_reservations_cb(self, name: str, custom_res: Dict) -> None:
        """Delete an reservation from auctioneers which owns it."""
        # Remove the current reservation from all entries in dictionary
        with self._open_reservations_lock:
            for res in self.open_reservations.values():
                if name in res:
                    res.pop(name)

    def _get_open_reservations_cb(self, name: str, custom_res: Dict) -> None:
        """Get an open reservation and determine the auctioneer which owns it."""
        # Remove the current reservation from all entries in dictionary
        with self._open_reservations_lock:
            for res in self.open_reservations.values():
                if name in res:
                    res.pop(name)

            res_open = False
            # Reservation is open if it does not have a status
            if not custom_res.get('status'):
                res_open = True
            else:
                # Evaluate status of reservation
                status = structure(custom_res.get('status'), OrderReservationStatus)
                if status.status in OrderReservationStatus.IN_PROCESS_STATUS:
                    res_open = True

            if res_open:
                owner_refs = custom_res['metadata'].get('ownerReferences')
                if owner_refs is not None:
                    for owner_ref in owner_refs:
                        if owner_ref['kind'] == 'Auctioneer':
                            self._open_reservations[owner_ref['name']][name] = True

    @property
    def open_reservations(self) -> DefaultDict[str, Dict]:
        """Return open_reservations defaultdict."""
        with self._open_reservations_lock:
            return self._open_reservations
