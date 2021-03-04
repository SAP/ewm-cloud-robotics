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
import logging
import copy
import time
import functools

import threading
from concurrent.futures import ThreadPoolExecutor, Future
from collections import defaultdict, OrderedDict

from typing import DefaultDict, Dict, Callable, List, Optional, OrderedDict as TOrderedDict

from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

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
        operation = args[2]
        with self.cr_locks[name]:
            _LOGGER.debug('CR "%s" locked by operation "%s"', name, operation)
            try:
                return func(self, *args, **kwargs)
            finally:
                if operation == 'DELETED':
                    self.cr_locks.pop(name, None)

    _LOGGER.info('Method "%s" is decorated as K8s callback method', func)
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
    REQUEST_TIMEOUT = (5, 30)

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

        # Identify from CRD which method should be used to update CR status
        self.get_status_update_method()

        self.label_selector = ''
        for k, val in labels.items():
            self.label_selector += k + '=' + val + ','
        self.label_selector = self.label_selector[:-1]

        # Latest resource version processed by watcher
        self.resv_watcher = ''

        # Error counter for watcher
        self.err_count_watcher = 0

        # CR Cache
        self._cr_cache: Dict[str, Dict] = {}
        self._cr_cache_lock = threading.Lock()
        self._cr_cache_initialized = False

        # Callback stack for watch on cr
        self.callbacks: Dict[
            str, TOrderedDict[str, Callable]] = self.get_callback_dict()
        self.robot_callbacks: Dict[
            str, Dict[str, TOrderedDict[str, Callable]]] = {}
        self.callbacks_lock = threading.Lock()

        # JSON template used while creating custom resources
        self.raw_cr = template_cr

        # Waiting time to reprocess all custom resource if function is enabled
        self.reprocess_waiting_time = 10.0

        # Lock objects to synchronize processing of CRs
        self.cr_locks: DefaultDict[str, threading.Lock] = defaultdict(threading.Lock)
        # Dict to save thread exceptions
        self.thread_exceptions: Dict[str, Exception] = {}
        # Init threads
        self.watcher_thread = threading.Thread(target=self._watch_on_crs_loop, daemon=True)
        self.synchronize_thread = threading.Thread(
            target=self._synchronize_cache_loop, daemon=True)
        self.reprocess_thread = threading.Thread(target=self._reprocess_crs_loop, daemon=True)
        # Control flag for thread
        self.thread_run = True
        self.executor = ThreadPoolExecutor(max_workers=1)

    @staticmethod
    def get_callback_dict() -> Dict[str, TOrderedDict[str, Callable]]:
        """Get a dictionary to store callback methods."""
        callbacks: Dict[
            str, TOrderedDict[str, Callable]] = {
                'ADDED': OrderedDict(),
                'MODIFIED': OrderedDict(),
                'DELETED': OrderedDict(),
                'REPROCESS': OrderedDict()
                }
        return copy.deepcopy(callbacks)

    def get_status_update_method(self) -> None:
        """
        Get status update method from CRD.

        Depends on status subresource is set or unset in CRD.
        """
        cls = self.__class__
        name = '{}.{}'.format(self.plural, self.group)
        self.status_update_method = self.co_api.patch_namespaced_custom_object
        try:
            api_response = self.crd_api.read_custom_resource_definition(
                name, _request_timeout=cls.REQUEST_TIMEOUT)
        except ApiException as err:
            _LOGGER.error(
                '%s/%s: Exception when calling ApiextensionsV1beta1Api->'
                'read_custom_resource_definition: %s', self.group, self.plural, err)
            raise
        else:
            _LOGGER.debug(
                '%s/%s: Successfully read custom resource definition %s', self.group, self.plural,
                name)
            if api_response.spec.subresources is not None:
                if api_response.spec.subresources.status is not None:
                    self.status_update_method = self.co_api.patch_namespaced_custom_object_status
                    _LOGGER.info('There is a status subresource defined in CRD %s', name)
                    return

            _LOGGER.info('There is no status subresource defined in CRD %s', name)

    def register_callback(
            self, name: str, operations: List, callback: Callable[[str, Dict], None],
            robot_name: Optional[str] = None) -> None:
        """
        Register a callback function.

        example cb: def callback(self, data: Dict) -> None:
        """
        cls = self.__class__
        with self.callbacks_lock:
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

            # Assign the right callback attribute
            log_suffix = ' for robot {}'.format(robot_name) if robot_name is not None else ''
            if robot_name is None:
                callbacks = self.callbacks
            elif self.robot_callbacks.get(robot_name) is None:
                callbacks = self.get_callback_dict()
                self.robot_callbacks[robot_name] = callbacks
            else:
                callbacks = self.robot_callbacks[robot_name]

            # Check if a callback with the same name alread existing
            already_registered = False
            for operation, callback_list in callbacks.items():
                if name in callback_list:
                    already_registered = True

            # Value error if callback is existing, if not register it
            if already_registered:
                raise ValueError(
                    '{}/{}: A callback with that name already registered{}'.format(
                        self.group, self.plural, log_suffix))

            for operation in operations:
                callbacks[operation][name] = callback
                _LOGGER.info(
                    '%s/%s: Callback %s registered to operation %s%s', self.group, self.plural,
                    name, operation, log_suffix)

    def unregister_callback(self, name: str, robot_name: Optional[str] = None) -> None:
        """Unregister a Pub/Sub order manager queue callback function."""
        with self.callbacks_lock:
            # Assign the right callback attribute
            log_suffix = ' for robot {}'.format(robot_name) if robot_name is not None else ''
            if robot_name is None:
                callbacks = self.callbacks
            elif self.robot_callbacks.get(robot_name) is None:
                return
            else:
                callbacks = self.robot_callbacks[robot_name]
            # Unregister callback
            for operation in callbacks:
                removed = callbacks[operation].pop(name, None)
                if removed:
                    _LOGGER.info(
                        '%s/%s: Callback %s unregistered from operation %s%s', self.group,
                        self.plural, name, operation, log_suffix)

    def run(self, reprocess: bool = False,
            multiple_executor_threads: bool = False) -> None:
        """
        Start running all callbacks.

        Supporting multiple executor threads for blocking callbacks.
        """
        if self.thread_run:
            # Restart ThreadPoolExecutor when not running with default max_worker=1
            if multiple_executor_threads:
                self.executor.shutdown()
                self.executor = ThreadPoolExecutor(max_workers=5)
            _LOGGER.info(
                'Watching for changes on %s.%s/%s', self.plural, self.group, self.version)
            self.watcher_thread.start()
            # Wait until cache is initialized
            while self._cr_cache_initialized is False:
                time.sleep(0.01)
            self.synchronize_thread.start()
            if reprocess:
                self.reprocess_thread.start()
        else:
            _LOGGER.error(
                'Runner thread for %s/%s is currently deactivated', self.group, self.plural)

    def _cache_custom_resource(self, name: str, operation: str, custom_res: Dict) -> None:
        """Cache this custom resource."""
        with self._cr_cache_lock:
            if operation in ('ADDED', 'MODIFIED'):
                self._cr_cache[name] = custom_res
            elif operation == 'DELETED':
                self._cr_cache.pop(name, None)

    def _refresh_custom_resource_cache(self) -> Dict[str, Dict]:
        """Refresh custom resource cache from a list with custom resources."""
        _LOGGER.debug("Refreshing custom resource cache")
        with self._cr_cache_lock:
            cr_resp = self._list_all_cr()
            crs = cr_resp['items']
            cr_cache = {}
            for obj in crs:
                metadata = obj.get('metadata')
                if not metadata:
                    continue
                name = metadata['name']
                cr_cache[name] = obj
            self._cr_cache = cr_cache

        return cr_resp

    def _synchronize_cache_loop(self) -> None:
        """Synchronize custom resource cache every 5 minutes."""
        while self.thread_run:
            time.sleep(300)
            try:
                self._refresh_custom_resource_cache()
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error(
                    '%s/%s: Error refreshing CR cache: %s', self.group, self.plural, err,
                    exc_info=True)
                # On uncovered exception in thread save the exception
                self.thread_exceptions['cr-cache-synchronizer'] = err
                # Stop the watcher
                self.stop_watcher()

    @k8s_cr_callback
    def _callback(self, name: str, labels: Dict, operation: str, custom_res: Dict) -> None:
        """Process custom resource operation."""
        robot_name = labels.get('cloudrobotics.com/robot-name', '')
        # Run all registered callback functions
        with self.callbacks_lock:
            callbacks = list(self.callbacks[operation].values())
            if self.robot_callbacks.get(robot_name) is not None:
                callbacks.extend(self.robot_callbacks[robot_name][operation].values())
        try:
            for callback in callbacks:
                callback(name, custom_res)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error(
                '%s/%s: Error in callback when processing CR %s: %s', self.group, self.plural,
                name, err, exc_info=True)
        else:
            _LOGGER.debug(
                '%s/%s: Successfully processed custom resource %s', self.group, self.plural, name)

    def _watch_on_crs(self) -> None:
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
                # Break loop when thread stops
                if not self.thread_run:
                    break
                # Process event
                obj = event['object']
                operation = event['type']
                # Too old resource version error handling
                # https://github.com/kubernetes-client/python/issues/609
                # Outdated from python  API version 12 which includes this PR
                # https://github.com/kubernetes-client/python-base/pull/133/files
                # No an ApiException is raised instead
                if obj.get('code') == 410:
                    new_version = parse_too_old_failure(obj.get('message'))
                    if new_version is not None:
                        self.resv_watcher = str(new_version)
                        _LOGGER.error(
                            'Updating resource version to %s due to "too old resource version" '
                            'error', new_version)
                        # CRD could be the reason for a too old resource version error
                        # Refresh status update method
                        self.get_status_update_method()
                        break

                # Skip CRs without a spec or without metadata
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
                # Cache custom resource
                self._cache_custom_resource(name, operation, obj)
                # Submit callbacks to ThreadPoolExecutor
                self.executor.submit(self._callback, name, labels, operation, obj)
        except ApiException as err:
            if err.status == 410:
                new_version = parse_too_old_failure(err.reason)
                if new_version is not None:
                    self.resv_watcher = str(new_version)
                    _LOGGER.error(
                        'Updating resource version to %s due to "too old resource version" '
                        'error', new_version)
                    # CRD could be the reason for a too old resource version error
                    # Refresh status update method
                    self.get_status_update_method()
                    return

            # If resource version could not be updated, reset it to allow a clean restart
            self.resv_watcher = ''
            _LOGGER.error(
                '%s/%s: Exception when watching CustomObjectsApi: %s',
                self.group, self.plural, err)

            # On unknown errors backoff for a maximum of 60 seconds
            self.err_count_watcher += 1
            backoff = min(60, self.err_count_watcher)
            _LOGGER.info('%s/%s: Backing off for %s seconds', self.group, self.plural, backoff)
            time.sleep(backoff)
        else:
            # Reset error counter
            self.err_count_watcher = 0

    def _init_watcher(self) -> None:
        """Initialize CR watcher."""
        # Sync cache
        cr_resp = self._refresh_custom_resource_cache()
        self._cr_cache_initialized = True
        _LOGGER.debug(
            '%s/%s: Initialize CR watcher: Got all CRs. Cache synced', self.group, self.plural)
        if cr_resp:
            # Set resource version for watcher to the version of the list. According to
            # https://github.com/kubernetes-client/python/issues/693#issuecomment-442893494
            # and https://github.com/kubernetes-client/python/issues/819#issuecomment-491630022
            resource_version = cr_resp.get('metadata', {}).get('resourceVersion')
            if resource_version is None:
                _LOGGER.error('Could not determine resourceVersion. Start from the beginning')
                self.resv_watcher = ''
            else:
                self.resv_watcher = resource_version

            # Process custom resources
            for obj in cr_resp['items']:
                metadata = obj.get('metadata')
                if not metadata:
                    continue
                name = metadata['name']
                labels = metadata.get('labels', {})
                # Submit callbacks to ThreadPoolExecutor
                self.executor.submit(
                    self._callback, name, labels, 'ADDED', obj)

    def _watch_on_crs_loop(self) -> None:
        """Start watching on custom resources in a loop."""
        _LOGGER.info(
            '%s/%s: Start watching on custom resources', self.group, self.plural)
        while self.thread_run:
            try:
                if self.resv_watcher == '':
                    self._init_watcher()
                self._watch_on_crs()
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error(
                    '%s/%s: Error reprocessing custom resources: %s', self.group, self.plural, err,
                    exc_info=True)
                # On uncovered exception in thread save the exception
                self.thread_exceptions['watcher'] = err
                # Stop the watcher
                self.stop_watcher()
            finally:
                if self.thread_run:
                    _LOGGER.debug('%s/%s: Restarting watcher', self.group, self.plural)

        _LOGGER.info("Custom resource watcher stopped")

    def update_cr_status(self, name: str, status: Dict) -> None:
        """Update the status field of named cr."""
        cls = self.__class__
        custom_res = {'status': status}
        try:
            self.status_update_method(
                self.group,
                self.version,
                self.namespace,
                self.plural,
                name,
                custom_res,
                _request_timeout=cls.REQUEST_TIMEOUT)
        except ApiException as err:
            _LOGGER.error(
                '%s/%s: Exception when updating CR status of %s: %s', self.group, self.plural,
                name, err)
            raise
        else:
            _LOGGER.debug(
                '%s/%s: Successfully updated status of CR %s', self.group, self.plural, name)

    def update_cr_spec(
            self, name: str, spec: Dict, labels: Optional[Dict] = None,
            owner_cr: Optional[Dict] = None) -> None:
        """Update the status field of named cr."""
        cls = self.__class__
        custom_res = {'spec': spec}
        # Optionally change labels
        if labels is not None:
            custom_res['metadata'] = {'labels': labels}
        if owner_cr is not None:
            custom_res = self.set_controller_reference(custom_res, owner_cr)
        # Optionally add controller reference
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
                '%s/%s: Exception when updating CR spec of %s: %s', self.group, self.plural,
                name, err)
            raise
        else:
            _LOGGER.debug(
                '%s/%s: Successfully updated spec of CR %s', self.group, self.plural, name)

    def delete_cr(self, name: str) -> None:
        """Delete specific custom resource by name."""
        cls = self.__class__
        try:
            self.co_api.delete_namespaced_custom_object(
                self.group,
                self.version,
                self.namespace,
                self.plural,
                name,
                _request_timeout=cls.REQUEST_TIMEOUT)
        except ApiException as err:
            _LOGGER.error(
                '%s/%s: Exception when deleting CR of %s: %s', self.group, self.plural,
                name, err)
            raise
        else:
            _LOGGER.debug(
                '%s/%s: Successfully deleted CR %s', self.group, self.plural, name)

    def create_cr(
            self, name: str, labels: Dict, spec: Dict, owner_cr: Optional[Dict] = None) -> None:
        """Create custom resource on 'orders' having json parameter as spec."""
        cls = self.__class__
        custom_res = copy.deepcopy(self.raw_cr)
        custom_res['metadata']['name'] = name
        custom_res['metadata']['labels'] = labels
        custom_res['spec'] = spec
        if owner_cr is not None:
            custom_res = self.set_controller_reference(custom_res, owner_cr)
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
                '%s/%s: Exception when creating CR %s: %s', self.group, self.plural, name, err)
            raise
        else:
            _LOGGER.debug(
                '%s/%s: Successfully created CR %s', self.group, self.plural, name)

    def get_cr(self, name: str, use_cache: bool = True) -> Dict:
        """Retrieve a specific custom resource by name."""
        cls = self.__class__
        if use_cache is True:
            try:
                return copy.deepcopy(self._cr_cache[name])
            except KeyError as err:
                _LOGGER.error(
                    '%s/%s: Exception when retrieving CR %s: not found', self.group, self.plural,
                    name)
                raise ApiException(status=404) from err

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
                '%s/%s: Exception when retrieving CR %s: %s', self.group, self.plural, name, err)
            raise
        else:
            _LOGGER.debug(
                '%s/%s: Successfully retrieved CR %s', self.group, self.plural, name)
            return api_response

    def check_cr_exists(self, name: str, use_cache: bool = True) -> bool:
        """Check if a cr exists by name."""
        cls = self.__class__
        if use_cache is True:
            return bool(self._cr_cache.get(name))

        try:
            self.co_api.get_namespaced_custom_object(
                self.group,
                self.version,
                self.namespace,
                self.plural,
                name,
                _request_timeout=cls.REQUEST_TIMEOUT)
        except ApiException as err:
            if err.status == 404:
                return False
            _LOGGER.error(
                '%s/%s: Exception when retrieving CR %s: %s', self.group, self.plural, name, err)
            raise
        else:
            return True

    def list_all_cr(self, use_cache: bool = True) -> List[Dict]:
        """List all currently available custom resources of a kind."""
        if use_cache is True:
            return copy.deepcopy(list(self._cr_cache.values()))

        return self._list_all_cr().get('items', [])

    def _list_all_cr(self) -> Dict:
        """List all currently available custom resources of a kind internally."""
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
                '%s/%s: Exception when listing of CRs: %s', self.group, self.plural, err)
            raise
        else:
            _LOGGER.debug(
                '%s/%s: Successfully listed all CRs', self.group, self.plural)
            return api_response

    def process_all_crs(self) -> None:
        """
        Reprocess custom resources.

        This method processes all existing custom resources with the given operation.
        """
        _LOGGER.debug('%s/%s: CR reprocess started', self.group, self.plural)
        with self._cr_cache_lock:
            crs = copy.deepcopy(list(self._cr_cache.values()))

        futures: List[Future] = []

        for obj in crs:
            metadata = obj.get('metadata')
            if not metadata:
                continue
            name = metadata['name']
            labels = metadata.get('labels', {})
            # Submit callbacks to ThreadPoolExecutor
            futures.append(self.executor.submit(
                self._callback, name, labels, 'REPROCESS', obj))

        # Wait for all futures
        for future in futures:
            future.result()

    def _reprocess_crs_loop(self) -> None:
        """Reprocess existing custom resources in a loop."""
        _LOGGER.info(
            'Start continiously reprocessing existing custom resources')
        last_run = time.time()
        while self.thread_run:
            try:
                self.process_all_crs()
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error(
                    '%s/%s: Error reprocessing custom resources: %s', self.group, self.plural, err,
                    exc_info=True)
                self.thread_exceptions['reprocessor'] = err
                # Stop the watcher
                self.stop_watcher()
            finally:
                # Wait up to self.reprocess_waiting_time seconds
                if self.thread_run:
                    time.sleep(max(0, last_run - time.time() + self.reprocess_waiting_time))
                    last_run = time.time()

        _LOGGER.info("Reprocessing custom resources stopped")

    def stop_watcher(self) -> None:
        """Stop watching CR stream."""
        self.thread_run = False
        _LOGGER.info('Stopping watcher for %s/%s', self.group, self.plural)
        self.watcher.stop()
        _LOGGER.info('Stopping ThreadPoolExecutor')
        self.executor.shutdown(wait=False)

    def add_finalizer(self, name: str, finalizer: str) -> bool:
        """Add a finalizer to a CR."""
        cls = self.__class__
        if self.check_cr_exists(name):
            # Get current finalizers
            cr_resp = self.get_cr(name)
            finalizers = cr_resp['metadata'].get('finalizers', [])
            # Add finalize to list
            finalizers.append(finalizer)
            custom_res = {'metadata': {'finalizers': finalizers}}
            # Update CR
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
                    '%s/%s: Exception when adding finalizer to CR %s: %s', self.group, self.plural,
                    name, err)
                raise
            else:
                _LOGGER.debug('Added finalizer %s to CR %s', finalizer, name)
                return True
        else:
            _LOGGER.error('Unable to add finalizer to CR %s. CR not found', name)
            return False

    def remove_finalizer(self, name: str, finalizer: str) -> bool:
        """Remove a finalizer from a CR."""
        cls = self.__class__
        if self.check_cr_exists(name):
            # Get current finalizers
            cr_resp = self.get_cr(name)
            finalizers = cr_resp['metadata'].get('finalizers', [])
            # Remove finalizer from list
            try:
                finalizers.remove(finalizer)
            except ValueError:
                _LOGGER.error(
                    'Unable to remove finalizer from CR %s. Finalizer %s not found', name,
                    finalizer)
                return False
            custom_res = {'metadata': {'finalizers': finalizers}}
            # Update CR
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
                    '%s/%s: Exception when removing finalizer from CR %s: %s', self.group,
                    self.plural, name, err)
                raise
            else:
                _LOGGER.debug('Removed finalizer %s from CR %s', finalizer, name)
                return True
        else:
            _LOGGER.error('Unable to remove finalizer from CR %s. CR not found', name)
            return False

    @staticmethod
    def set_controller_reference(controlled_cr: Dict, owner_cr: Dict) -> Dict:
        """Set controller reference to custom resource."""
        controller_reference = {
            'apiVersion': owner_cr['apiVersion'],
            'blockOwnerDeletion': True,
            'controller': True,
            'kind': owner_cr['kind'],
            'name': owner_cr['metadata']['name'],
            'uid': owner_cr['metadata']['uid']
        }

        refs = controlled_cr['metadata'].get('ownerReferences', [])
        existing = False
        for ref in refs:
            if ref.get('controller') is True:
                existing = True

        if existing is False:
            refs.append(controller_reference)
            controlled_cr['metadata']['ownerReferences'] = refs

        return controlled_cr
