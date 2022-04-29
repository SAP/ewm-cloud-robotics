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

"""Connect RobCo to FetchCore."""

import os
import logging
import json
import time
import threading

from typing import Dict

import requests

from retrying import retry


_LOGGER = logging.getLogger(__name__)


class HTTPstatusCodeFailed(requests.RequestException):
    """HTTP Status Code indicates error."""


class HTTPstatusNotFound(requests.RequestException):
    """HTTP Status Code indicates not found (404)."""


class HTTPAuthError(HTTPstatusCodeFailed):
    """HTTP Status Code indicates authentication error."""


def identify_requests_exception(exception: BaseException) -> bool:
    """Check if a requests exception occurred."""
    _LOGGER.error('Exception %s on HTTP request to FetchCore, retrying', exception)
    return isinstance(
        exception, (requests.Timeout, requests.ConnectionError, HTTPstatusCodeFailed))


class FetchInterface:
    """Interface class to FetchCore."""

    def __init__(self) -> None:
        """Construct."""
        self.init_fetchcore_fromenv()
        self._bearer = None
        self._bearer_expires = time.time()
        self._auth_error = False
        self.refresh_bearer_thread = threading.Thread(target=self._refresh_bearer, daemon=True)

    def init_fetchcore_fromenv(self) -> None:
        """Initialize FetchCore from environment variables."""
        # Read environment variables
        envvar = {}
        envvar['FETCHCORE_HOST'] = os.environ.get('FETCHCORE_HOST')
        envvar['FETCHCORE_USER'] = os.environ.get('FETCHCORE_USER')
        envvar['FETCHCORE_PASSWORD'] = os.environ.get('FETCHCORE_PASSWORD')
        envvar['FETCHCORE_CLIENTID'] = os.environ.get('FETCHCORE_CLIENTID')
        envvar['FETCHCORE_CLIENTSECRET'] = os.environ.get('FETCHCORE_CLIENTSECRET')
        envvar['FETCHCORE_AUTHHOST'] = os.environ.get(
            'FETCHCORE_AUTHHOST', 'https://auth.fsp.fetchcore-cloud.com/oauth/token')
        # Check if complete
        for var, val in envvar.items():
            if val is None:
                raise ValueError(
                    'Environment variable "{}" is not set'.format(var))

        self._fetchcore_host = envvar['FETCHCORE_HOST']
        self._fetchcore_user = envvar['FETCHCORE_USER']
        self._fetchcore_password = envvar['FETCHCORE_PASSWORD']
        self._fetchcore_clientid = envvar['FETCHCORE_CLIENTID']
        self._fetchcore_clientsecret = envvar['FETCHCORE_CLIENTSECRET']
        self._fetchcore_authhost = envvar['FETCHCORE_AUTHHOST']
        _LOGGER.info(
            'Connecting to FetchCore host"%s"', self._fetchcore_host)

    @retry(retry_on_exception=identify_requests_exception, wait_fixed=1000)
    def auth_fetchcore(self) -> None:
        """Authenticate on FetchCore auth provider."""
        auth_body = {
            'grant_type': 'password',
            'client_id': self._fetchcore_clientid,
            'audience': 'fetchcore',
            'username': self._fetchcore_user,
            'password': self._fetchcore_password,
            'client_secret': self._fetchcore_clientsecret
            }

        resp = requests.post(str(self._fetchcore_authhost), json=auth_body)

        if resp.status_code == 200:
            resp_dict = json.loads(resp.text)
            self._bearer = resp_dict.get('access_token')
            self._auth_error = False
            # Add a 10 minutes buffer for token expiration
            self._bearer_expires = time.time() + resp_dict.get('expires_in') - 600
        else:
            raise HTTPstatusCodeFailed('HTTP status Code {}'.format(resp.status_code))

    def _refresh_bearer(self) -> None:
        """Refresh bearer token before it expires."""
        while True:
            if time.time() > self._bearer_expires or self._auth_error:
                try:
                    self.auth_fetchcore()
                except requests.RequestException as err:
                    _LOGGER.error(
                        'Exception %s when connecting to FetchCore AUTH endpoint', err)
                else:
                    _LOGGER.info('Bearer token refreshed')
            else:
                time.sleep(0.5)

    @retry(retry_on_exception=identify_requests_exception, wait_fixed=1000,
           stop_max_attempt_number=5)
    def http_get(self, endpoint: str) -> Dict:
        """Perform a HTTP GET request to the given FetchCore endpoint."""
        headers = {'Authorization': 'Bearer {}'.format(self._bearer)}
        params = {'page_size': 999999}
        url = 'https://{}{}'.format(self._fetchcore_host, endpoint)
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 200:
            return json.loads(resp.text)
        elif resp.status_code == 401:
            _LOGGER.error('401 error calling %s', url)
            self._auth_error = True
            raise HTTPAuthError
        elif resp.status_code == 404:
            raise HTTPstatusNotFound
        else:
            _LOGGER.error('%s error calling %s', resp.status_code, url)
            raise HTTPstatusCodeFailed

    @retry(retry_on_exception=identify_requests_exception, wait_fixed=1000,
           stop_max_attempt_number=5)
    def http_patch(self, endpoint: str, body: Dict) -> Dict:
        """Perform a HTTP PATCH request to the given FetchCore endpoint."""
        headers = {'Authorization': 'Bearer {}'.format(self._bearer)}
        url = 'https://{}{}'.format(self._fetchcore_host, endpoint)
        resp = requests.patch(url, headers=headers, json=body)
        if resp.status_code == 200:
            return json.loads(resp.text)
        elif resp.status_code == 401:
            _LOGGER.error('401 error calling %s', url)
            self._auth_error = True
            raise HTTPAuthError
        else:
            _LOGGER.error('%s error calling %s', resp.status_code, url)
            raise HTTPstatusCodeFailed

    @retry(retry_on_exception=identify_requests_exception, wait_fixed=1000,
           stop_max_attempt_number=5)
    def http_post(self, endpoint: str, body: Dict) -> Dict:
        """Perform a HTTP POST request to the given FetchCore endpoint."""
        headers = {'Authorization': 'Bearer {}'.format(self._bearer)}
        url = 'https://{}{}'.format(self._fetchcore_host, endpoint)
        resp = requests.post(url, headers=headers, json=body)
        if resp.status_code == 201:
            return json.loads(resp.text)
        elif resp.status_code == 401:
            _LOGGER.error('401 error calling %s', url)
            self._auth_error = True
            raise HTTPAuthError
        else:
            _LOGGER.error('%s error calling %s', resp.status_code, url)
            raise HTTPstatusCodeFailed
