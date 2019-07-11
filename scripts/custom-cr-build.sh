#!/bin/bash

##
## Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
##
## This file is part of ewm-cloud-robotics
## (see https://github.com/SAP/ewm-cloud-robotics).
##
## This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
##

cleanup() {
    rv=$?
    rm -rf "$tmpdir"
    exit $rv
}

tmpdir="$(mktemp)"
trap "cleanup" INT TERM EXIT
# Do things...


tag=$(date +%s)

loc=$(pwd)
cd $3

docker build -f $2 -t $1:"dirty" -t $CR"/"$1:$tag -t $CR"/"$1":latest" .
if [ $? -eq 0 ] 
then
    docker push $CR"/"$1:$tag 
    docker push $CR"/"$1":latest"

    cd "$loc"
    exit 0
else
    exit 1
fi