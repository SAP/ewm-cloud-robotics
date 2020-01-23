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
import threading
import time

from typing import Dict
from collections import OrderedDict
from cattr import structure

from robcoewmtypes.helper import get_sample_cr
from robcoewmtypes.robot import RequestFromRobotStatus

from k8scrhandler.k8scrhandler import K8sCRHandler

_LOGGER = logging.getLogger(__name__)


class RobotRequestController(K8sCRHandler):
    """Handle K8s custom resources."""

    def __init__(self) -> None:
        """Construct."""
        self.init_robot_fromenv()
        # Robotrequest status dictionary
        self.robotrequest_status = OrderedDict()
        self.robotrequest_status_lock = threading.RLock()
        template_cr = get_sample_cr('robotrequest')

        labels = {}
        labels['cloudrobotics.com/robot-name'] = self.robco_robot_name
        super().__init__(
            'sap.com',
            'v1',
            'robotrequests',
            'default',
            template_cr,
            labels
        )

        # Register robotrequest status update callback
        self.register_callback(
            'update_robotrequest_status', ['ADDED', 'MODIFIED', 'REPROCESS'],
            self.update_robotrequest_status_cb)
        self.register_callback('robotrequest_deleted', ['DELETED'], self.robotrequest_deleted_cb)

        # Thread to check for deleted robotrequest CRs
        self.deleted_robotrequests_thread = threading.Thread(
            target=self._deleted_robotrequests_checker)

    def init_robot_fromenv(self) -> None:
        """Initialize EWM Robot from environment variables."""
        # Read environment variables
        envvar = {}
        envvar['ROBCO_ROBOT_NAME'] = os.environ.get('ROBCO_ROBOT_NAME')
        # Check if complete
        for var, val in envvar.items():
            if val is None:
                raise ValueError(
                    'Environment variable "{}" is not set'.format(var))

        # Robot identifier
        self.robco_robot_name = envvar['ROBCO_ROBOT_NAME']

    def check_deleted_robotrequests(self):
        """Remove self.robotrequest_state entries if there is no corresponding CR."""
        cr_resp = self.list_all_cr()
        _LOGGER.debug('%s/%s: Check deleted CR: Got all CRs.', self.group, self.plural)
        if cr_resp:
            # Collect names of all existing CRs
            robotrequest_crs = {}
            for obj in cr_resp['items']:
                spec = obj.get('spec')
                if not spec:
                    continue
                metadata = obj.get('metadata')
                robotrequest_crs[metadata['name']] = True

            # Compare with self.robotrequests_status
            delete_robotrequests = []
            with self.robotrequest_status_lock:
                for robotrequest in self.robotrequest_status.keys():
                    if robotrequest not in robotrequest_crs:
                        delete_robotrequests.append(robotrequest)

                for robotrequest in delete_robotrequests:
                    self.robotrequest_status[
                        robotrequest].status = RequestFromRobotStatus.STATE_DELETED

    def run(self, watcher: bool = True, reprocess: bool = False,
            multiple_executor_threads: bool = False) -> None:
        """Start running all callbacks."""
        # If reprocessing is enabled, check for deleted roborequest CRs too
        if reprocess:
            self.deleted_robotrequests_thread.start()
        # start own callbacks
        super().run(watcher=watcher, reprocess=reprocess,
                    multiple_executor_threads=multiple_executor_threads)

    def _deleted_robotrequests_checker(self):
        """Continously check for deleted robotrequest CR and mark them deleted."""
        _LOGGER.info(
            'Start continiously checking for deleted robotrequest CRs')
        while self.thread_run:
            try:
                self.check_deleted_robotrequests()
            except Exception as exc:  # pylint: disable=broad-except
                exc_info = sys.exc_info()
                _LOGGER.error(
                    '%s/%s: Error checking for deleted robotrequests - Exception: "%s" / "%s" - '
                    'TRACEBACK: %s', self.group, self.plural, exc_info[0], exc_info[1],
                    traceback.format_exception(*exc_info))
                # On uncovered exception in thread save the exception
                self.thread_exceptions['deleted_robotrequests_checker'] = exc
                # Stop the watcher
                self.stop_watcher()
            finally:
                # Wait 10 seconds
                if self.thread_run:
                    time.sleep(10)

    def send_robot_request(self, dtype: str, request: Dict) -> None:
        """Send robot request to order manager."""
        # Don't create the same request twice when it is not processed yet
        existing_requests = self.list_all_cr()
        for existing_request in existing_requests['items']:
            if existing_request.get('status', {}).get(
                    'status') != RequestFromRobotStatus.STATE_PROCESSED:
                if request == existing_request.get('spec', {}):
                    _LOGGER.info(
                        'There is already a robotrequest with the same content running - skip')
                    return True

        # No robotrequest existing. Create a new one
        labels = {}
        labels['cloudrobotics.com/robot-name'] = self.robco_robot_name
        spec = request
        name = '{}.{}'.format(self.robco_robot_name, time.time())

        success = self.create_cr(name, labels, spec)

        return success

    def robotrequest_deleted_cb(self, name: str, custom_res: Dict) -> None:
        """Update self.robotrequest_status."""
        with self.robotrequest_status_lock:
            # If robotrequest was deleted remove it from dictionary
            if name in self.robotrequest_status:
                self.robotrequest_status[name].status = RequestFromRobotStatus.STATE_DELETED

    def update_robotrequest_status_cb(self, name: str, custom_res: Dict) -> None:
        """Update self.robotrequest_status."""
        # No status means nothing to update yet
        if not custom_res.get('status'):
            return
        # Request is not running and marked as deleted before. Nothing to do here.
        try:
            if (custom_res['status'].get('status') != RequestFromRobotStatus.STATE_RUNNING
                    and self.robotrequest_status[
                        name].status == RequestFromRobotStatus.STATE_DELETED):
                return
        except KeyError:
            pass
        # Update the robotrequest dictionary
        request_status = structure(custom_res['status'], RequestFromRobotStatus)
        # OrderedDict must not be changed when iterating (self.robotrequest_status)
        with self.robotrequest_status_lock:
            self.robotrequest_status[name] = request_status
            # Delete finished robotrequests with status PROCESSED
            # Keep maximum of 5 robotrequests
            finished = 0
            delete_robotrequests = []
            deleted = 0
            clean_robotrequests = []
            # Start counting from the back of robotrequests OrderedDict
            for robotrequest, status in reversed(self.robotrequest_status.items()):
                if status.status == RequestFromRobotStatus.STATE_PROCESSED:
                    finished += 1
                    if finished > 5:
                        # Save robotrequest to be deleted
                        delete_robotrequests.append(robotrequest)
                elif status.status == RequestFromRobotStatus.STATE_DELETED:
                    deleted += 1
                    if deleted > 5:
                        # Save robotrequest to be deleted
                        clean_robotrequests.append(robotrequest)

            # Delete robotrequest CR and remove it from dictionary
            for robotrequest in delete_robotrequests:
                if self.check_cr_exists(robotrequest):
                    success = self.delete_cr(robotrequest)
                    if success:
                        self.robotrequest_status[
                            robotrequest].status = RequestFromRobotStatus.STATE_DELETED
                        _LOGGER.info('RobCo robotrequest CR %s was cleaned up', robotrequest)
                    else:
                        _LOGGER.error('Deleting RobCo robotrequest CR %s failed', robotrequest)
                else:
                    self.robotrequest_status[
                        robotrequest].status = RequestFromRobotStatus.STATE_DELETED

            # Clean dictionary
            for robotrequest in clean_robotrequests:
                self.robotrequest_status.pop(robotrequest, None)
