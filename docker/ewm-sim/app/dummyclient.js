// #############################################################################
// ###############################   Logging    ################################
var { createLogger, format, transports } = require('winston');
var path = require('path');

var { combine, timestamp, label, printf } = format;
var myFormat = printf(info => {
     return `${info.timestamp} [${info.label}] - ${info.level}: ${info.message}`;
});
 
var logger = createLogger({
    format: combine(
        label({ label: '' + path.basename(__filename) }),
        timestamp(),
        myFormat
    ),
    transports: [new transports.Console()]
});


// #############################################################################
// ###############################   Gracefully Exiting   ######################
process.on('SIGTERM', () => {
    logger.info('Got SIGTERM. Graceful shutdown initiated at ' + (new Date().toISOString()))
    process.exit(0)
})
process.on('SIGINT', () => {
    logger.info('Got SIGINT. Graceful shutdown initiated at ' + (new Date().toISOString()))
    process.exit(0)
})


// #############################################################################
// ###############################   Chrome + Session   ########################
const chromeLauncher = require('chrome-launcher');
const CDP = require('chrome-remote-interface');

(async function() {
    async function launchChrome() {
        return await chromeLauncher.launch({
            chromeFlags: [
                "--disable-background-networking", 
                //Disable installation of default apps on first run
                "--disable-default-apps", 
                //Disable all chrome extensions entirely
                "--disable-extensions", 
                //Disable the GPU hardware acceleration
                "--disable-gpu", 
                //Disable syncing to a Google account
                "--disable-sync", 
                //Disable built-in Google Translate service
                "--disable-translate", 
                //Run in headless mode
                "--headless", 
                //Hide scrollbars on generated images/PDFs
                "--hide-scrollbars", 
                //Disable reporting to UMA, but allows for collection
                "--metrics-recording-only", 
                //Mute audio
                "--mute-audio", 
                //Skip first run wizards
                "--no-first-run", 
                //Disable sandbox mode
                //TODO get this running without it
                "--no-sandbox", 
                //Disable fetching safebrowsing lists, likely 
                //redundant due to disable-background-networking
                "--safebrowsing-disable-auto-update",
                // Disable cache
                "--disk-cache-size=1",
                "--disk-cache-dir=/dev/null"
            ]
        });
    }
  
    const chrome = await launchChrome();
    const protocol = await CDP({
        port: chrome.port
    });

    const {
        DOM,
        Network,
        Page,
        Emulation,
        Runtime,
        Console
    } = protocol;

    await Promise.all([Network.enable(), Page.enable(), DOM.enable(), Runtime.enable(), Console.enable()]);
    await Page.navigate({url: 'http://localhost:8081/index.html'});

    Console.messageAdded((result) => {
        if(typeof(result.message.text) !== "string") {
            logger.info(JSON.stringify(result.message.text))
        } else {
            logger.info(result.message.text)
        }
    });
})();