var { createLogger, format, transports } = require('winston')
var path = require('path')

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

var request = require('request').defaults({ rejectUnauthorized: false })
var user = process.env.ODATA_USER
var pswd = process.env.ODATA_PASSWD
var auth = new Buffer.from(user + ":" + pswd).toString("base64")
var port = "8080";
if (process.env.ODATA_PORT) {
	port = process.env.ODATA_PORT
}
var protocol = "http";

module.exports = {
	createEntity(entitySet, entity) {
		let uri = protocol + "://localhost:" + port + "/odata/SAP/ZEWM_ROBCO_SRV/" + entitySet
		let options = {
			method: 'POST',
			body: entity
		}
		return this.makeRequest(uri, options)
	},

	// waitForService() {
	// 	let uri = protocol + "://localhost:" + port + "/odata/SAP/ZEWM_ROBCO_SRV/$metadata"
	// 	let options = {
	// 		method: 'GET'
	// 	}
	// 	return this.makeRequest(uri, options)
	// },

	getEntity(entitySet, oUrlParams) {
		let sUrlParams = this.buildODataPrimaryQueryFromObject(oUrlParams)
		let uri = protocol + "://localhost:" + port + "/odata/SAP/ZEWM_ROBCO_SRV/" + entitySet + sUrlParams
		let options = {
			method: 'GET',
			body: {}
		}
		return this.makeRequest(uri, options)
	},

	updateEntity(entitySet, oUrlParams, entity) {
		let sUrlParams = this.buildODataPrimaryQueryFromObject(oUrlParams)
		let uri = protocol + "://localhost:" + port + "/odata/SAP/ZEWM_ROBCO_SRV/" + entitySet + sUrlParams
		let options = {
			method: 'PATCH',
			body: entity
		}
		return this.makeRequest(uri, options)
	},

	async deleteAllEntities(entitySet, primKeys) {
		let entities = await this.getEntity(entitySet, {})
		let promiseStack = []
		entities.body.d.results.forEach(async (elem) => {
			let oUrlParams = {}
			primKeys.forEach((key) => {
				oUrlParams[key] = elem[key]
			})
			promiseStack.push(this.deleteEntity(entitySet, oUrlParams, {}))
		})
		return promiseStack
	},

	deleteEntity(entitySet, oUrlParams, entity) {
		let sUrlParams = this.buildODataPrimaryQueryFromObject(oUrlParams)
		let uri = protocol + "://localhost:" + port + "/odata/SAP/ZEWM_ROBCO_SRV/" + entitySet + sUrlParams
		let options = {
			method: 'DELETE',
			body: entity
		}
		return this.makeRequest(uri, options)
	},

	oDataPostFunction(functionName, oUrlParams) {
		let sUrlParams = this.buildUrlParamsFromObject(oUrlParams)
		let uri = protocol + "://localhost:" + port + "/odata/SAP/ZEWM_ROBCO_SRV/" + functionName + sUrlParams
		let options = {
			method: 'POST',
			body: {}
		}
		return this.makeRequest(uri, options)
	},

	oDataGetFunction(functionName, oUrlParams) {
		let sUrlParams = this.buildUrlParamsFromObject(oUrlParams)
		let uri = protocol + "://localhost:" + port + "/odata/SAP/ZEWM_ROBCO_SRV/" + functionName + sUrlParams
		let options = {
			url: uri,
			method: 'GET',
			body: {}
		}
		return this.makeRequest(uri, options)
	},

	buildUrlParamsFromObject(oUrlParams) {
		let res = "?"
		Object.keys(oUrlParams).forEach((key, index) => {
			res += key + "=" + oUrlParams[key]
			if (index < Object.keys(oUrlParams).length - 1)
				res += "&"
		})
		return res;
	},

	allPromiseWrapper(stack) {
		return new Promise((resolve) => {
			Promise.all(stack).then(() => {
				resolve()
			})
		})
	},

	buildODataPrimaryQueryFromObject(oUrlParams) {
		if (this.isEmpty(oUrlParams))
			return ""
		let res = "("
		Object.keys(oUrlParams).forEach((key, index) => {
			res += key + "='" + oUrlParams[key] + "'"
			if (index < Object.keys(oUrlParams).length - 1)
				res += ","
		})
		return (res += ")")
	},

	isEmpty(obj) {
		for (var key in obj) {
			if (obj.hasOwnProperty(key))
				return false;
		}
		return true;
	},

	makeRequest(uri, options) {
		options['headers'] = {
			"Authorization": 'Basic ' + auth,
			"Content-Type": "application/json"
		}
		options['json'] = true

		return new Promise((resolve, reject) => {
			request(
				uri,
				options,
				function (err, response) {
					if (err) {
						logger.error(err)
						reject(err)
					} else {
						logger.debug('statusCode:' + response.statusCode)
						resolve(response)
					}
				}
			)
		})
	}
}

