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

"""Python library to control SAP EWM order processing on a robot."""
from setuptools import find_packages, setup

REQUIRES = [
    'attrs==19.3.0',
    'cattrs==1.0.0',
    'requests',
    'transitions==0.7.2',
    'prometheus-client',
    'robcoewmtypes',
    'k8scrhandler',
    ]

setup(
    name='robcoewmrobotcontroller',
    version='0.2.0',
    description='Python library to control SAP EWM order processing on a robot',
    url='https://github.com/SAP/ewm-cloud-robotics',
    author='SAP SE',
    license='Apache License 2.0',
    packages=find_packages(),
    install_requires=REQUIRES,
    include_package_data=True
    )
