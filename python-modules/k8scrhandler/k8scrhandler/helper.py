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

"""Helper functions for K8s custom resource handler."""

import logging
import cProfile
import pstats
import functools

from typing import Callable, Any

_LOGGER = logging.getLogger(__name__)


def run_cprofile(func: Callable) -> Callable:
    """Decorate a function with this function to get profiled."""
    @functools.wraps(func)
    def profiled_func(*args, **kwargs) -> Any:
        """Profile the function and print the results."""
        profile = cProfile.Profile()
        _LOGGER.info('Start profiling function "%s"', func)
        profile.enable()
        try:
            return func(*args, **kwargs)
        finally:
            profile.disable()
            _LOGGER.info('Finished profiling function "%s"', func)
            pstats.Stats(profile).sort_stats('cumulative').print_stats(30)
            _LOGGER.info('End of profiling results for "%s"', func)
    return profiled_func
