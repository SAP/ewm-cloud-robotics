#!/bin/bash

##
## Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
##
## This file is part of ewm-cloud-robotics
## (see https://github.com/SAP/ewm-cloud-robotics).
##
## This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
##

echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/v0.31.0/skaffold-linux-amd64 
chmod +x skaffold
skaffold run -p dockerhub