// #############################################################################
// ###############################   Logging    ################################
var { createLogger, format, transports } = require('winston')
var path = require('path')

var { combine, timestamp, label, printf } = format
var myFormat = printf(info => {
     return `${info.timestamp} [${info.label}] - ${info.level}: ${info.message}`
})
 
var logger = createLogger({
    format: combine(
        label({ label: '' + path.basename(__filename) }),
        timestamp(),
        myFormat
    ),
    transports: [new transports.Console()]
})


// #############################################################################
// ###############################   Envs to Config   ##########################
var users = undefined
if(process.env.ODATA_USER !== undefined && process.env.ODATA_PASSWORD !== undefined) {
    users={}
    logger.info("password + user provided, included in user list")
    users[process.env.ODATA_USER] = process.env.ODATA_PASSWORD
    logger.info("user list: " + JSON.stringify(users))
}

if(process.env.ODATA_BASEPATH === undefined ) {
    process.env.ODATA_BASEPATH="/odata/SAP/ZEWM_ROBCO_SRV"
    logger.info("process.env.ODATA_BASEPATH not defined, defaulting to \"/odata/SAP/ZEWM_ROBCO_SRV\"")
} else {
    logger.info("detected ODATA_BASEPATH env: " + process.env.ODATA_BASEPATH)
}


// #############################################################################
// ###############################   Gracefully Exiting   ######################
process.on('SIGTERM', () => {
    logger.info('Got SIGTERM. Graceful shutdown initiated at ' + (new Date().toISOString()))
    try {
        httpserver.close(() => {
            process.exit(0)
        })
    } catch(err) {
        logger.error(err)
    }})
process.on('SIGINT', () => {
    logger.info('Got SIGINT. Graceful shutdown initiated at ' + (new Date().toISOString()))
    try {
        httpserver.close(() => {
            process.exit(0)
        })
    } catch(err) {
        logger.error(err)
    }
})

// #############################################################################
// ###############################   Websocket Server    #######################
var WebSocket = require('ws')
var wssPort = 9090 

var wss = new WebSocket.Server({ port: wssPort })
logger.info('websocket server listening on port ' + wssPort)

var thereCanOnlyBeOne = true
wss.on('connection', function connection(ws) {
    logger.info("mockserver client connected to websocket server")
    if(thereCanOnlyBeOne) {
        initWebServer(ws)
        thereCanOnlyBeOne = false
    }
})


// #############################################################################
// ###############################   Webserver    ##############################
function initWebServer(socket) {
    var express = require('express')
    var https = require('https')
    var fs = require('fs')
    var compression = require('compression')
    var bodyParser = require('body-parser')
    var uuidv1 = require('uuid/v1')

    app = express()
    app.use(bodyParser.json())
    app.use(bodyParser.urlencoded({ extended: true }))
    app.use(compression())

    app.get('/', function (req, res) { 
        res.status(200).end()
    })

    app.get('/healthz', function (req, res) { 
        res.status(200).end()
    })

    app.get('/readyz', function (req, res) { 
        res.status(200).end()
    })

    if(users !== undefined) {
        var basicAuth = require('express-basic-auth')
        logger.info("user credentials detected, securing with basic auth")
        app.use(basicAuth({
            users: users,
            challenge: true,
            unauthorizedResponse: getUnauthorizedResponse
        }))

        function getUnauthorizedResponse(req) {
            let unauthorizedResponse = req.auth ? ('Credentials ' + req.auth.user + ':' + req.auth.password + ' rejected'): 'No credentials provided'
            logger.info("received unauthorized request: " + unauthorizedResponse)
            return unauthorizedResponse
        }
    }

    var callStack = {}
    socket.on('message', function incoming(message) {
        let msg = JSON.parse(message)

        logger.info('socket received response ' + msg.result.status + ' for mID ' + msg.mID + ' from mockserver')
        if(msg.result.status < 300 && msg.result.status >= 200) {
            callStack[msg.mID].res.status(msg.result.status).json(msg.result.responseJSON)
        } else if(msg.result.status === 400) {
            callStack[msg.mID].res.status(msg.result.status).json(msg.result.responseJSON)
        } else {
            callStack[msg.mID].res.status(msg.result.status).json(msg.result.responseText)
        }

        logger.info("sent response to odata consumer")

        delete callStack[msg.mID]
        logger.info("deleted request " + msg.mID + " from callStack")
    })    

    socket.on('close', () => {
        httpserver.close() 
        thereCanOnlyBeOne = true
    })

    app.all('*', function (req, res) { 
        if(req.url.includes(process.env.ODATA_BASEPATH)) {
            var mID = uuidv1()
            logger.info(req.method + ' (mID = \"' + mID + '\")  | url: ' + req.url)    
            req['ODATA_BASEPATH'] = process.env.ODATA_BASEPATH
            req['mID'] = mID

            if(req.headers['x-csrf-token'] === "Fetch") {
                res.setHeader('X-CSRF-Token', 'foobar')      
                let randomNumber=Math.random().toString()
                randomNumber=randomNumber.substring(2,randomNumber.length)
                res.cookie('someCookie',randomNumber, { maxAge: 900000 })
            }

            callStack[mID] = {
                "req" : req,
                "res" : res
            }

            socket.send(stringifyCircularReference(req))
            logger.info('forwarded to mockserver, awaiting response')
        } else {
            logger.info(req.url + ' - not interested in odata, socketserver dropped request')
        }
    })

    const HTTP_PORT = 8080
    const HTTPS_PORT = 8000
    let options = {
        key: fs.readFileSync("/app/cert/key.pem"),
        cert: fs.readFileSync("/app/cert/cert.pem")
    }
    httpserver = app.listen(HTTP_PORT, () => logger.info('http server listening on port ' + HTTP_PORT))    
    https.createServer(options, app).listen(HTTPS_PORT, () => logger.info('https server listening on port ' + HTTPS_PORT))
}


// #############################################################################
// ###############################   Helpers    ################################
function stringifyCircularReference (o) {
    // Ref: https://stackoverflow.com/questions/11616630/json-stringify-avoid-typeerror-converting-circular-structure-to-json/11616993#11616993
    // Note: cache should not be re-used by repeated calls to JSON.stringify.
    let cache = []
    let res = JSON.stringify(o, function(key, value) {
        if (typeof value === 'object' && value !== null) {
            if (cache.indexOf(value) !== -1) {
                // Duplicate reference found
                try {
                    // If this value does not reference a parent it can be deduped
                    return JSON.parse(JSON.stringify(value))
                } catch (error) {
                    // discard key if value cannot be deduped
                    return
                }
            }
            // Store value in our collection
            cache.push(value)
        }
        return value
    })
    cache = null // Enable garbage collection
    return res
}