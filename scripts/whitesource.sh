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
    sudo java -jar wss-unified-agent-19.5.1.jar -c ci/scan-modules/whitesource-fs-agent-configs/$1.config -d python-modules/$1
}

## UTILITIES
#########################################################################################
## MAIN

## Get WSS config from env
openssl aes-256-cbc -K $encrypted_27999f60500b_key -iv $encrypted_27999f60500b_iv -in whitesource-fs-agent-configs.tgz.enc -out whitesource-fs-agent-configs.tgz -d
tar -xf whitesource-fs-agent-configs.tgz

## Get WSS executable
wget https://s3.amazonaws.com/unified-agent/wss-unified-agent-19.5.1.jar

## Test all modules
execute_scan k8scrhandler
execute_scan robcoewminterface
execute_scan robcoewmtypes
execute_scan robcoewmordermanager
execute_scan robcoewmrobotcontroller

## Cleanup
rm wss-unified-agent-19.5.1.jar
rm -rf ci/scan-modules/whitesource-fs-agent-configs



