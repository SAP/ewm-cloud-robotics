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
	"sap/f/library",
	"sap/ui/Device",
	"sap/ui/model/Filter",
	"sap/ui/model/Sorter"
], function (Controller, JSONModel, formatter, fioriLibrary, Device, Filter, Sorter) {
	"use strict";

	return Controller.extend("monitoring.controller.Master", {
		formatter: formatter,
		onInit: function () {
			this._mViewSettingsDialogs = {};
			this.oRouter = this.getOwnerComponent().getRouter();
			this.getOwnerComponent().setModel(new JSONModel(), "masterLayout");
			this.oRouter.getRoute("master").attachPatternMatched(this._onRouteMatched, this);
			this.oRouter.getRoute("robotDetail").attachPatternMatched(this._onRouteMatched, this);
			this.oRouter.getRoute("whoDetail").attachPatternMatched(this._onRouteMatched, this);
			var that = this;
			var srcModel = this.getOwnerComponent().getModel("src");
			if (srcModel.getData() === {}) {
				srcModel.attachRequestCompleted(function (oEvent) {
					that._bindModels();
				});
			} else {
				this._bindModels();
			}
			this.getOwnerComponent().setModel(new JSONModel({"automaticUpdates": false, "updateTimer": 30}), "uiStates");
			this._timerId = null;
		},

		onExit: function () {
			var oDialogKey,
				oDialogValue;

			for (oDialogKey in this._mViewSettingsDialogs) {
				oDialogValue = this._mViewSettingsDialogs[oDialogKey];

				if (oDialogValue) {
					oDialogValue.destroy();
				}
			}
		},
		
		changeUpdateStyle: function(oEvent) {
			if(oEvent.getParameter("pressed")) {
				this.changeUpdateTimer();
			}
			else {
				clearInterval(this._timerId);
			}
		}, 
		
		changeUpdateTimer: function() {
			clearInterval(this._timerId);
			var that = this;
			this._timerId = setInterval(function() {
				that._bindModels();
			}, this.getOwnerComponent().getModel("uiStates").getProperty("/updateTimer") * 1000);
		},

		_bindModels: function () {
			sap.ui.getCore().getEventBus().publish("Master", "UpdateEvent");
			this._bindRobotModel();
			this._bindWarehouseOrderModel();
		},

		_bindRobotModel: function () {
			this._robotIndex = {};
			var modelData = {"rows": []};
			var furtherLinks = [];
			var that = this;
			// load robots data
			$.get(this.getOwnerComponent().getModel("src").getData().robots, function (data) {
				var robotJSON = {};
				for (var i = 0; i < data.items.length; ++i) {
					if (data.items[i].kind !== "Robot") {
						continue;
					}
					that._robotIndex[data.items[i].metadata.name] = i;
					robotJSON = {
						"uid": data.items[i].metadata.uid,
						"creationTimestamp": data.items[i].metadata.creationTimestamp,
						"name": data.items[i].metadata.name,
						"model": data.items[i].metadata.labels.model,
						"batteryPercentage": data.items[i].status.robot.batteryPercentage,
						"lastStateChangeTime": data.items[i].status.robot.lastStateChangeTime,
						"state": data.items[i].status.robot.state,
						"updateTime": data.items[i].status.robot.updateTime
					};

					modelData.rows.push(robotJSON);
					furtherLinks.push(data.items[i].metadata.selfLink.replace("robots", "robotconfigurations"));
				}
				var robotConfigFeedback = 0;
				// enhance robot information with robotconfiguration regarding the ewm status
				furtherLinks.forEach(function(link) {
					$.get(link, function (robotconfiguration) {
						var statemachine = "";
						var statemachine_uistate = "Success";
						if (robotconfiguration.hasOwnProperty("status")) {
							if (robotconfiguration.status.hasOwnProperty("statemachine")) {
								statemachine = robotconfiguration.status.statemachine;
								if (["robotError", "moveTrolley_waitingForErrorRecovery", "pickPackPass_waitingForErrorRecovery"].includes(statemachine)) {
									statemachine_uistate = "Error";
								}
							}
						}
						modelData.rows[that._robotIndex[robotconfiguration.metadata.name]]["statemachine"] = statemachine;
						modelData.rows[that._robotIndex[robotconfiguration.metadata.name]]["statemachine_uistate"] = statemachine_uistate;
					}).always(function() {
						robotConfigFeedback++;
						if(robotConfigFeedback === furtherLinks.length) {
							that.getOwnerComponent().setModel(new JSONModel(modelData), "robots");
						}
					});
				});
			});
		},

		_bindWarehouseOrderModel: function () {
			var that = this;
			$.get(this.getOwnerComponent().getModel("src").getData().warehouseOrders, function (data) {
				var warehouseJSON = {
					"rows": [],
					"columns": {
						"who": {"visible": true},
						"flgto": {"visible": false},
						"areawho": {"visible": true},
						"flgwho": {"visible": false},
						"lgnum": {"visible": true},
						"lgtyp": {"visible": false},
						"lsd": {"visible": true},
						"queue": {"visible": true},
						"refwhoid": {"visible": false},
						"rsrc": {"visible": true},
						"order_status": {"visible": true},
						"topwhoid": {"visible": false}
					}
				};
				for (var i = 0; i < data.items.length; ++i) {
					if (data.items[i].kind !== "WarehouseOrder") {
						continue;
					}
					warehouseJSON.rows.push({
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
						"status": data.items[i].spec.data.status,
						"topwhoid": data.items[i].spec.data.topwhoid,
						"order_status": data.items[i].spec.order_status
					});
				}
				var aFilters = [];
				var oBinding = that.getView().byId("idWarehouseOrders").getBinding("items");
				if(oBinding) {
					aFilters = oBinding.aFilters;
				}
				that.getOwnerComponent().setModel(new JSONModel(warehouseJSON), "who");
				that.byId("idWarehouseOrders").getBinding("items").filter(aFilters);
			});
		},

		onRobotListItemPress: function (oEvent) {
			var robotPath = oEvent.getSource().getBindingContextPath(),
				robotIndex = robotPath.split("/").slice(-1).pop(),
				robotName = this.getOwnerComponent().getModel("robots").getData().rows[robotIndex].name;

			this.oRouter.navTo("robotDetail", {
				layout: fioriLibrary.LayoutType.TwoColumnsMidExpanded,
				robot: robotName
			});
			/*
			var oFCL = this.oView.getParent().getParent();
			oFCL.setLayout(fioriLibrary.LayoutType.TwoColumnsMidExpanded);
			*/
		},

		onWhoListItemPress: function (oEvent) {
			var whoPath = oEvent.getSource().getBindingContextPath(),
				whoIndex = whoPath.split("/").slice(-1).pop(),
				warehouseOrder = this.getOwnerComponent().getModel("who").getData().rows[whoIndex].who;

			this.oRouter.navTo("whoDetail", {
				layout: fioriLibrary.LayoutType.TwoColumnsMidExpanded,
				who: warehouseOrder
			});
		},

		createViewSettingsDialog: function (sDialogFragmentName) {
			var oDialog = this._mViewSettingsDialogs[sDialogFragmentName];

			if (!oDialog) {
				oDialog = sap.ui.xmlfragment(sDialogFragmentName, this);
				oDialog.setModel(this.getView().getModel("i18n"), "i18n");
				oDialog.setModel(this.getOwnerComponent().getModel("who"), "who");
				oDialog.setModel(this.getOwnerComponent().getModel("odata"), "odata");
				this._mViewSettingsDialogs[sDialogFragmentName] = oDialog;

				if (Device.system.desktop) {
					oDialog.addStyleClass("sapUiSizeCompact");
				}
			}
			return oDialog;
		},
		
		handleColumnPressed: function() {
			this.createViewSettingsDialog("monitoring.view.fragments.MasterColumnDialog").open();
		},
		
		handleSortPressed: function () {
			this.createViewSettingsDialog("monitoring.view.fragments.MasterSortDialog").open();
		},

		handleSortDialogConfirm: function (oEvent) {
			var oTable = this.byId("idWarehouseOrders"),
				mParams = oEvent.getParameters(),
				oBinding = oTable.getBinding("items"),
				sPath,
				bDescending,
				aSorters = [];

			sPath = "whos>" + mParams.sortItem.getKey();
			bDescending = mParams.sortDescending;
			aSorters.push(new Sorter(sPath, bDescending));

			oBinding.sort(aSorters);
		},

		handleFilterPressed: function () {
			this.createViewSettingsDialog("monitoring.view.fragments.MasterFilterDialog").open();
		},
		
		onInputLiveChange: function(oEvent) {
			var value = oEvent.getParameter("value");
			var index = oEvent.getSource().getId().split("_")[1];
			var oCustomFilter = this._mViewSettingsDialogs["monitoring.view.fragments.MasterFilterDialog"].getFilterItems()[index];
			if(value === "") {
				oCustomFilter.setFilterCount(0);
				oCustomFilter.setSelected(false);
			}
			else {
				oCustomFilter.setFilterCount(1);
				oCustomFilter.setSelected(true);
			}
				
		},
		
		onSelectChange: function(oEvent) {
			var key = oEvent.getParameter("selectedItem").getKey();
			var index = oEvent.getSource().getId().split("_")[1];
			var oCustomFilter = this._mViewSettingsDialogs["monitoring.view.fragments.MasterFilterDialog"].getFilterItems()[index];
			if(key === "") {
				oCustomFilter.setFilterCount(0);
				oCustomFilter.setSelected(false);
			}
			else {
				oCustomFilter.setFilterCount(1);
				oCustomFilter.setSelected(true);
			}
		},

		handleFilterDialogConfirm: function (oEvent) {
			var oTable = this.byId("idWarehouseOrders"),
				mParams = oEvent.getParameters(),
				oBinding = oTable.getBinding("items"),
				aFilters = [];

			mParams.filterItems.forEach(function(oItem) {
				var	sPath = oItem.getKey();
				var sOperator = oItem.getCustomControl().getItems()[0].getSelectedKey();
				var control = oItem.getCustomControl().getItems()[1].getId().split("_")[0];
				var sValue1 = "";
				switch (control) {
					case "input":
						sValue1 = oItem.getCustomControl().getItems()[1].getValue();
						break;
					case "selectBoolean":
						sValue1 = oItem.getCustomControl().getItems()[1].getSelectedKey() === "true"; // parse string to boolean
						break;
					case "selectText":
						sValue1 = oItem.getCustomControl().getItems()[1].getSelectedKey();
						break;
				}
				var oFilter = new Filter(sPath, sOperator, sValue1);
				aFilters.push(oFilter);
			});

			// apply filter settings
			oBinding.filter(aFilters);

			// update filter bar
			this.byId("vsdFilterBar").setVisible(aFilters.length > 0);
			this.byId("vsdFilterLabel").setText(mParams.filterString);
		},
		
		handleResetFilters: function() {
			this._mViewSettingsDialogs["monitoring.view.fragments.MasterFilterDialog"].getFilterItems().forEach(function(oItem) {
				switch (oItem.getCustomControl().getItems()[1].getId().split("_")[0]) {
					case "input":
						oItem.getCustomControl().getItems()[1].setValue("");
						break;
					case "selectBoolean":
					case "selectText":
						oItem.getCustomControl().getItems()[1].setSelectedKey("");
						break;
				}
				oItem.setFilterCount(0);
				oItem.setSelected(false);
			});
		},

		_onRouteMatched: function (oEvent) {
			var layout = oEvent.getParameter("arguments").layout;
			if (layout === "TwoColumnsMidExpanded") {
				this.getOwnerComponent().getModel("masterLayout").setData({
					"expanded": false,
					"mediumExpanded": false
				});
			} else if (layout === "TwoColumnsBeginExpanded") {
				this.getOwnerComponent().getModel("masterLayout").setData({
					"expanded": false,
					"mediumExpanded": true
				});
			} else {
				this.getOwnerComponent().getModel("masterLayout").setData({
					"expanded": true,
					"mediumExpanded": true
				});
			}
		}
	});
});