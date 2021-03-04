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
import threading
import time

from typing import Dict
from collections import OrderedDict

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.robot import RequestFromRobotStatus

from k8scrhandler.k8scrhandler import K8sCRHandler

from .robotconfigcontroller import RobotConfigurationController

_LOGGER = logging.getLogger(__name__)


class RobotRequestHandler(K8sCRHandler):
    """Handle RobotRequest custom resources."""

    def __init__(self) -> None:
        """Construct."""
        template_cr = get_sample_cr('robotrequest')

        labels: Dict[str, str] = {}
        super().__init__(
            'ewm.sap.com',
            'v1alpha1',
            'robotrequests',
            'default',
            template_cr,
            labels
        )


class RobotRequestController:
    """Send RobotRequests to order-manager via Kubernetes custom resources"."""

    def __init__(self, robot_config: RobotConfigurationController,
                 robotrequest_handler: RobotRequestHandler) -> None:
        """Construct."""
        # RobotRequest handler
        self.handler = robotrequest_handler
        # Robot Configuration Controller
        self.robot_config = robot_config

        # Processed robotrequest CRs dictionary
        self._processed_robotrequests: OrderedDict[  # pylint: disable=unsubscriptable-object
            str, str] = OrderedDict()
        self._processed_robotrequests_lock = threading.Lock()

        # Register robotrequest status update callback
        self.handler.register_callback(
            'cleanup_robotrequests_{}'.format(self.robot_config.robot_name),
            ['ADDED', 'MODIFIED', 'REPROCESS'], self._cleanup_robotrequests_cb,
            self.robot_config.robot_name)
        self.handler.register_callback(
            'robotrequest_deleted_{}'.format(self.robot_config.robot_name),
            ['DELETED'], self._robotrequest_deleted_cb, self.robot_config.robot_name)

    def check_deleted_robotrequests(self):
        """Remove self.robotrequest_state entries if there is no corresponding CR."""
        # Compare with self.robotrequests_status
        delete_robotrequests = []
        with self._processed_robotrequests_lock:
            for robotrequest in self._processed_robotrequests.keys():
                if self.handler.check_cr_exists(robotrequest) is False:
                    delete_robotrequests.append(robotrequest)

            for robotrequest in delete_robotrequests:
                self._processed_robotrequests.pop(robotrequest, None)

    def send_robot_request(self, request: Dict) -> None:
        """Send robot request to order manager."""
        # Don't create the same request twice when it is not processed yet
        existing_requests = self.handler.list_all_cr()
        for existing_request in existing_requests:
            if existing_request.get('status', {}).get(
                    'status') != RequestFromRobotStatus.STATE_PROCESSED:
                if request == existing_request.get('spec', {}):
                    _LOGGER.info(
                        'There is already a robotrequest with the same content running - skip')
                    return

        # No robotrequest existing. Create a new one
        labels = {}
        labels['cloudrobotics.com/robot-name'] = self.robot_config.robot_name
        spec = request
        name = '{}.{}'.format(self.robot_config.robot_name, time.time())

        self.handler.create_cr(name, labels, spec)

    def delete_robot_request(self, request: Dict) -> None:
        """Delete a robot request."""
        # Delete all running robot requests of the same kind
        existing_requests = self.handler.list_all_cr()
        for existing_request in existing_requests:
            # Only process custom resources labeled with own robot name
            if existing_request['metadata'].get('labels', {}).get(
                    'cloudrobotics.com/robot-name') != self.robot_config.robot_name:
                continue
            if existing_request.get('status', {}).get(
                    'status') != RequestFromRobotStatus.STATE_PROCESSED:
                if request == existing_request.get('spec', {}):
                    _LOGGER.info('Deleting robotrequest %s', existing_request['metadata']['name'])
                    self.handler.delete_cr(existing_request['metadata']['name'])

    def _robotrequest_deleted_cb(self, name: str, custom_res: Dict) -> None:
        """Remove deleted CR from self._processed_robotrequests."""
        # Only process custom resources labeled with own robot name
        if custom_res['metadata'].get('labels', {}).get(
                'cloudrobotics.com/robot-name') != self.robot_config.robot_name:
            return

        with self._processed_robotrequests_lock:
            # If robotrequest was deleted remove it from dictionary
            if name in self._processed_robotrequests:
                self._processed_robotrequests.pop(name, None)

    def _cleanup_robotrequests_cb(self, name: str, custom_res: Dict) -> None:
        """Cleanup processed robotrequest CRs."""
        # Only process custom resources labeled with own robot name
        if custom_res['metadata'].get('labels', {}).get(
                'cloudrobotics.com/robot-name') != self.robot_config.robot_name:
            return

        # No status means nothing to update yet
        if not custom_res.get('status'):
            return

        # Clean up robotrequests with status PROCESSED
        if custom_res['status'].get('status') == RequestFromRobotStatus.STATE_PROCESSED:
            # Already in status PROCESSED no need for cleanup
            if self._processed_robotrequests.get(name) == RequestFromRobotStatus.STATE_PROCESSED:
                return
        elif custom_res['status'].get('status') in [
                RequestFromRobotStatus.STATE_RUNNING, RequestFromRobotStatus.STATE_WAITING]:
            if self._processed_robotrequests.get(name):
                with self._processed_robotrequests_lock:
                    self._processed_robotrequests.pop(name, None)
            # status RUNNING, no reason for cleanup
            return
        else:
            _LOGGER.warning('Unknown status "%s"', custom_res['status'].get('status'))
            return

        # OrderedDict must not be changed when iterating (self._processed_robotrequests)
        with self._processed_robotrequests_lock:
            # New in status PROCESSED
            self._processed_robotrequests[name] = RequestFromRobotStatus.STATE_PROCESSED
            # Delete finished robotrequests with status PROCESSED
            # Keep maximum of 5 robotrequests
            processed = 0
            delete_robotrequests = []
            # Start counting from the back of robotrequests OrderedDict
            for robotrequest in reversed(self._processed_robotrequests.keys()):
                processed += 1
                if processed > 5:
                    # Save robotrequest to be deleted
                    delete_robotrequests.append(robotrequest)

            # Delete robotrequest CR and remove it from dictionary
            for robotrequest in delete_robotrequests:
                if self.handler.check_cr_exists(robotrequest):
                    self.handler.delete_cr(robotrequest)
                    self._processed_robotrequests.pop(robotrequest, None)
                    _LOGGER.info('RobCo robotrequest CR %s was cleaned up', robotrequest)
                else:
                    self._processed_robotrequests.pop(robotrequest, None)
