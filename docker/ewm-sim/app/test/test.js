// #############################################################################
// ###############################   Logging    ################################
var { createLogger, format, transports } = require('winston')
var path = require('path')

process.env.LOGLEVEL = 'info'

var { combine, timestamp, label, printf } = format
var myFormat = printf(info => {
     return `${info.timestamp} [${info.label}] - ${info.level}: ${info.message}`
})

var logger = createLogger({
    level: process.env.LOGLEVEL,
    format: combine(
        label({ label: '' + path.basename(__filename) }),
        timestamp(),
        myFormat
    ),
    transports: [new transports.Console()]
})


// #############################################################################
// ###############################   Tests    ##################################
var assert = require('assert')
var tools = require('../tools/toolbox.js')


describe('Deleting Entities', () => {
    describe('Delete All Robots', () => {
        it('should execute drop-if-exists', async () => {
            await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Isaac" })
            let deletion = await tools.deleteAllEntities("RobotSet", ["Lgnum", "Rsrc"])
            await tools.allPromiseWrapper(deletion)
    
            let res = await tools.getEntity("RobotSet", { })
            assert.deepEqual(res.body.d.results.length === 0, true)    
        })

        it('verify that http status code is 200', async () => {
            let deletion = await tools.deleteAllEntities("RobotSet", ["Lgnum", "Rsrc"])
            await tools.allPromiseWrapper(deletion)
    
            let res = await tools.getEntity("RobotSet", { })
            assert.deepEqual(res.statusCode, 200)    
        })
    })

    describe('Delete All OpenWarehouseTasks', () => {
        it('should execute drop-if-exists', async () => {
            await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "12345" })
            let deletion = await tools.deleteAllEntities("OpenWarehouseTaskSet", ["Lgnum", "Tanum"])
            await tools.allPromiseWrapper(deletion)
    
            let res = await tools.getEntity("OpenWarehouseTaskSet", { })
            assert.deepEqual(res.body.d.results.length === 0, true)    
        })

        it('verify that http status code is 200', async () => {
            let deletion = await tools.deleteAllEntities("OpenWarehouseTaskSet", ["Lgnum", "Tanum"])
            await tools.allPromiseWrapper(deletion)
    
            let res = await tools.getEntity("OpenWarehouseTaskSet", { })
            assert.deepEqual(res.statusCode, 200)    
        })
    })

    describe('Delete All WarehouseOrders', () => {
        it('should execute drop-if-exists', async () => {
            await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "12345" })
            let deletion = await tools.deleteAllEntities("WarehouseOrderSet", ["Lgnum", "Who"])
            await tools.allPromiseWrapper(deletion)
    
            let res = await tools.getEntity("WarehouseOrderSet", { })
            assert.deepEqual(res.body.d.results.length === 0, true)    
        })

        it('verify that http status code is 200', async () => {
            let deletion = await tools.deleteAllEntities("WarehouseOrderSet", ["Lgnum", "Who"])
            await tools.allPromiseWrapper(deletion)
    
            let res = await tools.getEntity("WarehouseOrderSet", { })
            assert.deepEqual(res.statusCode, 200)    
        })
    })
})



describe('Creating Entities', () => {
    describe('Create Robot', () => {
        it('should return json with robot', async () => {
            let exp = {"d":{"Lgnum":"1337","Rsrc":"Isaac","__metadata":{"id":"/RobotSet(Lgnum='1337',Rsrc='Isaac')","type":"ZEWM_ROBCO_SRV.Robot","uri":"/RobotSet(Lgnum='1337',Rsrc='Isaac')"}},"uri":"/RobotSet(Lgnum='1337',Rsrc='Isaac')"} 
            let res = await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Isaac" })
            assert.deepEqual(res.body, exp)    
        })

        it('verify that http status code is 201', async() => {
            let res = await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Asimov" })
            assert.deepEqual(res.statusCode, 201)
        })
    })

    describe('Create WarehouseOrder', () => {
        it('should return json with warehouseorder', async () => {
            let exp = {"d":{"Lgnum":"1337","Who":"123456","__metadata":{"id":"/WarehouseOrderSet(Lgnum='1337',Who='123456')","type":"ZEWM_ROBCO_SRV.WarehouseOrder","uri":"/WarehouseOrderSet(Lgnum='1337',Who='123456')"},"OpenWarehouseTasks":{"__deferred":{"uri":"/WarehouseOrderSet(Lgnum='1337',Who='123456')/OpenWarehouseTasks"}}},"uri":"/WarehouseOrderSet(Lgnum='1337',Who='123456')"}
            let res = await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "123456" })
            assert.deepEqual(res.body, exp)    
        })

        it('verify that http status code is 201', async() => {
            let res = await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "654321" })
            assert.deepEqual(res.statusCode, 201)
        })
    })

    describe('Create WarehouseTask', () => {
        it('should return json with warehousetask', async () => {
            let exp = {"d":{"Lgnum":"1337","Tanum":"987654","__metadata":{"id":"/OpenWarehouseTaskSet(Lgnum='1337',Tanum='987654')","type":"ZEWM_ROBCO_SRV.OpenWarehouseTask","uri":"/OpenWarehouseTaskSet(Lgnum='1337',Tanum='987654')"}},"uri":"/OpenWarehouseTaskSet(Lgnum='1337',Tanum='987654')"}
            let res = await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "987654" })
            assert.deepEqual(res.body, exp)    
        })

        it('verify that http status code is 201', async() => {
            let res = await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "123456" })
            assert.deepEqual(res.statusCode, 201)
        })
    })
})


describe('Retrieving Entities', () => {
    describe('Get Robot', () => {
        it('get robot using Lgnum and Rsrc', async () => {
            let exp = {"d":{"Lgnum":"1337","Rsrc":"Isaac","__metadata":{"id":"/RobotSet(Lgnum='1337',Rsrc='Isaac')","type":"ZEWM_ROBCO_SRV.Robot","uri":"/RobotSet(Lgnum='1337',Rsrc='Isaac')"}}}
            let res = await tools.getEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Isaac" })
            assert.deepEqual(res.body, exp)    
        })

        it('verify that http status code is 200', async() => {
            let res = await tools.getEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Isaac" })
            assert.deepEqual(res.statusCode, 200)
        })
    })

    describe('Get WarehouseOrder', () => {
        it('get warehouseorder using Lgnum and Who', async () => {
            let exp = {"d":{"Lgnum":"1337","Who":"654321","__metadata":{"id":"/WarehouseOrderSet(Lgnum='1337',Who='654321')","type":"ZEWM_ROBCO_SRV.WarehouseOrder","uri":"/WarehouseOrderSet(Lgnum='1337',Who='654321')"},"OpenWarehouseTasks":{"__deferred":{"uri":"/WarehouseOrderSet(Lgnum='1337',Who='654321')/OpenWarehouseTasks"}}}}
            let res = await tools.getEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "654321" })
            assert.deepEqual(res.body, exp)    
        })

        it('verify that http status code is 200', async() => {
            let res = await tools.getEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "654321" })
            assert.deepEqual(res.statusCode, 200)
        })
    })

    describe('Get WarehouseTask', () => {
        it('get warehousetask using Lgnum and Tanum', async () => {
            let exp = {"d":{"Lgnum":"1337","Tanum":"123456","__metadata":{"id":"/OpenWarehouseTaskSet(Lgnum='1337',Tanum='123456')","type":"ZEWM_ROBCO_SRV.OpenWarehouseTask","uri":"/OpenWarehouseTaskSet(Lgnum='1337',Tanum='123456')"}}}
            let res = await tools.getEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "123456" })
            assert.deepEqual(res.body, exp)    
        })

        it('verify that http status code is 200', async() => {
            let res = await tools.getEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "123456" })
            assert.deepEqual(res.statusCode, 200)
        })
    })
})


describe('Retrieving Entitylists', () => {
    describe('Get Robots', () => {
        it('get all robots', async () => {
            let res = await tools.getEntity("RobotSet", { })
            assert.deepEqual(res.body.d.results.length >= 1, true)    
        })

        it('verify that http status code is 200', async() => {
            let res = await tools.getEntity("RobotSet", { })
            assert.deepEqual(res.statusCode, 200)
        })
    })

    describe('Get WarehouseOrders', () => {
        it('get all warehouseorders', async () => {
            let res = await tools.getEntity("WarehouseOrderSet", { })
            assert.deepEqual(res.body.d.results.length >= 1, true)
        })

        it('verify that http status code is 200', async() => {
            let res = await tools.getEntity("WarehouseOrderSet", { })
            assert.deepEqual(res.statusCode, 200)
        })
    })

    describe('Get WarehouseTasks', () => {
        it('get all warehousetasks', async () => {
            let res = await tools.getEntity("OpenWarehouseTaskSet", { })
            assert.deepEqual(res.body.d.results.length >= 1, true)
        })

        it('verify that http status code is 200', async() => {
            let res = await tools.getEntity("OpenWarehouseTaskSet", { })
            assert.deepEqual(res.statusCode, 200)
        })
    })
})


describe('Update Entities', () => {
    describe('Update Robot', () => {
        it('verify that http status code is 204', async() => {
            let res = await tools.updateEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Asimov" }, { "RsrcGrp": "Uberfleet" })
            assert.deepEqual(res.statusCode, 204)
        })

        it('verify that patch was correct', async() => {
            let res = await tools.getEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Asimov" })
            assert.deepEqual(res.body.d.RsrcGrp, "Uberfleet")
        })
    })
})


describe('Malformed Requests', () => {
    describe('Retrieve Unknown Entity', () => {
        it('verify that http status code is 404', async() => {
            let res = await tools.getEntity("RobotSet", { "Lgnum": "13371337", "Rsrc": "Tron" })
            assert.deepEqual(res.statusCode, 404)
        })
    })

    describe('Point to Illegal Entityset', () => {
        it('verify that http status code is 404', async() => {
            let res = await tools.createEntity("ProtoSet", { "abc" : "123!" })
            assert.deepEqual(res.statusCode, 404)
        })
    })
})


describe('Custom Function \'GetNewRobotWarehouseOrder\'', () => {
    describe('Errorcases', () => {
        describe('ROBOT_NOT_FOUND', () => {
            it('check for correct business_error', async() => {
                let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { })
                assert.deepEqual(res.body.error.code, "ROBOT_NOT_FOUND")
            })
            
            it('verify that http status code is 400', async() => {
                let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { })
                assert.deepEqual(res.statusCode, 400)
            })
        })

        describe('NO_ORDER_FOUND', () => {
            it('check for correct business_error', async() => {
                let deletion = await tools.deleteAllEntities("WarehouseOrderSet", ["Lgnum", "Who"])
                await tools.allPromiseWrapper(deletion)
                
                let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { "Lgnum" : "1337", "Rsrc": "Isaac" })
                assert.deepEqual(res.body.error.code, "NO_ORDER_FOUND")
            })
            
            it('verify that http status code is 400', async() => {
                let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { "Lgnum" : "1337", "Rsrc": "Isaac" })
                assert.deepEqual(res.statusCode, 400)
            })
        })

        describe('ROBOT_HAS_ORDER', () => {
            it('check for correct business_error', async() => {
                await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "123456", "Rsrc": "Isaac", "Status": "D" })

                let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { "Lgnum" : "1337", "Rsrc": "Isaac" })
                assert.deepEqual(res.body.error.code, "ROBOT_HAS_ORDER")
            })
            
            it('verify that http status code is 400', async() => {
                await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "123456", "Rsrc": "Asimov", "Status": "D" })

                let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { "Lgnum" : "1337", "Rsrc": "Asimov" })
                assert.deepEqual(res.statusCode, 400)
            })
        })
    })

    describe('Success', () => {
        it('verify that Rsrc in who is set and Status is \'D\'', async() => {
            await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Cobot" })
            await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "123456789", "Rsrc": "", "Status": "" })
            
            let exp = {"d":{"Lgnum":"1337","Who":"123456789","Rsrc":"Cobot","Status":"D","__metadata":{"id":"/WarehouseOrderSet(Lgnum='1337',Who='123456789')","type":"ZEWM_ROBCO_SRV.WarehouseOrder","uri":"/WarehouseOrderSet(Lgnum='1337',Who='123456789')"},"OpenWarehouseTasks":{"__deferred":{"uri":"/WarehouseOrderSet(Lgnum='1337',Who='123456789')/OpenWarehouseTasks"}}}}
            let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { "Lgnum" : "1337", "Rsrc": "Cobot" })            
            assert.deepEqual(res.body, exp)
        })
        
        it('verify that http status code is 200', async() => {
            await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Cobot123" })
            await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "987654321", "Rsrc": "", "Status": "" })

            let res = await tools.oDataPostFunction("GetNewRobotWarehouseOrder", { "Lgnum" : "1337", "Rsrc": "Cobot123" })            
            assert.deepEqual(res.statusCode, 200)
        })
    })
})


describe('Custom Function \'GetRobotWarehouseOrders\'', () => {
    describe('Errorcases', () => {
        describe('ROBOT_NOT_FOUND', () => {
            it('check for correct business_error', async() => {
                let res = await tools.oDataGetFunction("GetRobotWarehouseOrders", { })
                assert.deepEqual(res.body.error.code, "ROBOT_NOT_FOUND")
            })
            
            it('verify that http status code is 400', async() => {
                let res = await tools.oDataGetFunction("GetRobotWarehouseOrders", { })
                assert.deepEqual(res.statusCode, 400)
            })
        })

        describe('NO_ORDER_FOUND', () => {
            it('check for correct business_error', async() => {
                await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Turtlebot" })

                let res = await tools.oDataGetFunction("GetRobotWarehouseOrders", { "Lgnum" : "1337", "Rsrc": "Turtlebot" })
                assert.deepEqual(res.body.error.code, "NO_ORDER_FOUND")
            })
            
            it('verify that http status code is 400', async() => {
                await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "Turtlebot-B" })

                let res = await tools.oDataGetFunction("GetRobotWarehouseOrders", { "Lgnum" : "1337", "Rsrc": "Turtlebot-B" })
                assert.deepEqual(res.statusCode, 400)
            })
        })
    })

    describe('Success', () => {
        it('verify that who is returned', async() => {
            await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "123456789", "Rsrc": "Turtlebot", "Status": "D" })
            
            let exp = {"d":{"results":[{"Lgnum":"1337","Who":"123456789","Rsrc":"Turtlebot","Status":"D","__metadata":{"id":"/WarehouseOrderSet(Lgnum='1337',Who='123456789')","type":"ZEWM_ROBCO_SRV.WarehouseOrder","uri":"/WarehouseOrderSet(Lgnum='1337',Who='123456789')"},"OpenWarehouseTasks":{"__deferred":{"uri":"/WarehouseOrderSet(Lgnum='1337',Who='123456789')/OpenWarehouseTasks"}}}]}}
            let res = await tools.oDataGetFunction("GetRobotWarehouseOrders", { "Lgnum" : "1337", "Rsrc": "Turtlebot" })
            assert.deepEqual(res.body, exp)
        })

        it('verify that http status code is 200', async() => {
            await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "123456789", "Rsrc": "Turtlebot-B", "Status": "D" })

            let res = await tools.oDataGetFunction("GetRobotWarehouseOrders", { "Lgnum" : "1337", "Rsrc": "Turtlebot-B" })
            assert.deepEqual(res.statusCode, 200)
        })
    })
})


describe('Custom Function \'ConfirmWarehouseTaskFirstStep\'', () => {
    describe('Errorcases', () => {
        describe('WAREHOUSE_TASK_NOT_CONFIRMED', () => {
            describe('wht does not exist', () => {
                it('check for correct business_error', async() => {
                    let deletion = await tools.deleteAllEntities("OpenWarehouseTaskSet", ["Lgnum", "Tanum"])
                    await tools.allPromiseWrapper(deletion)
    
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Cobot123" })            
                    assert.deepEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
                })

                it('verify that http status code is 400', async() => {
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Cobot123" })            
                    assert.deepEqual(res.statusCode, 400)
                })
            })
            
            describe('who \'Status\' is already \'C\'', () => {
                it('check for correct business_error', async() => {
                    await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "abcde", "Rsrc": "Isaac", "Status": "C" })
                    await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Who": "abcde", "Tanum": "abcde", "Tostat": "C" })
    
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Isaac" })            
                    assert.deepEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
                })

                it('verify that http status code is 400', async() => {
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Isaac" })            
                    assert.deepEqual(res.statusCode, 400)
                })
            })

            describe('wht \'Tostat\' is already \'C\'', () => {
                it('check for correct business_error', async() => {
                    await tools.updateEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "abcde" }, { "Status": "" })
    
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Isaac" })            
                    assert.deepEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
                })

                it('verify that http status code is 400', async() => {
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Isaac" })            
                    assert.deepEqual(res.statusCode, 400)
                })
            })
        })
    })

    describe('Success', () => {
        it('wht is returned and \'Vltyp\', \'Vlber\' and \'Vlpla\' are deleted', async() => {
            await tools.updateEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "abcde" }, { "Tostat": "" })

            let exp = {"d":{"Lgnum":"1337","Who":"abcde","Tanum":"abcde","Tostat":"","__metadata":{"id":"/OpenWarehouseTaskSet(Lgnum='1337',Tanum='abcde')","type":"ZEWM_ROBCO_SRV.OpenWarehouseTask","uri":"/OpenWarehouseTaskSet(Lgnum='1337',Tanum='abcde')"},"Vltyp":"","Vlber":"","Vlpla":""}}
            let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Isaac" })            
            assert.deepEqual(res.body, exp)
        })
        
        it('verify that http status code is 200', async() => {
            await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "213", "Rsrc": "Isaac", "Status": "" })
            await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Who": "213", "Tanum": "4321", "Tostat": "" })

            let res = await tools.oDataPostFunction("ConfirmWarehouseTaskFirstStep", { "Lgnum" : "1337", "Tanum": "4321", "Rsrc": "Isaac" })            
            assert.deepEqual(res.statusCode, 200)
        })
    })
})


describe('Custom Function \'ConfirmWarehouseTask\'', () => {
    describe('Errorcases', () => {
        describe('WAREHOUSE_TASK_NOT_CONFIRMED', () => {
            describe('wht does not exist', () => {
                it('check for correct business_error', async() => {
                    let deletion = await tools.deleteAllEntities("OpenWarehouseTaskSet", ["Lgnum", "Tanum"])
                    await tools.allPromiseWrapper(deletion)
    
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Cobot123" })            
                    assert.deepEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
                })

                it('verify that http status code is 400', async() => {
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Cobot123" })            
                    assert.deepEqual(res.statusCode, 400)
                })
            })
            
            describe('who \'Status\' is already \'C\'', () => {
                it('check for correct business_error', async() => {
                    let deletion = await tools.deleteAllEntities("WarehouseOrderSet", ["Lgnum", "Who"])
                    await tools.allPromiseWrapper(deletion)

                    await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "abcde", "Rsrc": "Isaac", "Status": "C" })
                    await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Who": "abcde", "Tanum": "abcde", "Tostat": "C" })
    
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Isaac" })            
                    assert.deepEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
                })

                it('verify that http status code is 400', async() => {
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Isaac" })            
                    assert.deepEqual(res.statusCode, 400)
                })
            })

            describe('wht \'Tostat\' is already \'C\'', () => {
                it('check for correct business_error', async() => {
                    await tools.updateEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "abcde" }, { "Status": "" })
    
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Isaac" })            
                    assert.deepEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
                })

                it('verify that http status code is 400', async() => {
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Isaac" })            
                    assert.deepEqual(res.statusCode, 400)
                })
            })

            describe('who includes other incomplete tasks', () => {
                it('check for correct business_error', async() => {
                    await tools.createEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Who": "abcde", "Tanum": "54321", "Tostat": "" })
    
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Isaac" })            
                    assert.deepEqual(res.body.error.code, "WAREHOUSE_TASK_NOT_CONFIRMED")
                })

                it('verify that http status code is 400', async() => {
                    let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Isaac" })            
                    assert.deepEqual(res.statusCode, 400)
                })
            })
        })
    })

    describe('Success', () => {
        it('who is returned and \'Status\' is \'C\'', async() => {
            await tools.updateEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "54321" }, { "Tostat": "C" })
            await tools.updateEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "abcde" }, { "Tostat": "" })

            let exp= {"d":{"Lgnum":"1337","Who":"abcde","Rsrc":"Isaac","Status":"C","__metadata":{"id":"/WarehouseOrderSet(Lgnum='1337',Who='abcde')","type":"ZEWM_ROBCO_SRV.WarehouseOrder","uri":"/WarehouseOrderSet(Lgnum='1337',Who='abcde')"},"OpenWarehouseTasks":{"__deferred":{"uri":"/WarehouseOrderSet(Lgnum='1337',Who='abcde')/OpenWarehouseTasks"}}}}
            let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Isaac" })            
            assert.deepEqual(res.body, exp)
        })

        it('verify that http status code is 200', async() => {
            await tools.updateEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "54321" }, { "Tostat": "C" })
            await tools.updateEntity("OpenWarehouseTaskSet", { "Lgnum": "1337", "Tanum": "abcde" }, { "Tostat": "" })
            await tools.updateEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "abcde" }, { "Status": "" })

            let res = await tools.oDataPostFunction("ConfirmWarehouseTask", { "Lgnum" : "1337", "Tanum": "abcde", "Rsrc": "Isaac" })            
            assert.deepEqual(res.statusCode, 200)
        })
    })
})


describe('Custom Function \'SendFirstConfirmationError\'', () => {
    describe('Errorcases', () => {
        describe('ROBOT_NOT_FOUND', () => {
            it('check for correct business_error', async() => {
                let res = await tools.oDataPostFunction("SendFirstConfirmationError", { "Lgnum" : "1337", "Who": "someWho", "Rsrc": "someRobot" })
                assert.deepEqual(res.body.error.code, "ROBOT_NOT_FOUND")
            })
            
            it('verify that http status code is 400', async() => {
                let res = await tools.oDataPostFunction("SendFirstConfirmationError", { "Lgnum" : "1337", "Who": "someWho", "Rsrc": "someRobot" })
                assert.deepEqual(res.statusCode, 400)
            })
        })

        describe('NO_ORDER_FOUND', () => {
            it('check for correct business_error', async() => {
                await tools.createEntity("RobotSet", { "Lgnum": "1337", "Rsrc": "someRobot" })

                let res = await tools.oDataPostFunction("SendFirstConfirmationError", { "Lgnum" : "1337", "Who": "someWho", "Rsrc": "someRobot" })
                assert.deepEqual(res.body.error.code, "NO_ORDER_FOUND")
            })
            
            it('verify that http status code is 400', async() => {
                let res = await tools.oDataPostFunction("SendFirstConfirmationError", { "Lgnum" : "1337", "Who": "someWho", "Rsrc": "someRobot" })
                assert.deepEqual(res.statusCode, 400)
            })
        })
    })

    describe('Success', () => {
        it('who is returned and \'Status\'=\"\", \'Rsrc\'=\"\" and \'Queue\'=\"ERROR\"', async() => {
            await tools.createEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "someWho" , "Rsrc": "someRobot", "Status": "D", "Queue": "someQueue" })

            let exp = {"d":{"Lgnum":"1337","Who":"someWho","Rsrc":"","Status":"","Queue":"ERROR","__metadata":{"id":"/WarehouseOrderSet(Lgnum='1337',Who='someWho')","type":"ZEWM_ROBCO_SRV.WarehouseOrder","uri":"/WarehouseOrderSet(Lgnum='1337',Who='someWho')"},"OpenWarehouseTasks":{"__deferred":{"uri":"/WarehouseOrderSet(Lgnum='1337',Who='someWho')/OpenWarehouseTasks"}}}}
            let res = await tools.oDataPostFunction("SendFirstConfirmationError", { "Lgnum" : "1337", "Who": "someWho", "Rsrc": "someRobot" })
            assert.deepEqual(res.body, exp)
        })

        it('verify that http status code is 200', async() => {
            await tools.updateEntity("WarehouseOrderSet", { "Lgnum": "1337", "Who": "someWho" }, { "Queue": "someRobot", "Rsrc": "someRobot", "Status": "D" })

            let res = await tools.oDataPostFunction("SendFirstConfirmationError", { "Lgnum" : "1337", "Who": "someWho", "Rsrc": "someRobot" })
            assert.deepEqual(res.statusCode, 200)
        })
    })
})

