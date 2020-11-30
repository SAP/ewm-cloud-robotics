## TODO: Replace Badges
[![Coverage Status](https://coveralls.io/repos/yschiebelhut/odata-mock-server/badge.svg?branch=master)](https://coveralls.io/r/yschiebelhut/odata-mock-server?branch=master)
[![Build Status](https://travis-ci.org/yschiebelhut/odata-mock-server.svg?branch=master)](https://travis-ci.org/yschiebelhut/odata-mock-server)

These Badges are a nice way to show the current state and quality of the application. Although they're currently out of service as they point to an old repository and **do not** represent the actual state of the project.
To repare them, the ewm-sim has to be included into the ewm-cloud-robotics main build pipeline on Travis CI.


# odata-mock-server
This project is inspired by the [mockserver-server](https://github.com/ArnaudBuchholz/mockserver-server) by [Arnaud Buchholz](https://github.com/ArnaudBuchholz).
It makes use of the SAPUI5 MockServer and runs it in a standalone mode to mock a real odata service.
The aim of the project is to replace the old implementation of the ewm-sim mockserver from [EWM Cloud Robotics](https://github.com/SAP/ewm-cloud-robotics).

## Getting Started
To get the project up and running, issue the following commands in the root directory of the project:
* `npm install`
* `npm start`

## Current State of Implementation
Currently, the basic mockserver is up and running. It is served by an express web service.
This includes:
* initializing the server from the provided mockdata .json files
* serving the data as an odata service
* providing **basic** odata functionality out of the box like
    * GET,
    * PUSH,
    * PUT,
    * DELETE
  requests

### Function Imports
Additionally we are currently working to get the special functionality provided by the oData service of a real EWM system.
Current status of those function imports is:
* **fully mocked**
    * AssignRobotToWarehouseOrder
    * ConfirmWarehouseTask
    * ConfirmWarehouseTaskFirstStep
    * GetInProcessWarehouseOrders¹
    * GetNewRobotTypeWarehouseOrders¹
    * GetNewRobotWarehouseOrder
    * GetRobotWarehouseOrders
    * SendFirstConfirmationError
    * SendSecondConfirmationError
    * SetRobotStatus
    * UnassignRobotFromWarehouseOrder
    * UnsetWarehouseOrderInProcessStatus
* **WIP**
    * --
* **not implemented yet**
    * --

¹ Due to missing properties in the oData model, implementation is only for demo purpose. The returned **values will differ** from an actual EWM system. The resource type is hardcoded to RB01, the resource group to RB02.

## Additional Notes
* Speciall error cases of EWM Systems tend not to occur in a mocked environment. Among them but not limited to:
    * INTERNAL_ERROR
    * WAREHOUSE_ORDER_LOCKED
    * WAREHOUSE_ORDER_NOT_UNASSIGNED
    * WAREHOUSE_TASK_ASSIGNED (property missing in oData Entity OpenWarehouseTaskSet)