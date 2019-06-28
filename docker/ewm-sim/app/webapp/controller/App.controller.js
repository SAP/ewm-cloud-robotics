sap.ui.define([
	"sap/ui/core/mvc/Controller"
], function(Controller) {
	"use strict";

	return Controller.extend("sap.ui.demo.MockServer.controller.App", {
		onInit: function() {
			var oModel = new sap.ui.model.json.JSONModel();
			oModel.setDefaultBindingMode(sap.ui.model.BindingMode.TwoWay);
		}
	});

});