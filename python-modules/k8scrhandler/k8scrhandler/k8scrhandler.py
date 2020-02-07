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

"""K8s custom resource handler for robcoewmordermanager."""

import os
import re
import sys
import traceback
import logging
import copy
import time
import functools

import threading
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, OrderedDict

from typing import Dict, Callable, List, Optional

from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

from retrying import retry

_LOGGER = logging.getLogger(__name__)

TOO_OLD_RESOURCE_VERSION = re.compile(r"too old resource version: .* \((.*)\)")


def k8s_cr_callback(func: Callable) -> Callable:
    """
    Decorate a method as a K8s CR callback.

    Is working only for K8sCRHandler and child classes.
    """
    @functools.wraps(func)
    def decorated_func(self, *args, **kwargs):
        """Provide automatic locking of CRs in process by this method."""
        # Ensure that signature of K8sCRHandler._callback stays the same
        name = args[0]
        labels = args[1]
        operation = args[2]
        blocking = bool(operation != 'REPROCESS')
        locked = self.cr_locks[name].acquire(blocking=blocking)
        if locked:
            _LOGGER.debug(
                'CR "%s" locked by operation "%s" with label "%s"', name, operation, labels)
            try:
                return func(self, *args, **kwargs)
            finally:
                self.cr_locks[name].release()
                _LOGGER.debug(
                    'CR "%s" unlocked by operation "%s" with label "%s"', name, operation, labels)
                # Cleanup lock objects dictionary when CR was deleted
                if operation == 'DELETED':
                    self.cr_locks.pop(name, None)
        else:
            _LOGGER.info(
                'CR "%s" in process - skipping operation "%s" this run', name, operation)

    _LOGGER.debug('Method "%s" is decorated as K8s callback method', func)
    return decorated_func


def parse_too_old_failure(message: str) -> Optional[int]:
    """
    Parse stream watcher 'too old resource version' error.

    According to https://github.com/kubernetes-client/python/issues/609.
    """
    result = TOO_OLD_RESOURCE_VERSION.search(message)
    if result is None:
        return None

    match = result.group(1)
    if match is None:
        return None

    try:
        return int(match)
    except (ValueError, TypeError):
        return None


class K8sCRHandler:
    """
    Handle K8s custom resources.

    On instance represents one controller watching changes on a single custom
    resource definition.
    """

    VALID_EVENT_TYPES = ['ADDED', 'MODIFIED', 'DELETED', 'REPROCESS']
    REQUEST_TIMEOUT = 5

    def __init__(self,
                 group: str,
                 version: str,
                 plural: str,
                 namespace: str,
                 template_cr: Dict,
                 labels: Dict) -> None:
        """Construct."""
        if 'KUBERNETES_PORT' in os.environ:
            _LOGGER.info('%s/%s: Handler starting "incluster_config" mode', group, plural)
            config.load_incluster_config()
        else:
            _LOGGER.info('%s/%s: Handler starting "kube_config" mode', group, plural)
            config.load_kube_config()

        # Instantiate required K8s APIs
        self.core_api = client.CoreV1Api()
        self.crd_api = client.ApiextensionsV1beta1Api()
        self.co_api = client.CustomObjectsApi()

        # K8s stream watcher
        self.watcher = watch.Watch()

        # Configs set to specify which CRs to monitor/control
        self.group = group
        self.version = version
        self.plural = plural
        self.namespace = namespace

        self.label_selector = ''
        for k, val in labels.items():
            self.label_selector += k + '=' + val + ','
        self.label_selector = self.label_selector[:-1]

        # Latest resource version processed by watcher
        self.resv_watcher = ''

        # Callback stack for watch on cr
        self.callbacks: Dict[str, OrderedDict] = {
            'ADDED': OrderedDict(),
            'MODIFIED': OrderedDict(),
            'DELETED': OrderedDict(),
            'REPROCESS': OrderedDict()
            }

        # JSON template used while creating custom resources
        self.raw_cr = template_cr

        # Lock objects to synchronize processing of CRs
        self.cr_locks: Dict[str, threading.RLock] = defaultdict(threading.RLock)
        # Dict to save thread exceptions
        self.thread_exceptions: Dict[str, Exception] = {}
        # Init threads
        self.watcher_thread = threading.Thread(target=self._watch_on_crs_loop, daemon=True)
        self.reprocess_thread = threading.Thread(target=self._reprocess_crs_loop)
        # Control flag for thread
        self.thread_run = True
        self.number_executor_threads = 1

    def register_callback(
            self, name: str, operations: List, callback: Callable[[Dict], None]) -> None:
        """
        Register a callback function.

        example cb: def callback(self, data: Dict) -> None:
        """
        cls = self.__class__
        # Check for invalid operations
        for operation in operations:
            if operation not in cls.VALID_EVENT_TYPES:
                raise ValueError(
                    '{}/{}: "{}" is not a valid event type'.format(
                        self.group, self.plural, operation))

        # Check if callback is callabe
        if callable(callback) is False:
            raise TypeError('{}/{}: Object "{}" is not callable'.format(
                self.group, self.plural, callback))

        # Check if a callback with the same name alread existing
        already_registered = False
        for operation, callback_list in self.callbacks.items():
            if name in callback_list:
                already_registered = True

        # Value error if callback is existing, if not register it
        if already_registered:
            raise ValueError(
                '{}/{}: A callback with that name already registered'.format(
                    self.group, self.plural))
        else:
            for operation in operations:
                self.callbacks[operation][name] = callback

    def unregister_callback(self, name: str) -> None:
        """Unregister a Pub/Sub order manager queue callback function."""
        for operation in self.callbacks:
            removed = self.callbacks[operation].pop(name, None)
            if removed:
                _LOGGER.info(
                    'Callback %s unregistered from operation %s', name, operation)

    def run(self, watcher: bool = True, reprocess: bool = False,
            multiple_executor_threads: bool = False) -> None:
        """
        Start running all callbacks.

        Supporting multiple executor threads for blocking callbacks.
        """
        if self.thread_run:
            if multiple_executor_threads:
                self.number_executor_threads = 5
            else:
                self.number_executor_threads = 1
            if watcher:
                _LOGGER.info(
                    'Watching for changes on %s.%s/%s', self.plural, self.group, self.version)
                self.watcher_thread.start()
            if reprocess:
                self.reprocess_thread.start()
        else:
            _LOGGER.error(
                'Runner thread for %s/%s is currently deactivated', self.group, self.plural)

    @k8s_cr_callback
    def _callback(self, name: str, labels: Dict, operation: str, custom_res: Dict) -> None:
        """Process custom resource operation."""
        # Run all registered callback functions
        try:
            for callback in self.callbacks[operation].values():
                callback(name, custom_res)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.error(
                '%s/%s: Error while processing custom resource %s', self.group,
                self.plural, name)
            exc_info = sys.exc_info()
            _LOGGER.error(
                '%s/%s: Error in callback - Exception: "%s" / "%s" - TRACEBACK: %s', self.group,
                self.plural, exc_info[0], exc_info[1], traceback.format_exception(*exc_info))
        else:
            _LOGGER.debug(
                '%s/%s: Successfully processed custom resource %s', self.group, self.plural, name)

    def _watch_on_crs(self, executor: ThreadPoolExecutor) -> None:
        """Stream events on orders and execute callbacks."""
        _LOGGER.info(
            '%s/%s: Starting watcher at resourceVersion "%s"',
            self.group, self.plural, self.resv_watcher)
        try:
            self.watcher = watch.Watch()
            stream = self.watcher.stream(
                self.co_api.list_namespaced_custom_object,
                self.group,
                self.version,
                self.namespace,
                self.plural,
                label_selector=self.label_selector,
                resource_version=self.resv_watcher
            )
            for event in stream:
                obj = event['object']
                operation = event['type']
                # Too old resource version error handling
                # https://github.com/kubernetes-client/python/issues/609
                if obj.get('code') == 410:
                    new_version = parse_too_old_failure(obj.get('message'))
                    if new_version is not None:
                        self.resv_watcher = str(new_version)
                        _LOGGER.error(
                            'Updating resource version to %s due to "too old resource version" '
                            'error', new_version)
                        break

                # Skip CRs without a spec or without metadata
                if not obj.get('spec'):
                    continue
                metadata = obj.get('metadata')
                if not metadata:
                    continue
                if metadata.get('resourceVersion'):
                    self.resv_watcher = metadata['resourceVersion']
                name = metadata['name']
                labels = metadata.get('labels', {})
                _LOGGER.debug(
                    '%s/%s: Handling %s on %s', self.group, self.plural,
                    operation, name)
                # Submit callbacks to ThreadPoolExecutor
                executor.submit(self._callback, name, labels, operation, obj)
        except ApiException as err:
            _LOGGER.error(
                '%s/%s: Exception when watching CustomObjectsApi: %s',
                self.group, self.plural, err)

    def _watch_on_crs_loop(self) -> None:
        """Start watching on custom resources in a loop."""
        _LOGGER.info(
            '%s/%s: Start watching on custom resources', self.group, self.plural)
        max_workers = self.number_executor_threads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while self.thread_run:
                try:
                    if self.resv_watcher == '':
                        self.process_all_crs(executor, 'ADDED', set_resv_watcher=True)
                    self._watch_on_crs(executor)
                except Exception as exc:  # pylint: disable=broad-except
                    exc_info = sys.exc_info()
                    _LOGGER.error(
                        '%s/%s: Error reprocessing custom resources - Exception: "%s" / "%s" - '
                        'TRACEBACK: %s', self.group, self.plural, exc_info[0], exc_info[1],
                        traceback.format_exception(*exc_info))
                    # On uncovered exception in thread save the exception
                    self.thread_exceptions['watcher'] = exc
                    # Stop the watcher
                    self.stop_watcher()
                finally:
                    if self.thread_run:
                        _LOGGER.debug('%s/%s: Restarting watcher', self.group, self.plural)

    @retry(wait_fixed=500, stop_max_attempt_number=10)
    def update_cr_status(self, name: str, status: Dict) -> bool:
        """Update the status field of named cr."""
        cls = self.__class__
        custom_res = {'status': status}
        try:
            self.co_api.patch_namespaced_custom_object(
                self.group,
                self.version,
                self.namespace,
                self.plural,
                name,
                custom_res,
                _request_timeout=cls.REQUEST_TIMEOUT)
        except ApiException as err:
            _LOGGER.error(
                '%s/%s: Exception when calling CustomObjectsApi->patch_namespaced_custom_object:'
                ' %s', self.group, self.plural, err)
            raise
        else:
            _LOGGER.debug(
                '%s/%s: Successfully patched custom resource %s', self.group, self.plural, name)

            return True

    @retry(wait_fixed=500, stop_max_attempt_number=10)
    def update_cr_spec(self, name: str, spec: Dict, labels: Optional[Dict] = None) -> bool:
        """Update the status field of named cr."""
        cls = self.__class__
        custom_res = {'spec': spec}
        # Optionally change labels
        if labels:
            custom_res['metadata'] = {'labels': labels}
        try:
            self.co_api.patch_namespaced_custom_object(
                self.group,
                self.version,
                self.namespace,
                self.plural,
                name,
                custom_res,
                _request_timeout=cls.REQUEST_TIMEOUT)
        except ApiException as err:
            _LOGGER.error(
                '%s/%s: Exception when calling CustomObjectsApi->patch_namespaced_custom_object:'
                ' %s', self.group, self.plural, err)
            raise
        else:
            _LOGGER.debug(
                '%s/%s: Successfully patched custom resource %s', self.group, self.plural, name)
            return True

    @retry(wait_fixed=500, stop_max_attempt_number=10)
    def delete_cr(self, name: str) -> bool:
        """Delete specific custom resource by name."""
        cls = self.__class__
        try:
            self.co_api.delete_namespaced_custom_object(
                self.group,
                self.version,
                self.namespace,
                self.plural,
                name,
                client.V1DeleteOptions(),
                _request_timeout=cls.REQUEST_TIMEOUT)
        except ApiException as err:
            _LOGGER.error(
                '%s/%s: Exception when calling CustomObjectsApi->delete_namespaced_custom_object:'
                ' %s', self.group, self.plural, err)
            return False
        else:
            _LOGGER.debug(
                '%s/%s: Successfully deleted custom resource %s', self.group, self.plural, name)
            return True

    @retry(wait_fixed=500, stop_max_attempt_number=10)
    def create_cr(self, name: str, labels: Dict, spec: Dict) -> bool:
        """Create custom resource on 'orders' having json parameter as spec."""
        cls = self.__class__
        custom_res = copy.deepcopy(self.raw_cr)
        custom_res['metadata']['name'] = name
        custom_res['metadata']['labels'] = labels
        custom_res['spec'] = spec
        try:
            self.co_api.create_namespaced_custom_object(
                self.group,
                self.version,
                self.namespace,
                self.plural,
                custom_res,
                _request_timeout=cls.REQUEST_TIMEOUT)
        except ApiException as err:
            _LOGGER.error(
                '%s/%s: Exception when calling CustomObjectsApi->create_namespaced_custom_object:'
                ' %s', self.group, self.plural, err)
            raise
        else:
            _LOGGER.debug(
                '%s/%s: Successfully created custom resource %s', self.group, self.plural, name)
            return True

    @retry(wait_fixed=500, stop_max_attempt_number=10)
    def get_cr(self, name: str) -> Dict:
        """Retrieve a specific custom resource by name."""
        cls = self.__class__
        try:
            api_response = self.co_api.get_namespaced_custom_object(
                self.group,
                self.version,
                self.namespace,
                self.plural,
                name,
                _request_timeout=cls.REQUEST_TIMEOUT)
        except ApiException as err:
            _LOGGER.error(
                '%s/%s: Exception when calling CustomObjectsApi->get_namespaced_custom_object:'
                ' %s', self.group, self.plural, err)
            raise
        else:
            _LOGGER.debug(
                '%s/%s: Successfully retrieved custom resource %s', self.group, self.plural, name)
            return api_response

    @retry(wait_fixed=500, stop_max_attempt_number=10)
    def check_cr_exists(self, name: str) -> bool:
        """Check if a cr exists by name."""
        cls = self.__class__
        try:
            self.co_api.get_namespaced_custom_object(
                self.group,
                self.version,
                self.namespace,
                self.plural,
                name,
                _request_timeout=cls.REQUEST_TIMEOUT)
        except ApiException:
            return False
        else:
            return True

    @retry(wait_fixed=500, stop_max_attempt_number=10)
    def list_all_cr(self) -> Dict:
        """List all currently available custom resources of a kind."""
        cls = self.__class__
        try:
            api_response = self.co_api.list_namespaced_custom_object(
                self.group,
                self.version,
                self.namespace,
                self.plural,
                label_selector=self.label_selector,
                _request_timeout=cls.REQUEST_TIMEOUT
            )
        except ApiException as err:
            _LOGGER.error(
                '%s/%s: Exception when calling CustomObjectsApi->list_namespaced_custom_object:'
                ' %s', self.group, self.plural, err)
            raise
        else:
            _LOGGER.debug(
                '%s/%s: Successfully retrieved all custom resources', self.group, self.plural)
            return api_response

    def process_all_crs(
            self, executor: ThreadPoolExecutor, operation: str,
            set_resv_watcher: bool = False) -> None:
        """
        Reprocess custom resources.

        This method processes all existing custom resources with the given operation.
        """
        cls = self.__class__
        if operation not in cls.VALID_EVENT_TYPES:
            _LOGGER.error('Operation %s is not supported.', operation)
            return

        cr_resp = self.list_all_cr()
        _LOGGER.debug('%s/%s: CR process: Got all CRs.', self.group, self.plural)
        if cr_resp:
            resource_version = ''
            for obj in cr_resp['items']:
                spec = obj.get('spec')
                if not spec:
                    continue
                metadata = obj.get('metadata')
                if not metadata:
                    continue
                resource_version = max(resource_version, metadata.get('resourceVersion', ''))
                name = metadata['name']
                labels = metadata.get('labels', {})
                # Submit callbacks to ThreadPoolExecutor
                executor.submit(
                    self._callback, name, labels, operation, obj)

            # Set resource version for watcher to highest version found here
            if set_resv_watcher:
                self.resv_watcher = resource_version

    def _reprocess_crs_loop(self) -> None:
        """Reprocess existing custom resources in a loop."""
        _LOGGER.info(
            'Start continiously reprocessing existing custom resources')
        last_run = time.time()
        max_workers = self.number_executor_threads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while self.thread_run:
                try:
                    self.process_all_crs(executor, 'REPROCESS')
                except Exception as exc:  # pylint: disable=broad-except
                    exc_info = sys.exc_info()
                    _LOGGER.error(
                        '%s/%s: Error reprocessing custom resources - Exception: "%s" / "%s" - '
                        'TRACEBACK: %s', self.group, self.plural, exc_info[0], exc_info[1],
                        traceback.format_exception(*exc_info))
                    # On uncovered exception in thread save the exception
                    self.thread_exceptions['reprocessor'] = exc
                    # Stop the watcher
                    self.stop_watcher()
                finally:
                    # Wait up to 10 seconds
                    if self.thread_run:
                        time.sleep(max(0, last_run - time.time() + 10))
                        last_run = time.time()

    def stop_watcher(self) -> None:
        """Stop watching CR stream."""
        self.thread_run = False
        _LOGGER.info('Stopping watcher for %s/%s', self.group, self.plural)
        self.watcher.stop()
