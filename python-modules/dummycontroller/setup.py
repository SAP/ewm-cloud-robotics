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

"""Mission and status controller for dummy robots (based upon MiR robot scenario)."""
from setuptools import find_packages, setup

REQUIRES = [
    'attrs==20.2.0',
    'requests',
    'retrying',
    'k8scrhandler'
    ]

setup(
    name='dummycontroller',
    version='0.1.0',
    description='Mission and status controller for dummy robots.',
    url='https://github.com/SAP/ewm-cloud-robotics',
    author='SAP SE',
    license='Apache License 2.0',
    packages=find_packages(),
    package_data={'dummycontroller': ['k8s-files/*']},
    include_package_data=True,
    install_requires=REQUIRES
    )
