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

"""K8s custom resource handler for requests from order auctioneer."""

import logging

from typing import List

from cattr import structure

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.auction import AuctioneerRequestStatus
from robcoewmtypes.warehouseorder import WarehouseOrderIdent

from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class AuctioneerRequestController(K8sCRHandler):
    """Handle K8s custom resources."""

    def __init__(self) -> None:
        """Construct."""
        template_cr = get_sample_cr('auctioneerrequest')

        super().__init__(
            'sap.com',
            'v1',
            'auctioneerrequests',
            'default',
            template_cr,
            {}
        )

    def get_reserved_warehouseorders(self) -> List[WarehouseOrderIdent]:
        """Get reserved warehouse orders of requests which are in process."""
        reserved_whos: List[WarehouseOrderIdent] = []
        # Get all CRs
        cr_resp = self.list_all_cr()
        if cr_resp:
            for custom_res in cr_resp['items']:
                # Continue if CR has no status
                if not custom_res.get('status'):
                    continue
                # Continue if CR is not in process
                status = structure(custom_res.get('status'), AuctioneerRequestStatus)
                if status.status not in AuctioneerRequestStatus.IN_PROCESS_STATUS:
                    continue
                # Append warehouse order idents to list
                reserved_whos.extend(status.warehouseorders)

        return reserved_whos
