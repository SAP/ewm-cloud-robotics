var server = require('./mockserver')

if (process.env.START_WITHOUT_ORDERROUTINE) {
    server.init()
} else {
    server.initWithOrderroutine()
}

