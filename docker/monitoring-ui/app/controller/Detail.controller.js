/*
Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.

This file is part of ewm-cloud-robotics
(see https://github.com/SAP/ewm-cloud-robotics).

This file is licensed under the Apache Software License, v. 2 except as noted
otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
*/

sap.ui.define([
	"sap/ui/core/mvc/Controller",
	"sap/ui/model/json/JSONModel",
	"monitoring/model/formatter",
	'sap/f/library',
	'sap/m/MessageToast',
	"sap/ui/model/Filter"
], function (Controller, JSONModel, formatter, fioriLibrary, MessageToast, Filter) {
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

			sap.ui.getCore().getEventBus().subscribe("Master", "UpdateEvent", this.updateModels, this);
		},

		updateModels: function() {
			if(this.getOwnerComponent().getModel("viewType").getProperty("/robot")) {
				this._bindRobotConfiguration(this._robotName);
			}
			else {
				this._bindWhoConfiguration(this._warhouseOrder);
			}
		},

		_bindRobotConfiguration: function (robotName) {
			var that = this;
			$.get(this.getOwnerComponent().getModel("src").getData().robotConfigurations, function (data) {
				var robotConfigurationJSON = {};
				for (var i = 0; i < data.items.length; ++i) {
					if (data.items[i].kind !== "RobotConfiguration") {
						continue;
					}
					if (data.items[i].metadata.name !== robotName) {
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
					
					var statemachine_error = false;
					var statemachine_uistate = "None";
					if (data.items[i].hasOwnProperty("status")) {
						if (data.items[i].status.hasOwnProperty("statemachine")) {
							if (["robotError", "moveTrolley_waitingForErrorRecovery", "pickPackPass_waitingForErrorRecovery"].includes(data.items[i].status.statemachine)) {
								statemachine_error = true;
								statemachine_uistate = "Error";
							}
							else 
							{
								statemachine_uistate = "Success";
							}
						}
					}
					robotConfigurationJSON.statemachine_error = statemachine_error;
					robotConfigurationJSON.statemachine_uistate = statemachine_uistate;

					that.getOwnerComponent().setModel(new JSONModel(robotConfigurationJSON), "robotConfig");
					return;
				}
			});
		},

		_bindWhoConfiguration: function (warhouseOrder) {
			var that = this;
			$.get(this.getOwnerComponent().getModel("src").getData().warehouseOrders, function (data) {
				var whoJSON = {};
				for (var i = 0; i < data.items.length; ++i) {
					if (data.items[i].kind !== "WarehouseOrder") {
						continue;
					}
					if (data.items[i].spec.data.who !== warhouseOrder) {
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

					if ("warehousetasks" in data.items[i].spec.data) {
						whoJSON.warehousetasks = data.items[i].spec.data.warehousetasks;
					}
					if ("process_status" in data.items[i].spec) {
						whoJSON.process_status = data.items[i].spec.process_status;
					}

					that.getOwnerComponent().setModel(new JSONModel(whoJSON), "whoDetail");
					return;
				}
			});
		},

		handleSave: function () {
			var that = this;
			var configData = this.getOwnerComponent().getModel("robotConfig").getData();
			var patchData = {};
			patchData["spec"] = {};
			patchData.spec["batteryIdle"] = parseInt(configData.batteryIdle);
			patchData.spec["batteryMin"] = parseInt(configData.batteryMin);
			patchData.spec["batteryOk"] = parseInt(configData.batteryOk);
			patchData.spec["chargers"] = configData.chargers;
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
				success: function () {
					MessageToast.show(that.getOwnerComponent().getModel("i18n").getResourceBundle().getText("successPatch"));
				},
				error: function () {
					MessageToast.show(that.getOwnerComponent().getModel("i18n").getResourceBundle().getText("errorPatch"));
				}
			});
		},
		
		recoverFromErrorPressed: function() {
			var that = this;
			var patchData = {};
			patchData["spec"] = {};
			patchData.spec["recoverFromRobotError"] = true;
			$.ajax({
				type: 'PATCH',
				url: this.getOwnerComponent().getModel("robotConfig").getData().selfLink,
				data: JSON.stringify(patchData),
				processData: false,
				contentType: 'application/merge-patch+json',
				success: function () {
					MessageToast.show(that.getOwnerComponent().getModel("i18n").getResourceBundle().getText("successPatch"));
				},
				error: function () {
					MessageToast.show(that.getOwnerComponent().getModel("i18n").getResourceBundle().getText("errorPatch"));
				}
			});
		},

		handleChargerAdd: function () {
			var chargers = this.getOwnerComponent().getModel("robotConfig").getProperty("/chargers");
			chargers.push("");
			this.getOwnerComponent().getModel("robotConfig").setProperty("/chargers", chargers);
		},

		handleChargerRemove: function () {
			var chargers = this.getOwnerComponent().getModel("robotConfig").getProperty("/chargers");
			var selections = this.getView().byId("idChargers").getSelectedItems();
			var binding;
			for (var i = 0; i < selections.length; ++i) {
				binding = selections[i].getBindingContextPath().split("/"); //last index of contains the index of object in json model
				chargers.splice(binding[binding.length - 1], 1);
			}
			this.getOwnerComponent().getModel("robotConfig").setProperty("/chargers", chargers);
		},

		handleClose: function () {
			this.oRouter.navTo("master");
		},

		handleRobotFullscreen: function () {
			if (this.getOwnerComponent().getModel("viewType").getData().layout === fioriLibrary.LayoutType.MidColumnFullScreen) {
				// Exit Fullscreen
				this.oRouter.navTo("robotDetail", {
					layout: fioriLibrary.LayoutType.TwoColumnsMidExpanded,
					robot: this._robotName
				});
			} else {
				// Enter Fullscreen
				this.oRouter.navTo("robotDetailFullscreen", {
					layout: fioriLibrary.LayoutType.MidColumnFullScreen,
					robot: this._robotName
				});
			}
		},

		handleWhoFullscreen: function () {
			if (this.getOwnerComponent().getModel("viewType").getData().layout === fioriLibrary.LayoutType.MidColumnFullScreen) {
				// Exit Fullscreen
				this.oRouter.navTo("whoDetail", {
					layout: fioriLibrary.LayoutType.TwoColumnsMidExpanded,
					who: this._warhouseOrder
				});
			} else {
				// Enter Fullscreen
				this.oRouter.navTo("whoDetailFullscreen", {
					layout: fioriLibrary.LayoutType.MidColumnFullScreen,
					who: this._warhouseOrder
				});
			}
		},
		
		_getSprasKey: function() {
			var langKey = sap.ui.getCore().getConfiguration().getLanguage();
			if(langKey === "de") {
				langKey = "D";
			}
			else {
				langKey = "E";
			}
			return langKey;
		},

		handleValueHelpLgnum: function (oEvent) {
			var sInputValue = oEvent.getSource().getValue();
			// create value help dialog
			if (!this._valueHelpDialogLgnum) {
				this._valueHelpDialogLgnum = sap.ui.xmlfragment(
					"monitoring.view.fragments.DetailRobotLgnumValueHelp",
					this
				);
				this.getView().addDependent(this._valueHelpDialogLgnum);
				//this._valueHelpDialogLgnum.setModel(this.getOwnerComponent().getModel("odata"), "odata");
			}
			
			// create a filter for the binding
			this._valueHelpDialogLgnum.getBinding("items").filter([new Filter(
				"Spras", sap.ui.model.FilterOperator.EQ, this._getSprasKey()
			)]);

			// open value help dialog filtered by the input value
			this._valueHelpDialogLgnum.open(sInputValue);
		},
		
		handleValueHelpLgnumSearch: function(oEvent) {
			var sValue = oEvent.getParameter("value");
			var oFilter = new Filter({
				filters:[
					new Filter({
						filters: [
							new Filter("Lgnum", sap.ui.model.FilterOperator.Contains, sValue),
							new Filter("Lnumt", sap.ui.model.FilterOperator.Contains, sValue)
						],
						and: false
					}),
					new Filter("Spras", sap.ui.model.FilterOperator.EQ, this._getSprasKey())
				],
				and: true
			});
			oEvent.getSource().getBinding("items").filter([oFilter]);
		}, 
		
		handleValueHelpLgnumConfirm: function(oEvent) {
			var oSelectedItem = oEvent.getParameter("selectedItem");
			if (oSelectedItem) {
				this.getView().byId("configLgnum").setValue(oSelectedItem.getTitle());
			}
			oEvent.getSource().getBinding("items").filter([]);
		},
		
		handleValueHelpRsrcgrp: function(oEvent) {
			var sInputValue = oEvent.getSource().getValue();
			// create value help dialog
			if (!this._valueHelpDialogRsrcgrp) {
				this._valueHelpDialogRsrcgrp = sap.ui.xmlfragment(
					"monitoring.view.fragments.DetailRobotRsrcgrpValueHelp",
					this
				);
				this.getView().addDependent(this._valueHelpDialogRsrcgrp);
				var that = this;
				this.getView().getModel("odata").read("/ResourceGroupSet", {
					urlParameters: {
						"$expand": "ResourceGroupDescriptions"
					},
					success: function(data) {
						that._valueHelpDialogRsrcgrp.setModel(new JSONModel(data), "rsrcgrp");
					}
				});
			} 

			// open value help dialog filtered by the input value
			this._valueHelpDialogRsrcgrp.open(sInputValue);
		},
		
		handleValueHelpRsrcgrpSearch: function(oEvent) {
			var sValue = oEvent.getParameter("value");
			var oFilter = new Filter({
				filters:[
					new Filter({
						filters: [
							new Filter("RsrcGrp", sap.ui.model.FilterOperator.Contains, sValue),
							new Filter("Lgnum", sap.ui.model.FilterOperator.Contains, sValue)
						],
						and: false
					})
				]
			});
			oEvent.getSource().getBinding("items").filter([oFilter]);
		},
		
		handleValueHelpRsrcgrpConfirm: function(oEvent) {
			var oSelectedItem = oEvent.getParameter("selectedItem");
			if (oSelectedItem) {
				this.getView().byId("configRsrcgrp").setValue(oSelectedItem.getCells()[0].getTitle());
				this.getView().byId("configLgnum").setValue(oSelectedItem.getCells()[1].getText());
			}
			oEvent.getSource().getBinding("items").filter([]);
		},
		
		handleValueHelpRsrctype: function(oEvent) {
			var sInputValue = oEvent.getSource().getValue();
			// create value help dialog
			if (!this._valueHelpDialogRsrctype) {
				this._valueHelpDialogRsrctype = sap.ui.xmlfragment(
					"monitoring.view.fragments.DetailRobotRsrctypeValueHelp",
					this
				);

				this.getView().addDependent(this._valueHelpDialogRsrctype);
				var that = this;
				this.getView().getModel("odata").read("/RobotResourceTypeSet", {
					urlParameters: {
						"$expand": "ResourceTypeDescriptions"
					},
					success: function(data) {
						that._valueHelpDialogRsrctype.setModel(new JSONModel(data), "rsrctype");
					}
				});
			}

			// open value help dialog filtered by the input value
			this._valueHelpDialogRsrctype.open(sInputValue);
		},
			
		handleValueHelpRsrctypeSearch: function(oEvent) {
			var sValue = oEvent.getParameter("value");
			var oFilter = new Filter({
				filters:[
					new Filter({
						filters: [
							new Filter("RsrcType", sap.ui.model.FilterOperator.Contains, sValue),
							new Filter("Lgnum", sap.ui.model.FilterOperator.Contains, sValue)
						],
						and: false
					})
				]
			});
			oEvent.getSource().getBinding("items").filter([oFilter]);
		},
		
		handleValueHelpRsrctypeConfirm: function(oEvent) {
			var oSelectedItem = oEvent.getParameter("selectedItem");
			if (oSelectedItem) {
				this.getView().byId("configRsrctype").setValue(oSelectedItem.getCells()[0].getTitle());
				this.getView().byId("configLgnum").setValue(oSelectedItem.getCells()[1].getText());
			}
			oEvent.getSource().getBinding("items").filter([]);
		},

		_onRobotRouteMatched: function (oEvent) {
			this.getOwnerComponent().getModel("viewType").setData({
				"robot": true,
				"who": false,
				"layout": oEvent.getParameter("arguments").layout
			});
			this._robotName = oEvent.getParameter("arguments").robot;
			this._bindRobotConfiguration(this._robotName);
		},

		_onWhoRouteMatched: function (oEvent) {
			this.getOwnerComponent().getModel("viewType").setData({
				"robot": false,
				"who": true,
				"layout": oEvent.getParameter("arguments").layout
			});
			this._warhouseOrder = oEvent.getParameter("arguments").who;
			this._bindWhoConfiguration(this._warhouseOrder);
		},

		onExit: function () {
			this.oRouter.getRoute("whoDetail").detachPatternMatched(this._onRobotRouteMatched, this);
			this.oRouter.getRoute("robotDetail").detachPatternMatched(this._onWhoRouteMatched, this);
			this.oRouter.getRoute("whoDetailFullscreen").detachPatternMatched(this._onWhoRouteMatched, this);
			this.oRouter.getRoute("robotDetailFullscreen").detachPatternMatched(this._onRobotRouteMatched, this);
			sap.ui.getCore().getEventBus().unsubscribe("Master", "UpdateEvent", this.updateModels, this)
		}
	});
});