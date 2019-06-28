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

"""OData handler for robcoewminterface."""

from typing import Optional, Dict
import logging
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
        'sap_odata_calls', 'OData calls to SAP EWM', ['endpoint', 'result'])

    def __init__(self, config: ODataConfig) -> None:
        """Constructor."""
        self._config = config
        self._csrftoken = None
        self._cookies = None

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

        # Basic authorization
        if self._config.authorization == ODataConfig.AUTH_BASIC:
            try:
                resp = requests.get(
                    uri, params=params, headers=headers, timeout=cls.TIMEOUT,
                    auth=(self._config.user, self._config.password))
            except requests.ConnectionError as err:
                _LOGGER.error(
                    'Connection error on OData GET request to URI %s: %s',
                    uri, err)
                self.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=err.__class__.__name__).inc()
                raise ConnectionError(err)
            except requests.Timeout as err:
                _LOGGER.error(
                    'Timeout on OData GET request to URI %s: %s',
                    uri, err)
                self.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=err.__class__.__name__).inc()
                raise TimeoutError(err)
            except requests.RequestException as err:
                _LOGGER.error(
                    'Error on OData GET request to URI %s: %s', uri, err)
                self.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=err.__class__.__name__).inc()
                raise IOError(err)
            else:
                # Save X-CSRF-Token and cookies
                if fetch_csrf:
                    try:
                        self._csrftoken = resp.headers['X-CSRF-Token']
                        self._cookies = resp.cookies
                    except KeyError:
                        _LOGGER.error('CSRF-Token requested but not returned')
                        raise ConnectionError(
                            'CSRF-Token requested but not returned')
                return resp
        else:
            # Other authorization types not implemented yet
            raise NotImplementedError

    def http_patch_post(
            self, mode: ['patch', 'post'], endpoint: str, jsonbody: Optional[Dict] = None,
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
        if self._csrftoken is None or self._cookies is None:
            self.http_get('', fetch_csrf=True)
        headers['X-CSRF-Token'] = self._csrftoken

        # Basic authorization
        if self._config.authorization == ODataConfig.AUTH_BASIC:
            try:
                resp = req(
                    uri, json=jsonbody, params=params, headers=headers, cookies=self._cookies,
                    timeout=cls.TIMEOUT, auth=(self._config.user, self._config.password))
            except requests.ConnectionError as err:
                _LOGGER.error(
                    'Connection error on OData %s request to URI %s: %s', mode.upper(), uri, err)
                self.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=err.__class__.__name__).inc()
                raise ConnectionError(err)
            except requests.Timeout as err:
                _LOGGER.error(
                    'Timeout on OData %s request to URI %s: %s', mode.upper(), uri, err)
                self.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=err.__class__.__name__).inc()
                raise TimeoutError(err)
            except requests.RequestException as err:
                _LOGGER.error(
                    'Error on OData %s request to URI %s: %s', mode.upper(), uri, err)
                self.odata_counter.labels(  # pylint: disable=no-member
                    endpoint=endpoint, result=err.__class__.__name__).inc()
                raise IOError(err)
            else:
                # Invalid X-CSRF-Token returns 403 error.
                # Refresh token and try again
                if resp.status_code == 403:
                    # Request new token_csrftoken_csrftoken
                    self.http_get('', fetch_csrf=True)
                    headers['X-CSRF-Token'] = self._csrftoken
                    try:
                        resp = req(
                            uri, json=jsonbody, params=params, headers=headers,
                            cookies=self._cookies, auth=(self._config.user, self._config.password))
                    except requests.ConnectionError as err:
                        _LOGGER.error(
                            'Connection error on OData %s request: %s', mode.upper(), err)
                        raise ConnectionError(err)
                    except requests.Timeout as err:
                        _LOGGER.error('Timeout on OData %s request: %s', mode.upper(), err)
                        raise TimeoutError(err)
                    except requests.RequestException as err:
                        _LOGGER.error('Error on OData %s request: %s', mode.upper(), err)
                        raise IOError(err)

                return resp
        else:
            # Other authorization types not implemented yet
            raise NotImplementedError

    def prepare_uri(
            self, endpoint: str, ids: dict, navigation: Optional[str] = None) -> str:
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


def prepare_ids_str(ids: dict) -> str:
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


def prepare_params_dict(urlparams: dict) -> dict:
    """Prepare dictionary of URL parameter."""
    if isinstance(urlparams, dict):
        params = urlparams
    else:
        params = {}

    return params
