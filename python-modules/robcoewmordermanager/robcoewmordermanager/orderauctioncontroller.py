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
from typing import DefaultDict, Dict

from cattr import structure

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.auction import OrderAuctionSpec, OrderAuctionStatus

from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class OrderAuctionController(K8sCRHandler):
    """Handle K8s custom resources."""

    def __init__(self) -> None:
        """Construct."""
        template_cr = get_sample_cr('orderauction')

        super().__init__(
            'ewm.sap.com',
            'v1alpha1',
            'orderauctions',
            'default',
            template_cr,
            {}
        )

        # Robots where the bid agent seems to work
        self._robot_bid_agent_working: DefaultDict[str, bool] = defaultdict(lambda: True)

        # Register callbacks
        self.register_callback(
            'CheckBidAgentStatus', ['ADDED', 'MODIFIED'],
            self._check_bid_agent_status_cb)

    def _check_bid_agent_status_cb(self, name: str, custom_res: Dict) -> None:
        """Check if the bid agent on the robot seems to run."""
        robot = custom_res['metadata'].get('labels', {}).get('cloudrobotics.com/robot-name')
        if robot is None:
            return
        # If orderauction has no status at all, bid agent on robot might not work
        if not custom_res.get('status'):
            self._robot_bid_agent_working[robot] = False
            return

        spec = structure(custom_res['spec'], OrderAuctionSpec)
        status = structure(custom_res['status'], OrderAuctionStatus)

        # When auction is OPEN bidstatus should be RUNNING or COMPLETED
        if (spec.auctionstatus == OrderAuctionSpec.STATUS_OPEN
                and (status.bidstatus == OrderAuctionStatus.STATUS_RUNNING
                     or status.bidstatus == OrderAuctionStatus.STATUS_COMPLETED)):
            self._robot_bid_agent_working[robot] = True
            return

        # When auction is CLOSED or COMPLETED, bidstatus should be COMPLETED
        if ((spec.auctionstatus == OrderAuctionSpec.STATUS_COMPLETED
             or spec.auctionstatus == OrderAuctionSpec.STATUS_CLOSED)
                and status.bidstatus == OrderAuctionStatus.STATUS_COMPLETED):
            self._robot_bid_agent_working[robot] = True
            return

        self._robot_bid_agent_working[robot] = False

    @property
    def robot_bid_agent_working(self) -> DefaultDict[str, bool]:
        """Return robot_bid_agent_working defaultdict."""
        return self._robot_bid_agent_working
