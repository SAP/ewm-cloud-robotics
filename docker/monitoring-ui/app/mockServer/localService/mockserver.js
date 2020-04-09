sap.ui.define([
	"sap/ui/core/util/MockServer",
	"sap/base/Log"
], function(MockServer, Log) {
	"use strict";

	return {
		/**
		 * Initializes the mock server.
		 * You can configure the delay with the URL parameter "serverDelay".
		 * The local mock data in this folder is returned instead of the real data for testing.
		 * @public
		 */
		init: function() {
			// create
			var oMockServer = new MockServer({
				rootUri: "/ewm-monitoring-ui/ZEWM_ROBCO_SRV/"
			});

			// simulate against the metadata and mock data
			oMockServer.simulate("/app/mockServer/localService/metadata.xml", {
				sMockdataBaseUrl: "/app/mockServer/localService/mockdata",
				bGenerateMissingMockData: true
			});
			
			// Trace requests
			Object.keys(MockServer.HTTPMETHOD).forEach(function (sMethodName) {
				var sMethod = MockServer.HTTPMETHOD[sMethodName];
				oMockServer.attachBefore(sMethod, function (oEvent) {
					var oXhr = oEvent.getParameters().oXhr;
					console.log("MockServer::before", sMethod, oXhr.url, oXhr);
				});
				oMockServer.attachAfter(sMethod, function (oEvent) {
					var oXhr = oEvent.getParameters().oXhr;
					console.log("MockServer::after", sMethod, oXhr.url, oXhr);
				});
			}.bind(this));

			// start
			oMockServer.start();

			Log.info("Running the app with mock data");
		}

	};

});