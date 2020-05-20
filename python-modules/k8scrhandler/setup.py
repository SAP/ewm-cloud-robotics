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

"""Kubernetes Custom Resource Handler."""
from setuptools import find_packages, setup

REQUIRES = [
    'kubernetes==11.0.0'
    ]

setup(
    name='k8scrhandler',
    version='0.2.0',
    description='Kubernetes Custom Resource Handler',
    url='https://github.com/SAP/ewm-cloud-robotics',
    author='SAP SE',
    license='Apache License 2.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=REQUIRES
)
