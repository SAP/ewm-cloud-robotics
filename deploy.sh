#!/bin/bash

##
## Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
##
## This file is part of ewm-cloud-robotics
## (see https://github.com/SAP/ewm-cloud-robotics).
##
## This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
##



## deploy.sh can be used to push and rollout the ewm-cloud-robotics Apps to a Google Cloud Robotics cluster
## it assumes that images are already pushed (e.g. to Dockerhub as result of:
## - `skaffold run -p dockerhub`

#########################################################################################
## UTILITIES

die() {
    printf '\n%s\n' "$1" >&2
    exit 1
}

verify_kubectl_context() {
    printf "kubectl is currently configured to: \n    "
    kubectl config current-context
    read -p "Do you want to proceed (Y/n):" ver
    
    if [[ $ver = "" ]] || [[ $ver = "Y" ]] || [[ $ver = "Yes" ]] || [[ $ver = "y" ]] || [[ $ver = "yes" ]]; then
        printf "\nConfirmed: "$(kubectl config current-context)"\n"
    else
        die "ABORTED: Please configure kubectl to use the correct context."
    fi
}

package_chart() {
    chart_path=$1
    loc=$(pwd)
    printf "\nPackaging: "$chart_path"\n"

    mkdir tmp/packages
    cd "$chart_path"
    helm dependency update
    helm lint --strict .
    helm package . --destination "$loc/tmp/packages"

    cd "$loc"
    printf "\n"
}

## UTILITIES
#########################################################################################
## COMMANDS

help() {
    printf 'Usage: "./deploy.sh COMMAND <APP>"\n'
    printf '    COMMANDS:\n'
    printf '    build:     Build Docker images and push to container registry\n'
    printf '               DEFAULT:\n'
    printf '                   - "./deploy.sh build ewm-order-manager"\n'
    printf '               OPTIONS:\n'
    printf '               registry ("-r <R> | --registry <R> | --Registry=<R>"): Specify the container registry (default = "")\n'
    printf '                   - "./deploy.sh --registry=eu.gcr.io/my-gcp-project build ewm-order-manager"\n'    
    printf '                   - "./deploy.sh -r gcr.io/my-other-gcp-project build mir-mission-controller"\n'    
    printf '    push:      Package application and create an App at the Cloud Robotics application registry\n'
    printf '               DEFAULT:\n'
    printf '                   - "./deploy.sh push ewm-order-manager"\n'
    printf '               OPTIONS:\n'
    printf '               file ("-f <F> | --file <F> | --file=<F>"): Specify the App YAML file you want to use (default = "~/.config/ewm-cloud-robotics-deployments/<GCP_PROJECT>/<APP>/app.yaml")\n'
    printf '                   - "./deploy.sh --file=sample/dir/app.yaml push mir-mission-controller"\n'
    printf '                   - "./deploy.sh --f another/sample/dir/app.yaml push ewm-order-manager"\n'    
    printf '               version ("-v <V> | --version <V> | --version=<V>"): Specify the version used within the App (default = "dev")\n'
    printf '                   - "./deploy.sh --version=0.0.1 push ewm-order-manager"\n'
    printf '                   - "./deploy.sh -v 0.0.1 push mir-mission-controller"\n'
    printf '    rollout:   Create an AppRollout for your application in your Cloud Robotics cluster\n'    
    printf '               DEFAULT:\n'
    printf '                   - "./deploy.sh rollout ewm-order-manager"\n'
    printf '               OPTIONS:\n'
    printf '               file ("-f <F> | --file <F> | --file=<F>"): Specify the AppRollout YAML file you want to use for instantiation (default = "~/.config/ewm-cloud-robotics-deployments/<GCP_PROJECT>/<APP>/approllout.yaml")\n'
    printf '                   - "./deploy.sh --file=sample/dir/approllout.yaml rollout mir-mission-controller"\n'
    printf '                   - "./deploy.sh --f another/sample/dir/approllout.yaml rollout ewm-order-manager"\n'
    printf '               version ("-v <V> | --version <V> | --version=<V>"): Specify the version used within the AppRollout (default = "dev")\n'
    printf '                   - "./deploy.sh --version=0.0.1 rollout ewm-order-manager"\n'
    printf '                   - "./deploy.sh -v 0.0.1 rollout mir-mission-controller"\n'
}

build() {
    if [[ "$registry" = '' ]]; then
        registry="eu.gcr.io/"$(gcloud config get-value project)
    fi
    printf "Building images for "$1" and pushing to "$registry"\n"
    export CR=$registry
    skaffold run -p $1
    unset CR
}

push() {
    verify_kubectl_context
    if [[ "$file" = '' ]]; then
        file=~/.config/ewm-cloud-robotics-deployments/$(gcloud config get-value project)/$1/app.yaml    
    fi
    printf 'Using: '$file' to register the App '$1'\n'

    ## Update Helm dependencies for the chart
    cd helm/charts/$1/
    helm dependency update
    cd ../../../

    ## Create a temporary directory to avoid touching originals
    mkdir tmp

    cp -R helm/charts/$1 ./tmp

    ## Package Helm charts
    package_chart tmp/$1/

    ## Copy the app.yaml file prior modification
    cp $file tmp/app.yaml
    
    if [[ $(uname -s) = "Darwin" ]]; then
        inlinechart=$(cat tmp/packages/$1-0.0.1.tgz | base64 -b 0)
    
        sed -i '' -e 's#\$APP_VERSION#'$version'#' tmp/app.yaml
        sed -i '' -e 's#\$INLINE_CLOUD_CHART#'"$inlinechart"'#' tmp/app.yaml
        sed -i '' -e 's#\$INLINE_ROBOT_CHART#'"$inlinechart"'#' tmp/app.yaml
    else
        inlinechart=$(cat tmp/packages/$1-0.0.1.tgz | base64 -w 0)
        
        sed -i -e 's#\$APP_VERSION#'$version'#' tmp/app.yaml
        sed -i -e 's#\$INLINE_CLOUD_CHART#'"$inlinechart"'#' tmp/app.yaml
        sed -i -e 's#\$INLINE_ROBOT_CHART#'"$inlinechart"'#' tmp/app.yaml
    fi

    ## Apply changes to the App at apps.cloudrobotics.com/v1alpha1
    kubectl create -f tmp/app.yaml --dry-run=true -o yaml | kubectl apply -f -

    ## Clean up tmp dir
    rm -rf ./tmp
}

rollout() {
    verify_kubectl_context
    if [[ "$file" = '' ]]; then
        file=~/.config/ewm-cloud-robotics-deployments/$(gcloud config get-value project)/$1/approllout.yaml
    fi
    printf 'Using: '$file' to create an AppRollout of '$1'\n'

    # create a temporary copy prior modification
    mkdir tmp
    cp $file tmp/approllout.yaml

    ## Insert specified version, defaults to 'dev'
    if [[ $(uname -s) = "Darwin" ]]; then
        sed -i '' -e 's#\$APP_VERSION#'$version'#' tmp/approllout.yaml
    else
        sed -i -e 's#\$APP_VERSION#'$version'#' tmp/approllout.yaml
    fi
    
    ## Apply changes to the AppRollout at approllouts.apps.cloudrobotics.com/v1alpha1
    kubectl create -f tmp/approllout.yaml --dry-run=true -o yaml | kubectl apply -f -

    ## Clean up (temporary directory)
    rm -rf tmp/
}

## COMMANDS
#########################################################################################
## MAIN

#############################################
## DEFAULT OPTIONS
version='dev'
file=''
registry=''

#############################################
## GET OPTIONS
while :; do
    case $1 in
        -v | --version)
            if [ "$2" ]; then
                version=$2
                shift
            else
                die 'ERROR: "-v " | "--version " detected, but no version was specified'
            fi
            ;;
        --version=?*)
            version=${1#*=}
            ;;
        --version=)    
            die 'ERROR: "--version=" flag detected, but value was not specified.'
            ;;
        -f | --file)
            if [ "$2" ]; then
                file=$2
                shift
            else
                die 'ERROR: "-f" | "--file " detected, but no file was specified'
            fi
            ;;
        --file=?*)
            file=${1#*=}
            ;;
        --file=)    
            die 'ERROR: "--file=" flag detected, but file was not specified.'
            ;;
        -r | --registry)
            if [ "$2" ]; then
                registry=$2
                shift
            else
                die 'ERROR: "-r" | "--registry " detected, but no registry was specified'
            fi
            ;;
        --registry=?*)
            file=${1#*=}
            ;;
        --registry=)    
            die 'ERROR: "--registry=" flag detected, but registry was not specified.'
            ;;
        --)
            shift
            break
            ;;
        -?*)
            printf 'WARN: Unknown option (ignored): %s\n' "$1" >&2
            ;;
        *)
            break
    esac

    shift
done

#############################################
## CALL COMMAND (FROM REMAINING POSITIONAL PARAMETERS)
if [[ ! ""$1"" =~ ^(build|push|rollout|help)$ ]]; then
    help && exit 1
else
    if [ "$2" ]; then
        "$@"
    else
        help && die 'Please specify the application you want to '$1
    fi
fi