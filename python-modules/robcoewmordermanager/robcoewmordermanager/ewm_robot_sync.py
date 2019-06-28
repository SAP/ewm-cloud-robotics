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
import logging

from typing import Dict

from robcoewminterface.types import ODataConfig
from robcoewminterface.odata import ODataHandler
from robcoewminterface.ewm import RobotOData
from robcoewminterface.exceptions import ODataAPIException

_LOGGER = logging.getLogger(__name__)


class EWMRobotSync:
    """Sync robots with SAP EWM."""

    def __init__(self) -> None:
        """Constructor."""
        self.init_odata_fromenv()

        # SAP EWM OData handler
        self.odatahandler = ODataHandler(self.odataconfig)
        # SAP EWM OData APIs
        self.ewmrobot = RobotOData(self.odatahandler)
        # Existing robots
        self.existing_robots = {}

    def init_odata_fromenv(self) -> None:
        """Initialize OData interface from environment variables."""
        # Read environment variables
        envvar = {}
        envvar['EWM_USER'] = os.environ.get('EWM_USER')
        envvar['EWM_PASSWORD'] = os.environ.get('EWM_PASSWORD')
        envvar['EWM_HOST'] = os.environ.get('EWM_HOST')
        envvar['EWM_BASEPATH'] = os.environ.get('EWM_BASEPATH')
        envvar['EWM_AUTH'] = os.environ.get('EWM_AUTH')
        envvar['EWM_LGNUM'] = os.environ.get('EWM_LGNUM')
        envvar['EWM_RSRC_TYPE'] = os.environ.get('EWM_RSRC_TYPE')
        envvar['EWM_RSRC_GRP'] = os.environ.get('EWM_RSRC_GRP')
        # Check if complete
        for var, val in envvar.items():
            if val is None:
                raise ValueError(
                    'Environment variable "{}" is not set'.format(var))

        self.odataconfig = ODataConfig(
            host=envvar['EWM_HOST'],
            basepath=envvar['EWM_BASEPATH'],
            authorization=envvar['EWM_AUTH'],
            user=envvar['EWM_USER'],
            password=envvar['EWM_PASSWORD'])

        _LOGGER.info('Connecting to OData host "%s"', self.odataconfig.host)

        self.lgnum = envvar['EWM_LGNUM']
        self.rsrc_type = envvar['EWM_RSRC_TYPE']
        self.rsrc_grp = envvar['EWM_RSRC_GRP']

    def robco_robot_cb(self, name: str, custom_res: Dict) -> None:
        """Process Cloud Robotics robot CR."""
        # check if robot exists
        if self.existing_robots.get(name) is True:
            _LOGGER.debug(
                'Resource "%s" exists in EWM warehouse "%s"', name, self.lgnum)
        else:
            try:
                ewm_robot = self.ewmrobot.get_robot(self.lgnum, name)
            except ODataAPIException:
                _LOGGER.info(
                    'Resource "%s" not found in EWM warehouse "%s". Create it', name, self.lgnum)
                ewm_robot = self.ewmrobot.create_robot(
                    self.lgnum, name, self.rsrc_type, self.rsrc_grp)
                self.existing_robots[name] = True
                _LOGGER.info(
                    'Robot "%s" in EWM warehouse "%s" created with resource type "%s" and resource'
                    ' group "%s"', ewm_robot.rsrc, ewm_robot.lgnum, ewm_robot.rsrctype,
                    ewm_robot.rsrcgrp)
            else:
                self.existing_robots[name] = True
                _LOGGER.info(
                    'Resource "%s" exists in EWM warehouse "%s"', ewm_robot.rsrc, ewm_robot.lgnum)
