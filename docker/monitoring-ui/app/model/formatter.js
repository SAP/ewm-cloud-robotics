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
			if(typeof(dateTime) === "undefined") {
				return this.getOwnerComponent().getModel("i18n").getResourceBundle().getText("na");
			}
			var date = new Date(dateTime);
			return (
				('0' + date.getDate()).slice(-2) + "." + 
				(('0' + (date.getMonth()+1)).slice(-2)) + "." + 
				date.getFullYear() + " " + 
				(('0' + (date.getHours())).slice(-2)) + ":" + 
				('0' + date.getMinutes()).slice(-2) + ":" +
				('0' + date.getSeconds()).slice(-2)
			);
        },
        
        lsdToDateTime: function(lsd) {
            if(typeof(lsd) === "undefined") {
				return this.getOwnerComponent().getModel("i18n").getResourceBundle().getText("na");
            }
            var lsdString = lsd.toString();
            var dateString = lsdString.substring(0,4) + "-" + lsdString.substring(4,6) + "-" + lsdString.substring(6,8) + "T" + lsdString.substring(8,10) + ":" + lsdString.substring(10,12) + ":" + lsdString.substring(12,14);
			var date = new Date(dateString);
			return (
				('0' + date.getDate()).slice(-2) + "." + 
				(('0' + (date.getMonth()+1)).slice(-2)) + "." + 
				date.getFullYear() + " " + 
				(('0' + (date.getHours())).slice(-2)) + ":" + 
				('0' + date.getMinutes()).slice(-2) + ":" +
				('0' + date.getSeconds()).slice(-2)
			);
        },
		
		toInt: function(num) {
			return parseInt(num);
		},
		
		toVisible: function(value) {
			if(typeof(value) === "undefined") {
				return false;
			}
			return true;
		},
		
		toRobotState: function(state) {
			if(typeof(state) === "undefined") {
				return "None";
			}
			if(state === "AVAILABLE") {
				return "Success";
			}
			return "Error";
		}
	};
});