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

from concurrent.futures import ThreadPoolExecutor
from typing import Dict

from cattr import structure, unstructure
from retrying import retry

from robcoewminterface.types import ODataConfig
from robcoewminterface.odata import ODataHandler
from robcoewminterface.ewm import RobotOData
from robcoewminterface.exceptions import (
    ODataAPIException, RobotNotFoundError, InternalError, InternalServerError,
    ForeignLockError)
from robcoewmtypes.robot import RobotConfigurationSpec

from .helper import retry_on_connection_error
from .robotconfigcontroller import RobotConfigurationController

_LOGGER = logging.getLogger(__name__)


class EWMRobotSync:
    """Sync robots with SAP EWM."""

    def __init__(self, robot_config: RobotConfigurationController) -> None:
        """Construct."""
        self.init_odata_fromenv()

        # SAP EWM OData handler
        self.odatahandler = ODataHandler(self.odataconfig)
        # SAP EWM OData APIs
        self.ewmrobot = RobotOData(self.odatahandler)
        # Robot config controller
        self.robot_config = robot_config
        # Existing robots
        self.existing_robots: Dict[str, RobotConfigurationSpec] = {}
        # Running robot checks
        self.running_robot_checks: Dict[str, bool] = {}
        # Thread Pool Executor
        self.executor = ThreadPoolExecutor(max_workers=1)

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
            self.running_robot_checks[name] = True
            self.executor.submit(
                self.ewm_resource_check, name, structure(
                    custom_res['spec'], RobotConfigurationSpec))

    def ewm_resource_check(self, name: str, config_spec: RobotConfigurationSpec) -> None:
        """Run EWM resource check."""
        try:
            self.create_ewm_resource(name.upper(), config_spec)
            self.update_ewm_resource(name.upper(), config_spec)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error(
                'Error checking EWM resource for robot %s: %s', name, err, exc_info=True)
        finally:
            self.running_robot_checks.pop(name, None)

    @retry(wait_fixed=10000, retry_on_exception=retry_on_connection_error)
    def create_ewm_resource(self, rsrc: str, config_spec: RobotConfigurationSpec) -> None:
        """Create a new EWM resource if it does not exist yet."""
        # check if robot exists
        robots_key = '{}.{}'.format(config_spec.lgnum, rsrc)
        if self.existing_robots.get(robots_key) is not None:
            _LOGGER.debug(
                'Resource "%s" exists in EWM warehouse "%s"', rsrc, config_spec.lgnum)
            return

        try:
            ewm_robot = self.ewmrobot.get_robot(config_spec.lgnum, rsrc)
        except ODataAPIException:
            _LOGGER.info(
                'Resource "%s" not found in EWM warehouse "%s". Create it', rsrc,
                config_spec.lgnum)
            ewm_robot = self.ewmrobot.create_robot(
                config_spec.lgnum, rsrc, config_spec.rsrctype, config_spec.rsrcgrp)
            self.existing_robots[robots_key] = config_spec
            _LOGGER.info(
                'Robot "%s" in EWM warehouse "%s" created with resource type "%s" and resource '
                'group "%s"', ewm_robot.rsrc, ewm_robot.lgnum, ewm_robot.rsrctype,
                ewm_robot.rsrcgrp)
        else:
            self.existing_robots[robots_key] = config_spec
            _LOGGER.info(
                'Resource "%s" exists in EWM warehouse "%s"', ewm_robot.rsrc, ewm_robot.lgnum)

    @retry(wait_fixed=10000, retry_on_exception=retry_on_connection_error)
    def update_ewm_resource(self, rsrc: str, config_spec: RobotConfigurationSpec) -> None:
        """Update an existing EWM resource."""
        # check if robot exists
        robots_key = '{}.{}'.format(config_spec.lgnum, rsrc)
        if self.existing_robots.get(robots_key) is None:
            _LOGGER.error(
                'Resource "%s" does not exist in EWM warehouse "%s" yet', rsrc, config_spec.lgnum)
            return

        if self.existing_robots.get(robots_key) == config_spec:
            _LOGGER.debug('Resource "%s" did not change', rsrc)
            return

        try:
            self.ewmrobot.change_robot(
                config_spec.lgnum, rsrc, rsrctype=config_spec.rsrctype,
                rsrcgrp=config_spec.rsrcgrp)
        except RobotNotFoundError:
            _LOGGER.error(
                'Robot resource %s not found in EWM warehouse %s - recreating on next run', rsrc,
                config_spec.lgnum)
            self.existing_robots.pop(robots_key, None)
        except (InternalError, InternalServerError, ForeignLockError) as err:
            _LOGGER.error(
                'Updating Robot resource %s in EWM warehouse %s failed: %s - trying again', rsrc,
                config_spec.lgnum, err)
        except ODataAPIException as err:
            _LOGGER.error('%s: restoring previous version of CR %s', err, rsrc.lower())
            self.robot_config.update_cr_spec(
                rsrc.lower(), unstructure(self.existing_robots.get(robots_key)))
        else:
            self.existing_robots[robots_key] = config_spec
            _LOGGER.info(
                'EWM robot resource %s in warehouse %s updated to resource type %s and resource '
                'group %s', rsrc, config_spec.lgnum, config_spec.rsrctype, config_spec.rsrcgrp)
