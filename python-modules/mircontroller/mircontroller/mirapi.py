#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
#
# This file is part of ewm-cloud-robotics
# (see https://github.com/SAP/ewm-cloud-robotics).
#
# This file is licensed under the Apache Software License, v. 2 except as noted
# otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
#

"""Connect RobCo to MiR robot."""

from typing import Optional, Dict
import json
import os
import logging

import attr
import requests
from retrying import retry
from websocket import create_connection, WebSocketTimeoutException

_LOGGER = logging.getLogger(__name__)

HTTP_SUCCESS = [200, 201, 202, 203, 204, 205, 206, 207, 208, 226]


class HTTPstatusCodeFailed(requests.RequestException):
    """HTTP Status Code indicates error."""


class HTTPbadPostRequest(requests.RequestException):
    """HTTP Status Code indicates a bad HTTP POST request."""


def identify_conn_exception(exception: Exception) -> bool:
    """Check if a requests exception occurred."""
    try_again = isinstance(
        exception, (requests.Timeout, requests.ConnectionError, HTTPstatusCodeFailed))
    if try_again:
        _LOGGER.info('Exception %s on HTTP request to MiR API, retrying', exception)
    return try_again


@attr.s(frozen=True)
class MiRConfig:
    """MiR REST API config type."""

    host = attr.ib(validator=attr.validators.instance_of(str), converter=str)
    user = attr.ib(validator=attr.validators.instance_of(str), converter=str)
    password = attr.ib(validator=attr.validators.instance_of(str), converter=str)


class MiRInterface:
    """Send commands to MiR robots via REST."""

    def __init__(self) -> None:
        """Construct."""
        self.init_mir_fromenv()

    def init_mir_fromenv(self) -> None:
        """Initialize MiR interface from environment variables."""
        # Read environment variables
        envvar = {}
        envvar['MIR_USER'] = os.environ.get('MIR_USER')
        envvar['MIR_PASSWORD'] = os.environ.get('MIR_PASSWORD')
        envvar['MIR_HOST'] = os.environ.get('MIR_HOST')
        # Check if complete
        for var, val in envvar.items():
            if val is None:
                raise ValueError(
                    'Environment variable "{}" is not set'.format(var))

        self.mirconfig = MiRConfig(
            host=envvar['MIR_HOST'],
            user=envvar['MIR_USER'],
            password=envvar['MIR_PASSWORD'])

    @retry(retry_on_exception=identify_conn_exception, wait_fixed=1000, stop_max_attempt_number=10)
    def http_delete(self, endpoint: str) -> None:
        """Delete data via MiR REST interface."""
        # Prepare uri
        uri = 'http://{host}/api/v2.0.0/{endpoint}'.format(
            host=self.mirconfig.host, endpoint=endpoint)
        # Prepare additional headers
        headers = {'Accept': 'application/json'}

        # Call REST service
        resp = requests.delete(uri, headers=headers, timeout=5.0, auth=(
            self.mirconfig.user, self.mirconfig.password))

        if 400 <= resp.status_code < 500:
            msg = '{} error on DELETE call to {} - Bad HTTP request'.format(
                resp.status_code, uri)
            _LOGGER.debug(msg)
            raise HTTPbadPostRequest(msg)
        if resp.status_code not in HTTP_SUCCESS:
            msg = '{} error on DELETE call to {} - HTTP status failed'.format(
                resp.status_code, uri)
            _LOGGER.debug(msg)
            raise HTTPstatusCodeFailed(msg)

    @retry(retry_on_exception=identify_conn_exception, wait_fixed=1000, stop_max_attempt_number=10)
    def http_get(self, endpoint: str) -> requests.Response:
        """Get data from MiR REST interface."""
        # Prepare uri
        uri = 'http://{host}/api/v2.0.0/{endpoint}'.format(
            host=self.mirconfig.host, endpoint=endpoint)
        # Prepare additional headers
        headers = {'Accept': 'application/json'}
        # Call REST service
        resp = requests.get(
            uri, headers=headers, timeout=5.0, auth=(self.mirconfig.user, self.mirconfig.password))

        if resp.status_code not in HTTP_SUCCESS:
            msg = '{} error on GET call to {} - HTTP status failed'.format(
                resp.status_code, uri)
            _LOGGER.debug(msg)
            raise HTTPstatusCodeFailed(msg)

        return resp

    @retry(retry_on_exception=identify_conn_exception, wait_fixed=1000, stop_max_attempt_number=10)
    def http_post(
            self, endpoint: str, jsonbody: Optional[Dict] = None) -> requests.Response:
        """Post data to MiR REST interface."""
        # Prepare uri
        uri = 'http://{host}/api/v2.0.0/{endpoint}'.format(
            host=self.mirconfig.host, endpoint=endpoint)
        # Prepare additional headers
        headers = {'Accept': 'application/json'}
        # Prepare JSON body
        if jsonbody is None:
            jsonbody = {}
        # Call REST service
        resp = requests.post(
            uri, json=jsonbody, headers=headers, timeout=5.0,
            auth=(self.mirconfig.user, self.mirconfig.password))

        if 400 <= resp.status_code < 500:
            msg = '{} error on POST call to {} - Bad HTTP request'.format(
                resp.status_code, uri)
            _LOGGER.debug(msg)
            raise HTTPbadPostRequest(msg)
        if resp.status_code not in HTTP_SUCCESS:
            msg = '{} error on POST call to {} - HTTP status failed'.format(
                resp.status_code, uri)
            _LOGGER.debug(msg)
            raise HTTPstatusCodeFailed(msg)

        return resp

    @retry(retry_on_exception=identify_conn_exception, wait_fixed=1000, stop_max_attempt_number=10)
    def http_put(
            self, endpoint: str, jsonbody: Optional[Dict] = None) -> requests.Response:
        """Put data to MiR REST interface."""
        # Prepare uri
        uri = 'http://{host}/api/v2.0.0/{endpoint}'.format(
            host=self.mirconfig.host, endpoint=endpoint)
        # Prepare additional headers
        headers = {'Accept': 'application/json'}
        # Prepare JSON body
        if jsonbody is None:
            jsonbody = {}
        # Call REST service
        resp = requests.put(
            uri, json=jsonbody, headers=headers, timeout=5.0,
            auth=(self.mirconfig.user, self.mirconfig.password))

        if 400 <= resp.status_code < 500:
            msg = '{} error on PUT call to {} - Bad HTTP request'.format(
                resp.status_code, uri)
            _LOGGER.debug(msg)
            raise HTTPbadPostRequest(msg)
        if resp.status_code not in HTTP_SUCCESS:
            msg = '{} error on PUT call to {} - HTTP status failed'.format(
                resp.status_code, uri)
            _LOGGER.debug(msg)
            raise HTTPstatusCodeFailed(msg)

        return resp

    def send_ws_message(self, message: Dict) -> None:
        """Send a message via websocket."""
        try:
            # Open websocket connection
            wsclient = create_connection('ws://{host}:9090'.format(
                host=self.mirconfig.host), timeout=5)
            wsclient.send(json.dumps(message))
        except (WebSocketTimeoutException, TimeoutError):
            msg = 'Connection to rosbridge websocket timed out'
            _LOGGER.debug(msg)
            raise requests.Timeout(msg)
        else:
            wsclient.close()
