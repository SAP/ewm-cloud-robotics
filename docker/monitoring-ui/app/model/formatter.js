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