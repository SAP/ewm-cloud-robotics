#!/bin/bash

##
## Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
##
## This file is part of ewm-cloud-robotics
## (see https://github.com/SAP/ewm-cloud-robotics).
##
## This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
##

tag=$(date +%s)
gcr="eu.gcr.io/"$(gcloud config get-value project)

loc=$(pwd)
cd "$3"

docker build -f $2 -t $1:"dirty" -t $gcr"/"$1:$tag -t $gcr"/"$1":latest" .

docker push $gcr"/"$1:$tag 
docker push $gcr"/"$1":latest"

cd "$loc"