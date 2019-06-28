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
    transports: [ new transports.Console() ]
})


// #############################################################################
// ###############################   Webserver    ##############################
var express = require('express')
var compression = require('compression')
var path = require('path')
var bodyParser = require('body-parser')

app = express()
app.use(bodyParser.json())
app.use(bodyParser.urlencoded({ extended: false }))
app.use(compression())
const PORT = 8081

if(process.env.HOME === "/home/appuser") {
    app.use(express.static(path.join(__dirname, 'dist/')))
    app.get('*', function (req, res) {
        res.sendFile(path.join(__dirname, 'dist/', 'index.html'))
    })
} else {
    app.use(express.static(path.join(__dirname, 'webapp/')))
    app.get('*', function (req, res) {
        res.sendFile(path.join(__dirname, 'webapp/', 'index.html'))
    })
}

server = app.listen(PORT, () => logger.info('webserver listening on port ' + PORT))


// #############################################################################
// ###############################   Gracefully Exiting   ######################
var shutdown = false
process.on('SIGTERM', () => {
    if(!shutdown) {
        logger.info('Got SIGTERM. Graceful shutdown initiated at ' + (new Date().toISOString()))
        shutdown=true
    }        
    logger.info('..shutdown already in process (SIGTERM)')
    if(server) {
        server.close(() => {
            process.exit(0)
        })
    }
})
process.on('SIGINT', () => {
    if(!shutdown) {
        logger.info('Got SIGTERM. Graceful shutdown initiated at ' + (new Date().toISOString()))
        shutdown=true
    }        
    logger.info('..shutdown already in process (SIGINT)')
    if(server) {
        server.close(() => {
            process.exit(0)
        })
    }
})