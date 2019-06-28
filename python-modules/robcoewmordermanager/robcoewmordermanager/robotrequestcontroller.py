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

"""K8s custom resource handler for new warehouse orders."""

import sys
import traceback
import logging

from typing import Dict

from robcoewmtypes.helper import create_robcoewmtype_str, get_sample_cr
from robcoewmtypes.robot import RequestFromRobot, RequestFromRobotStatus

from robcoewminterface.exceptions import NoOrderFoundError, RobotHasOrderError

from k8scrhandler.k8scrhandler import K8sCRHandler, k8s_cr_callback

_LOGGER = logging.getLogger(__name__)

ROBOTREQUEST_TYPE = create_robcoewmtype_str(RequestFromRobot('lgnum', 'rsrc'))


class RobotRequestController(K8sCRHandler):
    """Handle K8s custom resources."""

    def __init__(self) -> None:
        """Constructor."""
        template_cr = get_sample_cr('robotrequest')

        labels = {}
        super().__init__(
            'sap.com',
            'v1',
            'robotrequests',
            'default',
            template_cr,
            labels
        )

    @k8s_cr_callback
    def _callback(
            self, name: str, labels: Dict, operation: str, custom_res: Dict) -> None:
        """Process custom resource operation."""
        _LOGGER.debug('Handling %s on %s', operation, name)
        # Run all registered callback functions
        try:
            # Check if robot request has to be processed in callback.
            process_cr = self._robot_request_precheck(name, custom_res)
            # If pre check was successfull set iterate over all callbacks
            if process_cr:
                for callback in self.callbacks[operation].values():
                    callback(
                        ROBOTREQUEST_TYPE, name, custom_res['spec'],
                        custom_res.get('status', {}).get('data', {}))
        except NoOrderFoundError:
            _LOGGER.debug(
                'No warehouse order was found for robot "%s" - try again later', name)
        except RobotHasOrderError:
            _LOGGER.debug(
                'Warehouse order still assigned to robot "%s" - try again later', name)
        except (ConnectionError, TimeoutError, IOError) as err:
            _LOGGER.error(
                'Error connecting to SAP EWM Backend: "%s" - try again later', err)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.error('Error while processing custom resource %s', name)
            exc_info = sys.exc_info()
            _LOGGER.error(
                '%s/%s: Error in callback - Exception: "%s" / "%s" - TRACEBACK: %s', self.group,
                self.plural, exc_info[0], exc_info[1], traceback.format_exception(*exc_info))
        else:
            _LOGGER.debug('Successfully processed custom resource %s', name)

    def _robot_request_precheck(self, name: str, custom_res: Dict) -> bool:
        """Check if robot request has to be processed in callback."""
        # If not processed yet, iterate over all trigger arrays
        cr_status = custom_res.get('status') if isinstance(custom_res.get('status'), dict) else {}
        if cr_status.get('status') == RequestFromRobotStatus.STATE_PROCESSED:
            return False

        return True

    def update_request(
            self, name: str, dtype: str, status_data: Dict,
            process_complete: bool = False) -> bool:
        """Cleanup robotrequest when work when it was processed."""
        status = {}
        status['data'] = status_data
        if process_complete:
            status['status'] = RequestFromRobotStatus.STATE_PROCESSED
        else:
            status['status'] = RequestFromRobotStatus.STATE_RUNNING
        if self.check_cr_exists(name):
            return self.update_cr_status(name, status)
        else:
            return False
