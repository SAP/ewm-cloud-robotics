/*
Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.

This file is part of ewm-cloud-robotics
(see https://github.com/SAP/ewm-cloud-robotics).

This file is licensed under the Apache Software License, v. 2 except as noted
otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
*/

sap.ui.define([
	'sap/ui/core/UIComponent',
	'sap/ui/model/json/JSONModel',
	'sap/f/library'
], function(UIComponent, JSONModel, fioriLibrary) {
	'use strict';

	return UIComponent.extend('monitoring.Component', {

		metadata: {
			manifest: 'json'
		},

		init: function () {
			var oModel,
				oRouter;
				
			UIComponent.prototype.init.apply(this, arguments);
				
			oModel = new JSONModel();
			this.setModel(oModel);
			
			oRouter = this.getRouter();
			oRouter.attachBeforeRouteMatched(this._onBeforeRouteMatched, this);
			oRouter.initialize();
		},

		_onBeforeRouteMatched: function(oEvent) {
			var oModel = this.getModel(),
				sLayout = oEvent.getParameters().arguments.layout;

			// If there is no layout parameter, set a default layout (normally OneColumn)
			if (!sLayout) {
				sLayout = fioriLibrary.LayoutType.OneColumn;
			}

			oModel.setProperty("/layout", sLayout);
		}
	});
});