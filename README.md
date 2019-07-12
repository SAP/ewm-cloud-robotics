# 🤖 ewm-cloud-robotics 🤖  - [![Build Status](https://travis-ci.com/SAP/ewm-cloud-robotics.svg?token=UgRpWYHRU3yqYszd3B6x&branch=master)](https://travis-ci.com/SAP/ewm-cloud-robotics)



## Description
Human-safe collaborative robots ("Cobots") are widely available from hundreds of low-cost vendors, leading to heterogenous fleets of cobots that need to easily integrate with corresponding management systems. **ewm-cloud-robotics** represents such an integration, leveraging the core of Google Cloud Robotics ([repo](https://github.com/googlecloudrobotics/core), [doc](https://googlecloudrobotics.github.io/core/)) to package and distribute [applications](#cloud-robotics-apps) for autonomous fulfilment of warehouse orders & tasks commissioned by [SAP EWM (Extended Warehouse Management](https://www.sap.com/germany/products/extended-warehouse-management.html)) just like in the video below.
<div align="center">
  <a href="https://youtu.be/CFo4-BlGO74"><img src="https://img.youtube.com/vi/CFo4-BlGO74/0.jpg" alt="EWM Cloud Robotics"></a>
</div>



## Table of Contents
- [Repository outline](#repository-outline)
- [Sample process](#sample-process)
- [Instructions](#instructions)
  - [Prerequisites](#prerequisites)
    - [MacOS](#macos)
    - [Ubuntu Linux](#ubuntu-linux)
  - [Cloud Robotics cluster](#cloud-robotics-cluster)
  - [Deployment](#deployment)
    - [Container registry](#custom-container-registry)
    - [Configuration](#configuration)
    - [Installation](#installation)
- [SAP EWM Cloud Robotics applications](#sap-ewm-cloud-robotics-applications)
  - [SAP EWM extension](#sap-ewm-extension)
  - [Cloud Robotics apps](#cloud-robotics-apps)
    - [ewm-order-manager](#ewm-order-manager)
    - [ewm-robot-controller](#ewm-robot-controller)
    - [ewm-sim](#ewm-sim)
    - [Mission controllers](#mission-controllers)
      - [mir-mission-controller](#mir-mission-controller)
      - [fetch-mission-controller](#fetch-mission-controller)
      - [dummy-mission-controller](#dummy-mission-controller)
- [Known issues & limitations](#known-issues--limitations)
- [Upcoming changes](#upcoming-changes)
- [Get involved](#get-involved)
- [License](#license)



## Repository outline
The `abap/` folder holds code to extend running SAP EWM systems with a custom OData interface, which is explained [here](#sap-ewm-extension). `python-modules/` are used to build containers (`docker/`) for [six different applications](#cloud-robotics-apps), which are packaged into Helm charts (`helm/`) and can subsequently be deployed in the [Cloud Robotics application management](https://googlecloudrobotics.github.io/core/concepts/app-management.html)(`applayer-yaml/`) as described [here](#deployment).

## Sample process
If all components are installed to their target location and linked as depicted below, process automation can start:
1. [ewm-robot-controller](#ewm-robot-controller) recognizes that the robot is available and asks for work by creating a robotrequest in their local cluster
2. robotrequests are [K8s Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/), which are synced between cloud/robot cluster by [Cloud Robotics' federation system](https://googlecloudrobotics.github.io/core/concepts/federation.html)
3. [ewm-order-manager](#ewm-order-manager) notices the new robotrequest and queries the [EWM OData interface](#SAP-EWM-extension) for a new warehouseorder
4. EWM checks open warehouseorders and one is assigned to the given robot in the system and the order sent in the response body 
5. [ewm-order-manager](#ewm-order-manager) creates a corresponding warehouseorder in the cloud
6. warehouseorders are CRs, thus it is synced to the desired robot
7. [ewm-robot-controller](#ewm-robot-controller) notices the new warehouseorder and start processing it by creating new missions for the robot
8. [\<ROBOT\>-mission-controller](#Mission-controllers) interprets the missions, executes the required actions and reports back
9. [etc.] Status changes and confirmations as well as errors are propagated back to SAP EWM
<div align="center">
  <img src="./docs/img/architecture_overview.png" alt="architecture_overview.png">
</div>


## Instructions
### Prerequisites
__ewm-cloud-robotics__ can be developed and deployed on macOS or Linux, it requires the following components to be installed:
- [install helm](https://helm.sh/docs/using_helm/#installing-helm) (tested with 2.13.1)
- [install kubectl](https://kubernetes.io/docs/tasks/tools/install-minikube/#install-kubectl) 
- [install docker](https://runnable.com/docker/getting-started/) (tested with engine v18.09.2)
- [install skaffold](https://github.com/GoogleContainerTools/skaffold) (tested with v0.31)
- [install container-structure-test](https://github.com/GoogleContainerTools/container-structure-test) (tested with v1.8.0)

If you have not yet set up a Cloud Robotics cluster, it is also required to install bazel to build it from source (ref. [Cloud Robotics cluster](#cloud-robotics-cluster)). Building Cloud Robotics was tested running Debian (Stretch) or Ubuntu (16.04 and 18.04) Linux. Build adaptations for macOS are not planned, thus Linux (e.g. Ubuntu 18.04) is mandatory if you're required deploy Cloud Robotics as well. 
- [install bazel](https://docs.bazel.build/versions/master/install.html) (tested with 0.26.0)

#### macOS
```bash
## Install Docker🐳, follow: https://runnable.com/docker/install-docker-on-macos

# Using Homebrew🍺 (https://brew.sh/):
# kubectl
brew install kubernetes-cli
# Helm
brew install kubernetes-helm
# skaffold
brew install skaffold

# Proceed by installing container-structure-test
curl -LO https://storage.googleapis.com/container-structure-test/latest/container-structure-test-darwin-amd64 && chmod +x container-structure-test-darwin-amd64 && sudo mv container-structure-test-darwin-amd64 /usr/local/bin/container-structure-test
```

#### Ubuntu Linux
```bash
## Install Docker🐳, follow: https://runnable.com/docker/install-docker-on-linux

# kubectl
sudo apt-get update && sudo apt-get install -y apt-transport-https
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee -a /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubectl

# Helm (for specific versions refer to https://helm.sh/docs/using_helm/#from-the-binary-releases)
sudo snap install helm --classic

# skaffold
curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64
chmod +x skaffold
sudo mv skaffold /usr/local/bin

# container-structure-test
curl -LO https://storage.googleapis.com/container-structure-test/latest/container-structure-test-linux-amd64 && chmod +x container-structure-test-linux-amd64 && sudo mv container-structure-test-linux-amd64 /usr/local/bin/container-structure-test
```


### Cloud Robotics cluster
Follow the instructions given [here](https://googlecloudrobotics.github.io/core/how-to/deploy-from-sources) to set up your Google Cloud Platform (GCP) project containing the Cloud Robotics Core. Pay attention to the fact that the build scripts are designed for usage on Debian (Stretch) or Ubuntu (16.04 and 18.04) Linux.

### Deployment

#### Container registry
If you have modified the images and would like to use the GCR of your project you can either use the predefined skaffold profile to build, test & push all images (1), or build images required for single cloud robotics applications (2). Within both options the container registry is dynamically generated based upon your gcloud configuration (`gcloud config get-value project` - configurable via `gcloud config set project <GCP_PROJECT>`) and host `eu.gcr.io`. Consequently, images are pushed to `eu.gcr.io/<GCP_PROJECT>/<IMAGE_NAME>`. You can also use a specific container registry (3), it is assumed that access has been established beforehand. 
```bash
# (1)
skaffold run --profile gcp

# (2)
./deploy.sh build ewm-order-manager

# (3)
./deploy.sh --registry=eu.gcr.io/my-gcp-project build ewm-order-manager
```

#### Configuration
In order to customize the settings of any of the Cloud Robotics applications, adjust the YAML of the AppRollout. By default the `deploy.sh` script uses the `approllout.yaml`/`app.yaml` files at `~/.config/ewm-cloud-robotics-deployments/<GCP_PROJECT>/<APP>/`, thus one gets the best user experience by doing the following:
```bash
# (1) create the dir
mkdir -p ~/.config/ewm-cloud-robotics-deployments/$(gcloud config get-value project)

# (2) copy the templates to the created dir
cp -R applayer-yaml/ ~/.config/ewm-cloud-robotics-deployments/$(gcloud config get-value project)

# (3) verify that app folders are in the correct place (expected print: 6 app directories)
ls ~/.config/ewm-cloud-robotics-deployments/$(gcloud config get-value project)
```
If you work on multiple projects, switch your gcloud project configuration and repeat the steps above. This way you do not interfer with any of your previous configurations. Alternatively copy the AppRollout template files to adjust the values and continue using the copy within the installation process by specifying the path via the corresponding flag (`./deploy.sh -f <path> rollout <APP>`).

#### Installation
Installing the apps to your Google Cloud Robotics cluster is a two-step process (ref. [Cloud Robotics Appliction Management](https://googlecloudrobotics.github.io/core/concepts/app-management.html)): 
1. Make your application available in the Google Cloud Robotics cluster by creating an App that describes which Helm charts should run in the respective cloud/robot targets.
2. Instantiate your application by creating an AppRollout referencing the previously created App. The AppRollout contains your specific configurations for your ewm-cloud-robotics deployment.

If you have complected the [configuration steps](#configuration), you can leverage the `deploy.sh` script as follows:
```bash
# Example: ewm-order-manager

# (1) Register 'dev' version of the ewm-order-manager App
./deploy.sh push ewm-order-manager

# (2) Create a corresponding AppRollout
./deploy.sh rollout ewm-order-manager
```
Otherwise you need to specify `approllout.yaml`/`app.yaml` files for `push` and `rollout`. You can get examples and further information about this by running `./deploy.sh help`.

## SAP EWM Cloud Robotics applications
This repository includes the applications to run the outlined SAP EWM scenarios. This chapter describes these applications which can be divided in SAP S/4 HANA based ABAP developments and containerized applications to be run in Cloud Robotics Kubernetes clusters.

### SAP EWM extension
SAP EWM extension for Cloud Robotics includes all developments required to run Cloud Robotics enabled robots in an SAP EWM controlled warehouse. It consists of an OData interface, several robot specific master data and some process enhancements. It supports two different process types: 
1. The **Move Handling Unit** process meant for robots which are able to move a Handling Unit, such as mobile shelves, autonomously 
2. The **Pick, Pack and Pass** scenario designed for collaboration of human pickers and robots. In this scenario warehouse orders are assigned to a robot which is waiting for the picker at the source bins. The picker scans the robot to start the picking process.

All foundations and the **Move Handling Unit** process are part of this repository. The robot enabled **Pick, Pack and Pass** scenario can be found in a separate [repository](https://github.com/SAP/ewm-cloud-robotics-s4), because it includes some modifications of the system.
Both repositories can be deployed to a SAP system using [abapGit](https://github.com/larshp/abapGit).


[This document](./docs/setup-EWM.md) describes the configuration steps in SAP EWM after the deployment of the code.

### Cloud Robotic apps

#### ewm-order-manager
The ewm-order-manager runs in the cloud cluster and represents the interface between an SAP EWM system and Cloud Robotics. It watches for available robots with free capacities and subsequently requests warehouse orders from SAP EWMs OData interface. It also processes warehouse order confirmations by robots and propagates the new status to SAP EWM.

#### ewm-robot-controller
The ewm-robot-controller is an app which should run on the robot and includes the business logic for robots to process SAP EWM warehouse orders autonomously. It currently supports the Move Handling Unit and the robot enabled Pick, Pack and Pass scenario including error handling capabilities. It uses the Cloud Robotics mission API to control the robots.

#### ewm-sim
🚧🚧 The ewm-sim application is currently being redesigned in order to make it slimmer and remove obsolete parts. For further information/questions refer to [this issue](https://github.com/SAP/ewm-cloud-robotics/issues/1).

#### Mission controllers
A mission controller watches and interprets mission CRs and calls the corresponding robot APIs. Consequently, a separate mission controller is required per robot manufacturer/model. This repository contains sample implementations for a small choice of robots as well as a **basic mission controller**, meant for development/testing that simply confirms every mission generated.

##### mir-mission-controller 
🚧🚧 The mir-mission-controller is currently under construction and will be added within the next couple of weeks (status June 18th, 2019). For further information/questions refer to [this issue](https://github.com/SAP/ewm-cloud-robotics/issues/3).

##### fetch-mission-controller 
🚧🚧 The fetch-mission-controller is currently under construction and will be added within the next couple of weeks (status June 18th, 2019). For further information/questions refer to [this issue](https://github.com/SAP/ewm-cloud-robotics/issues/3).

##### dummy-mission-controller 
🚧🚧 The dummy-mission-controller is currently under construction and will be added within the next couple of weeks (status June 18th, 2019). For further information/questions refer to [this issue](https://github.com/SAP/ewm-cloud-robotics/issues/3).



## Known issues & limitations
Please see [Issues](https://github.com/SAP/ewm-cloud-robotics/issues) list.



## Upcoming changes
Please refer to the Github issue board. For upcoming features check the "enhancement" label.

## Get involved
You are welcome to join forces with us in the quest to increase the number of warehouse orders & tasks fulfilled by 🤖! Simply check the [Contribution Guidelines](CONTRIBUTING.md).

## License
Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved. This file is licensed under the Apache Software License, v.2 except as noted in the [LICENSE file](LICENSE).
