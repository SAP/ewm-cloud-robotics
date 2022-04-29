#!/bin/bash

##
## Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
##
## This file is part of ewm-cloud-robotics
## (see https://github.com/SAP/ewm-cloud-robotics).
##
## This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
##



#########################################################################################
## UTILITIES

execute_scan () {
    cd ${TRAVIS_BUILD_DIR}/python-modules/$1
    
    ## ref: https://github.com/PyCQA/bandit
    bandit -r ./ -n 3 -lll
}

## UTILITIES
#########################################################################################
## MAIN

## Install bandit
pip3 install bandit

## Test all modules
execute_scan k8scrhandler
execute_scan robcoewminterface
execute_scan robcoewmtypes
execute_scan robcoewmordermanager
execute_scan robcoewmrobotcontroller

