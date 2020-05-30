// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// Auctioneer represents the Auctioneer CRD
type Auctioneer struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec AuctioneerSpec `json:"spec,omitempty"`
	// +optional
	Status AuctioneerStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// AuctioneerList represents the array of Auctioneer CRD
type AuctioneerList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`

	Items []Auctioneer `json:"items"`
}

// AuctioneerSpec represents the spec of Auctioneer CRD
type AuctioneerSpec struct {
	Scope         Scope         `json:"scope"`
	Configuration Configuration `json:"configuration"`
}

// AuctioneerStatus represents the status of Auctioneer CRD
type AuctioneerStatus struct {
	AvailableRobots          []string               `json:"availableRobots"`
	RobotsInScope            []string               `json:"robotsInScope"`
	WarehouseOrdersInProcess int                    `json:"warehouseOrdersInProcess"`
	RunningAuctions          int                    `json:"runningAuctions"`
	Status                   AuctioneerStatusStatus `json:"status"`
	Message                  string                 `json:"message,omitempty"`
	LastStatusChangeTime     metav1.Time            `json:"lastStatusChangeTime,omitempty"`
	UpdateTime               metav1.Time            `json:"updateTime,omitempty"`
}

// Scope defines to which resource types the given auction should be applied
type Scope struct {
	Lgnum    string `json:"lgnum"`
	Rsrctype string `json:"rsrctype"`
	Rsrcgrp  string `json:"rsrcgrp"`
}

// Configuration defines the configuration of an Auctioneer
type Configuration struct {
	MaxOrdersPerRobot   int `json:"maxOrdersPerRobot"`
	MinOrdersPerRobot   int `json:"minOrdersPerRobot"`
	MinOrdersPerAuction int `json:"minOrdersPerAuction"`
}

// AuctioneerStatusStatus describes the status of an Auctioneer
type AuctioneerStatusStatus string

// Values for AuctioneerStatusStatus
const (
	AuctioneerStatusWatching AuctioneerStatusStatus = "WATCHING"
	AuctioneerStatusWaiting  AuctioneerStatusStatus = "WAITING"
	AuctioneerStatusAuction  AuctioneerStatusStatus = "AUCTION"
	AuctioneerStatusError    AuctioneerStatusStatus = "ERROR"
)

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// OrderReservation represents the OrderReservation CRD
type OrderReservation struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec OrderReservationSpec `json:"spec,omitempty"`
	// +optional
	Status OrderReservationStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// OrderReservationList represents the array of OrderReservation CRD
type OrderReservationList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`

	Items []OrderReservation `json:"items"`
}

// OrderReservationSpec represents the spec of OrderReservation CRD
type OrderReservationSpec struct {
	OrderRequest     OrderRequest      `json:"orderrequest"`
	OrderAssignments []OrderAssignment `json:"orderassignments,omitempty"`
}

// OrderReservationStatus represents the status of OrderReservation CRD
type OrderReservationStatus struct {
	WarehouseOrders  []EWMWarehouseOrder          `json:"warehouseorders,omitempty"`
	OrderAssignments []OrderAssignment            `json:"orderassignments,omitempty"`
	Status           OrderReservationStatusStatus `json:"status,omitempty"`
	Message          string                       `json:"message,omitempty"`
	ValidUntil       metav1.Time                  `json:"validuntil,omitempty"`
}

// OrderRequest represents the request of warehouse orders by order auctioneer
type OrderRequest struct {
	Lgnum    string `json:"lgnum"`
	Rsrctype string `json:"rsrctype"`
	Rsrcgrp  string `json:"rsrcgrp"`
	Quantity int    `json:"quantity"`
}

// OrderAssignment represents the assignment of warehouse orders by order auctioneer
type OrderAssignment struct {
	Lgnum string `json:"lgnum"`
	Who   string `json:"who"`
	Rsrc  string `json:"rsrc"`
}

// OrderReservationStatusStatus describes the status of an OrderReservation
type OrderReservationStatusStatus string

// Values for OrderReservationStatusStatus
const (
	OrderReservationStatusNew          OrderReservationStatusStatus = "NEW"
	OrderReservationStatusAccepted     OrderReservationStatusStatus = "ACCEPTED"
	OrderReservationStatusReservations OrderReservationStatusStatus = "RESERVATIONS"
	OrderReservationStatusFailed       OrderReservationStatusStatus = "FAILED"
	OrderReservationStatusSucceeded    OrderReservationStatusStatus = "SUCCEEDED"
	OrderReservationStatusTimeout      OrderReservationStatusStatus = "TIMEOUT"
)

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// OrderAuction represents the OrderAuction CRD
type OrderAuction struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec OrderAuctionSpec `json:"spec,omitempty"`
	// +optional
	Status OrderAuctionStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// OrderAuctionList represents the array of OrderAuction CRD
type OrderAuctionList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`

	Items []OrderAuction `json:"items"`
}

// OrderAuctionSpec represents the spec of OrderAuction CRD
type OrderAuctionSpec struct {
	WarehouseOrders []EWMWarehouseOrder       `json:"warehouseorders"`
	ValidUntil      metav1.Time               `json:"validuntil"`
	AuctionStatus   OrderAuctionAuctionStatus `json:"auctionstatus"`
}

// OrderAuctionStatus represents the status of OrderAuction CRD
type OrderAuctionStatus struct {
	BidStatus OrderAuctionBidStatus   `json:"bidstatus,omitempty"`
	Biddings  []WarehouseOrderBidding `json:"biddings,omitempty"`
}

// WarehouseOrderBidding represents the a bidding from a robot for a warehouse order
type WarehouseOrderBidding struct {
	Lgnum   string  `json:"lgnum"`
	Who     string  `json:"who"`
	Bidding float64 `json:"bidding"`
}

// OrderAuctionAuctionStatus describes the status of this OrderAuction
type OrderAuctionAuctionStatus string

// Values for OrderAuctionAuctionStatus
const (
	OrderAuctionAuctionStatusOpen      OrderAuctionAuctionStatus = "OPEN"
	OrderAuctionAuctionStatusClosed    OrderAuctionAuctionStatus = "CLOSED"
	OrderAuctionAuctionStatusCompleted OrderAuctionAuctionStatus = "COMPLETED"
)

// OrderAuctionBidStatus describes the status of the bid to an OrderAuction
type OrderAuctionBidStatus string

// Values for OrderAuctionBidStatus
const (
	OrderAuctionBidStatusRunning   OrderAuctionBidStatus = "RUNNING"
	OrderAuctionBidStatusCompleted OrderAuctionBidStatus = "COMPLETED"
)

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// RobotConfiguration represents the RobotConfiguration CRD
type RobotConfiguration struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec RobotConfigurationSpec `json:"spec,omitempty"`
	// +optional
	Status RobotConfigurationStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// RobotConfigurationList represents the array of RobotConfiguration CRD
type RobotConfigurationList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`

	Items []RobotConfiguration `json:"items"`
}

// RobotConfigurationSpec represents the spec of RobotConfiguration CRD
type RobotConfigurationSpec struct {
	Lgnum                 string   `json:"lgnum"`
	Rsrctype              string   `json:"rsrctype"`
	Rsrcgrp               string   `json:"rsrcgrp"`
	Chargers              []string `json:"chargers"`
	BatteryMin            float64  `json:"batteryMin"`
	BatteryOk             float64  `json:"batteryOk"`
	BatteryIdle           float64  `json:"batteryIdle"`
	MaxIdleTime           float64  `json:"maxIdleTime"`
	RecoverFromRobotError bool     `json:"recoverFromRobotError"`
}

// RobotConfigurationStatus represents the status of RobotConfiguration CRD
type RobotConfigurationStatus struct {
	Lgnum        string `json:"lgnum"`
	Mission      string `json:"mission"`
	Statemachine string `json:"statemachine"`
	SubWho       string `json:"subwho"`
	Tanum        string `json:"tanum"`
	Who          string `json:"who"`
}

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// RobotRequest represents the RobotRequest CRD
type RobotRequest struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec RobotRequestSpec `json:"spec,omitempty"`
	// +optional
	Status RobotRequestStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// RobotRequestList represents the array of RobotRequest CRD
type RobotRequestList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`

	Items []RobotRequest `json:"items"`
}

// RobotRequestSpec represents the spec of RobotRequest CRD
type RobotRequestSpec struct {
	Lgnum               string `json:"lgnum"`
	Rsrc                string `json:"rsrc"`
	NotifyWhoCompletion string `json:"notifywhocompletion"`
	NotifyWhtCompletion string `json:"notifywhtcompletion"`
	RequestWork         bool   `json:"requestwork"`
	RequestNewWho       bool   `json:"requestnewwho"`
}

// RobotRequestStatus represents the status of RobotRequest CRD
type RobotRequestStatus struct {
	Data   []RobotRequestSpec       `json:"data,omitempty"`
	Status RobotRequestStatusStatus `json:"status,omitempty"`
}

// RobotRequestStatusStatus describes the status of a RobotRequest
type RobotRequestStatusStatus string

// Values for RobotRequestStatusStatus
const (
	RobotRequestStatusRunning   RobotRequestStatusStatus = "RUNNING"
	RobotRequestStatusProcessed RobotRequestStatusStatus = "PROCESSED"
)

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// RunTimeEstimation represents the RunTimeEstimation CRD
type RunTimeEstimation struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec RunTimeEstimationSpec `json:"spec,omitempty"`
	// +optional
	Status RunTimeEstimationStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// RunTimeEstimationList represents the array of RunTimeEstimation CRD
type RunTimeEstimationList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`

	Items []RunTimeEstimation `json:"items"`
}

// RunTimeEstimationSpec represents the spec of RunTimeEstimation CRD
type RunTimeEstimationSpec struct {
	Paths         []Path      `json:"paths"`
	StartPosition string      `json:"startPosition"`
	ValidUntil    metav1.Time `json:"validuntil"`
}

// RunTimeEstimationStatus represents the status of RunTimeEstimation CRD
type RunTimeEstimationStatus struct {
	RunTimes []RunTime                     `json:"runtimes,omitempty"`
	Status   RunTimeEstimationStatusStatus `json:"status,omitempty"`
}

// Path represents a path from start to goal#
type Path struct {
	Start string `json:"start"`
	Goal  string `json:"goal"`
}

// RunTime represents the run time of a path from start to goal
type RunTime struct {
	Start string  `json:"start"`
	Goal  string  `json:"goal"`
	Time  float64 `json:"time"`
}

// RunTimeEstimationStatusStatus describes the status of a RunTimeEstimation
type RunTimeEstimationStatusStatus string

// Values for RunTimeEstimationStatusStatus
const (
	RunTimeEstimationStatusRunning   RunTimeEstimationStatusStatus = "RUNNING"
	RunTimeEstimationStatusProcessed RunTimeEstimationStatusStatus = "PROCESSED"
)

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// WarehouseOrder represents the WarehouseOrder CRD
type WarehouseOrder struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec WarehouseOrderSpec `json:"spec,omitempty"`
	// +optional
	Status WarehouseOrderStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// WarehouseOrderList represents the array of WarehouseOrder CRD
type WarehouseOrderList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`

	Items []WarehouseOrder `json:"items"`
}

// WarehouseOrderSpec represents the spec of WarehouseOrder CRD
type WarehouseOrderSpec struct {
	Data          EWMWarehouseOrder              `json:"data"`
	OrderStatus   WarehouseOrderOrderStatus      `json:"order_status"`
	ProcessStatus []EWMWarehouseTaskConfirmation `json:"process_status,omitempty"`
}

// WarehouseOrderStatus represents the status of WarehouseOrder CRD
type WarehouseOrderStatus struct {
	Data []EWMWarehouseTaskConfirmation `json:"data,omitempty"`
}

// EWMWarehouseOrder represents the EWM warehouse order type in Cloud Robotics
type EWMWarehouseOrder struct {
	Lgnum          string             `json:"lgnum"`
	Who            string             `json:"who"`
	Status         string             `json:"status"`
	Areawho        string             `json:"areawho"`
	Lgtyp          string             `json:"lgtyp"`
	Lgpla          string             `json:"lgpla"`
	Queue          string             `json:"queue"`
	Rsrc           string             `json:"rsrc"`
	Lsd            Time               `json:"lsd"`
	Topwhoid       string             `json:"topwhoid"`
	Refwhoid       string             `json:"refwhoid"`
	Flgwho         bool               `json:"flgwho"`
	Flgto          bool               `json:"flgto"`
	Warehousetasks []EWMWarehouseTask `json:"warehousetasks"`
}

// EWMWarehouseTask represents the EWM warehouse task type in Cloud Robotics
type EWMWarehouseTask struct {
	Flghuto  bool    `json:"flghuto"`
	Lgnum    string  `json:"lgnum"`
	Nlber    string  `json:"nlber"`
	Nlenr    string  `json:"nlenr"`
	Nlpla    string  `json:"nlpla"`
	Nltyp    string  `json:"nltyp"`
	Priority int     `json:"priority"`
	Procty   string  `json:"procty"`
	Tanum    string  `json:"tanum"`
	Tostat   string  `json:"tostat"`
	Unitv    string  `json:"unitv"`
	Unitw    string  `json:"unitw"`
	Vlber    string  `json:"vlber"`
	Vlenr    string  `json:"vlenr"`
	Vlpla    string  `json:"vlpla"`
	Vltyp    string  `json:"vltyp"`
	Volum    float64 `json:"volum"`
	Weight   float64 `json:"weight"`
	Who      string  `json:"who"`
}

// EWMWarehouseTaskConfirmation represents the warehouse task confirmation sent by the robots
type EWMWarehouseTaskConfirmation struct {
	ConfirmationDate   metav1.Time `json:"confirmationdate"`
	ConfirmationNumber string      `json:"confirmationnumber"`
	ConfirmationType   string      `json:"confirmationtype"`
	Lgnum              string      `json:"lgnum"`
	Rsrc               string      `json:"rsrc"`
	Tanum              string      `json:"tanum"`
	Who                string      `json:"who"`
}

// WarehouseOrderOrderStatus describes the status of a WarehouseOrder
type WarehouseOrderOrderStatus string

// Values for WarehouseOrderOrderStatus
const (
	WarehouseOrderOrderStatusRunning   WarehouseOrderOrderStatus = "RUNNING"
	WarehouseOrderOrderStatusProcessed WarehouseOrderOrderStatus = "PROCESSED"
)
