var exec = require('child-process-promise').exec;
var tools = require('./toolbox.js')

var counter = 1

async function continueWaitingForService(rejection) {
    if(counter <= 150) {
        setTimeout(() => {
            console.log("Attempt: " + counter)
            counter += 1
            tools.waitForService().then(serviceAvailable).catch(continueWaitingForService)
        }, 333)
    } else {
        console.log("Server did not become available")
        process.exit(1)
    }
}

function serviceAvailable() {
    if(process.argv[2] === "test") {
        console.log("Execute test.js")
        exec('npm test').then((result) => {
            var stdout = result.stdout
            var stderr = result.stderr
            console.log(stdout)
            console.log(stderr)
        })
        .catch(function (err) {
            console.error('ERROR: ', err)
        })
    }
}

tools.waitForService().then(serviceAvailable).catch(continueWaitingForService)