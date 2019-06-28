sap.ui.define([
	"jquery.sap.global",
	"sap/ui/core/util/MockServer"
], function(jQuery, MockServer) {
	"use strict"

	return {
		/**
		 * Initializes the mock server.
		 * You can configure the delay with the URL parameter "serverDelay".
		 * The local mock data in this folder is returned instead of the real data for testing.
		 * @public
		 */

		SendFirstConfirmationError: function(oXhr, sUrlParams) {
			console.log("invoking SendFirstConfirmationError")
			console.log("sUrlParams: " + sUrlParams)
			// Expected parameters: Lgnum, Rsrc, Who
			var oUrlParams = sUrlParams.split("&").reduce(function(prev, curr, i, arr) {
				var p = curr.split("=")
				prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
				return prev
			}, {})  
			console.log("oUrlParams: " + JSON.stringify(oUrlParams))
			var uri = ""
			var abort = false
			

			// 1. Check if the robot resource exists in EWM
			// yes: continue
			// no: return business_error: ROBOT_NOT_FOUND
			uri = "/RobotSet(Lgnum='" + oUrlParams.Lgnum + "',Rsrc='" + oUrlParams.Rsrc + "')"
			console.log("checking if robot resource exists at: " + uri)
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					console.log("found that robot resource " + oUrlParams.Rsrc + " exists")
				}, error : function(err) {
					console.log(JSON.stringify(err))
					console.log("robot resource " + oUrlParams.Rsrc + " does not exist")
					oXhr.respondJSON(400, {}, { "error": { "code": "ROBOT_NOT_FOUND" } })	
					abort = true
				}
			})
			if(abort)
				return true

			// 2. Check if the who exists in EWM
			// yes: continue
			// no: return business_error: NO_ORDER_FOUND
			uri = "/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + oUrlParams.Who + "')"
			console.log("checking if warehouseorder exists at: " + uri)
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					console.log("found that warehouseorder " + oUrlParams.Who + " exists")
				}, error : function(err) {
					console.log(JSON.stringify(err))
					console.log("warehouseorder " + oUrlParams.Who + " does not exist")
					oXhr.respondJSON(400, {}, { "error": { "code": "NO_ORDER_FOUND" } })	
					abort = true
				}
			})
			if(abort)
				return true

			// 3. Unassign - Set Status="", Queue="ERROR" and Rsrc="" 
			// yes: return who
			// no: return business_error: WHO_NOT_UNASSIGNED
			let who = {}
			who.Status = ""
			who.Queue = "ERROR"
			who.Rsrc = ""
			uri = "/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + oUrlParams.Who + "')"
			console.log("updating entity at " + uri)
			jQuery.ajax({
				url: uri,
				method: 'PATCH',
				dataType: 'json',
				async: false,
				data: JSON.stringify(who), 
				success: function() {
					console.log("updated entity Status, Queue and Rsrc")
				}, error: function(err) {
					console.log(JSON.stringify(err))
					oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_ORDER_NOT_UNASSIGNED" } })	
					abort = true
				}
			})

			uri = "/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + oUrlParams.Who + "')"
			console.log("checking if warehouseorder exists at: " + uri)
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					oXhr.respondJSON(200, {}, res)
				}, error : function(err) {
					console.log(JSON.stringify(err))
					console.log("warehouseorder " + oUrlParams.Who + " does not exist")
					oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_ORDER_NOT_UNASSIGNED" } })	
				}
			})

			return true
		},

		GetNewRobotWarehouseOrder: function(oXhr, sUrlParams) {
			console.log("invoking GetNewRobotWarehouseOrder")
			// Expected parameters: Lgnum, Rsrc
			console.log("sUrlParams: " + sUrlParams)
			// Expected parameters: Lgnum, Rsrc, Who
			var oUrlParams = sUrlParams.split("&").reduce(function(prev, curr, i, arr) {
				var p = curr.split("=")
				prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
				return prev
			}, {})  
			console.log("oUrlParams: " + JSON.stringify(oUrlParams))
			var uri = ""
			var abort = false

			// 1. Check if the robot resource exists in EWM
			// yes: continue
			// no: return business_error: ROBOT_NOT_FOUND
			uri = "/RobotSet(Lgnum='" + oUrlParams.Lgnum + "',Rsrc='" + oUrlParams.Rsrc + "')"
			console.log("checking if robot resource exists at: " + uri)
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					console.log("found that robot resource " + oUrlParams.Rsrc + " exists")
				}, error : function(err) {
					console.log(JSON.stringify(err))
					console.log("robot resource " + oUrlParams.Rsrc + " does not exist")
					oXhr.respondJSON(400, {}, { "error": { "code": "ROBOT_NOT_FOUND" } })	
					abort = true
				}
			})
			if(abort)
				return true

			// 2. Check if a warehouse order is assigned to the robot
			// yes: return business_error: ROBOT_HAS_ORDER
			// no: continue
			uri = "/WarehouseOrderSet?$filter=Rsrc eq '" + oUrlParams.Rsrc + "' and Status eq 'D'"
			console.log("checking if unconfirmed warehouseorder is assigned to robot: " + uri)	
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					if(res.d.results.length > 0) {
						console.log("found incomplete warehouseorders linked to robot " + oUrlParams.Rsrc)
						oXhr.respondJSON(400, {}, { "error": { "code": "ROBOT_HAS_ORDER" } })
						abort = true
					} else {
						console.log("no warehouseorders associated with robot " + oUrlParams.Rsrc)
					}
				}, error : function(err) {
					console.log(JSON.stringify(err))
					oXhr.respondJSON(400, {}, { "error": { "code": "ROBOT_HAS_ORDER" } })
					abort = true
				}
			})
			if(abort)
				return true

   			// 3 Check if there is a warehouse order with Status="", Queue!="ERROR" and not assigned to any robot
			// yes: return warehouse order of type WarehouseOrder
			//    3.1 Set warehouse order in process "Status": "D"
			//    3.2 Assign robot resource to warehouse order "Rsrc"
			// no: return business_error: NO_ORDER_FOUND
			var who=""
			uri = "/WarehouseOrderSet?$filter=Rsrc eq '' and Status eq ''"
			console.log("checking for open warehouseorder that hasn't been assigned yet")
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					console.log(res)
					if(res.d.results.length > 0) {
						console.log("found open unassigned warehouseorders")
						who = res.d.results.find((element) => {
							return (element.Queue !== "ERROR")
						})
					} else {
						console.log("no open unassigned warehouseorder available")
						oXhr.respondJSON(400, {}, { "error": { "code": "NO_ORDER_FOUND" } })
						abort = true
					}
				}, error : function(err) {
					console.log(JSON.stringify(err))
					oXhr.respondJSON(400, {}, { "error": { "code": "NO_ORDER_FOUND" } })
					abort = true
				}
			})
			if(abort)
				return true

			// Assign who to robot and update status
			who.Status="D"
			who.Rsrc=oUrlParams.Rsrc
			uri="/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + who.Who + "')"
			console.log("updating entity at " + uri)
			jQuery.ajax({
				url: uri,
				method : 'MERGE',
				data : JSON.stringify(who),
				async: false,
				success : function(res) {
					console.log("updated entity Status and Rsrc")
					oXhr.respondJSON(200, {}, {"d":who})
				}, error : function(err) {
					console.log(JSON.stringify(err))
				}
			})

			return true
		},

		ConfirmWarehouseTaskFirstStep: function(oXhr, sUrlParams) {
			console.log("invoking ConfirmWarehouseTaskFirstStep")
			// Expected parameters: Lgnum, Tanum, Rsrc
			var oUrlParams = sUrlParams.split("&").reduce(function(prev, curr, i, arr) {
				var p = curr.split("=")
				prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
				return prev
			}, {})
			var uri = ""
			var abort = false
			var who = ""
			var wht = null

			// 1. Verify that warehousetask exists
			// yes: continue
			// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
			uri = "/OpenWarehouseTaskSet(Lgnum='" + oUrlParams.Lgnum + "',Tanum='" + oUrlParams.Tanum + "')"
			console.log("checking if openwarehousetask exists at: " + uri)
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					console.log("found that openwarehousetask " + oUrlParams.Tanum + " exists for who " + res.d.Who)
					who=res.d.Who
				}, error : function(err) {
					console.log(JSON.stringify(err))
					console.log("openwarehousetask " + oUrlParams.Tanum + " does not exist")
					oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })	
					abort = true
				}
			})
			if(abort)
				return true

			// 2. Verify that warehouseorder Status is not "C"
			// yes: continue
			// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
			uri = "/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + who + "')"
			console.log("checking if warehouseorder exists at: " + uri)
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					console.log("found that warehouseorder " + who + " exists")
					if(res.d.Status !== "C") {
						console.log("warehouseorder is not yet confirmed")
					} else {
						console.log("warehouseorder has already been confirmed")
						oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })	
						abort = true
					}
				}, error : function(err) {
					console.log(JSON.stringify(err))
					console.log("warehouseorder " + who + " does not exist")
					oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })	
					abort = true
				}
			})
			if(abort)
				return true

			// 3. Verify that warehousetask Tostat is not "C"
			// yes: continue
			// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
			uri = "/OpenWarehouseTaskSet(Lgnum='" + oUrlParams.Lgnum + "',Tanum='" + oUrlParams.Tanum + "')"
			console.log("checking if openwarehousetask " + oUrlParams.Tanum + " Tostat is 'C' at: " + uri)
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					if(res.d.Tostat !== "C") {
						console.log("warehousetask is not yet confirmed")
						wht = res.d
					} else {
						console.log("warehousetask has already been confirmed")
						oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })	
						abort = true
					}
				}, error : function(err) {
					console.log(JSON.stringify(err))
					console.log("openwarehousetask " + oUrlParams.Tanum + " does not exist")
					oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })	
					abort = true
				}
			})
			if(abort)
				return true

			
			// 4. Delete "Vltyp", "VlBer", "Vlpla" From warehousetask 
			// yes: return warehousetask
			// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
			wht.Vltyp=""
			wht.Vlber=""
			wht.Vlpla=""
			uri = "/OpenWarehouseTaskSet(Lgnum='" + oUrlParams.Lgnum + "',Tanum='" + oUrlParams.Tanum + "')"
			console.log("deleting 'Vltyp', 'Vlber' and 'Vlpla' from openwarehousetask " + oUrlParams.Tanum + " at: " + uri)
			jQuery.ajax({
				url: uri,
				method : 'MERGE',
				data : JSON.stringify(wht),
				async: false,
				success : function(res) {
					console.log("deleted 'Vltyp', 'Vlber' and 'Vlpla' from warehousetask " + oUrlParams.Tanum)
					oXhr.respondJSON(200, {}, {"d":wht})
				}, error : function(err) {
					console.log("unable to delete 'Vltyp', 'Vlber' and 'Vlpla' from " + oUrlParams.Tanum)
					oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })	
				}
			})

			return true
		}, 

		ConfirmWarehouseTask: function(oXhr, sUrlParams) {
			console.log("invoking ConfirmWarehouseTask")
			// Expected parameters: Lgnum, Tanum
			var oUrlParams = sUrlParams.split("&").reduce(function(prev, curr, i, arr) {
				var p = curr.split("=")
				prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
				return prev
			}, {})
			var uri = ""
			var abort = false
			var who = null
			var whoObj = null
			var wht = null

			// 1. Verify that warehousetask exists
			// yes: continue
			// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
			uri = "/OpenWarehouseTaskSet(Lgnum='" + oUrlParams.Lgnum + "',Tanum='" + oUrlParams.Tanum + "')"
			console.log("checking if openwarehousetask exists at: " + uri)
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					console.log("found that openwarehousetask " + oUrlParams.Tanum + " exists for who " + res.d.Who)
					who=res.d.Who
				}, error : function(err) {
					console.log(JSON.stringify(err))
					console.log("openwarehousetask " + oUrlParams.Tanum + " does not exist")
					oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })	
					abort = true
				}
			})
			if(abort)
				return true

			// 2. Verify that warehouseorder Status is not "C"
			// yes: continue
			// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
			uri = "/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + who + "')"
			console.log("checking if warehouseorder exists at: " + uri)
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					console.log("found that warehouseorder " + who + " exists")
					whoObj = res.d
					if(res.d.Status !== "C") {
						console.log("warehouseorder is not yet confirmed")
					} else {
						console.log("warehouseorder has already been confirmed")
						oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })	
						abort = true
					}
				}, error : function(err) {
					console.log(JSON.stringify(err))
					console.log("warehouseorder " + who + " does not exist")
					oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })	
					abort = true
				}
			})
			if(abort)
				return true

			// 3. Verify that warehousetask Tostat is not "C"
			// yes: continue
			// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
			uri = "/OpenWarehouseTaskSet(Lgnum='" + oUrlParams.Lgnum + "',Tanum='" + oUrlParams.Tanum + "')"
			console.log("checking if openwarehousetask " + oUrlParams.Tanum + " Tostat is 'C' at: " + uri)
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					if(res.d.Tostat !== "C") {
						console.log("warehousetask is not yet confirmed")
						wht = res.d
					} else {
						console.log("warehousetask has already been confirmed")
						oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })	
						abort = true
					}
				}, error : function(err) {
					console.log(JSON.stringify(err))
					console.log("openwarehousetask " + oUrlParams.Tanum + " does not exist")
					oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })	
					abort = true
				}
			})
			if(abort)
				return true

			// 4. Set warehousetask Tostat:"C" to C
			// yes: continue
			// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
			wht.Tostat="C"
			uri = "/OpenWarehouseTaskSet(Lgnum='" + oUrlParams.Lgnum + "',Tanum='" + oUrlParams.Tanum + "')"
			console.log("deleting 'Vltyp', 'Vlber' and 'Vlpla' from openwarehousetask " + oUrlParams.Tanum + " at: " + uri)
			jQuery.ajax({
				url: uri,
				method : 'MERGE',
				data : JSON.stringify(wht),
				async: false,
				success : function(res) {
					console.log("set 'Tostat' to 'C' for warehousetask " + oUrlParams.Tanum)
				}, error : function(err) {
					console.log("unable to set 'Tostat' to 'C' for warehousetask " + oUrlParams.Tanum)
					oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
					abort = true
				}
			})
			if(abort)
				return true

			// 5. Check tasks in warehouseorder, if all Tostat="C" -> set Status="C"
			// yes: 
			// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
			uri = "/OpenWarehouseTaskSet?$filter=Who eq '" + who + "'"
			console.log("checking all tasks for who " + who + " regarding their 'Tostat'")
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					console.log("found warehousetasks for who " + who + ", checking Tostat")
					
					var allTasksComplete = true
					res.d.results.forEach((task) => {
						console.log(task)
						if(task.Tostat !== "C") {
							allTasksComplete = false
						}
					})
					if(!allTasksComplete) {
						console.log("there are still open warehousetasks for who " + who)
						oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
						abort = true	
					}
				}, error : function(err) {
					console.log("unable to retrieve warehousetasks having who " + who)
					oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
					abort = true
				}
			})
			if(abort)
				return true

			// 5.1. Set Who Status to "C"
			// yes:  return whoObj
			// no: return business_error: WAREHOUSE_TASK_NOT_CONFIRMED
			whoObj.Status="C"
			uri = "/WarehouseOrderSet(Lgnum='" + oUrlParams.Lgnum + "',Who='" + who + "')"
			console.log("setting Status to 'C' for warehouseorder " + who + " at: " + uri)
			jQuery.ajax({
				url: uri,
				method : 'MERGE',
				data : JSON.stringify(whoObj),
				async: false,
				success : function(res) {
					console.log("set 'Status' to 'C' for warehouseorder " + who)
					oXhr.respondJSON(200, {}, {"d":whoObj} )
				}, error : function(err) {
					console.log("unable to set 'Status' to 'C' for warehouseorder " + who)
					oXhr.respondJSON(400, {}, { "error": { "code": "WAREHOUSE_TASK_NOT_CONFIRMED" } })
				}
			})

			return true
		},

		GetRobotWarehouseOrders: function(oXhr, sUrlParams) {
			console.log("invoking GetRobotWarehouseOrders")
			// Expected parameters: Lgnum, Rsrc
			console.log("sUrlParams: " + sUrlParams)
			// Expected parameters: Lgnum, Rsrc, Who
			var oUrlParams = sUrlParams.split("&").reduce(function(prev, curr, i, arr) {
				var p = curr.split("=")
				prev[decodeURIComponent(p[0])] = decodeURIComponent(p[1]).replace(/\'/g, '')
				return prev
			}, {})  
			console.log("oUrlParams: " + JSON.stringify(oUrlParams))
			var uri = ""
			var abort = false

			// 1. Check if the robot resource exists in EWM
			// yes: continue
			// no: return business_error: ROBOT_NOT_FOUND
			uri = "/RobotSet(Lgnum='" + oUrlParams.Lgnum + "',Rsrc='" + oUrlParams.Rsrc + "')"
			console.log("checking if robot resource exists at: " + uri)
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					console.log("found that robot resource " + oUrlParams.Rsrc + " exists")
				}, error : function(err) {
					console.log(JSON.stringify(err))
					console.log("robot resource " + oUrlParams.Rsrc + " does not exist")
					oXhr.respondJSON(400, {}, { "error": { "code": "ROBOT_NOT_FOUND" } })	
					abort = true
				}
			})
			if(abort)
				return true

			// 2. Check if a warehouse order is assigned to the robot
			// yes: return warehouse order of type WarehouseOrder
			// no: return business_error: NO_ORDER_FOUND
			uri = "/WarehouseOrderSet?$filter=Rsrc eq '" + oUrlParams.Rsrc + "' and Status eq 'D'"
			console.log("checking if unconfirmed warehouseorder is assigned to robot: " + uri)	
			jQuery.ajax({
				url: uri,
				dataType : 'json',
				async: false,
				success : function(res) {
					if(res.d.results.length > 0) {
						console.log("found incomplete warehouseorders linked to robot " + oUrlParams.Rsrc)
						oXhr.respondJSON(200, {}, res)
						abort = true
					} else {
						oXhr.respondJSON(400, {}, { "error": { "code": "NO_ORDER_FOUND" } })
					}
				}, error : function(err) {
					console.log(JSON.stringify(err))
					oXhr.respondJSON(400, {}, { "error": { "code": "NO_ORDER_FOUND" } })
					abort = true
				}
			})

			return true
		},

		init: function() {
			// create
			var oMockServer = new MockServer({
				rootUri: "/"
			})

			Object.keys(MockServer.HTTPMETHOD).forEach(function(sMethodName) {
				var sMethod = MockServer.HTTPMETHOD[sMethodName];
				oMockServer.attachBefore(sMethod, function(oEvent) {
					// var oXhr = oEvent.getParameters().oXhr;
					// console.log("MockServer::before", sMethod, oXhr.url, oXhr);
				});
				oMockServer.attachAfter(sMethod, function(oEvent) {
					// var oXhr = oEvent.getParameters().oXhr;
					// console.log("MockServer::after", sMethod, oXhr.url, oXhr);
				});
			});


			oMockServer.simulate("../localService/metadata.xml", {
				sMockdataBaseUrl: "../localService/mockdata",
				bGenerateMissingMockData: false
			})

			// handling mocking a function import call step
			var aRequests = oMockServer.getRequests()
			aRequests.push({
				method: "GET",
				path: new RegExp("GetRobotWarehouseOrders\\?(.*)"),
				response: this.GetRobotWarehouseOrders
			})
			aRequests.push({
				method: "POST",
				path: new RegExp("GetNewRobotWarehouseOrder\\?(.*)"),
				response: this.GetNewRobotWarehouseOrder
			})
			aRequests.push({
				method: "POST",
				path: new RegExp("ConfirmWarehouseTaskFirstStep\\?(.*)"),
				response: this.ConfirmWarehouseTaskFirstStep
			})
			aRequests.push({
				method: "POST",
				path: new RegExp("ConfirmWarehouseTask\\?(.*)"),
				response: this.ConfirmWarehouseTask
			})
			aRequests.push({
				method: "POST",
				path: new RegExp("SendFirstConfirmationError\\?(.*)"),
				response: this.SendFirstConfirmationError
			})

			oMockServer.setRequests(aRequests)
			oMockServer.start()

			// ##############################################################################
			// #############  WebSocket Comm Handler for OData Requests      ################
			// ##############################################################################
			// Create WebSocket connection.
			const socket = new WebSocket('ws://localhost:9090')

			// Connection opened
			socket.addEventListener('open', function (event) {
				console.log("socket open, listening for odata requests")
			})

			// Listen for messages
			socket.addEventListener('message', function (event) {
				let req=JSON.parse(event.data)
				let uri = req.url.replace(req.ODATA_BASEPATH, "")
				let method = req.method					
				var mID = req.mID
				console.log("received mID " + mID + " requesting " + method + " on " + uri)
				var response = {}
				response['mID']=mID

				if(method === "PATCH") {
					console.log("detected PATCH, converting to MERGE")
					method = "MERGE"
				}

				$.ajax({
					url: uri, 
					method: method,
					async: false,
					headers: req.headers, 
					data: JSON.stringify(req.body),
					complete: function(result){
						response['result']=result
						console.log("processing for mID " + response['mID'] + " complete.")
						if(result.responseText.includes("<!DOCTYPE HTML>")) {
							console.log("detected html, reverting to 404 Not Found")
							result.status=404
							result.statusText="Not Found"
							result.responseJSON= { "error": { "code": "NOT_FOUND", "message": { "lang": "en", "value": "Could not find an entity set or function import." } } }
							result.responseText= result.responseJSON
						}
							
						let strResponse = JSON.stringify(response)
						console.log("response for mID " + response['mID'] + " is: " + strResponse)
						socket.send(strResponse)
					}
				})
			})

			// ##############################################################################
			// ##############################################################################
			// ##############################################################################
		}
	}
})