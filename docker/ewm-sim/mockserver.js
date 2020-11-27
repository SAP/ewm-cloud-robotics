"use strict"

const logger = require('./lib/log.js')
var appServer

module.exports = {
	init() {
		logger.info("initializing server")
		require('node-ui5/factory')({
			exposeAsGlobals: true,
			resourceroots: {
				myApp: __dirname
			}
		}).then(() => {
			process.on('unhandledRejection', error => {
				logger.error('unhandledRejection: ' + error.message)
			})
			sap.ui.require([
				"jquery.sap.global",
				"sap/ui/core/util/MockServer"
			], function (jQuery, MockServer) {
				logger.info("import of node-ui5 successful!")


				// Begin of function imports
				//#region function Imports

				var SendFirstConfirmationError = function (oXhr, sUrlParams) {
					logger.debug("invoking SendFirstConfirmationError")
					logger.debug("sUrlParams: " + sUrlParams)
					// Expected parameters: Lgnum, Rsrc, Who
					var oUrlParams = sUrlParams.split("&").reduce(function (prev, curr, i, arr) {
						var p = curr.split("=")
						prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
						return prev
					}, {})
					logger.debug("oUrlParams: " + JSON.stringify(oUrlParams))
					var uri = ""


					// 1. Check if the robot resource exists in EWM
					// yes: continue
					// no: return business_error: ROBOT_NOT_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='" + oUrlParams.Lgnum + "',Rsrc='" + oUrlParams.Rsrc + "')"
					logger.debug("checking if robot resource exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that robot resource " + oUrlParams.Rsrc + " exists")
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("robot resource " + oUrlParams.Rsrc + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "ROBOT_NOT_FOUND" } })
							return true
						}
					})


					// 2. Check if the who exists in EWM
					// yes: continue
					// no: return business_error: NO_ORDER_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + oUrlParams.Who + "')"
					logger.debug("checking if warehouseorder exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that warehouseorder " + oUrlParams.Who + " exists")
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("warehouseorder " + oUrlParams.Who + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
							return true
						}
					})


					// 3. Unassign - Set Status="", Queue="ERROR" and Rsrc="" 
					// yes: return who
					// no: return business_error: WHO_NOT_UNASSIGNED
					let who = {}
					who.Status = ""
					who.Queue = "ERROR"
					who.Rsrc = ""
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + oUrlParams.Who + "')"
					logger.debug("updating entity at " + uri)
					jQuery.ajax({
						url: uri,
						method: 'PATCH',
						dataType: 'json',
						async: false,
						data: JSON.stringify(who),
						success: function () {
							logger.debug("updated entity Status, Queue and Rsrc")
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_ORDER_NOT_UNASSIGNED" } })
							return true
						}
					})

					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + oUrlParams.Who + "')"
					logger.debug("checking if warehouseorder exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							oXhr.respondJSON(200, {}, res)
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("warehouseorder " + oUrlParams.Who + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_ORDER_NOT_UNASSIGNED" } })
						}
					})
					return true
				}

				var SendSecondConfirmationError = function (oXhr, sUrlParams) {
					logger.debug("invoking SendSecondConfirmationError")
					logger.debug("sUrlParams: " + sUrlParams)
					// Expected parameters: Lgnum, Rsrc, Who
					var oUrlParams = sUrlParams.split("&").reduce(function (prev, curr, i, arr) {
						var p = curr.split("=")
						prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
						return prev
					}, {})
					logger.debug("oUrlParams: " + JSON.stringify(oUrlParams))
					var uri = ""


					// 1. Check if the robot resource exists in EWM
					// yes: continue
					// no: return business_error: ROBOT_NOT_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='" + oUrlParams.Lgnum + "',Rsrc='" + oUrlParams.Rsrc + "')"
					logger.debug("checking if robot resource exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that robot resource " + oUrlParams.Rsrc + " exists")
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("robot resource " + oUrlParams.Rsrc + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "ROBOT_NOT_FOUND" } })
							return true
						}
					})


					// 2. Check if the who exists in EWM
					// yes: continue
					// no: return business_error: NO_ORDER_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + oUrlParams.Who + "')"
					logger.debug("checking if warehouseorder exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that warehouseorder " + oUrlParams.Who + " exists")
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("warehouseorder " + oUrlParams.Who + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
							return true
						}
					})


					// 3.Queue="ERROR" 
					// yes: return who
					// no: return business_error: QUEUE_NOT_CHANGED
					let who = {}

					who.Queue = "ERROR"

					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + oUrlParams.Who + "')"
					logger.debug("updating entity at " + uri)
					jQuery.ajax({
						url: uri,
						method: 'PATCH',
						dataType: 'json',
						async: false,
						data: JSON.stringify(who),
						success: function () {
							logger.debug("updated entity Queue")
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							oXhr.respondJSON(404, {}, { "error": { "code": "QUEUE_NOT_CHANGED" } })
							return true
						}
					})

					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + oUrlParams.Who + "')"
					logger.debug("checking if warehouseorder exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							oXhr.respondJSON(200, {}, res)
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("warehouseorder " + oUrlParams.Who + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "QUEUE_NOT_CHANGED" } })
						}
					})
					return true
				}


				var GetNewRobotWarehouseOrder = function (oXhr, sUrlParams) {
					logger.debug("invoking GetNewRobotWarehouseOrder")
					// Expected parameters: Lgnum, Rsrc
					logger.debug("sUrlParams: " + sUrlParams)
					// Expected parameters: Lgnum, Rsrc, Who
					var oUrlParams = sUrlParams.split("&").reduce(function (prev, curr, i, arr) {
						var p = curr.split("=")
						prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
						return prev
					}, {})
					logger.debug("oUrlParams: " + JSON.stringify(oUrlParams))
					var uri = ""


					// 1. Check if the robot resource exists in EWM
					// yes: continue
					// no: return business_error: ROBOT_NOT_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='" + oUrlParams.Lgnum + "',Rsrc='" + oUrlParams.Rsrc + "')"
					logger.debug("checking if robot resource exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that robot resource " + oUrlParams.Rsrc + " exists")
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("robot resource " + oUrlParams.Rsrc + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "ROBOT_NOT_FOUND" } })
							return true
						}
					})


					// 2. Check if a warehouse order is assigned to the robot
					// yes: return business_error: ROBOT_HAS_ORDER
					// no: continue
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet?$filter=Rsrc eq '" + oUrlParams.Rsrc + "' and Status eq 'D'"
					logger.debug("checking if unconfirmed warehouseorder is assigned to robot: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							if (res.d.results.length > 0) {
								logger.debug("found incomplete warehouseorders linked to robot " + oUrlParams.Rsrc)
								oXhr.respondJSON(404, {}, { "error": { "code": "ROBOT_HAS_ORDER" } })
								return true
							} else {
								logger.debug("no warehouseorders associated with robot " + oUrlParams.Rsrc)
							}
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							oXhr.respondJSON(404, {}, { "error": { "code": "ROBOT_HAS_ORDER" } })
							return true
						}
					})


					// 3 Check if there is a warehouse order with Status="", Queue!="ERROR" and not assigned to any robot
					// yes: return warehouse order of type WarehouseOrder
					//    3.1 Set warehouse order in process "Status": "D"
					//    3.2 Assign robot resource to warehouse order "Rsrc"
					// no: return business_error: NO_ORDER_FOUND
					var who = ""
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet?$filter=Rsrc eq '' and Status eq ''"
					logger.debug("checking for open warehouseorder that hasn't been assigned yet")
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug(res)
							if (res.d.results.length > 0) {
								logger.debug("found open unassigned warehouseorders")
								who = res.d.results.find((element) => {
									return (element.Queue !== "ERROR")
								})
							} else {
								logger.debug("no open unassigned warehouseorder available")
								oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
								return true
							}
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
							return true
						}
					})


					// Assign who to robot and update status
					who.Status = "D"
					who.Rsrc = oUrlParams.Rsrc
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + who.Who + "')"
					logger.debug("updating entity at " + uri)
					jQuery.ajax({
						url: uri,
						method: 'MERGE',
						data: JSON.stringify(who),
						async: false,
						success: function (res) {
							logger.debug("updated entity Status and Rsrc")
							oXhr.respondJSON(200, {}, { "d": who })
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
						}
					})
					return true
				}


				var ConfirmWarehouseTaskFirstStep = function (oXhr, sUrlParams) {
					logger.debug("invoking ConfirmWarehouseTaskFirstStep")
					// Expected parameters: Lgnum, Tanum, Rsrc
					var oUrlParams = sUrlParams.split("&").reduce(function (prev, curr, i, arr) {
						var p = curr.split("=")
						prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
						return prev
					}, {})
					var uri = ""
					var who = ""
					var wht = null


					// 1. Verify that warehousetask exists
					// yes: continue
					// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet(Lgnum='" + oUrlParams.Lgnum + "',Tanum='" + oUrlParams.Tanum + "')"
					logger.debug("checking if openwarehousetask exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that openwarehousetask " + oUrlParams.Tanum + " exists for who " + res.d.Who)
							who = res.d.Who
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("openwarehousetask " + oUrlParams.Tanum + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
							return true
						}
					})


					// 2. Verify that warehouseorder Status is not "C"
					// yes: continue
					// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + who + "')"
					logger.debug("checking if warehouseorder exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that warehouseorder " + who + " exists")
							if (res.d.Status !== "C") {
								logger.debug("warehouseorder is not yet confirmed")
							} else {
								logger.debug("warehouseorder has already been confirmed")
								oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
								return true
							}
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("warehouseorder " + who + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
							return true
						}
					})


					// 3. Verify that warehousetask Tostat is not "C"
					// yes: continue
					// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet(Lgnum='" + oUrlParams.Lgnum + "',Tanum='" + oUrlParams.Tanum + "')"
					logger.debug("checking if openwarehousetask " + oUrlParams.Tanum + " Tostat is 'C' at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							if (res.d.Tostat !== "C") {
								logger.debug("warehousetask is not yet confirmed")
								wht = res.d
							} else {
								logger.debug("warehousetask has already been confirmed")
								oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
								return true
							}
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("openwarehousetask " + oUrlParams.Tanum + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
							return true
						}
					})


					// 4. Delete "Vltyp", "VlBer", "Vlpla" From warehousetask 
					// yes: return warehousetask
					// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
					wht.Vltyp = ""
					wht.Vlber = ""
					wht.Vlpla = ""
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet(Lgnum='" + oUrlParams.Lgnum + "',Tanum='" + oUrlParams.Tanum + "')"
					logger.debug("deleting 'Vltyp', 'Vlber' and 'Vlpla' from openwarehousetask " + oUrlParams.Tanum + " at: " + uri)
					jQuery.ajax({
						url: uri,
						method: 'MERGE',
						data: JSON.stringify(wht),
						async: false,
						success: function (res) {
							logger.debug("deleted 'Vltyp', 'Vlber' and 'Vlpla' from warehousetask " + oUrlParams.Tanum)
							oXhr.respondJSON(200, {}, { "d": wht })
						},
						error: function (err) {
							logger.debug("unable to delete 'Vltyp', 'Vlber' and 'Vlpla' from " + oUrlParams.Tanum)
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
						}
					})
					return true
				}


				var ConfirmWarehouseTask = function (oXhr, sUrlParams) {
					logger.debug("invoking ConfirmWarehouseTask")
					// Expected parameters: Lgnum, Tanum
					var oUrlParams = sUrlParams.split("&").reduce(function (prev, curr, i, arr) {
						var p = curr.split("=")
						prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
						return prev
					}, {})
					var uri = ""
					var who = null
					var whoObj = null
					var wht = null


					// 1. Verify that warehousetask exists
					// yes: continue
					// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet(Lgnum='" + oUrlParams.Lgnum + "',Tanum='" + oUrlParams.Tanum + "')"
					logger.debug("checking if openwarehousetask exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that openwarehousetask " + oUrlParams.Tanum + " exists for who " + res.d.Who)
							who = res.d.Who
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("openwarehousetask " + oUrlParams.Tanum + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
							return true
						}
					})


					// 2. Verify that warehouseorder Status is not "C"
					// yes: continue
					// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + who + "')"
					logger.debug("checking if warehouseorder exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that warehouseorder " + who + " exists")
							whoObj = res.d
							if (res.d.Status !== "C") {
								logger.debug("warehouseorder is not yet confirmed")
							} else {
								logger.debug("warehouseorder has already been confirmed")
								oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
								return true
							}
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("warehouseorder " + who + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
							return true
						}
					})


					// 3. Verify that warehousetask Tostat is not "C"
					// yes: continue
					// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet(Lgnum='" + oUrlParams.Lgnum + "',Tanum='" + oUrlParams.Tanum + "')"
					logger.debug("checking if openwarehousetask " + oUrlParams.Tanum + " Tostat is 'C' at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							if (res.d.Tostat !== "C") {
								logger.debug("warehousetask is not yet confirmed")
								wht = res.d
							} else {
								logger.debug("warehousetask has already been confirmed")
								oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
								return true
							}
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("openwarehousetask " + oUrlParams.Tanum + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
							return true
						}
					})


					// 4. Set warehousetask Tostat:"C" to C
					// yes: continue
					// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
					wht.Tostat = "C"
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet(Lgnum='" + oUrlParams.Lgnum + "',Tanum='" + oUrlParams.Tanum + "')"
					logger.debug("deleting 'Vltyp', 'Vlber' and 'Vlpla' from openwarehousetask " + oUrlParams.Tanum + " at: " + uri)
					jQuery.ajax({
						url: uri,
						method: 'MERGE',
						data: JSON.stringify(wht),
						async: false,
						success: function (res) {
							logger.debug("set 'Tostat' to 'C' for warehousetask " + oUrlParams.Tanum)
						},
						error: function (err) {
							logger.debug("unable to set 'Tostat' to 'C' for warehousetask " + oUrlParams.Tanum)
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
							return true
						}
					})


					// 5. Check tasks in warehouseorder, if all Tostat="C" -> set Status="C"
					// yes: 
					// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet?$filter=Who eq '" + who + "'"
					logger.debug("checking all tasks for who " + who + " regarding their 'Tostat'")
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found warehousetasks for who " + who + ", checking Tostat")

							var allTasksComplete = true
							res.d.results.forEach((task) => {
								logger.debug(task)
								if (task.Tostat !== "C") {
									allTasksComplete = false
								}
							})
							if (!allTasksComplete) {
								logger.debug("there are still open warehousetasks for who " + who)
								oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
								return true
							}
						},
						error: function (err) {
							logger.debug("unable to retrieve warehousetasks having who " + who)
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
							return true
						}
					})


					// 5.1. Set Who Status to "C"
					// yes:  return whoObj
					// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
					whoObj.Status = "C"
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + who + "')"
					logger.debug("setting Status to 'C' for warehouseorder " + who + " at: " + uri)
					jQuery.ajax({
						url: uri,
						method: 'MERGE',
						data: JSON.stringify(whoObj),
						async: false,
						success: function (res) {
							logger.debug("set 'Status' to 'C' for warehouseorder " + who)
							oXhr.respondJSON(200, {}, { "d": whoObj })
						},
						error: function (err) {
							logger.debug("unable to set 'Status' to 'C' for warehouseorder " + who)
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
						}
					})
					return true
				}


				var GetRobotWarehouseOrders = function (oXhr, sUrlParams) {
					logger.debug("invoking GetRobotWarehouseOrders")
					// Expected parameters: Lgnum, Rsrc
					logger.debug("sUrlParams: " + sUrlParams)
					// Expected parameters: Lgnum, Rsrc, Who
					var oUrlParams = sUrlParams.split("&").reduce(function (prev, curr, i, arr) {
						var p = curr.split("=")
						prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
						return prev
					}, {})
					logger.debug("oUrlParams: " + JSON.stringify(oUrlParams))
					var uri = ""


					// 1. Check if the robot resource exists in EWM
					// yes: continue
					// no: return business_error: ROBOT_NOT_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='" + oUrlParams.Lgnum + "',Rsrc='" + oUrlParams.Rsrc + "')"
					logger.debug("checking if robot resource exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that robot resource " + oUrlParams.Rsrc + " exists")
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("robot resource " + oUrlParams.Rsrc + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "ROBOT_NOT_FOUND" } })
							return true
						}
					})


					// 2. Check if a warehouse order is assigned to the robot
					// yes: return warehouse order of type WarehouseOrder
					// no: return business_error: NO_ORDER_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet?$filter=Rsrc eq '" + oUrlParams.Rsrc + "' and Status eq 'D'"
					logger.debug("checking if unconfirmed warehouseorder is assigned to robot: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							if (res.d.results.length > 0) {
								logger.debug("found incomplete warehouseorders linked to robot " + oUrlParams.Rsrc)
								oXhr.respondJSON(200, {}, res)
								return true
							} else {
								oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
							}
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
							return true
						}
					})
				}


				var SetRobotStatus = function (oXhr, sUrlParams) {
					logger.debug("invoking SetRobotStatus")
					logger.debug("sUrlParams: " + sUrlParams)
					var oUrlParams = sUrlParams.split("&").reduce(function (prev, curr, i, arr) {
						var p = curr.split("=")
						prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
						return prev
					}, {})
					logger.debug("oUrlParams: " + JSON.stringify(oUrlParams))
					var uri = ""


					// 1. Check if the robot resource exists in EWM
					// yes: continue
					// no: return business_error: ROBOT_NOT_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='" + oUrlParams.Lgnum + "',Rsrc='" + oUrlParams.Rsrc + "')"
					logger.debug("checking if robot resource exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that robot resource " + oUrlParams.Rsrc + " exists")
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("robot resource " + oUrlParams.Rsrc + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "ROBOT_NOT_FOUND" } })
							return true
						}
					})


					// 2. Check if parameter "ExccodeOverall" has the right length
					// yes: set status for robot (and return robot?)
					// no: return business_error: ROBOT_STATUS_NOT_SET
					if (oUrlParams.ExccodeOverall) {
						if (oUrlParams.ExccodeOverall.length <= 4) {
							jQuery.ajax({
								url: uri, // set at 1.
								method: 'PUT',
								data: JSON.stringify(oUrlParams),
								async: false,
								success: function (res) {
									oXhr.respondJSON(200, {}, res)
								},
								error: function (err) {
									logger.debug(JSON.stringify(err))
									oXhr.respondJSON(404, {}, { "error": { "code": "ROBOT_STATUS_NOT_SET" } })
								}
							})
						}
					}
					// else respond with error
					oXhr.respondJSON(404, {}, { "error": { "code": "ROBOT_STATUS_NOT_SET" } })
				}


				var AssignRobotToWarehouseOrder = function (oXhr, sUrlParams) {
					logger.debug("invoking AssignRobotToWarehouseOrder")
					logger.debug("sUrlParams: " + sUrlParams)
					var oUrlParams = sUrlParams.split("&").reduce(function (prev, curr, i, arr) {
						var p = curr.split("=")
						prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
						return prev
					}, {})
					logger.debug("oUrlParams: " + JSON.stringify(oUrlParams))
					var uri = ""


					// 1. Check if the robot resource exists in EWM
					// yes: continue
					// no: return business_error: ROBOT_NOT_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='" + oUrlParams.Lgnum + "',Rsrc='" + oUrlParams.Rsrc + "')"
					logger.debug("checking if robot resource exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that robot resource " + oUrlParams.Rsrc + " exists")
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("robot resource " + oUrlParams.Rsrc + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "ROBOT_NOT_FOUND" } })
							return true
						}
					})


					// 2. Check if the WarehouseOrder exists in EWM
					// yes: continue
					// no: return business_error: NO_ORDER_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + oUrlParams.Who + "')"
					logger.debug("checking if WHO exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that WHO " + oUrlParams.Who + " exists")

							// 3. check if WHO is already assigned to a robot
							// yes: return business_error: WAREHOUSE_ORDER_ASSIGNED
							// no: continue
							if (res.d.Rsrc && res.d.Rsrc !== "") {
								oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_ORDER_ASSIGNED" } })
								return true
							} else {
								// Actually assign robot to WHO
								jQuery.ajax({
									url: uri,
									method: 'PUT',
									data: JSON.stringify(oUrlParams),
									async: false,
									success: function (res) {
										oXhr.respondJSON(200, {}, res)
									},
									error: function (err) {
										logger.debug(JSON.stringify(err))
										oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
									}
								})
							}
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("WHO " + oUrlParams.Who + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
							return true
						}
					})

					// TODO: implement WHT_ASSIGNED


				}


				var GetInProcessWarehouseOrders = function (oXhr, sUrlParams) {
					logger.debug("invoking GetInProcessWarehouseOrders")
					// Expected parameters: Lgnum, Rsrc, RsrcType
					var oUrlParams = sUrlParams.split("&").reduce(function (prev, curr, i, arr) {
						var p = curr.split("=")
						prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
						return prev
					}, {})
					logger.debug("oUrlParams: " + JSON.stringify(oUrlParams))
					var uri = ""


					// 1. Check if Resourcetype is RB01
					// yes: response with status 200
					// no: return business_error: RESOURCE_TYPE_IS_NO_ROBOT
					if (oUrlParams.RsrcType != "RB01") {
						oXhr.respondJSON(404, {}, { "error": { "code": "RESOURCE_TYPE_IS_NO_ROBOT" } })
						return true
					}


					// 2. Check if an order in process exists with no ressource assigned
					// yes: return warehouse order of type WarehouseOrder with status 'D'
					// no: return business_error: NO_ORDER_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet?$filter=Lgnum eq '" + oUrlParams.Lgnum + "' and Status eq 'D' and Rsrc eq ''"
					logger.debug("checking if order exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							if (res.d.results.length == 0) {
								oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
								return true
							} else {
								oXhr.respondJSON(200, {}, res)
							}
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
							return true
						}
					})
				}


				var UnsetWarehouseOrderInProcessStatus = function (oXhr, sUrlParams) {
					logger.debug("invoking UnsetWarehouseOrderInProcessStatus")
					// Expected parameters: Lgnum, Who
					logger.debug("sUrlParams: " + sUrlParams)
					var oUrlParams = sUrlParams.split("&").reduce(function (prev, curr, i, arr) {
						var p = curr.split("=")
						prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
						return prev
					}, {})
					logger.debug("oUrlParams: " + JSON.stringify(oUrlParams))
					var uri = ""


					// 1. Check if the Who exists in WhoSet
					// yes: continue
					// no: return business_error: NO_ORDER_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet?$filter=Who eq '" + oUrlParams.Who + "' and Lgnum eq '" + oUrlParams.Lgnum + "'"
					logger.debug("checking if Who exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							if (res.d.results.length == 0) {
								oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
								return true
							}
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
							return true
						}
					})



					// 2. Unset WHO in process status
					// yes: Unset status
					// no: return business_error: WHO_STATUS_NOT_UPDATED
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + oUrlParams.Who + "')"
					logger.debug(uri)
					oUrlParams.Status = ""
					jQuery.ajax({
						url: uri,
						method: 'PATCH',
						data: JSON.stringify(oUrlParams),
						async: false,
						success: function (res) {
							//	oXhr.respondJSON(200, {}, res)
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_ORDER_STATUS_NOT_UPDATED" } })
						}
					})


					logger.debug("checking if warehouseorder exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							oXhr.respondJSON(200, {}, res)
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("warehouseorder " + oUrlParams.Who + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_ORDER_STATUS_NOT_UPDATED" } })
						}
					})
					return true

				}


				var UnassignRobotFromWarehouseOrder = function (oXhr, sUrlParams) {
					logger.debug("invoking UnassignRobotFromWarehouseOrder")
					logger.debug("sUrlParams: " + sUrlParams)
					var oUrlParams = sUrlParams.split("&").reduce(function (prev, curr, i, arr) {
						var p = curr.split("=")
						prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
						return prev
					}, {})
					logger.debug("oUrlParams: " + JSON.stringify(oUrlParams))
					var uri = ""


					// 1. Check if the robot resource exists in EWM
					// yes: continue
					// no: return business_error: ROBOT_NOT_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='" + oUrlParams.Lgnum + "',Rsrc='" + oUrlParams.Rsrc + "')"
					logger.debug("checking if robot resource exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that robot resource " + oUrlParams.Rsrc + " exists")
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("robot resource " + oUrlParams.Rsrc + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "ROBOT_NOT_FOUND" } })
							return true
						}
					})


					// 2. Check if the WarehouseOrder exists in EWM
					// yes: continue
					// no: return business_error: NO_ORDER_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + oUrlParams.Who + "')"
					logger.debug("checking if WHO exists at: " + uri)
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						success: function (res) {
							logger.debug("found that WHO " + oUrlParams.Who + " exists")

							// 3. Check if WarehouseOrder is in Process
							// yes: return business_error: WAREHOUSE_ORDER_IN_PROCESS
							// no: actually unassign robot from WHO
							if (res.d.Status === "D") {
								logger.debug("Order is in Process - cannnot unassign")
								oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_ORDER_IN_PROCESS" } })
								return true
							} else {
								delete oUrlParams.Rsrc
								jQuery.ajax({
									url: uri,
									method: 'PUT',
									data: JSON.stringify(oUrlParams),
									async: false,
									success: function (res) {
										oXhr.respondJSON(200, {}, res)
									},
									error: function (err) {
										logger.debug(JSON.stringify(err))
										oXhr.respondJSON(404, {}, { "error": { "code": "WAREHOUSE_ORDER_NOT_UNASSIGNED" } })
									}
								})
							}
						},
						error: function (err) {
							logger.debug(JSON.stringify(err))
							logger.debug("WHO " + oUrlParams.Who + " does not exist")
							oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
							return true
						}
					})
				}


				var GetNewRobotTypeWarehouseOrders = function (oXhr, sUrlParams) {
					logger.debug("invoking GetNewRobotTypeWarehouseOrders")
					logger.debug("sUrlParams: " + sUrlParams)
					var oUrlParams = sUrlParams.split("&").reduce(function (prev, curr, i, arr) {
						var p = curr.split("=")
						prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
						return prev
					}, {})
					logger.debug("oUrlParams: " + JSON.stringify(oUrlParams))
					var uri = ""


					// 1. check if resource type exists in specified warehouse
					// yes: continue
					// no: return business_error: RESOURCE_TYPE_IS_NO_ROBOT
					logger.debug("check if robot resource type exists in warehoue at " + uri)
					if (oUrlParams.RsrcType !== "RB01" || oUrlParams.RsrcGrp !== "RB02") {
						logger.debug("robot doesn't match hardcoded resource type 'RB01' and resource group 'RB01'")
						oXhr.respondJSON(404, {}, { "error": { "code": "RESOURCE_TYPE_IS_NO_ROBOT" } })
						return true
					}
					logger.debug("robot matches hardcoded types")


					// 2. check if there are open WHOs that are not yet assigned to a robot
					// yes: return oUrlParams.NoWho warehouse orders at maximum
					// no: return businuess_error: NO_ORDER_FOUND
					uri = "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet?$filter=Lgnum eq '" + oUrlParams.Lgnum + "' and Rsrc eq '' and Status eq ''&$top=" + oUrlParams.NoWho + ""
					jQuery.ajax({
						url: uri,
						dataType: 'json',
						async: false,
						method: 'GET',
						success: function (res) {
							logger.debug(res)
							if (res.d.results.length != 0) {
								oXhr.respondJSON(200, {}, res)
							} else {
								oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
							}
						},
						error: function (err) {
							logger.debug(err)
							oXhr.respondJSON(404, {}, { "error": { "code": "NO_ORDER_FOUND" } })
						}
					})
				}

				//#endregion
				// End of function imports



				// creation of the MockServer
				var ms = new MockServer({
					rootUri: "/odata/SAP/ZEWM_ROBCO_SRV/"
				})

				logger.info("rootUri set to " + ms.getRootUri())

				// set the MockServer to automatically respond with a little delay
				MockServer.config({
					autoRespond: true,
					autoRespondAfter: 10
				})

				// set the data to be used by the MockServer
				ms.simulate(sap.ui.require.toUrl('myApp/metadata.xml'), {
					sMockdataBaseUrl: sap.ui.require.toUrl('myApp/mockdata'),
					bGenerateMissingMockData: true
				})


				// add request handlers for the function imports
				//#region request handlers
				var aRequests = ms.getRequests()
				aRequests.push({
					method: "POST",
					path: "AssignRobotToWarehouseOrder\\?(.*)",
					response: AssignRobotToWarehouseOrder
				})
				aRequests.push({
					method: "POST",
					path: "ConfirmWarehouseTask\\?(.*)",
					response: ConfirmWarehouseTask
				})
				aRequests.push({
					method: "POST",
					path: "ConfirmWarehouseTaskFirstStep\\?(.*)",
					response: ConfirmWarehouseTaskFirstStep
				})
				aRequests.push({
					method: "GET",
					path: "GetInProcessWarehouseOrders\\?(.*)",
					response: GetInProcessWarehouseOrders
				})
				aRequests.push({
					method: "POST",
					path: "GetNewRobotTypeWarehouseOrders\\?(.*)",
					response: GetNewRobotTypeWarehouseOrders
				})
				aRequests.push({
					method: "POST",
					path: "GetNewRobotWarehouseOrder\\?(.*)",
					response: GetNewRobotWarehouseOrder
				})
				aRequests.push({
					method: "GET",
					path: "GetRobotWarehouseOrders\\?(.*)",
					response: GetRobotWarehouseOrders
				})
				aRequests.push({
					method: "POST",
					path: "SendFirstConfirmationError\\?(.*)",
					response: SendFirstConfirmationError
				})
				aRequests.push({
					method: "POST",
					path: "SendSecondConfirmationError\\?(.*)",
					response: SendSecondConfirmationError
				})
				aRequests.push({
					method: "POST",
					path: "SetRobotStatus\\?(.*)",
					response: SetRobotStatus
				})
				aRequests.push({
					method: "POST",
					path: "UnassignRobotFromWarehouseOrder\\?(.*)",
					response: UnassignRobotFromWarehouseOrder
				})
				aRequests.push({
					method: "POST",
					path: "UnsetWarehouseOrderInProcessStatus\\?(.*)",
					response: UnsetWarehouseOrderInProcessStatus
				})
				ms.setRequests(aRequests)
				//#endregion

				// start the MockServer
				// (also log some debug information)
				ms.start()
				logger.info("ms running")

				// import required frameworks for webservice
				const express = require('express')
				const app = express()
				const bodyParser = require('body-parser')
				const basicAuth = require('express-basic-auth')

				// parser needed for PUT and POST requests
				app.use(bodyParser.text({
					type: '*/*'
				}))

				// handle authentication
				if (process.env.ODATA_USER && process.env.ODATA_PASSWD) {
					app.use(basicAuth({
						authorizer: (username, password) => {
							const userMatches = basicAuth.safeCompare(username, process.env.ODATA_USER)
							const passwordMatches = basicAuth.safeCompare(password, process.env.ODATA_PASSWD)
							return userMatches & passwordMatches
						}
					}))
				} else {
					logger.warn("credentials not set correctly - aborting")
					process.exit()
				}
				logger.info("created express-app with body-parser and authentication")

				// forward HTTP-requests to MockServer
				app.all('/odata/SAP/ZEWM_ROBCO_SRV/*', function (req, res) {
					logger.debug(req.method + "\t" + req.url)
					window.jQuery.ajax({
						method: req.method,
						url: req.url,
						headers: req.headers,
						data: req.body,
						complete: jqXHR => {
							jqXHR.getAllResponseHeaders()
								.split('\n')
								.filter(header => header)
								.forEach(header => {
									const pos = header.indexOf(':')
									res.set(header.substr(0, pos).trim(), header.substr(pos + 1).trim())
								})
							res
								.status(jqXHR.status)
								.send(jqXHR.responseText)
						}
					})
				})

				// start webservice on process.env.ODATA_PORT (default: 8080)
				var port = 8080
				if (process.env.ODATA_PORT) {
					port = process.env.ODATA_PORT
				}
				appServer = app.listen(port, () => {
					logger.info("express-app running")
				})
			})
		})
	},

	initWithOrderroutine() {
		this.init()
		// start orderroutine
		var orderroutine = require("./orderroutine")
		orderroutine.generate();
	},

	stop() {
		appServer.close()
	}
}