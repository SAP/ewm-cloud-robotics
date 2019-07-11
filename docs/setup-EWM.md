# Initial setup of SAP EWM system
After deployment of this repository's ABAP code there are some customzing and master data neccessary to get the processes running.
## Customizing
### Create Queues, Queue determination criteria for robots
Robots are treated as resources in SAP EWM. Thus, there should be dedicated robot _Queues_ with depend settings like _Queue determination criteria_ where warehouses order which should be processed by robots. There are two types of _Queues_:
- *Robot queue*: This is the queue to which robots should be assigned includes the warehouse orders for the robots
- *Error queue*: Robot warehouse orders where an error occured during processing are moved to this queue. It should be monitored by a warehouse operator. They could be assigned on a Resource Type level.

Example of queue defintion in customizing:
<div align="center">
  <img src="./img/ewm-queue-definition.jpg" alt="ewm-queue-definition.jpg">
</div>
Example of queue determination in customizing:
<div align="center">
  <img src="./img/ewm-queue-determination.jpg" alt="ewm-queue-determination.jpg">
</div>

### Create Resource Types for robots
There is a new attribute on _Resource Type_ level to classify a resource either as transport or as picking robot. As of now only transport robots are supported.
The attribute _Robot Type_ and the _Error Queue_ for this resource type are maintained in table view *ZEWM_TRSRC_TYP*

Example of enhancement table *ZEWM_TRSRC_TYP* for resource types in transaction SM30:
<div align="center">
  <img src="./img/ewm-view-zewm_trsrc_typ.jpg" alt="ewm-view-zewm_trsrc_typ.jpg">
</div>

## Master Data
## Create Resource Groups for robots
Create _Resource Groups_ for your robots using transaction _/SCWM/RGRP_
<div align="center">
  <img src="./img/ewm-resource-groups.jpg" alt="ewm-resource-groups.jpg">
</div>

## Maintain queue sequence for robot's Resource Group
The _Queue Sequence_ for the resource group is maintained in transaction _/SCWM/QSEQ_
<div align="center">
  <img src="./img/ewm-queue-sequence.jpg" alt="ewm-queue-sequence.jpg">
</div>

## Create Resource for robot
Resources for robots are created automatically by Cloud Robotics once they are active for the first time. But you can create and edit them too in transaction _/SCWM/RSRC_
<div align="center">
  <img src="./img/ewm-resources.jpg" alt="ewm-resources.jpg">
</div>
