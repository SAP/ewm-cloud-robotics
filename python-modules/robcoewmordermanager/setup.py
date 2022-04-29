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

"""Order manager for SAP EWM Cloud Robotic orders."""
from setuptools import find_packages, setup

REQUIRES = [
    'attrs==21.2.0',
    'cattrs==1.9.0',
    'retrying',
    'prometheus-client',
    'python-dateutil',
    'python-json-logger',
    'k8scrhandler',
    'robcoewmtypes',
    'robcoewminterface'
    ]

setup(
    name='robcoewmordermanager',
    version='0.2.0',
    description='Order manager for SAP EWM Cloud Robotic orders',
    url='https://github.com/SAP/ewm-cloud-robotics',
    author='SAP SE',
    license='Apache License 2.0',
    packages=find_packages(),
    install_requires=REQUIRES
)
