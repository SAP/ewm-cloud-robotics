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

from threading import RLock
from typing import Dict

from cattr import structure

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.auction import AuctioneerStatus

from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class AuctioneerController(K8sCRHandler):
    """Handle K8s custom resources."""

    def __init__(self) -> None:
        """Construct."""
        template_cr = get_sample_cr('auctioneer')

        super().__init__(
            'ewm.sap.com',
            'v1alpha1',
            'auctioneers',
            'default',
            template_cr,
            {}
        )

        # Robots which are controlled by an auctioneer
        self._robots_in_scope: Dict[str, str] = {}
        self._robots_in_scope_lock = RLock()

        # Status of the auctioneer
        self.auctioneer_status: Dict[str, str] = {}

        # Register callbacks
        self.register_callback(
            'GetRobotsInScope', ['ADDED', 'MODIFIED', 'REPROCESS'], self._get_robots_in_scope_cb)
        self.register_callback(
            'DeleteRobotsInScope', ['DELETED'], self._delete_robots_in_scope_cb)

    def _delete_robots_in_scope_cb(self, name: str, custom_res: Dict) -> None:
        """Delete robots which are in scope of an Auctioneer when the CR is deleted."""
        # Remove all robot from the dict which were previously assigned for this auctioneer
        with self._robots_in_scope_lock:
            self._robots_in_scope = {k: v for k, v in self._robots_in_scope.items() if v != name}
            self.auctioneer_status.pop(name, None)

    def _get_robots_in_scope_cb(self, name: str, custom_res: Dict) -> None:
        """Get robots which are in scope of an Auctioneer."""
        # Remove all robot from the dict which were previously assigned for this auctioneer
        with self._robots_in_scope_lock:
            self._robots_in_scope = {k: v for k, v in self._robots_in_scope.items() if v != name}
            # Add robots in scope again
            if custom_res.get('status') is not None:
                auctioneer_status = structure(custom_res['status'], AuctioneerStatus)
                self.auctioneer_status[name] = auctioneer_status.status
                for robot in auctioneer_status.robotsInScope:
                    self._robots_in_scope[robot] = name

    @property
    def robots_in_scope(self) -> Dict[str, str]:
        """Return robots_in_scope dict."""
        with self._robots_in_scope_lock:
            return self._robots_in_scope
