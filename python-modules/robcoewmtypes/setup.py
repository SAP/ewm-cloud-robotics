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

"""Data type library for SAP EWM Cloud Robotics."""
from setuptools import find_packages, setup

REQUIRES = [
    'attrs==20.3.0',
    'cattrs==1.2.0'
    ]

setup(
    name='robcoewmtypes',
    version='0.2.0',
    description='Data type library for SAP EWM Cloud Robotics',
    url='https://github.com/SAP/ewm-cloud-robotics',
    author='SAP SE',
    include_package_data=True,
    license='Apache License 2.0',
    packages=find_packages(),
    package_data={'robcoewmtypes': ['k8s-files/*']},
    install_requires=REQUIRES
)
