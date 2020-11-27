process.env.LOGGING_LOGTOFILE = true

var server = require('../mockserver')

var assert = require('assert')
var tools = require('../tools/toolbox.js')

describe('Test for basic server functionality', () => {
	before(() => {
		server.init()
	})

	describe('Deleting Entities', () => {
		describe('Delete All Robots', () => {
			it('should execute drop-if-exists', async () => {
				await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Isaac" })
				let deletion = await tools.deleteAllEntities("RobotSet", ["Lgnum", "Rsrc"])
				await tools.allPromiseWrapper(deletion)

				let res = await tools.getEntity("RobotSet", {})
				assert.deepStrictEqual(res.body.d.results.length === 0, true)
			})

			it('verify that http status code is 200', async () => {
				let deletion = await tools.deleteAllEntities("RobotSet", ["Lgnum", "Rsrc"])
				await tools.allPromiseWrapper(deletion)

				let res = await tools.getEntity("RobotSet", {})
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})

		describe('Delete All OpenWarehouseTasks', () => {
			it('should execute drop-if-exists', async () => {
				await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "12345" })
				let deletion = await tools.deleteAllEntities("OpenWarehouseTaskSet", ["Lgnum", "Tanum"])
				await tools.allPromiseWrapper(deletion)

				let res = await tools.getEntity("OpenWarehouseTaskSet", {})
				assert.deepStrictEqual(res.body.d.results.length === 0, true)
			})

			it('verify that http status code is 200', async () => {
				let deletion = await tools.deleteAllEntities("OpenWarehouseTaskSet", ["Lgnum", "Tanum"])
				await tools.allPromiseWrapper(deletion)

				let res = await tools.getEntity("OpenWarehouseTaskSet", {})
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})

		describe('Delete All WarehouseOrders', () => {
			it('should execute drop-if-exists', async () => {
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "12345" })
				let deletion = await tools.deleteAllEntities("WarehouseOrderSet", ["Lgnum", "Who"])
				await tools.allPromiseWrapper(deletion)

				let res = await tools.getEntity("WarehouseOrderSet", {})
				assert.deepStrictEqual(res.body.d.results.length === 0, true)
			})

			it('verify that http status code is 200', async () => {
				let deletion = await tools.deleteAllEntities("WarehouseOrderSet", ["Lgnum", "Who"])
				await tools.allPromiseWrapper(deletion)

				let res = await tools.getEntity("WarehouseOrderSet", {})
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})


	describe('Creating Entities', () => {
		describe('Create Robot', () => {
			it('should return json with robot', async () => {
				let exp = { "d": { "Lgnum": "1337", "Rsrc": "Isaac", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='1337',Rsrc='Isaac')", "type": "ZEWM_ROBCO_SRV.Robot", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='1337',Rsrc='Isaac')" } }, "uri": "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='1337',Rsrc='Isaac')" }
				let res = await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Isaac" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 201', async () => {
				let res = await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Asimov" })
				assert.deepStrictEqual(res.statusCode, 201)
			})
		})

		describe('Create WarehouseOrder', () => {
			it('should return json with warehouseorder', async () => {
				let exp = { "d": { "Lgnum": "1337", "Who": "123456", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='123456')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='123456')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='123456')/OpenWarehouseTasks" } } }, "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='123456')" }
				let res = await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "123456" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 201', async () => {
				let res = await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "654321" })
				assert.deepStrictEqual(res.statusCode, 201)
			})
		})

		describe('Create WarehouseTask', () => {
			it('should return json with warehousetask', async () => {
				let exp = { "d": { "Lgnum": "1337", "Tanum": "987654", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet(Lgnum='1337',Tanum='987654')", "type": "ZEWM_ROBCO_SRV.OpenWarehouseTask", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet(Lgnum='1337',Tanum='987654')" } }, "uri": "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet(Lgnum='1337',Tanum='987654')" }
				let res = await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "987654" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 201', async () => {
				let res = await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "123456" })
				assert.deepStrictEqual(res.statusCode, 201)
			})
		})
	})


	describe('Retrieving Entities', () => {
		describe('Get Robot', () => {
			it('get robot using Lgnum and Rsrc', async () => {
				let exp = { "d": { "Lgnum": "1337", "Rsrc": "Isaac", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='1337',Rsrc='Isaac')", "type": "ZEWM_ROBCO_SRV.Robot", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='1337',Rsrc='Isaac')" } } }
				let res = await tools.getEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Isaac" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				let res = await tools.getEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Isaac" })
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})

		describe('Get WarehouseOrder', () => {
			it('get warehouseorder using Lgnum and Who', async () => {
				let exp = { "d": { "Lgnum": "1337", "Who": "654321", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='654321')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='654321')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='654321')/OpenWarehouseTasks" } } } }
				let res = await tools.getEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "654321" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				let res = await tools.getEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "654321" })
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})

		describe('Get WarehouseTask', () => {
			it('get warehousetask using Lgnum and Tanum', async () => {
				let exp = { "d": { "Lgnum": "1337", "Tanum": "123456", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet(Lgnum='1337',Tanum='123456')", "type": "ZEWM_ROBCO_SRV.OpenWarehouseTask", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet(Lgnum='1337',Tanum='123456')" } } }
				let res = await tools.getEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "123456" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				let res = await tools.getEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "123456" })
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})


	describe('Retrieving Entitylists', () => {
		describe('Get Robots', () => {
			it('get all robots', async () => {
				let res = await tools.getEntity("RobotSet", {})
				assert.deepStrictEqual(res.body.d.results.length >= 1, true)
			})

			it('verify that http status code is 200', async () => {
				let res = await tools.getEntity("RobotSet", {})
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})

		describe('Get WarehouseOrders', () => {
			it('get all warehouseorders', async () => {
				let res = await tools.getEntity("WarehouseOrderSet", {})
				assert.deepStrictEqual(res.body.d.results.length >= 1, true)
			})

			it('verify that http status code is 200', async () => {
				let res = await tools.getEntity("WarehouseOrderSet", {})
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})

		describe('Get WarehouseTasks', () => {
			it('get all warehousetasks', async () => {
				let res = await tools.getEntity("OpenWarehouseTaskSet", {})
				assert.deepStrictEqual(res.body.d.results.length >= 1, true)
			})

			it('verify that http status code is 200', async () => {
				let res = await tools.getEntity("OpenWarehouseTaskSet", {})
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})


	describe('Update Entities', () => {
		describe('Update Robot', () => {
			it('verify that http status code is 204', async () => {
				let res = await tools.updateEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Asimov" }, { "RsrcGrp": "Uberfleet" })
				assert.deepStrictEqual(res.statusCode, 204)
			})

			it('verify that patch was correct', async () => {
				let res = await tools.getEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Asimov" })
				assert.deepStrictEqual(res.body.d.RsrcGrp, "Uberfleet")
			})
		})
	})


	describe('Malformed Requests', () => {
		describe('Retrieve Unknown Entity', () => {
			it('verify that http status code is 404', async () => {
				let res = await tools.getEntity("RobotSet", { "Lgnum": "13371337", "Rsrc": "Tron" })
				assert.deepStrictEqual(res.statusCode, 404)
			})
		})

		describe('Point to Illegal Entityset', () => {
			it('verify that http status code is 501', async () => {
				let res = await tools.createEntity("ProtoSet", { "abc": "123!" })
				assert.deepStrictEqual(res.statusCode, 501)
			})
		})
	})


	describe('Custom Function \'GetNewRobotWarehouseOrder\'', () => {
		describe('Errorcases', () => {
			describe('ROBOT_NOT_FOUND', () => {
				it('check for correct business_error', async () => {
					let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", {})
					assert.deepStrictEqual(res.body.error.code, "ROBOT_NOT_FOUND")
				})

				it('verify that http status code is 404', async () => {
					let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", {})
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})

			describe('NO_ORDER_FOUND', () => {
				it('check for correct business_error', async () => {
					let deletion = await tools.deleteAllEntities("WarehouseOrderSet", ["Lgnum", "Who"])
					await tools.allPromiseWrapper(deletion)

					let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { "Lgnum": "1337", "Rsrc": "Isaac" })
					assert.deepStrictEqual(res.body.error.code, "NO_ORDER_FOUND")
				})

				it('verify that http status code is 404', async () => {
					let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { "Lgnum": "1337", "Rsrc": "Isaac" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})

			describe('ROBOT_HAS_ORDER', () => {
				it('check for correct business_error', async () => {
					await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "123456", "Rsrc": "Isaac", "Status": "D" })

					let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { "Lgnum": "1337", "Rsrc": "Isaac" })
					assert.deepStrictEqual(res.body.error.code, "ROBOT_HAS_ORDER")
				})

				it('verify that http status code is 403', async () => {
					await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "123456", "Rsrc": "Asimov", "Status": "D" })

					let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { "Lgnum": "1337", "Rsrc": "Asimov" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})
		})

		describe('Success', () => {
			it('verify that Rsrc in who is set and Status is \'D\'', async () => {
				await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Cobot" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "123456789", "Rsrc": "", "Status": "" })

				let exp = { "d": { "Lgnum": "1337", "Who": "123456789", "Rsrc": "Cobot", "Status": "D", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='123456789')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='123456789')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='123456789')/OpenWarehouseTasks" } } } }
				let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { "Lgnum": "1337", "Rsrc": "Cobot" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Cobot123" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "987654321", "Rsrc": "", "Status": "" })

				let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { "Lgnum": "1337", "Rsrc": "Cobot123" })
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})


	describe('Custom Function \'GetRobotWarehouseOrders\'', () => {
		describe('Errorcases', () => {
			describe('ROBOT_NOT_FOUND', () => {
				it('check for correct business_error', async () => {
					let res = await tools.oDataGetFunction("GetRobotWarehouseOrders", {})
					assert.deepStrictEqual(res.body.error.code, "ROBOT_NOT_FOUND")
				})

				it('verify that http status code is 404', async () => {
					let res = await tools.oDataGetFunction("GetRobotWarehouseOrders", {})
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})

			describe('NO_ORDER_FOUND', () => {
				it('check for correct business_error', async () => {
					await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Turtlebot" })

					let res = await tools.oDataGetFunction("GetRobotWarehouseOrders", { "Lgnum": "1337", "Rsrc": "Turtlebot" })
					assert.deepStrictEqual(res.body.error.code, "NO_ORDER_FOUND")
				})

				it('verify that http status code is 404', async () => {
					await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Turtlebot-B" })

					let res = await tools.oDataGetFunction("GetRobotWarehouseOrders", { "Lgnum": "1337", "Rsrc": "Turtlebot-B" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})
		})

		describe('Success', () => {
			it('verify that who is returned', async () => {
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "123456789", "Rsrc": "Turtlebot", "Status": "D" })

				let exp = { "d": { "results": [{ "Lgnum": "1337", "Who": "123456789", "Rsrc": "Turtlebot", "Status": "D", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='123456789')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='123456789')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='123456789')/OpenWarehouseTasks" } } }] } }
				let res = await tools.oDataGetFunction("GetRobotWarehouseOrders", { "Lgnum": "1337", "Rsrc": "Turtlebot" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "123456789", "Rsrc": "Turtlebot-B", "Status": "D" })

				let res = await tools.oDataGetFunction("GetRobotWarehouseOrders", { "Lgnum": "1337", "Rsrc": "Turtlebot-B" })
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})


	describe('Custom Function \'ConfirmWarehouseTaskFirstStep\'', () => {
		describe('Errorcases', () => {
			describe('WAREHOUSE_TASK_NOT_CONFIRMED', () => {
				describe('wht does not exist', () => {
					it('check for correct business_error', async () => {
						let deletion = await tools.deleteAllEntities("OpenWarehouseTaskSet", ["Lgnum", "Tanum"])
						await tools.allPromiseWrapper(deletion)

						let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Cobot123" })
						assert.deepStrictEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
					})

					it('verify that http status code is 404', async () => {
						let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Cobot123" })
						assert.deepStrictEqual(res.statusCode, 404)
					})
				})

				describe('who \'Status\' is already \'C\'', () => {
					it('check for correct business_error', async () => {
						await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "abcde", "Rsrc": "Isaac", "Status": "C" })
						await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Who": "abcde", "Tanum": "abcde", "Tostat": "C" })

						let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Isaac" })
						assert.deepStrictEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
					})

					it('verify that http status code is 404', async () => {
						let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Isaac" })
						assert.deepStrictEqual(res.statusCode, 404)
					})
				})

				describe('wht \'Tostat\' is already \'C\'', () => {
					it('check for correct business_error', async () => {
						await tools.updateEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "abcde" }, { "Status": "" })

						let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Isaac" })
						assert.deepStrictEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
					})

					it('verify that http status code is 404', async () => {
						let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Isaac" })
						assert.deepStrictEqual(res.statusCode, 404)
					})
				})
			})
		})

		describe('Success', () => {
			it('wht is returned and \'Vltyp\', \'Vlber\' and \'Vlpla\' are deleted', async () => {
				await tools.updateEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "abcde" }, { "Tostat": "" })

				let exp = { "d": { "Lgnum": "1337", "Who": "abcde", "Tanum": "abcde", "Tostat": "", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet(Lgnum='1337',Tanum='abcde')", "type": "ZEWM_ROBCO_SRV.OpenWarehouseTask", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/OpenWarehouseTaskSet(Lgnum='1337',Tanum='abcde')" }, "Vltyp": "", "Vlber": "", "Vlpla": "" } }
				let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Isaac" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "213", "Rsrc": "Isaac", "Status": "" })
				await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Who": "213", "Tanum": "4321", "Tostat": "" })

				let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum": "1337", "Tanum": "4321", "Rsrc": "Isaac" })
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})


	describe('Custom Function \'ConfirmWarehouseTask\'', () => {
		describe('Errorcases', () => {
			describe('WAREHOUSE_TASK_NOT_CONFIRMED', () => {
				describe('wht does not exist', () => {
					it('check for correct business_error', async () => {
						let deletion = await tools.deleteAllEntities("OpenWarehouseTaskSet", ["Lgnum", "Tanum"])
						await tools.allPromiseWrapper(deletion)

						let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Cobot123" })
						assert.deepStrictEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
					})

					it('verify that http status code is 404', async () => {
						let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Cobot123" })
						assert.deepStrictEqual(res.statusCode, 404)
					})
				})

				describe('who \'Status\' is already \'C\'', () => {
					it('check for correct business_error', async () => {
						let deletion = await tools.deleteAllEntities("WarehouseOrderSet", ["Lgnum", "Who"])
						await tools.allPromiseWrapper(deletion)

						await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "abcde", "Rsrc": "Isaac", "Status": "C" })
						await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Who": "abcde", "Tanum": "abcde", "Tostat": "C" })

						let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Isaac" })
						assert.deepStrictEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
					})

					it('verify that http status code is 404', async () => {
						let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Isaac" })
						assert.deepStrictEqual(res.statusCode, 404)
					})
				})

				describe('wht \'Tostat\' is already \'C\'', () => {
					it('check for correct business_error', async () => {
						await tools.updateEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "abcde" }, { "Status": "" })

						let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Isaac" })
						assert.deepStrictEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
					})

					it('verify that http status code is 404', async () => {
						let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Isaac" })
						assert.deepStrictEqual(res.statusCode, 404)
					})
				})

				describe('who includes other incomplete tasks', () => {
					it('check for correct business_error', async () => {
						await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Who": "abcde", "Tanum": "54321", "Tostat": "" })

						let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Isaac" })
						assert.deepStrictEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
					})

					it('verify that http status code is 404', async () => {
						let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Isaac" })
						assert.deepStrictEqual(res.statusCode, 404)
					})
				})
			})
		})

		describe('Success', () => {
			it('who is returned and \'Status\' is \'C\'', async () => {
				await tools.updateEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "54321" }, { "Tostat": "C" })
				await tools.updateEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "abcde" }, { "Tostat": "" })

				let exp = { "d": { "Lgnum": "1337", "Who": "abcde", "Rsrc": "Isaac", "Status": "C", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='abcde')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='abcde')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='abcde')/OpenWarehouseTasks" } } } }
				let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Isaac" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				await tools.updateEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "54321" }, { "Tostat": "C" })
				await tools.updateEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "abcde" }, { "Tostat": "" })
				await tools.updateEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "abcde" }, { "Status": "" })

				let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum": "1337", "Tanum": "abcde", "Rsrc": "Isaac" })
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})


	describe('Custom Function \'SendFirstConfirmationError\'', () => {
		describe('Errorcases', () => {
			describe('ROBOT_NOT_FOUND', () => {
				it('check for correct business_error', async () => {
					let res = await tools.oDataPostFunction("SendFirstConfirmationError", { "Lgnum": "1337", "Who": "someWho", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.body.error.code, "ROBOT_NOT_FOUND")
				})

				it('verify that http status code is 404', async () => {
					let res = await tools.oDataPostFunction("SendFirstConfirmationError", { "Lgnum": "1337", "Who": "someWho", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})

			describe('NO_ORDER_FOUND', () => {
				it('check for correct business_error', async () => {
					await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })

					let res = await tools.oDataPostFunction("SendFirstConfirmationError", { "Lgnum": "1337", "Who": "someWho", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.body.error.code, "NO_ORDER_FOUND")
				})

				it('verify that http status code is 404', async () => {
					let res = await tools.oDataPostFunction("SendFirstConfirmationError", { "Lgnum": "1337", "Who": "someWho", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})
		})

		describe('Success', () => {
			it('who is returned and \'Status\'=\"\", \'Rsrc\'=\"\" and \'Queue\'=\"ERROR\"', async () => {
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "someWho", "Rsrc": "someRobot", "Status": "D", "Queue": "someQueue" })

				let exp = { "d": { "Lgnum": "1337", "Who": "someWho", "Rsrc": "", "Status": "", "Queue": "ERROR", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='someWho')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='someWho')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='someWho')/OpenWarehouseTasks" } } } }
				let res = await tools.oDataPostFunction("SendFirstConfirmationError", { "Lgnum": "1337", "Who": "someWho", "Rsrc": "someRobot" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				await tools.updateEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "someWho" }, { "Queue": "someRobot", "Rsrc": "someRobot", "Status": "D" })

				let res = await tools.oDataPostFunction("SendFirstConfirmationError", { "Lgnum": "1337", "Who": "someWho", "Rsrc": "someRobot" })
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})



	describe('Custom Function \'SendSecondConfirmationError\'', () => {
		describe('Errorcases', () => {
			describe('ROBOT_NOT_FOUND', () => {
				it('check for correct business_error', async () => {
					let res = await tools.oDataPostFunction("SendSecondConfirmationError", { "Lgnum": "1437", "Who": "someWho", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.body.error.code, "ROBOT_NOT_FOUND")
				})

				it('verify that http status code is 404', async () => {
					let res = await tools.oDataPostFunction("SendSecondConfirmationError", { "Lgnum": "1437", "Who": "someWho", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})

			describe('NO_ORDER_FOUND', () => {
				it('check for correct business_error', async () => {
					await tools.createEntity("RobotSet", { "Lgnum": "1437", "Rsrc": "someRobot" })

					let res = await tools.oDataPostFunction("SendSecondConfirmationError", { "Lgnum": "1437", "Who": "someWho", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.body.error.code, "NO_ORDER_FOUND")
				})

				it('verify that http status code is 404', async () => {
					let res = await tools.oDataPostFunction("SendSecondConfirmationError", { "Lgnum": "1437", "Who": "someWho", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})
		})

		describe('Success', () => {
			it('who is returned \'Queue\'=\"ERROR\"', async () => {
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1437", "Who": "someWho", "Rsrc": "someRobot", "Status": "D", "Queue": "someQueue" })

				let exp = { "d": { "Lgnum": "1437", "Who": "someWho", "Rsrc": "someRobot", "Status": "D", "Queue": "ERROR", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1437',Who='someWho')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1437',Who='someWho')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1437',Who='someWho')/OpenWarehouseTasks" } } } }
				let res = await tools.oDataPostFunction("SendSecondConfirmationError", { "Lgnum": "1437", "Who": "someWho", "Rsrc": "someRobot" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				await tools.updateEntity("WarehouseOrderSet", { "Lgnum": "1437", "Who": "someWho" }, { "Queue": "someRobot", "Rsrc": "someRobot", "Status": "D" })

				let res = await tools.oDataPostFunction("SendSecondConfirmationError", { "Lgnum": "1437", "Who": "someWho", "Rsrc": "someRobot" })
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})



	describe('Custom Function \'GetInProcessWarehouseOrders\'', () => {
		describe('Errorcases', () => {
			describe('NO_ORDER_FOUND', () => {
				it('checks for correct business_error', async () => {
					let res = await tools.oDataGetFunction("GetInProcessWarehouseOrders", { "Lgnum": "1337", "RsrcType": "RB01" })
					assert.deepStrictEqual(res.body.error.code, "NO_ORDER_FOUND")
				})

				it('verify that http status code is 400', async () => {
					let res = await tools.oDataGetFunction("GetInProcessWarehouseOrders", { "Lgnum": "1337", "RsrcType": "RB01" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})
			describe('RESOURCE_TYPE_IS_NO_ROBOT', () => {
				it('checks for correct business_error', async () => {
					await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1400", "RsrcType": "RB01", "Status": "D", "Who": "someWho", "Rsrc": "" })

					let res = await tools.oDataGetFunction("GetInProcessWarehouseOrders", { "Lgnum": "1400", "RsrcType": "wrongType" })
					assert.deepStrictEqual(res.body.error.code, "RESOURCE_TYPE_IS_NO_ROBOT")
				})


				it('verify that http status code is 400', async () => {
					let res = await tools.oDataGetFunction("GetInProcessWarehouseOrders", { "Lgnum": "1400", "RsrcType": "wrongType" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})
		})
		describe('Success', () => {
			it('checks for correct response', async () => {

				let exp = {
					"d": { "results": [{ "Lgnum": "1400", "RsrcType": "RB01", "Status": "D", "Who": "someWho", "Rsrc": "", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1400',Who='someWho')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1400',Who='someWho')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1400',Who='someWho')/OpenWarehouseTasks" } } }] }
				}

				let res = await tools.oDataGetFunction("GetInProcessWarehouseOrders", { "Lgnum": "1400", "RsrcType": "RB01" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				let res = await tools.oDataGetFunction("GetInProcessWarehouseOrders", { "Lgnum": "1400", "RsrcType": "RB01" })
				assert.deepStrictEqual(res.statusCode, 200)
			})

		})
	})



	describe('Custom Function \'SetRobotStatus\'', () => {
		describe('Errorcases', () => {
			describe('ROBOT_NOT_FOUND', () => {
				it('check for correct business_error', async () => {
					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("SetRobotStatus", { "Lgnum": "1337", "Rsrc": "someRobot", "ExccodeOverall": "someExccode" })
					assert.deepStrictEqual(res.body.error.code, "ROBOT_NOT_FOUND")
				})

				it('verify that http status code is 404', async () => {
					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("SetRobotStatus", { "Lgnum": "1337", "Rsrc": "someRobot", "ExccodeOverall": "CODE" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})

			describe('ROBOT_STATUS_NOT_SET', () => {
				it('check for correct business_error', async () => {
					await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("SetRobotStatus", { "Lgnum": "1337", "Rsrc": "someRobot", "ExccodeOverall": "tooLongCode" })
					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.body.error.code, "ROBOT_STATUS_NOT_SET")
				})

				it('verify that http status code is 404', async () => {
					await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("SetRobotStatus", { "Lgnum": "1337", "Rsrc": "someRobot", "ExccodeOverall": "tooLongCode" })
					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})
		})

		describe('Success', () => {
			it('successfully set status code of a robot', async () => {
				await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
				await tools.oDataPostFunction("SetRobotStatus", { "Lgnum": "1337", "Rsrc": "someRobot", "ExccodeOverall": "STAT" })
				let exp = { "d": { "Lgnum": "1337", "Rsrc": "someRobot", "ExccodeOverall": "STAT", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='1337',Rsrc='someRobot')", "type": "ZEWM_ROBCO_SRV.Robot", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/RobotSet(Lgnum='1337',Rsrc='someRobot')" } } }
				let res = await tools.getEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
				await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
				let res = await tools.oDataPostFunction("SetRobotStatus", { "Lgnum": "1337", "Rsrc": "someRobot", "ExccodeOverall": "STAT" })
				await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})


	describe('Custom Function \'AssignRobotToWarehouseOrder\'', () => {
		describe('Errorcases', () => {
			describe('ROBOT_NOT_FOUND', () => {
				it('check for correct business_error', async () => {
					await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" })
					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("AssignRobotToWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

					await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
					assert.deepStrictEqual(res.body.error.code, "ROBOT_NOT_FOUND")
				})

				it('verify that http status code is 404', async () => {
					await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" })
					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("AssignRobotToWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

					await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})

			describe('NO_ORDER_FOUND', () => {
				it('check for correct business_error', async () => {
					await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
					await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("AssignRobotToWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.body.error.code, "NO_ORDER_FOUND")
				})

				it('verify that http status code is 404', async () => {
					await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
					await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("AssignRobotToWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})

			describe('WAREHOUSE_ORDER_ASSIGNED', () => {
				it('check for correct business_error', async () => {
					await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890", "Rsrc": "someRobot" })
					await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("AssignRobotToWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

					await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.body.error.code, "WAREHOUSE_ORDER_ASSIGNED")
				})

				it('verify that http status code is 404', async () => {
					await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890", "Rsrc": "someRobot" })
					await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("AssignRobotToWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

					await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})
		})

		describe('Success', () => {
			it('successfully assigned who to a robot', async () => {
				await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" })
				await tools.oDataPostFunction("AssignRobotToWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })
				let exp = { "d": { "Lgnum": "1337", "Who": "1234567890", "Rsrc": "someRobot", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='1234567890')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='1234567890')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='1234567890')/OpenWarehouseTasks" } } } }
				let res = await tools.getEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" })

				await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
				await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" })
				let res = await tools.oDataPostFunction("AssignRobotToWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

				await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
				await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})



	describe('Custom Function \'UnassignRobotFromWarehouseOrder\'', () => {
		describe('Errorcases', () => {
			describe('ROBOT_NOT_FOUND', () => {
				it('check for correct business_error', async () => {
					await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" })
					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("UnassignRobotFromWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

					await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
					assert.deepStrictEqual(res.body.error.code, "ROBOT_NOT_FOUND")
				})

				it('verify that http status code is 404', async () => {
					await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" })
					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("UnassignRobotFromWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

					await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})

			describe('NO_ORDER_FOUND', () => {
				it('check for correct business_error', async () => {
					await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
					await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("UnassignRobotFromWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.body.error.code, "NO_ORDER_FOUND")
				})

				it('verify that http status code is 404', async () => {
					await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
					await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
					let res = await tools.oDataPostFunction("UnassignRobotFromWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})

			describe('WAREHOUSE_ORDER_IN_PROCESS', () => {
				it('check for correct business_error', async () => {
					await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
					await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890", "Rsrc": "someRobot", "Status": "D" })
					let res = await tools.oDataPostFunction("UnassignRobotFromWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
					assert.deepStrictEqual(res.body.error.code, "WAREHOUSE_ORDER_IN_PROCESS")
				})

				it('verify that http status code is 404', async () => {
					await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
					await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890", "Rsrc": "someRobot", "Status": "D" })
					let res = await tools.oDataPostFunction("UnassignRobotFromWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

					await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
					await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})
		})

		describe('Success', () => {
			it('successfully unassigned who from a robot', async () => {
				await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890", "Rsrc": "someRobot" })
				await tools.oDataPostFunction("UnassignRobotFromWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })
				let exp = { "d": { "Lgnum": "1337", "Who": "1234567890", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='1234567890')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='1234567890')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='1234567890')/OpenWarehouseTasks" } } } }
				let res = await tools.getEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" })

				await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
				await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890", "Rsrc": "someRobot" })
				let res = await tools.oDataPostFunction("UnassignRobotFromWarehouseOrder", { "Lgnum": "1337", "Rsrc": "someRobot", "Who": "1234567890" })

				await tools.deleteEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" }, { "Lgnum": "1337", "Rsrc": "someRobot" })
				await tools.deleteEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1234567890" }, { "Lgnum": "1337", "Who": "1234567890" })
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})


	describe('Custom Function \'UnsetWarehouseOrderInProcessStatus\'', () => {
		describe('Errorcases', () => {
			describe('NO_ORDER_FOUND', () => {
				it('checks for correct business_error', async () => {
					await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1401", "RsrcType": "RB01", "Status": "D", "Who": "someWho" })

					let res = await tools.oDataPostFunction("UnsetWarehouseOrderInProcessStatus", { "Lgnum": "1401", "Who": "wrongWho" })
					assert.deepStrictEqual(res.body.error.code, "NO_ORDER_FOUND")
				})

				it('verify that http status code is 404', async () => {
					let res = await tools.oDataPostFunction("UnsetWarehouseOrderInProcessStatus", { "Lgnum": "1401", "Who": "wrongWho" })
					assert.deepStrictEqual(res.statusCode, 404)
				})
			})
		})

		describe('Success', () => {
			it('checks for initial status', async () => {
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1401", "RsrcType": "RB01", "Status": "D", "Who": "someWho" })


				let exp = { "d": { "Lgnum": "1401", "RsrcType": "RB01", "Status": "", "Who": "someWho", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1401',Who='someWho')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1401',Who='someWho')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1401',Who='someWho')/OpenWarehouseTasks" } } } }
				await tools.oDataPostFunction("UnsetWarehouseOrderInProcessStatus", { "Lgnum": "1401", "Who": "someWho" })
				let res = await tools.getEntity("WarehouseOrderSet", { "Lgnum": "1401", "Who": "someWho" })

				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				let res = await tools.oDataPostFunction("UnsetWarehouseOrderInProcessStatus", { "Lgnum": "1401", "Who": "someWho" })
				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})



	describe('Custom Function \'GetNewRobotTypeWarehouseOrders\'', () => {
		describe('Errorcases', () => {
			describe('RESOURCE_TYPE_IS_NO_ROBOT', () => {
				it('check for correct business_error', async () => {
					await tools.deleteEntity("RobotResourceTypeSet", { "Lgnum": "1337", "RsrcType": "some", "RobotType": "some" }, { "Lgnum": "1337", "RsrcType": "some", "RobotType": "some" })
					let res = await tools.oDataPostFunction("GetNewRobotTypeWarehouseOrders", { "Lgnum": "1337", "RsrcType": "some", "RsrcGrp": "RB02", "NoWho": "2" })

					assert.deepStrictEqual(res.body.error.code, "RESOURCE_TYPE_IS_NO_ROBOT")
				})

				it('verify that http status code is 404', async () => {
					await tools.deleteEntity("RobotResourceTypeSet", { "Lgnum": "1337", "RsrcType": "some", "RobotType": "some" }, { "Lgnum": "1337", "RsrcType": "some", "RobotType": "some" })
					let res = await tools.oDataPostFunction("GetNewRobotTypeWarehouseOrders", { "Lgnum": "1337", "RsrcType": "some", "RsrcGrp": "RB02", "NoWho": "2" })

					assert.deepStrictEqual(res.statusCode, 404)
				})
			})

			describe('NO_ORDER_FOUND', () => {
				it('check for correct business_error', async () => {
					let deletion = await tools.deleteAllEntities("WarehouseOrderSet", ["Lgnum", "Who"])
					await tools.allPromiseWrapper(deletion)
					let res = await tools.oDataPostFunction("GetNewRobotTypeWarehouseOrders", { "Lgnum": "1337", "RsrcType": "RB01", "RsrcGrp": "RB02", "NoWho": "2" })

					assert.deepStrictEqual(res.body.error.code, "NO_ORDER_FOUND")
				})

				it('verify that http status code is 404', async () => {
					let deletion = await tools.deleteAllEntities("WarehouseOrderSet", ["Lgnum", "Who"])
					await tools.allPromiseWrapper(deletion)
					let res = await tools.oDataPostFunction("GetNewRobotTypeWarehouseOrders", { "Lgnum": "1337", "RsrcType": "RB01", "RsrcGrp": "RB02", "NoWho": "2" })

					assert.deepStrictEqual(res.statusCode, 404)
				})
			})
		})

		describe('Success', () => {
			it('check if correct set of WarehouseOrders is returned', async () => {
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1", "Rsrc": "", "Status": "" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "2", "Rsrc": "", "Status": "D" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "3", "Rsrc": "someRobot", "Status": "" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "4", "Rsrc": "", "Status": "" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "5", "Rsrc": "", "Status": "" })

				let exp = { "d": { "results": [{ "Lgnum": "1337", "Who": "1", "Rsrc": "", "Status": "", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='1')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='1')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='1')/OpenWarehouseTasks" } } }, { "Lgnum": "1337", "Who": "4", "Rsrc": "", "Status": "", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='4')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='4')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='4')/OpenWarehouseTasks" } } }] } }
				let res = await tools.oDataPostFunction("GetNewRobotTypeWarehouseOrders", { "Lgnum": "1337", "RsrcType": "RB01", "RsrcGrp": "RB02", "NoWho": "2" })

				let deletion = await tools.deleteAllEntities("WarehouseOrderSet", ["Lgnum", "Who"])
				await tools.allPromiseWrapper(deletion)

				assert.deepStrictEqual(res.body, exp)
			})

			it('verify that http status code is 200', async () => {
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "1", "Rsrc": "", "Status": "" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "2", "Rsrc": "", "Status": "D" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "3", "Rsrc": "someRobot", "Status": "" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "4", "Rsrc": "", "Status": "" })
				await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "5", "Rsrc": "", "Status": "" })

				let exp = { "d": { "results": [{ "Lgnum": "1337", "Who": "1", "Rsrc": "", "Status": "", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='1')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='1')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='1')/OpenWarehouseTasks" } } }, { "Lgnum": "1337", "Who": "4", "Rsrc": "", "Status": "", "__metadata": { "id": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='4')", "type": "ZEWM_ROBCO_SRV.WarehouseOrder", "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='4')" }, "OpenWarehouseTasks": { "__deferred": { "uri": "/odata/SAP/ZEWM_ROBCO_SRV/WarehouseOrderSet(Lgnum='1337',Who='4')/OpenWarehouseTasks" } } }] } }
				let res = await tools.oDataPostFunction("GetNewRobotTypeWarehouseOrders", { "Lgnum": "1337", "RsrcType": "RB01", "RsrcGrp": "RB02", "NoWho": "2" })

				let deletion = await tools.deleteAllEntities("WarehouseOrderSet", ["Lgnum", "Who"])
				await tools.allPromiseWrapper(deletion)

				assert.deepStrictEqual(res.statusCode, 200)
			})
		})
	})

	after(() => {
		server.stop()
	})
})


process.env.GEN_INT = 1000
describe('Tests for Orderroutine', () => {
	before(() => {
		server.initWithOrderroutine()
	})

	it('looks if WarehouseOrderSet is initial', async () => {
		let res = await tools.getEntity("WarehouseOrderSet", {})
		assert.deepStrictEqual(res.body.d.results.length, 1)
	})

	it('waits for intervall', function (done) {
		setTimeout(() => {
			done()
		}, 2000)
	}).timeout(3000)

	it('checks if intervall creates an order', async () => {
		let res = await tools.getEntity("WarehouseOrderSet", {})
		assert.deepStrictEqual(res.body.d.results.length > 1, true)
	})

	after(() => {
		server.stop()
		setTimeout(() => {
			process.exit()
		}, 1500)
	})
})

