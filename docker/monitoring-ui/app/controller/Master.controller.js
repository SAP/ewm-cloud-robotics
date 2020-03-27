sap.ui.define([
	"sap/ui/core/mvc/Controller",
	"sap/ui/model/json/JSONModel",
	"monitoring/model/formatter",
	'sap/f/library'
], function (Controller, JSONModel, formatter, fioriLibrary) {
	"use strict";

	return Controller.extend("monitoring.controller.Master", {
		formatter: formatter,
		onInit: function () {
			this.oRouter = this.getOwnerComponent().getRouter();
			this.getOwnerComponent().setModel(new JSONModel(), "masterLayout");
			this.oRouter.getRoute("master").attachPatternMatched(this._onRouteMatched, this);
			this.oRouter.getRoute("robotDetail").attachPatternMatched(this._onRouteMatched, this);
			this.oRouter.getRoute("whoDetail").attachPatternMatched(this._onRouteMatched, this);
			var that = this;
			var srcModel = this.getOwnerComponent().getModel("src");
			if(srcModel.getData() === {}) {
				srcModel.attachRequestCompleted(function(oEvent) {
					that._bindModels();
				});
			}
			else {
				this._bindModels();
			}
		},
		
		_bindModels: function() {
			this._bindRobotModel();
			this._bindWarehouseOrderModel();
		},
		
		_bindRobotModel: function() {
			var that = this;
			$.get( this.getOwnerComponent().getModel("src").getData().robots, function( data ) {
				var robotJSON = {"rows": []};
				for(var i=0; i< data.items.length; ++i) {
					if(data.items[i].kind !== "Robot") {
						continue;
					}
					robotJSON.rows.push({
						"uid": data.items[i].metadata.uid,
						"creationTimestamp": data.items[i].metadata.creationTimestamp,
						"name": data.items[i].metadata.name,
						"model": data.items[i].metadata.labels.model,
						"batteryPercentage": data.items[i].status.robot.batteryPercentage,
						"lastStateChangeTime": data.items[i].status.robot.lastStateChangeTime,
						"state": data.items[i].status.robot.state,
						"updateTime": data.items[i].status.robot.updateTime
					});
				}
				that.getOwnerComponent().setModel(new JSONModel(robotJSON), "robots");
			});
		},
		
		_bindWarehouseOrderModel: function() {
			var that = this;
			$.get( this.getOwnerComponent().getModel("src").getData().warehouseOrders, function( data ) {
				var warehouseJSON = {"rows": []};
				for(var i=0; i< data.items.length; ++i) {
					if(data.items[i].kind !== "WarehouseOrder") {
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
						"topwhoid": data.items[i].spec.data.topwhoid
					});
				}
				that.getOwnerComponent().setModel(new JSONModel(warehouseJSON), "who");
			});
		},

		onRobotListItemPress: function (oEvent) {
			var robotPath = oEvent.getSource().getBindingContextPath(),
				robotIndex = robotPath.split("/").slice(-1).pop(),
				robotName = this.getOwnerComponent().getModel("robots").getData().rows[robotIndex].name;

			this.oRouter.navTo("robotDetail", {layout: fioriLibrary.LayoutType.TwoColumnsMidExpanded, robot: robotName});
			/*
			var oFCL = this.oView.getParent().getParent();
			oFCL.setLayout(fioriLibrary.LayoutType.TwoColumnsMidExpanded);
			*/
		},
		
		onWhoListItemPress: function(oEvent) {
			var whoPath = oEvent.getSource().getBindingContextPath(),
				whoIndex = whoPath.split("/").slice(-1).pop(),
				warehouseOrder = this.getOwnerComponent().getModel("who").getData().rows[whoIndex].who;

			this.oRouter.navTo("whoDetail", {layout: fioriLibrary.LayoutType.TwoColumnsMidExpanded, who: warehouseOrder});
		},
		
		_onRouteMatched: function(oEvent) {
			var layout = oEvent.getParameter("arguments").layout;
			if(layout === "TwoColumnsMidExpanded") {
				this.getOwnerComponent().getModel("masterLayout").setData({"expanded": false, "mediumExpanded": false});
			}
			else if(layout === "TwoColumnsBeginExpanded") {
				this.getOwnerComponent().getModel("masterLayout").setData({"expanded": false, "mediumExpanded": true});
			}
			else {
				this.getOwnerComponent().getModel("masterLayout").setData({"expanded": true, "mediumExpanded": true});
			}
		}
	});
});
