[![Coverage Status](https://coveralls.io/repos/github/SAP/ewm-cloud-robotics/badge.svg?branch=master)](https://coveralls.io/github/SAP/ewm-cloud-robotics?branch=master)

# ewm-sim (v2)
This project is inspired by the [mockserver-server](https://github.com/ArnaudBuchholz/mockserver-server) by [Arnaud Buchholz](https://github.com/ArnaudBuchholz).
It makes use of the SAPUI5 MockServer and runs it in a standalone mode to mock the real odata service of an EWM system. By this, we now achieved a much slimmer approach compared to the former version of ewm-sim.

## Getting Started 
Note that the mockserver will not start, if the environment variables ODATA_USER and ODATA_PASSWD have not been set :warning: 

### Local
To get the project up and running, issue the following commands in the root directory of the project (docker/ewm-sim):
* `npm install`
* `npm start`

### Docker :whale:
Make sure you're in the correct directory (docker/ewm-sim).
```sh
$ docker build --tag ewm-sim:1.0 .
```
Now we need to set our environment variables, forward traffic to the host's port and run our docker image.
```sh
$ docker run -e ODATA_USER=root -e ODATA_PASSWD=123 -p 8080:8080 ewm-sim:1.0
```
(Surely the first occurance of 8080 can be replaced with any desired and free port of the host. **DO NOT** specify $ODATA_PORT when running in docker mode.)

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

* When running the project, additional configuration options can be applied via environment variables:
   * ODATA_PORT - port for the exposed http server; **only** use this if running via npm (default: 8080)
   * LOGGING_LOGTOFILE - redirect console log to files (default: false)
