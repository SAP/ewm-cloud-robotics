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

"""Maps, positions etc. in FetchCore."""

import logging

from typing import Dict

import attr

from requests import RequestException

from .fetchcore import FetchInterface, HTTPstatusNotFound

_LOGGER = logging.getLogger(__name__)


@attr.s
class FetchPose:
    """Representation of a FetchCore pose."""

    name: str = attr.ib(validator=attr.validators.instance_of(str))
    id: int = attr.ib(validator=attr.validators.instance_of(int))
    x: float = attr.ib(default=0.0, validator=attr.validators.instance_of(float))
    y: float = attr.ib(default=0.0, validator=attr.validators.instance_of(float))
    theta: float = attr.ib(default=0.0, validator=attr.validators.instance_of(float))

    def get_xytheta(self) -> Dict:
        """Get dictionary with coordinates of this pose."""
        return {'x': self.x, 'y': self.y, 'theta': self.theta}


class FetchMap:
    """Representation of a FetchCore Map."""

    def __init__(self, map_id: str, fetch_api: FetchInterface) -> None:
        """Construct."""
        self.map_id = map_id
        self.name = ''
        self._fetch_api = fetch_api
        self._poses = {}

    @property
    def poses(self) -> Dict:
        """Get poses."""
        return self._poses

    def get_pose(self, name: str) -> FetchPose:
        """Get instance of one pose."""
        try:
            pose = self._poses[name]
        except KeyError:
            raise ValueError('Pose {} is unknown on map {}'.format(name, self.name))

        return pose

    def update_map(self) -> None:
        """Update map data."""
        # Call FetchcCore API
        endpoint = '/api/v1/maps/{}/'.format(self.map_id)
        try:
            fetch_map = self._fetch_api.http_get(endpoint)
        except HTTPstatusNotFound:
            _LOGGER.error('Map ID %s not found in FetchCore', self.map_id)
        except RequestException as err:
            _LOGGER.error('Exception %s when connecting to FetchCore endpoint %s', err, endpoint)
        else:
            self.name = fetch_map['name']

    def update_poses(self) -> None:
        """Update poses of this map."""
        # Call FetchcCore API
        endpoint = '/api/v1/maps/{}/annotations/poses/'.format(self.map_id)
        try:
            fetch_poses = self._fetch_api.http_get(endpoint)
        except HTTPstatusNotFound:
            _LOGGER.error('Map ID %s not found in FetchCore', self.map_id)
        except RequestException as err:
            _LOGGER.error('Exception %s when connecting to FetchCore endpoint %s', err, endpoint)
        else:
            poses = {}
            for result in fetch_poses['results']:
                pose = FetchPose(
                    result['name'], result['id'], result['x'], result['y'], result['theta'])
                poses[pose.name] = pose
            self._poses = poses
