sap.ui.define([
	"sap/ui/core/mvc/Controller",
	"sap/ui/model/json/JSONModel",
	"monitoring/model/formatter",
	'sap/f/library',
	'sap/m/MessageToast'
], function (Controller, JSONModel, formatter, fioriLibrary, MessageToast) {
	"use strict";

	return Controller.extend("monitoring.controller.Detail", {
		formatter: formatter,
		
		onInit: function () {
			var oOwnerComponent = this.getOwnerComponent();
			
			this.getOwnerComponent().setModel(new JSONModel(), "viewType");

			this.oRouter = oOwnerComponent.getRouter();
			this.oModel = oOwnerComponent.getModel();
			
			this.oRouter.getRoute("robotDetail").attachPatternMatched(this._onRobotRouteMatched, this);
			this.oRouter.getRoute("whoDetail").attachPatternMatched(this._onWhoRouteMatched, this);
			this.oRouter.getRoute("whoDetailFullscreen").attachPatternMatched(this._onWhoRouteMatched, this);
			this.oRouter.getRoute("robotDetailFullscreen").attachPatternMatched(this._onRobotRouteMatched, this);
		},
		
		_bindRobotConfiguration: function(robotName) {
			var that = this;
			$.get( this.getOwnerComponent().getModel("src").getData().robotConfigurations, function( data ) {
				var robotConfigurationJSON = {};
				for(var i=0; i< data.items.length; ++i) {
					if(data.items[i].kind !== "RobotConfiguration") {
						continue;
					}
					if(data.items[i].metadata.name !== robotName) {
						continue;
					}
					
					robotConfigurationJSON = ({
						"selfLink": data.items[i].metadata.selfLink,
						"name": data.items[i].metadata.name,
						"batteryIdle": data.items[i].spec.batteryIdle,
						"batteryMin": data.items[i].spec.batteryMin,
						"batteryOk": data.items[i].spec.batteryOk,
						"lgnum": data.items[i].spec.lgnum,
						"maxIdleTime": data.items[i].spec.maxIdleTime,
						"recoverFromRobotError": data.items[i].spec.recoverFromRobotError,
						"rsrcgrp": data.items[i].spec.rsrcgrp,
						"rsrctype": data.items[i].spec.rsrctype,
						"chargers": data.items[i].spec.chargers,
						"status": data.items[i].status
					});
					
					that.getOwnerComponent().setModel(new JSONModel(robotConfigurationJSON), "robotConfig");
					return;
				}
			});
		},
		
		_bindWhoConfiguration: function(warhouseOrder) {
			var that = this;
			$.get( this.getOwnerComponent().getModel("src").getData().warehouseOrders, function( data ) {
				var whoJSON = {};
				for(var i=0; i< data.items.length; ++i) {
					if(data.items[i].kind !== "WarehouseOrder") {
						continue;
					}
					if(data.items[i].spec.data.who !== warhouseOrder) {
						continue;
					}
					
					whoJSON = ({
						"who": data.items[i].spec.data.who,
						"areawho": data.items[i].spec.data.areawho,
						"flgto": data.items[i].spec.data.flgto,
						"flgwho": data.items[i].spec.data.flgwho,
						"lgnum": data.items[i].spec.data.lgnum,
						"lgtyp": data.items[i].spec.data.lgtyp,
						"lsd": data.items[i].spec.data.lsd,
						"queue": data.items[i].spec.data.queue,
						"refwhoid": data.items[i].spec.data.refwhoid,
						"rsrc": data.items[i].spec.data.rsrc,
						"status": data.items[i].spec.order_status,
						"topwhoid": data.items[i].spec.data.topwhoid,
						"warehousetasks": [],
						"process_status": []
					});
					
					if("warehousetasks" in data.items[i].spec.data) {
						whoJSON.warehousetasks = data.items[i].spec.data.warehousetasks;
					}
					if("process_status" in data.items[i].spec) {
						whoJSON.process_status = data.items[i].spec.process_status;
					}
					
					that.getOwnerComponent().setModel(new JSONModel(whoJSON), "whoDetail");
					return;
				}
			});
		},
		
		handleSave: function() {
			var that = this;
			var configData = this.getOwnerComponent().getModel("robotConfig").getData();
			var patchData = {};
			patchData["spec"] = {};
			patchDaat.spec["batteryIdle"] = parseInt(configData.batteryIdle);
			patchData.spec["batteryMin"] = parseInt(configData.batteryMin);
			patchData.spec["batteryOk"] = parseInt(configData.batteryOk);
			patchData.spec["maxIdleTime"] = parseInt(configData.maxIdleTime);
			patchData.spec["lgnum"] = configData.lgnum;
			patchData.spec["rsrcgrp"] = configData.rsrcgrp;
			patchData.spec["rsrctype"] = configData.rsrctype;
			
			$.ajax({
			   type: 'PATCH',
			   url: configData.selfLink,
			   data: JSON.stringify(patchData),
			   processData: false,
			   contentType: 'application/merge-patch+json',
			   success: function() {
					MessageToast.show(that.getOwnerComponent().getModel("i18n").getResourceBundle().getText("successPatch"));
			   },
			   error: function() {
					MessageToast.show(that.getOwnerComponent().getModel("i18n").getResourceBundle().getText("errorPatch"));
			   }
			});
		},
		
		handleClose: function() {
			this.oRouter.navTo("master");
		},
		
		handleRobotFullscreen: function() {
			if(this.getOwnerComponent().getModel("viewType").getData().layout === fioriLibrary.LayoutType.MidColumnFullScreen) {
				// Exit Fullscreen
				this.oRouter.navTo("robotDetail", {layout: fioriLibrary.LayoutType.TwoColumnsMidExpanded, robot: this._robotName});
			}
			else {
				// Enter Fullscreen
				this.oRouter.navTo("robotDetailFullscreen", {layout: fioriLibrary.LayoutType.MidColumnFullScreen, robot: this._robotName});
			}
		},
		
		handleWhoFullscreen: function() {
			if(this.getOwnerComponent().getModel("viewType").getData().layout === fioriLibrary.LayoutType.MidColumnFullScreen) {
				// Exit Fullscreen
				this.oRouter.navTo("whoDetail", {layout: fioriLibrary.LayoutType.TwoColumnsMidExpanded, who: this._warhouseOrder});
			}
			else {
				// Enter Fullscreen
				this.oRouter.navTo("whoDetailFullscreen", {layout: fioriLibrary.LayoutType.MidColumnFullScreen, who: this._warhouseOrder});
			}
		},
		
		_onRobotRouteMatched: function (oEvent) {
			this.getOwnerComponent().getModel("viewType").setData({"robot": true, "who": false, "layout": oEvent.getParameter("arguments").layout});
			this._robotName = oEvent.getParameter("arguments").robot;
			this._bindRobotConfiguration(this._robotName);
		},
		
		_onWhoRouteMatched: function (oEvent) {
			this.getOwnerComponent().getModel("viewType").setData({"robot": false, "who": true, "layout": oEvent.getParameter("arguments").layout});
			this._warhouseOrder = oEvent.getParameter("arguments").who;
			this._bindWhoConfiguration(this._warhouseOrder);
		},

		onExit: function () {
			this.oRouter.getRoute("whoDetail").detachPatternMatched(this._onRobotRouteMatched, this);
			this.oRouter.getRoute("robotDetail").detachPatternMatched(this._onWhoRouteMatched, this);
			this.oRouter.getRoute("whoDetailFullscreen").detachPatternMatched(this._onWhoRouteMatched, this);
			this.oRouter.getRoute("robotDetailFullscreen").detachPatternMatched(this._onRobotRouteMatched, this);
		}
	});
});