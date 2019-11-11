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
    type=$2
    loc=$(pwd)
    printf "\nPackaging: "$chart_path"\n"

    mkdir -p tmp/packages/$type
    cd "$chart_path"
    helm lint --strict .
    helm package . --destination "$loc/tmp/packages/$type"

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
    printf '    dummies:   Instantiate dummy robots in your cluster based upon Helm chart: helm/dummy-robots\n'    
    printf '               DEFAULT:\n'
    printf '                   - "./deploy.sh dummies install"\n'
    printf '               OPTIONS:\n'
    printf '               install: Add dummy-robots to your cluster\n'
    printf '                   - "./deploy.sh dummies install"\n'
    printf '               uninstall: Remove dummy-robots from cluster\n'
    printf '                   - "./deploy.sh dummies uninstall"\n'
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

create_package() {
    chart=$1
    type=$2

    if [ -d "helm/charts/$type/$chart" ]; then

        ## Create a temporary directory to avoid touching originals
        mkdir -p tmp/$type/$chart

        cp -R helm/charts/$type/$chart ./tmp/$type
        cp -R helm/charts/dependency-charts ./tmp/$type

        ## Update Helm dependencies for the chart
        cd tmp/$type/$chart
        helm dependency update
        cd ../../..

        ## Package Helm charts
        package_chart tmp/$type/$chart $type
    
    else
        # Create empty file that cat command in push function does not fail
        mkdir -p tmp/packages/$type
        touch tmp/packages/$type/$chart-0.0.1.tgz
    fi

}

push() {
    chart=$1

    verify_kubectl_context
    if [[ "$file" = '' ]]; then
        file=~/.config/ewm-cloud-robotics-deployments/$(gcloud config get-value project)/$chart/app.yaml    
    fi
    printf 'Using: '$file' to register the App '$chart'\n'

    ### Create cloud and robot helm packages
    create_package $chart cloud
    create_package $chart robot

    ## Copy the app.yaml file prior modification
    cp $file tmp/app.yaml
    
    if [[ $(uname -s) = "Darwin" ]]; then
        cloudchart=$(cat tmp/packages/cloud/$chart-0.0.1.tgz | base64 -b 0)
        robotchart=$(cat tmp/packages/robot/$chart-0.0.1.tgz | base64 -b 0)
    
        sed -i '' -e 's#\$APP_VERSION#'$version'#' tmp/app.yaml
        sed -i '' -e 's#\$INLINE_CLOUD_CHART#'"$cloudchart"'#' tmp/app.yaml
        sed -i '' -e 's#\$INLINE_ROBOT_CHART#'"$robotchart"'#' tmp/app.yaml
    else
        cloudchart=$(cat tmp/packages/cloud/$chart-0.0.1.tgz | base64 -w 0)
        robotchart=$(cat tmp/packages/robot/$chart-0.0.1.tgz | base64 -w 0)
        
        sed -i -e 's#\$APP_VERSION#'$version'#' tmp/app.yaml
        sed -i -e 's#\$INLINE_CLOUD_CHART#'"$cloudchart"'#' tmp/app.yaml
        sed -i -e 's#\$INLINE_ROBOT_CHART#'"$robotchart"'#' tmp/app.yaml
    fi

    ## Apply changes to the App at apps.cloudrobotics.com/v1alpha1
    kubectl create -f tmp/app.yaml --dry-run=true -o yaml | kubectl apply -f -

    ## Clean up tmp dir
    rm -rf ./tmp
}

rollout() {
    chart=$1

    verify_kubectl_context
    if [[ "$file" = '' ]]; then
        file=~/.config/ewm-cloud-robotics-deployments/$(gcloud config get-value project)/$chart/approllout.yaml
    fi
    printf 'Using: '$file' to create an AppRollout of '$chart'\n'

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

dummies() {
    verify_kubectl_context

    if [[ $1 = install ]]; then
        helm install dummy-robots ./helm/charts/dummy-robots
    elif  [[ $1 = uninstall ]]; then
        helm uninstall dummy-robots
    else 
        printf 'Please specify whether you want to install/uninstall dummy-robots.\n'
    fi
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
if [[ ! ""$1"" =~ ^(build|push|rollout|help|dummies)$ ]]; then
    help && exit 1
else
    if [ "$2" ]; then
        "$@"
    elif [ ""$1"" =  "dummies" ]; then
        "$@"
    else
        help && die 'Please specify the application you want to '$1
    fi
fi