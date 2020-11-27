var request = require('request');
var fs = require('fs');
var path = require('path')

// Provide: 
var user = process.env.ODATA_USER
var pswd = process.env.ODATA_PASSWORD
var auth = "Basic " + new Buffer.from(user + ":" + pswd).toString("base64");

var basePath = __dirname.slice(0, __dirname.length-path.basename(path.dirname(__filename)).length-1)
basePath += "/webapp/localService/mockdata/"

async function retrieveSetList(setName, condition) {
    await request({
            url: 'https://gwaasdemo-a19efce72.hana.ondemand.com/odata/SAP/ZEWM_ROBCO_SRV/'+setName+'?$format=json&' + condition,
            headers : {
                "Authorization" : auth
            }
        }, function (err, response, body) {
            if(err) {
                console.log(err);
            }
            
            let list = JSON.parse(body).d.results
            console.log('statusCode: ' + response.statusCode + " for " + list.length + " elements in " + setName);
            set = [];

            list.forEach((elem, index) => {
                if(index<100) {
                    el = {}
                    Object.keys(elem).forEach((key) => {
                        if(!(key.includes("__"))) {
                            el[key] = elem[key];
                        }
                    });
                    set.push(el);
                }
            });

            fs.writeFile(basePath+setName+".json", JSON.stringify(set, null, 4), (err) => {
                if(err) {
                    return console.log(err);
                }
                console.log("writeFile " + basePath + setName + ".json done");
            }); 
        }
    );
}


var sets= [
    {
        "setName": "WarehouseDescriptionSet",
        "condition": ""
    },
    {
        "setName": "StorageBinSet",
        "condition": ""
    },
    {
        "setName": "WarehouseNumberSet",
        "condition": ""
    },
    {
        "setName": "RobotSet",
        "condition": ""
    },
    {
        "setName": "OpenWarehouseTaskSet",
        "condition": ""
    },
    {
        "setName": "GraphicalWarehouseLayoutObjSet",
        "condition": ""
    },
    {
        "setName": "WarehouseOrderSet",
        "condition": ""
    }
];

sets.forEach((elem) => {
    retrieveSetList(elem.setName, elem.condition);
});