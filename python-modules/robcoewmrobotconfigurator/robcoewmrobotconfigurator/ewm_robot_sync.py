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

"""Sync Cloud Robotics robots with SAP EWM."""


import os
import sys
import traceback
import logging
import threading

from typing import Dict

from retrying import retry

from robcoewminterface.types import ODataConfig
from robcoewminterface.odata import ODataHandler
from robcoewminterface.ewm import RobotOData
from robcoewminterface.exceptions import ODataAPIException

from .helper import retry_on_connection_error

_LOGGER = logging.getLogger(__name__)


class EWMRobotSync:
    """Sync robots with SAP EWM."""

    def __init__(self) -> None:
        """Construct."""
        self.init_odata_fromenv()

        # SAP EWM OData handler
        self.odatahandler = ODataHandler(self.odataconfig)
        # SAP EWM OData APIs
        self.ewmrobot = RobotOData(self.odatahandler)
        # Existing robots
        self.existing_robots: Dict[str, bool] = {}
        # Running robot checks
        self.running_robot_checks: Dict[str, threading.Thread] = {}

    def init_odata_fromenv(self) -> None:
        """Initialize OData interface from environment variables."""
        # Read environment variables
        envvar = {}
        envvar['EWM_HOST'] = os.environ.get('EWM_HOST')
        envvar['EWM_BASEPATH'] = os.environ.get('EWM_BASEPATH')
        envvar['EWM_AUTH'] = os.environ.get('EWM_AUTH')
        if envvar['EWM_AUTH'] == ODataConfig.AUTH_BASIC:
            envvar['EWM_USER'] = os.environ.get('EWM_USER')
            envvar['EWM_PASSWORD'] = os.environ.get('EWM_PASSWORD')
        else:
            envvar['EWM_CLIENTID'] = os.environ.get('EWM_CLIENTID')
            envvar['EWM_CLIENTSECRET'] = os.environ.get('EWM_CLIENTSECRET')
            envvar['EWM_TOKENENDPOINT'] = os.environ.get('EWM_TOKENENDPOINT')
        # Check if complete
        for var, val in envvar.items():
            if val is None:
                raise ValueError(
                    'Environment variable "{}" is not set'.format(var))

        # OData config
        if envvar['EWM_AUTH'] == ODataConfig.AUTH_BASIC:
            self.odataconfig = ODataConfig(
                host=envvar['EWM_HOST'],
                basepath=envvar['EWM_BASEPATH'],
                authorization=envvar['EWM_AUTH'],
                user=envvar['EWM_USER'],
                password=envvar['EWM_PASSWORD'],
                )
        else:
            self.odataconfig = ODataConfig(
                host=envvar['EWM_HOST'],
                basepath=envvar['EWM_BASEPATH'],
                authorization=envvar['EWM_AUTH'],
                clientid=envvar['EWM_CLIENTID'],
                clientsecret=envvar['EWM_CLIENTSECRET'],
                tokenendpoint=envvar['EWM_TOKENENDPOINT'],
                )

        _LOGGER.info('Connecting to OData host "%s"', self.odataconfig.host)

    def robotconfiguration_cb(self, name: str, custom_res: Dict) -> None:
        """Process robot configuration CR."""
        # Create new thread to check EWM resources if not running yet
        if name not in self.running_robot_checks:
            self.running_robot_checks[name] = threading.Thread(
                target=self.ewm_resource_check, args=(name, custom_res))
            self.running_robot_checks[name].start()

    def ewm_resource_check(self, name: str, custom_res: Dict) -> None:
        """Run EWM resource check."""
        try:
            self.create_ewm_resource(
                name, custom_res['spec']['lgnum'], custom_res['spec']['rsrctype'],
                custom_res['spec']['rsrcgrp'])
        except Exception:  # pylint: disable=broad-except
            exc_info = sys.exc_info()
            _LOGGER.error(
                'Error checking EWM resource for robot %s: "%s" / "%s" - TRACEBACK: %s',
                name, exc_info[0], exc_info[1], traceback.format_exception(*exc_info))
        finally:
            self.running_robot_checks.pop(name, None)

    @retry(wait_fixed=10000, retry_on_exception=retry_on_connection_error)
    def create_ewm_resource(self, name: str, lgnum: str, rsrc_type: str, rsrc_grp: str) -> None:
        """Create a new EWM resource if it does not exist yet."""
        # check if robot exists
        robots_key = '{}-{}'.format(lgnum, name)
        if self.existing_robots.get(robots_key) is True:
            _LOGGER.debug(
                'Resource "%s" exists in EWM warehouse "%s"', name, lgnum)
        else:
            try:
                ewm_robot = self.ewmrobot.get_robot(lgnum, name)
            except ODataAPIException:
                _LOGGER.info(
                    'Resource "%s" not found in EWM warehouse "%s". Create it', name, lgnum)
                ewm_robot = self.ewmrobot.create_robot(lgnum, name, rsrc_type, rsrc_grp)
                self.existing_robots[robots_key] = True
                _LOGGER.info(
                    'Robot "%s" in EWM warehouse "%s" created with resource type "%s" and resource'
                    ' group "%s"', ewm_robot.rsrc, ewm_robot.lgnum, ewm_robot.rsrctype,
                    ewm_robot.rsrcgrp)
            else:
                self.existing_robots[robots_key] = True
                _LOGGER.info(
                    'Resource "%s" exists in EWM warehouse "%s"', ewm_robot.rsrc, ewm_robot.lgnum)
