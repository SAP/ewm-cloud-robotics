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

"""OData handler for robcoewminterface."""

import logging
import time

from typing import Optional, Dict

import requests

from prometheus_client import Counter

from .helper import validate_urlpath
from .types import ODataConfig

_LOGGER = logging.getLogger(__name__)


class ODataHandler:
    """Handler for OData requests."""

    TIMEOUT = 10.0

    # Prometheus logging
    odata_counter = Counter(
        'sap_ewm_odata_calls', 'OData calls to SAP EWM', ['endpoint', 'result'])

    def __init__(self, config: ODataConfig) -> None:
        """Construct."""
        self._config = config
        self._csrftoken = ''
        self._cookies: Optional[requests.cookies.RequestsCookieJar] = None
        # OAuth related
        self._access_token = ''
        self._token_type = ''
        self._token_expires = time.time()
        self.auth_error = False

    def get_access_token(self) -> None:
        """Authenticate at OAuth token endpoint."""
        cls = self.__class__

        headers = {'Accept': 'application/json'}
        body = {'client_id': self._config.clientid, 'client_secret': self._config.clientsecret}

        resp = requests.post(
            self._config.tokenendpoint, headers=headers, data=body, timeout=cls.TIMEOUT,
            auth=(self._config.clientid, self._config.clientsecret))

        if resp.status_code == 200:
            resp_dict = resp.json()
            self._access_token = resp_dict.get('access_token')
            self._token_type = resp_dict.get('token_type')
            self.auth_error = False
            # Add a 1 minute buffer for token expiration
            self._token_expires = time.time() + resp_dict.get('expires_in') - 60
        else:
            msg = 'Unable to get access token, status code: {}'.format(resp.status_code)
            _LOGGER.error(msg)
            raise requests.RequestException(msg)

    def refresh_access_token(self) -> None:
        """Refresh access token before it expires."""
        if time.time() > self._token_expires or self.auth_error:
            try:
                self.get_access_token()
            except requests.RequestException as err:
                _LOGGER.error('Exception when connecting to token endpoint: %s', err)
            else:
                _LOGGER.info('Access token of type %s refreshed', self._token_type)

    def http_get(
            self, endpoint: str, urlparams: Optional[Dict] = None, ids: Optional[Dict] = None,
            navigation: Optional[str] = None, fetch_csrf: bool = False) -> requests.Response:
        """Perform a HTTP GET request."""
        cls = self.__class__
        # Validate endpoint and navigation
        if navigation is None:
            navigation = ''
        validate_urlpath(endpoint)
        validate_urlpath(navigation)

        # Prepare dictionary for URL parameter
        params = prepare_params_dict(urlparams)

        # Prepare URI
        uri = self.prepare_uri(endpoint, ids, navigation)

        # Prepare additional headers
        headers = {'Accept': 'application/json'}
        # Fetch X-CSRF-Token if requested
        if fetch_csrf:
            headers['X-CSRF-Token'] = 'Fetch'

        try:
            # Basic authorization
            if self._config.authorization == ODataConfig.AUTH_BASIC:
                resp = requests.get(
                    uri, params=params, headers=headers, timeout=cls.TIMEOUT,
                    auth=(self._config.user, self._config.password))
            # OAuth
            else:
                if not self._access_token:
                    self.get_access_token()
                headers['Authorization'] = '{} {}'.format(self._token_type, self._access_token)
                resp = requests.get(
                    uri, params=params, headers=headers, timeout=cls.TIMEOUT)
        except requests.ConnectionError as err:
            _LOGGER.debug('Connection error on OData GET request to URI %s: %s', uri, err)
            self.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=err.__class__.__name__).inc()
            msg = '{} on OData GET request to URI {}'.format(err, uri)
            raise ConnectionError(msg) from err
        except requests.Timeout as err:
            _LOGGER.debug('Timeout on OData GET request to URI %s: %s', uri, err)
            self.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=err.__class__.__name__).inc()
            msg = '{} on OData GET request to URI {}'.format(err, uri)
            raise TimeoutError(msg) from err
        except requests.RequestException as err:
            _LOGGER.debug('Error on OData GET request to URI %s: %s', uri, err)
            self.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=err.__class__.__name__).inc()
            msg = '{} on OData GET request to URI {}'.format(err, uri)
            raise IOError(msg) from err
        else:
            # Identify authorization error
            self._identify_authorization_error(resp)

            # Save X-CSRF-Token and cookies
            if fetch_csrf:
                try:
                    self._csrftoken = resp.headers['X-CSRF-Token']
                    self._cookies = resp.cookies
                except KeyError:
                    _LOGGER.debug('CSRF-Token requested but not returned')
                    raise ConnectionError('CSRF-Token requested but not returned')
            return resp

    def http_patch_post(
            self, mode: str, endpoint: str, jsonbody: Optional[Dict] = None,
            urlparams: Optional[Dict] = None, ids: Optional[Dict] = None) -> requests.Response:
        """Perform a HTTP Patch request."""
        cls = self.__class__
        # Select correct requests mode
        if mode in ['patch', 'post']:
            # pylint: disable=no-member
            req = requests.__getattribute__(mode)
        else:
            raise NotImplementedError(
                'HTTP mode "{}" not implemented'.format(mode))

        # Validate endpoint and navigation
        validate_urlpath(endpoint)

        # Prepare dictionary for URL parameter
        params = prepare_params_dict(urlparams)

        # Prepare URI
        uri = self.prepare_uri(endpoint, ids)

        # Prepare JSON body
        if jsonbody is None:
            jsonbody = {}

        # Prepare additional headers
        headers = {'Accept': 'application/json'}
        # If no CSRF token set, request one from base path of ODATA service
        if self._csrftoken == '' or self._cookies is None:
            self.http_get('', fetch_csrf=True)
        headers['X-CSRF-Token'] = self._csrftoken

        try:
            # Basic authorization
            if self._config.authorization == ODataConfig.AUTH_BASIC:
                resp = req(
                    uri, json=jsonbody, params=params, headers=headers, cookies=self._cookies,
                    timeout=cls.TIMEOUT, auth=(self._config.user, self._config.password))
            # OAuth
            else:
                if not self._access_token:
                    self.get_access_token()
                headers['Authorization'] = '{} {}'.format(self._token_type, self._access_token)
                resp = req(
                    uri, json=jsonbody, params=params, headers=headers, cookies=self._cookies,
                    timeout=cls.TIMEOUT)
        except requests.ConnectionError as err:
            _LOGGER.debug(
                'Connection error on OData %s request to URI %s: %s', mode.upper(), uri, err)
            self.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=err.__class__.__name__).inc()
            msg = '{} on OData {} request to URI {}'.format(err, mode.upper(), uri)
            raise ConnectionError(msg) from err
        except requests.Timeout as err:
            _LOGGER.debug(
                'Timeout on OData %s request to URI %s: %s', mode.upper(), uri, err)
            self.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=err.__class__.__name__).inc()
            msg = '{} on OData {} request to URI {}'.format(err, mode.upper(), uri)
            raise TimeoutError(msg) from err
        except requests.RequestException as err:
            _LOGGER.debug(
                'Error on OData %s request to URI %s: %s', mode.upper(), uri, err)
            self.odata_counter.labels(  # pylint: disable=no-member
                endpoint=endpoint, result=err.__class__.__name__).inc()
            msg = '{} on OData {} request to URI {}'.format(err, mode.upper(), uri)
            raise IOError(msg) from err
        else:
            # Identify authorization error
            self._identify_authorization_error(resp)

            # Invalid X-CSRF-Token returns 403 error.
            # Refresh token and try again
            if resp.status_code == 403:
                # Request new token_csrftoken_csrftoken
                self.http_get('', fetch_csrf=True)
                headers['X-CSRF-Token'] = self._csrftoken
                try:
                    # Basic authorization
                    if self._config.authorization == ODataConfig.AUTH_BASIC:
                        resp = req(
                            uri, json=jsonbody, params=params, headers=headers,
                            cookies=self._cookies, auth=(self._config.user, self._config.password))
                    # OAuth
                    else:
                        if not self._access_token:
                            self.get_access_token()
                        headers[
                            'Authorization'] = '{} {}'.format(self._token_type, self._access_token)
                        resp = req(
                            uri, json=jsonbody, params=params, headers=headers,
                            cookies=self._cookies, timeout=cls.TIMEOUT)
                except requests.ConnectionError as err:
                    _LOGGER.debug(
                        'Connection error on OData %s request to URI %s: %s', mode.upper(), uri,
                        err)
                    self.odata_counter.labels(  # pylint: disable=no-member
                        endpoint=endpoint, result=err.__class__.__name__).inc()
                    msg = '{} on OData {} request to URI {}'.format(err, mode.upper(), uri)
                    raise ConnectionError(msg) from err
                except requests.Timeout as err:
                    _LOGGER.debug(
                        'Timeout on OData %s request to URI %s: %s', mode.upper(), uri, err)
                    self.odata_counter.labels(  # pylint: disable=no-member
                        endpoint=endpoint, result=err.__class__.__name__).inc()
                    msg = '{} on OData {} request to URI {}'.format(err, mode.upper(), uri)
                    raise TimeoutError(msg) from err
                except requests.RequestException as err:
                    _LOGGER.debug(
                        'Error on OData %s request to URI %s: %s', mode.upper(), uri, err)
                    self.odata_counter.labels(  # pylint: disable=no-member
                        endpoint=endpoint, result=err.__class__.__name__).inc()
                    msg = '{} on OData {} request to URI {}'.format(err, mode.upper(), uri)
                    raise IOError(msg) from err
                else:
                    # Identify authorization error
                    self._identify_authorization_error(resp)

            return resp

    def _identify_authorization_error(self, resp: requests.Response) -> None:
        """Identify authorization errors."""
        # Identify authorization error
        if resp.status_code == 401:
            self.auth_error = True
            _LOGGER.error('Authorization error at %s', resp.url)
            raise ConnectionError(
                'Authorization error at {}'.format(resp.url))
        # This is for the "feature" of certain services to respond with status code 200 and
        # redirecting to a login page at authorization errors instead of status 401
        if resp.status_code == 200 and 'application/json' not in resp.headers.get(
                'content-type', ''):
            self.auth_error = True
            msg = 'Assuming authorization error at {}, content-type not application/json'.format(
                resp.url)
            _LOGGER.debug(msg)
            raise ConnectionError(msg)

    def prepare_uri(
            self, endpoint: str, ids: Optional[Dict], navigation: Optional[str] = None) -> str:
        """Prepare URI for OData call."""
        # Create IDs string for endpoint
        ids_str = prepare_ids_str(ids)

        if ids_str is None:
            # Create URI without ID string
            uri = 'https://{h}{bp}{ep}'.format(
                h=self._config.host, bp=self._config.basepath, ep=endpoint)
        else:
            # Create URI with ID string
            uri = 'https://{h}{bp}{ep}{id}'.format(
                h=self._config.host, bp=self._config.basepath, ep=endpoint, id=ids_str)

        if navigation is not None:
            uri = uri + navigation

        return uri


def prepare_ids_str(ids: Optional[Dict]) -> Optional[str]:
    """Prepare string with EntitySet IDs."""
    if isinstance(ids, dict):
        # Generate ID string (id1='value',id2='value')
        ids_str = ','.join("{}='{}'".format(k, v) for k, v in ids.items())
        ids_str = '({})'.format(ids_str)
        return ids_str
    elif ids is None:
        return ids
    else:
        raise ValueError('"ids" parameter must be of type "dict" or "None"')


def prepare_params_dict(urlparams: Optional[Dict]) -> Dict:
    """Prepare dictionary of URL parameter."""
    if isinstance(urlparams, dict):
        params = urlparams
    else:
        params = {}

    return params
