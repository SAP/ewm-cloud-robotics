/*
Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.

This file is part of ewm-cloud-robotics
(see https://github.com/SAP/ewm-cloud-robotics).

This file is licensed under the Apache Software License, v. 2 except as noted
otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
*/

sap.ui.define([
	"sap/ui/model/json/JSONModel",
	"sap/ui/Device"
], function (JSONModel, Device) {
	"use strict";

	return {

		createDeviceModel: function () {
			var oModel = new JSONModel(Device);
			oModel.setDefaultBindingMode("OneWay");
			return oModel;
		}

	};
});