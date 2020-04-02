/*
Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.

This file is part of ewm-cloud-robotics
(see https://github.com/SAP/ewm-cloud-robotics).

This file is licensed under the Apache Software License, v. 2 except as noted
otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
*/

sap.ui.define([], function () {
	"use strict";
	return {
		toDateTime: function (dateTime) {
			var date = new Date(dateTime);
			return (
				('0' + date.getDate()).slice(-2) + "." + 
				(('0' + (date.getMonth()+1)).slice(-2)) + "." + 
				date.getFullYear() + " " + 
				(('0' + (date.getHours()-1)).slice(-2)) + ":" + 
				('0' + date.getMinutes()).slice(-2) + ":" +
				('0' + date.getSeconds()).slice(-2)
			);
		},
		
		toInt: function(num) {
			return parseInt(num);
		}
	};
});