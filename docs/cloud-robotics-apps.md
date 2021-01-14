# SAP EWM Cloud Robotics applications
This repository includes the applications to run the outlined SAP EWM scenarios. This chapter describes these applications which can be divided in SAP S/4 HANA based ABAP developments and containerized applications to be run in Cloud Robotics Kubernetes clusters.

## SAP EWM extension
SAP EWM extension for Cloud Robotics includes all developments required to run Cloud Robotics enabled robots in an SAP EWM controlled warehouse. It consists of an OData interface, several robot specific master data and some process enhancements. It supports two different process types: 
1. The **Move Handling Unit** process meant for robots which are able to move a Handling Unit, such as mobile shelves, autonomously 
2. The **Pick, Pack and Pass** scenario designed for collaboration of human pickers and robots. In this scenario warehouse orders are assigned to a robot which is waiting for the picker at the source bins. The picker scans the robot to start the picking process. This scenario can be found in a separate [repository](https://github.com/SAP/ewm-cloud-robotics-s4), because it includes some modifications of the system.

## EWM Cloud Robotics apps
### ewm-order-manager
The ewm-order-manager runs in the cloud cluster and represents the interface between an SAP EWM system and Cloud Robotics. It watches for available robots with free capacities and subsequently requests warehouse orders from SAP EWM OData interface. It also processes warehouse order confirmations by robots and propagates the new status to SAP EWM.

### ewm-robot-controller
The ewm-robot-controller is an app which should run per robot and includes the business logic for robots to process SAP EWM warehouse orders autonomously. It currently supports the Move Handling Unit and the robot enabled Pick, Pack and Pass scenario including error handling capabilities. It uses the Cloud Robotics mission API to control the robots. There are two distinct versions available at the moment, __ewm-robot-controller__ and __ewm-robot-controller-cloud__ that differ regarding their deployment target (robot cluster vs. cloud cluster). The robot selector within the AppRollout YAML has to be used to specify which ewm-robot-controller is responsible for certain types of robots.

## ewm-order-auction
following soon

## Mission controllers
A mission controller watches and interprets mission CRs and calls the corresponding robot APIs. Consequently, a separate mission controller is required per robot manufacturer/model. This repository contains sample implementations for a small choice of robots as well as a **dummy-mission-controller**, meant for development/testing that simply confirms every mission generated.

### mir-mission-controller 
The mir-mission-controller is deployed to robot clusters. It watches on mission CRs, interprets the contained work instructions and issues corresponding calls to the MiR API, which is specified in the mir-mission-controller rollout configurations. 

### fetch-mission-controller 
The fetch mission controller is deployed to the cloud cluster. It watches on mission CRs for all existing Fetch robots, interprets the contained work instructions and issues corresponding calls to the FetchCore instance specified in the rollout. 

## Runtime estimators
following soon

# mir-runtime-estimator
following soon

# Simulation apps
In case you have no SAP EWM system or no real robot available there simulation apps which can be used in order to still be able to demonstrate an end-to-end scenario with SAP Cloud Robotics. Both apps are deployed in the Cloud Robotics Cluster.

## ewm-sim
The ewm-sim is deployed to the cloud cluster. It mimics the EWM OData interface and includes a routine to create warehouse orders and warehouse tasks. (cf. [ewm-sim](ewm-sim.md))

## dummy-mission-controller 
The dummy-mission-controller allows testing the warehouse scenarios without deploying actual robots by adding one or more dummies to the cluster. This can be achieved by either installing the Helm chart in `helm/charts/dummy-robots` or via the `deploy.sh` script:
```bash
# Add dummy robots:
./deploy.sh dummies install

# Remove dummy robots:
./deploy.sh dummies uninstall
```
The number of robots can be varied by modifying the corresponding list in the charts' `values.yaml` file. Once the robots are installed, a suitable mission controller is required, that can be installed just as every other app (cf. [Deployment](deployment.md)):
```bash
# Build and push containers
./deploy.sh build dummy-mission-controller

# Register the app with Cloud Robotics
./deploy.sh push dummy-mission-controller

# Rollout the application
./deploy.sh rollout dummy-mission-controller
```

Since the dummy robots do not have individual clusters, they also require the [ewm-robot-controller-cloud](#ewm-robot-controller) to be pushed and rolled out. The complete Pod setup should look somewhat like this:
```
NAMESPACE                        NAME                                                             READY   STATUS    RESTARTS   AGE
app-dummy-mission-controller     dummy-mission-controller-dummy-one-784d7b988c-zdns2              1/1     Running   0          1d
app-dummy-mission-controller     dummy-mission-controller-dummy-three-6c57788c7f-dpjjc            1/1     Running   0          1d
app-dummy-mission-controller     dummy-mission-controller-dummy-two-78ddb86d85-9mtlr              1/1     Running   0          1d
app-ewm-robot-controller-cloud   robot-controller-dummy-one-758d789dcc-tqfgh                      1/1     Running   0          1d
app-ewm-robot-controller-cloud   robot-controller-dummy-three-6768897989-tpljk                    1/1     Running   0          1d
app-ewm-robot-controller-cloud   robot-controller-dummy-two-79b7cdb649-qnjrw                      1/1     Running   0          1d
```