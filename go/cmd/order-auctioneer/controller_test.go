// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package main

import (
	"context"
	"fmt"
	"testing"
	"time"

	ewm "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	registry "github.com/googlecloudrobotics/core/src/go/pkg/apis/registry/v1alpha1"
	"github.com/stretchr/testify/assert"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/kubernetes/scheme"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

var (
	testTimeNotExpired    metav1.Time = metav1.Time{time.Now().Truncate(time.Second).Add(time.Minute * 5)}
	testTimeExpired       metav1.Time = metav1.Time{time.Now().Truncate(time.Second).Add(-time.Minute * 1)}
	testEwmTimeNotExpired ewm.Time    = ewm.Time{time.Now().Truncate(time.Second).Add(time.Minute * 5)}
	testEwmTimeExpired    ewm.Time    = ewm.Time{time.Now().Truncate(time.Second).Add(-time.Minute * 5)}
)

func createTestRobots() map[string]bool {
	r := map[string]bool{
		"robot-1": true,
		"robot-2": true,
		"robot-3": true,
		"robot-4": true,
		"robot-5": true,
		"robot-6": true,
		"robot-7": true,
		"robot-8": true,
		"robot-9": true,
	}

	return r
}

func createTestRobotStates() *robotStates {
	r := robotStates{
		isInScope: map[string]bool{
			"robot-1": false,
			"robot-2": true,
			"robot-3": true,
			"robot-4": true,
			"robot-5": true,
			"robot-6": true,
		},
		isAvailable: map[string]bool{
			"robot-1": false,
			"robot-2": false,
			"robot-3": true,
			"robot-4": true,
			"robot-5": true,
			"robot-6": true,
		},
	}

	return &r
}

func createTestAuctioneer() *ewm.Auctioneer {
	a := ewm.Auctioneer{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-auctioneer",
			Namespace: metav1.NamespaceDefault,
		},
		Spec: ewm.AuctioneerSpec{
			Scope: ewm.Scope{
				Lgnum:    "1710",
				Rsrctype: "RB01",
				Rsrcgrp:  "RB01",
			},
			Configuration: ewm.Configuration{
				MaxOrdersPerRobot:   5,
				MinOrdersPerRobot:   2,
				MinOrdersPerAuction: 3,
			},
		},
	}
	return &a
}

func createTestAuctioneerController(initObjs ...client.Object) *reconcileAuctioneer {
	sc := runtime.NewScheme()
	scheme.AddToScheme(sc)
	ewm.AddToScheme(sc)
	registry.AddToScheme(sc)
	client := fake.NewClientBuilder().WithScheme(sc).WithObjects(initObjs...).Build()
	r := &reconcileAuctioneer{client: client, scheme: sc, deployedRobots: createTestRobots()}
	return r
}

func createTestOrderAuction(orderAuction string, robotNumber int, auctionExpired bool, warehouseOrders []ewm.EWMWarehouseOrder, status ewm.OrderAuctionBidStatus) *ewm.OrderAuction {

	var validUntil metav1.Time

	if auctionExpired {
		validUntil = testTimeExpired
	} else {
		validUntil = testTimeNotExpired
	}

	robot := fmt.Sprintf("robot-%v", robotNumber)

	oa := ewm.OrderAuction{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("%s-%s", orderAuction, robot),
			Namespace: metav1.NamespaceDefault,
			Labels:    map[string]string{robotLabel: robot, orderAuctionLabel: orderAuction},
		},
		Spec: ewm.OrderAuctionSpec{
			WarehouseOrders: warehouseOrders,
			AuctionStatus:   ewm.OrderAuctionAuctionStatusOpen,
			ValidUntil:      validUntil,
		},
		Status: ewm.OrderAuctionStatus{
			BidStatus: status,
		},
	}

	if status == ewm.OrderAuctionBidStatusCompleted {
		biddings := make([]ewm.WarehouseOrderBidding, len(warehouseOrders))
		for i, who := range warehouseOrders {
			// Value of biddings is ascending by robotNumber and descending by position in slice
			biddings[i] = ewm.WarehouseOrderBidding{
				Lgnum:   who.Lgnum,
				Who:     who.Who,
				Bidding: float64(robotNumber) * 33.333 / float64(i+1),
			}
		}
		oa.Status.Biddings = biddings
	}

	return &oa
}

func createTestOrderReservation(orderAuction string, warehouseOrders []ewm.EWMWarehouseOrder, status ewm.OrderReservationStatusStatus) *ewm.OrderReservation {
	or := ewm.OrderReservation{
		ObjectMeta: metav1.ObjectMeta{
			Name:      orderAuction,
			Namespace: metav1.NamespaceDefault,
			Labels:    map[string]string{orderAuctionLabel: orderAuction},
		},
		Spec: ewm.OrderReservationSpec{
			OrderRequest: ewm.OrderRequest{
				Lgnum:    "1710",
				Rsrctype: "RB01",
				Rsrcgrp:  "RB01",
				Quantity: 3,
			},
		},
		Status: ewm.OrderReservationStatus{
			Status: status,
		},
	}

	if status != ewm.OrderReservationStatusNew && status != ewm.OrderReservationStatusAccepted {
		or.Status.WarehouseOrders = warehouseOrders
	}

	return &or
}

func createTestEWMWarehouseOrders() []ewm.EWMWarehouseOrder {

	w := []ewm.EWMWarehouseOrder{
		{
			Lgnum: "1710",
			Who:   "2000001",
			Flgto: true,
			Queue: "ROBOTS",
			Lsd:   testEwmTimeNotExpired,
			Warehousetasks: []ewm.EWMWarehouseTask{
				{
					Lgnum: "1710",
					Tanum: "1000001",
					Who:   "2000001",
					Vltyp: "Y021",
					Vlber: "YS01",
					Vlpla: "GR-YDI1",
					Nltyp: "Y920",
					Nlber: "YO01",
					Nlpla: "GI-YDO1",
				},
			},
		},
		{
			Lgnum: "1710",
			Who:   "2000002",
			Flgto: true,
			Queue: "ROBOTS",
			Lsd:   testEwmTimeNotExpired,
			Warehousetasks: []ewm.EWMWarehouseTask{
				{
					Lgnum: "1710",
					Tanum: "1000002",
					Who:   "2000002",
					Vltyp: "Y021",
					Vlber: "YS01",
					Vlpla: "GR-YDI2",
					Nltyp: "Y920",
					Nlber: "YO01",
					Nlpla: "GI-YDO2",
				},
			},
		},
		// Order with Latest Start Date (Lsd) in the past
		{
			Lgnum: "1710",
			Who:   "2000003",
			Flgto: true,
			Queue: "ROBOTS",
			Lsd:   testEwmTimeExpired,
			Warehousetasks: []ewm.EWMWarehouseTask{
				{
					Lgnum: "1710",
					Tanum: "1000003",
					Who:   "2000003",
					Vltyp: "Y021",
					Vlber: "YS01",
					Vlpla: "GR-YDI3",
					Nltyp: "Y920",
					Nlber: "YO01",
					Nlpla: "GI-YDO3",
				},
			},
		},
	}

	return w
}

func createTestRobot(robotNumber int, available, charged bool) *registry.Robot {
	r := registry.Robot{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("robot-%v", robotNumber),
			Namespace: metav1.NamespaceDefault,
			Labels:    map[string]string{robotLabel: fmt.Sprintf("robot-%v", robotNumber)},
		},
		Spec: registry.RobotSpec{
			Type:    "test-robot",
			Project: "test-project",
		},
		Status: registry.RobotStatus{
			Robot: registry.RobotStatusRobot{
				UpdateTime:                 metav1.Now(),
				LastStateChange:            metav1.Now(),
				State:                      registry.RobotStateUnavailable,
				BatteryPercentage:          25.0,
				EmergencyStopButtonPressed: false,
			},
		},
	}

	if available {
		r.Status.Robot.State = registry.RobotStateAvailable
	}

	if charged {
		r.Status.Robot.BatteryPercentage = 80.0
	}

	return &r
}

func createTestRobotConfiguration(robotNumber int, inScope, running, available, charging bool) *ewm.RobotConfiguration {
	r := ewm.RobotConfiguration{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("robot-%v", robotNumber),
			Namespace: metav1.NamespaceDefault,
			Labels:    map[string]string{robotLabel: fmt.Sprintf("robot-%v", robotNumber)},
		},
		Spec: ewm.RobotConfigurationSpec{
			Lgnum:                 "1710",
			Rsrctype:              "RB01",
			Rsrcgrp:               "OFF",
			Chargers:              []string{"Charger1"},
			BatteryMin:            20,
			BatteryIdle:           70,
			BatteryOk:             100,
			MaxIdleTime:           1,
			RecoverFromRobotError: false,
			Mode:                  ewm.RobotConfigurationModeStop,
		},
		Status: ewm.RobotConfigurationStatus{
			Lgnum:        "1710",
			Statemachine: "robotError",
		},
	}

	if inScope {
		r.Spec.Rsrcgrp = "RB01"
	}

	if running {
		r.Spec.Mode = ewm.RobotConfigurationModeRun
	}

	if available {
		r.Status.Statemachine = "idle"
	}

	if charging {
		r.Status.Statemachine = "charging"
	}

	return &r
}

func TestClassifyAuctions(t *testing.T) {
	type testCase struct {
		name     string
		auctions []auction
		expected *classifiedAuctions
	}

	tests := []testCase{
		{
			name: "New Auction",
			auctions: []auction{
				{
					orderAuction:  "1710.Test",
					reservationCR: *createTestOrderReservation("1710.Test", []ewm.EWMWarehouseOrder{}, ewm.OrderReservationStatusNew),
				},
			},
			expected: &classifiedAuctions{
				waitForOrderManager: []auction{
					{
						orderAuction:  "1710.Test",
						reservationCR: *createTestOrderReservation("1710.Test", []ewm.EWMWarehouseOrder{}, ewm.OrderReservationStatusNew),
					},
				},
			},
		},
		{
			name: "Accepted Auction",
			auctions: []auction{
				{
					orderAuction:  "1710.Test",
					reservationCR: *createTestOrderReservation("1710.Test", []ewm.EWMWarehouseOrder{}, ewm.OrderReservationStatusAccepted),
				},
			},
			expected: &classifiedAuctions{
				waitForOrderManager: []auction{
					{
						orderAuction:  "1710.Test",
						reservationCR: *createTestOrderReservation("1710.Test", []ewm.EWMWarehouseOrder{}, ewm.OrderReservationStatusAccepted),
					},
				},
			},
		},
		{
			name: "No Order Auction CRs",
			auctions: []auction{
				{
					orderAuction:  "1710.Test",
					reservationCR: *createTestOrderReservation("1710.Test", []ewm.EWMWarehouseOrder{}, ewm.OrderReservationStatusReservations),
				},
			},
			expected: &classifiedAuctions{
				auctionsToCreate: []auction{
					{
						orderAuction:  "1710.Test",
						reservationCR: *createTestOrderReservation("1710.Test", []ewm.EWMWarehouseOrder{}, ewm.OrderReservationStatusReservations),
					},
				},
			},
		},
		{
			name: "Order Auction CR without biddings",
			auctions: []auction{
				{
					orderAuction:  "1710.Test",
					reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusReservations),
					auctionCRs: []ewm.OrderAuction{
						*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
					},
				},
			},
			expected: &classifiedAuctions{
				auctionsRunning: []auction{
					{
						orderAuction:  "1710.Test",
						reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusReservations),
						auctionCRs: []ewm.OrderAuction{
							*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
						},
					},
				},
			},
		},
		{
			name: "Order Auction CR with completed biddings",
			auctions: []auction{
				{
					orderAuction:  "1710.Test",
					reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusReservations),
					auctionCRs: []ewm.OrderAuction{
						*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
						*createTestOrderAuction("1710.Test", 4, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
						*createTestOrderAuction("1710.Test", 5, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
					},
				},
			},
			expected: &classifiedAuctions{
				auctionsToClose: []auction{
					{
						orderAuction:  "1710.Test",
						reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusReservations),
						auctionCRs: []ewm.OrderAuction{
							*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
							*createTestOrderAuction("1710.Test", 4, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
							*createTestOrderAuction("1710.Test", 5, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
						},
					},
				},
			},
		},
		{
			name: "An incomplete Order Auction CR prevents closing of auction",
			auctions: []auction{
				{
					orderAuction:  "1710.Test",
					reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusReservations),
					auctionCRs: []ewm.OrderAuction{
						*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
						*createTestOrderAuction("1710.Test", 4, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
						*createTestOrderAuction("1710.Test", 5, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
					},
				},
			},
			expected: &classifiedAuctions{
				auctionsRunning: []auction{
					{
						orderAuction:  "1710.Test",
						reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusReservations),
						auctionCRs: []ewm.OrderAuction{
							*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
							*createTestOrderAuction("1710.Test", 4, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
							*createTestOrderAuction("1710.Test", 5, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
						},
					},
				},
			},
		},
		{
			name: "An incomplete expired Order Auction CR does not prevent closing of auction",
			auctions: []auction{
				{
					orderAuction:  "1710.Test",
					reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusReservations),
					auctionCRs: []ewm.OrderAuction{
						*createTestOrderAuction("1710.Test", 3, true, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
						*createTestOrderAuction("1710.Test", 4, true, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
						*createTestOrderAuction("1710.Test", 5, true, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
					},
				},
			},
			expected: &classifiedAuctions{
				auctionsToClose: []auction{
					{
						orderAuction:  "1710.Test",
						reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusReservations),
						auctionCRs: []ewm.OrderAuction{
							*createTestOrderAuction("1710.Test", 3, true, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
							*createTestOrderAuction("1710.Test", 4, true, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
							*createTestOrderAuction("1710.Test", 5, true, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
						},
					},
				},
			},
		},
		{
			name: "An incomplete Order Auction CR of an unavailable robot does not prevent closing of auction",
			auctions: []auction{
				{
					orderAuction:  "1710.Test",
					reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusReservations),
					auctionCRs: []ewm.OrderAuction{
						*createTestOrderAuction("1710.Test", 2, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
						*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
						*createTestOrderAuction("1710.Test", 4, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
						*createTestOrderAuction("1710.Test", 5, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
					},
				},
			},
			expected: &classifiedAuctions{
				auctionsToClose: []auction{
					{
						orderAuction:  "1710.Test",
						reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusReservations),
						auctionCRs: []ewm.OrderAuction{
							*createTestOrderAuction("1710.Test", 2, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
							*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
							*createTestOrderAuction("1710.Test", 4, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
							*createTestOrderAuction("1710.Test", 5, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
						},
					},
				},
			},
		},
		{
			name: "Order Auction complete",
			auctions: []auction{
				{
					orderAuction:  "1710.Test",
					reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusSucceeded),
					auctionCRs: []ewm.OrderAuction{
						*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
						*createTestOrderAuction("1710.Test", 4, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
						*createTestOrderAuction("1710.Test", 5, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
					},
				},
			},
			expected: &classifiedAuctions{
				auctionsToComplete: []auction{
					{
						orderAuction:  "1710.Test",
						reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusSucceeded),
						auctionCRs: []ewm.OrderAuction{
							*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
							*createTestOrderAuction("1710.Test", 4, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
							*createTestOrderAuction("1710.Test", 5, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
						},
					},
				},
			},
		},
		{
			name: "Reservervation timeout",
			auctions: []auction{
				{
					orderAuction:  "1710.Test",
					reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusTimeout),
					auctionCRs: []ewm.OrderAuction{
						*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
						*createTestOrderAuction("1710.Test", 4, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
						*createTestOrderAuction("1710.Test", 5, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
					},
				},
			},
			expected: &classifiedAuctions{
				auctionsToComplete: []auction{
					{
						orderAuction:  "1710.Test",
						reservationCR: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusTimeout),
						auctionCRs: []ewm.OrderAuction{
							*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
							*createTestOrderAuction("1710.Test", 4, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
							*createTestOrderAuction("1710.Test", 5, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
						},
					},
				},
			},
		},
	}

	for _, test := range tests {
		r := createTestAuctioneerController()
		t.Run(
			test.name,
			func(t *testing.T) {
				assert.Equal(t, test.expected, r.classifyAuctions(test.auctions, createTestRobotStates()))
			})
	}
}

func TestGetAuctionWinners(t *testing.T) {
	type testCase struct {
		name        string
		reservation ewm.OrderReservation
		auctions    []ewm.OrderAuction
		expected    []ewm.OrderAssignment
	}

	tests := []testCase{
		{
			name:        "Warehouse Order with expired LSD assigned to random robot",
			reservation: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusReservations),
			auctions: []ewm.OrderAuction{
				*createTestOrderAuction("1710.Test", 3, true, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusRunning),
			},
			expected: []ewm.OrderAssignment{
				{
					Lgnum: "1710",
					Who:   "2000003",
					Rsrc:  "ROBOT-3",
				},
			},
		},
		{
			name:        "Warehouse Order with expired LSD to robot-3 nothing to robot-6",
			reservation: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusReservations),
			auctions: []ewm.OrderAuction{
				*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
				*createTestOrderAuction("1710.Test", 4, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
				*createTestOrderAuction("1710.Test", 5, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
				*createTestOrderAuction("1710.Test", 6, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
			},
			expected: []ewm.OrderAssignment{
				{
					Lgnum: "1710",
					Who:   "2000003",
					Rsrc:  "ROBOT-3",
				},
				{
					Lgnum: "1710",
					Who:   "2000002",
					Rsrc:  "ROBOT-4",
				},
				{
					Lgnum: "1710",
					Who:   "2000001",
					Rsrc:  "ROBOT-5",
				},
			},
		},
		{
			name:        "No Warehouse Order Assigments for unavailable robots",
			reservation: *createTestOrderReservation("1710.Test", createTestEWMWarehouseOrders(), ewm.OrderReservationStatusReservations),
			auctions: []ewm.OrderAuction{
				*createTestOrderAuction("1710.Test", 1, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
				*createTestOrderAuction("1710.Test", 2, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
				*createTestOrderAuction("1710.Test", 3, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
				*createTestOrderAuction("1710.Test", 4, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
				*createTestOrderAuction("1710.Test", 5, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
				*createTestOrderAuction("1710.Test", 6, false, createTestEWMWarehouseOrders(), ewm.OrderAuctionBidStatusCompleted),
			},
			expected: []ewm.OrderAssignment{
				{
					Lgnum: "1710",
					Who:   "2000003",
					Rsrc:  "ROBOT-3",
				},
				{
					Lgnum: "1710",
					Who:   "2000002",
					Rsrc:  "ROBOT-4",
				},
				{
					Lgnum: "1710",
					Who:   "2000001",
					Rsrc:  "ROBOT-5",
				},
			},
		},
	}

	for _, test := range tests {
		a := createTestAuctioneerController()
		t.Run(
			test.name,
			func(t *testing.T) {
				assert.Equal(t, test.expected, a.getAuctionWinners(test.reservation, test.auctions, createTestRobotStates()))
			})
	}
}

func TestReconcileOne(t *testing.T) {

	ctx := context.Background()

	var clientObjects []client.Object

	// Test case: auctioneer only
	clientObjects = append(clientObjects, createTestAuctioneer())

	a := createTestAuctioneerController(clientObjects...)

	reconcileRequest := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "test-auctioneer",
			Namespace: metav1.NamespaceDefault,
		},
	}

	a.Reconcile(ctx, reconcileRequest)

	// Expected status of auctioneer
	var auctioneerResult ewm.Auctioneer
	a.client.Get(ctx, reconcileRequest.NamespacedName, &auctioneerResult)

	assert.Equal(t, auctioneerResult.Status.Status, ewm.AuctioneerStatusWatching)
	assert.Equal(t, auctioneerResult.Status.RunningAuctions, 0)
	assert.Equal(t, auctioneerResult.Status.WarehouseOrdersInProcess, 0)

}

func TestReconcileTwo(t *testing.T) {

	ctx := context.Background()

	var clientObjects []client.Object

	// Test case: auctioneer with several robots and no running auctions
	clientObjects = append(clientObjects, createTestAuctioneer())

	// Robot not in scope
	clientObjects = append(clientObjects, createTestRobot(1, false, false))
	clientObjects = append(clientObjects, createTestRobotConfiguration(1, false, false, false, false))
	// Robot in scope, but not running
	clientObjects = append(clientObjects, createTestRobot(2, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(2, true, false, false, false))
	// Robot in scope, running, but unavailable (Robot)
	clientObjects = append(clientObjects, createTestRobot(3, false, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(3, true, true, true, false))
	// Robot in scope, running, but unavailable (RobotConfiguration)
	clientObjects = append(clientObjects, createTestRobot(4, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(4, true, true, false, false))
	// Robot in scope, running and available
	clientObjects = append(clientObjects, createTestRobot(5, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(5, true, true, true, false))
	// Robot in scope, running, available and charging
	clientObjects = append(clientObjects, createTestRobot(6, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(6, true, true, true, true))
	// Robot in scope, running, available, charging, but not battery level too low
	clientObjects = append(clientObjects, createTestRobot(7, true, false))
	clientObjects = append(clientObjects, createTestRobotConfiguration(7, true, true, true, true))
	// Robot in scope, running, available, but not in list of deployed robots
	clientObjects = append(clientObjects, createTestRobot(10, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(10, true, true, true, false))

	a := createTestAuctioneerController(clientObjects...)

	reconcileRequest := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "test-auctioneer",
			Namespace: metav1.NamespaceDefault,
		},
	}

	a.Reconcile(ctx, reconcileRequest)

	// Expected status of auctioneer
	var auctioneerResult ewm.Auctioneer
	a.client.Get(ctx, reconcileRequest.NamespacedName, &auctioneerResult)

	assert.Equal(t, auctioneerResult.Status.Status, ewm.AuctioneerStatusWatching)
	assert.Equal(t, auctioneerResult.Status.RunningAuctions, 0)
	assert.Equal(t, auctioneerResult.Status.WarehouseOrdersInProcess, 0)
	assert.NotContains(t, auctioneerResult.Status.RobotsInScope, "robot-1")
	assert.NotContains(t, auctioneerResult.Status.AvailableRobots, "robot-1")
	assert.Contains(t, auctioneerResult.Status.RobotsInScope, "robot-2")
	assert.NotContains(t, auctioneerResult.Status.AvailableRobots, "robot-2")
	assert.Contains(t, auctioneerResult.Status.RobotsInScope, "robot-3")
	assert.NotContains(t, auctioneerResult.Status.AvailableRobots, "robot-3")
	assert.Contains(t, auctioneerResult.Status.RobotsInScope, "robot-4")
	assert.NotContains(t, auctioneerResult.Status.AvailableRobots, "robot-4")
	assert.Contains(t, auctioneerResult.Status.RobotsInScope, "robot-5")
	assert.Contains(t, auctioneerResult.Status.AvailableRobots, "robot-5")
	assert.Contains(t, auctioneerResult.Status.RobotsInScope, "robot-6")
	assert.Contains(t, auctioneerResult.Status.AvailableRobots, "robot-6")
	assert.Contains(t, auctioneerResult.Status.RobotsInScope, "robot-7")
	assert.NotContains(t, auctioneerResult.Status.AvailableRobots, "robot-7")
	assert.NotContains(t, auctioneerResult.Status.RobotsInScope, "robot-10")
	assert.NotContains(t, auctioneerResult.Status.AvailableRobots, "robot-10")

	// Expected OrderReservations
	var orderReservationsResult ewm.OrderReservationList
	a.client.List(ctx, &orderReservationsResult, client.MatchingFields{ownerReferencesUID: string(auctioneerResult.UID)})

	// One reservation with those specifications
	assert.Equal(t, len(orderReservationsResult.Items), 1)
	for i, res := range orderReservationsResult.Items {
		if i == 1 {
			assert.Equal(t, res.Spec.OrderRequest.Lgnum, "1710")
			assert.Equal(t, res.Spec.OrderRequest.Rsrctype, "RB01")
			assert.Equal(t, res.Spec.OrderRequest.Rsrcgrp, "RB01")
			assert.Equal(t, res.Spec.OrderRequest.Quantity, 3)
		}
	}

}

func TestReconcileThree(t *testing.T) {

	ctx := context.Background()

	var clientObjects []client.Object

	// Test case: auctioneer with several robots and existing order reservation for 3 orders
	clientObjects = append(clientObjects, createTestAuctioneer())
	whos := createTestEWMWarehouseOrders()
	clientObjects = append(clientObjects, createTestOrderReservation("1710.12345", whos, ewm.OrderReservationStatusReservations))

	// Robot not in scope
	clientObjects = append(clientObjects, createTestRobot(1, false, false))
	clientObjects = append(clientObjects, createTestRobotConfiguration(1, false, false, false, false))
	// Robot in scope, but not running
	clientObjects = append(clientObjects, createTestRobot(2, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(2, true, false, false, false))
	// Robot in scope, running, but unavailable (Robot)
	clientObjects = append(clientObjects, createTestRobot(3, false, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(3, true, true, true, false))
	// Robot in scope, running, but unavailable (RobotConfiguration)
	clientObjects = append(clientObjects, createTestRobot(4, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(4, true, true, false, false))
	// Robot in scope, running and available
	clientObjects = append(clientObjects, createTestRobot(5, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(5, true, true, true, false))
	// Robot in scope, running, available and charging
	clientObjects = append(clientObjects, createTestRobot(6, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(6, true, true, true, true))
	// Robot in scope, running, available, charging, but not battery level too low
	clientObjects = append(clientObjects, createTestRobot(7, true, false))
	clientObjects = append(clientObjects, createTestRobotConfiguration(7, true, true, true, true))
	// Robot in scope, running, available, but not in list of deployed robots
	clientObjects = append(clientObjects, createTestRobot(10, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(10, true, true, true, false))

	a := createTestAuctioneerController(clientObjects...)

	reconcileRequest := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "test-auctioneer",
			Namespace: metav1.NamespaceDefault,
		},
	}

	a.Reconcile(ctx, reconcileRequest)

	// Expected status of auctioneer
	var auctioneerResult ewm.Auctioneer
	a.client.Get(ctx, reconcileRequest.NamespacedName, &auctioneerResult)

	assert.Equal(t, auctioneerResult.Status.Status, ewm.AuctioneerStatusAuction)
	assert.Equal(t, auctioneerResult.Status.RunningAuctions, 1)
	assert.Equal(t, auctioneerResult.Status.WarehouseOrdersInProcess, 0)

	// Expected OrderAuctions
	var orderAuctionsResult ewm.OrderAuctionList
	a.client.List(ctx, &orderAuctionsResult)

	// Two OrderAuctions with those specifications
	assert.Equal(t, len(orderAuctionsResult.Items), 2)

	var robotsWithAuctions []string
	for _, auction := range orderAuctionsResult.Items {
		robotsWithAuctions = append(robotsWithAuctions, auction.GetLabels()[robotLabel])
		assert.Equal(t, auction.Spec.WarehouseOrders, whos)
	}
	assert.Contains(t, robotsWithAuctions, "robot-5")
	assert.Contains(t, robotsWithAuctions, "robot-6")

}

func TestReconcileFour(t *testing.T) {

	ctx := context.Background()

	var clientObjects []client.Object

	// Test case: auctioneer with several robots, existing order reservation for 3 orders and no bids from robots
	clientObjects = append(clientObjects, createTestAuctioneer())
	auctionName := "1710.12345"
	whos := createTestEWMWarehouseOrders()
	clientObjects = append(clientObjects, createTestOrderReservation(auctionName, whos, ewm.OrderReservationStatusReservations))

	// Robot not in scope
	clientObjects = append(clientObjects, createTestRobot(1, false, false))
	clientObjects = append(clientObjects, createTestRobotConfiguration(1, false, false, false, false))
	// Robot in scope, but not running
	clientObjects = append(clientObjects, createTestRobot(2, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(2, true, false, false, false))
	// Robot in scope, running, but unavailable (Robot)
	clientObjects = append(clientObjects, createTestRobot(3, false, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(3, true, true, true, false))
	// Robot in scope, running, but unavailable (RobotConfiguration)
	clientObjects = append(clientObjects, createTestRobot(4, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(4, true, true, false, false))
	clientObjects = append(clientObjects, createTestOrderAuction(auctionName, 4, false, whos, ewm.OrderAuctionBidStatusRunning))
	// Robot in scope, running and available
	clientObjects = append(clientObjects, createTestRobot(5, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(5, true, true, true, false))
	clientObjects = append(clientObjects, createTestOrderAuction(auctionName, 5, false, whos, ewm.OrderAuctionBidStatusRunning))
	// Robot in scope, running, available and charging
	clientObjects = append(clientObjects, createTestRobot(6, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(6, true, true, true, true))
	clientObjects = append(clientObjects, createTestOrderAuction(auctionName, 6, false, whos, ewm.OrderAuctionBidStatusRunning))
	// Robot in scope, running, available, charging, but not battery level too low
	clientObjects = append(clientObjects, createTestRobot(7, true, false))
	clientObjects = append(clientObjects, createTestRobotConfiguration(7, true, true, true, true))
	clientObjects = append(clientObjects, createTestOrderAuction(auctionName, 7, false, whos, ewm.OrderAuctionBidStatusRunning))
	// Robot in scope, running, available, but not in list of deployed robots
	clientObjects = append(clientObjects, createTestRobot(10, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(10, true, true, true, false))

	a := createTestAuctioneerController(clientObjects...)

	reconcileRequest := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "test-auctioneer",
			Namespace: metav1.NamespaceDefault,
		},
	}

	a.Reconcile(ctx, reconcileRequest)

	// Expected status of auctioneer
	var auctioneerResult ewm.Auctioneer
	a.client.Get(ctx, reconcileRequest.NamespacedName, &auctioneerResult)

	assert.Equal(t, auctioneerResult.Status.Status, ewm.AuctioneerStatusAuction)
	assert.Equal(t, auctioneerResult.Status.RunningAuctions, 1)
	assert.Equal(t, auctioneerResult.Status.WarehouseOrdersInProcess, 0)

	// Expected OrderAuctions
	var orderAuctionsResult ewm.OrderAuctionList
	a.client.List(ctx, &orderAuctionsResult)

	// Four OrderAuctions with those specifications
	assert.Equal(t, len(orderAuctionsResult.Items), 4)

	var robotsWithAuctions []string
	for _, auction := range orderAuctionsResult.Items {
		robotsWithAuctions = append(robotsWithAuctions, auction.GetLabels()[robotLabel])
	}
	assert.Contains(t, robotsWithAuctions, "robot-4")
	assert.Contains(t, robotsWithAuctions, "robot-5")
	assert.Contains(t, robotsWithAuctions, "robot-6")
	assert.Contains(t, robotsWithAuctions, "robot-7")

}

func TestReconcileFive(t *testing.T) {

	ctx := context.Background()

	var clientObjects []client.Object

	// Test case: auctioneer with several robots, existing order reservation for 3 orders and bids from robots
	clientObjects = append(clientObjects, createTestAuctioneer())
	auctionName := "1710.12345"
	whos := createTestEWMWarehouseOrders()
	clientObjects = append(clientObjects, createTestOrderReservation(auctionName, whos, ewm.OrderReservationStatusReservations))

	// Robot not in scope
	clientObjects = append(clientObjects, createTestRobot(1, false, false))
	clientObjects = append(clientObjects, createTestRobotConfiguration(1, false, false, false, false))
	// Robot in scope, but not running
	clientObjects = append(clientObjects, createTestRobot(2, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(2, true, false, false, false))
	// Robot in scope, running, but unavailable (Robot)
	clientObjects = append(clientObjects, createTestRobot(3, false, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(3, true, true, true, false))
	// Robot in scope, running, but unavailable (RobotConfiguration)
	clientObjects = append(clientObjects, createTestRobot(4, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(4, true, true, false, false))
	clientObjects = append(clientObjects, createTestOrderAuction(auctionName, 4, false, whos, ewm.OrderAuctionBidStatusCompleted))
	// Robot in scope, running and available
	clientObjects = append(clientObjects, createTestRobot(5, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(5, true, true, true, false))
	clientObjects = append(clientObjects, createTestOrderAuction(auctionName, 5, false, whos, ewm.OrderAuctionBidStatusCompleted))
	// Robot in scope, running, available and charging
	clientObjects = append(clientObjects, createTestRobot(6, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(6, true, true, true, true))
	clientObjects = append(clientObjects, createTestOrderAuction(auctionName, 6, false, whos, ewm.OrderAuctionBidStatusCompleted))
	// Robot in scope, running, available, charging, but not battery level too low
	clientObjects = append(clientObjects, createTestRobot(7, true, false))
	clientObjects = append(clientObjects, createTestRobotConfiguration(7, true, true, true, true))
	clientObjects = append(clientObjects, createTestOrderAuction(auctionName, 7, false, whos, ewm.OrderAuctionBidStatusCompleted))
	// Robot in scope, running, available, but not in list of deployed robots
	clientObjects = append(clientObjects, createTestRobot(10, true, true))
	clientObjects = append(clientObjects, createTestRobotConfiguration(10, true, true, true, false))

	a := createTestAuctioneerController(clientObjects...)

	reconcileRequest := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "test-auctioneer",
			Namespace: metav1.NamespaceDefault,
		},
	}

	a.Reconcile(ctx, reconcileRequest)

	// Expected status of auctioneer
	var auctioneerResult ewm.Auctioneer
	a.client.Get(ctx, reconcileRequest.NamespacedName, &auctioneerResult)

	assert.Equal(t, auctioneerResult.Status.Status, ewm.AuctioneerStatusWaiting)
	assert.Equal(t, auctioneerResult.Status.RunningAuctions, 0)
	assert.Equal(t, auctioneerResult.Status.WarehouseOrdersInProcess, 0)

	// Expected OrderReservations
	var orderReservationsResult ewm.OrderReservationList
	a.client.List(ctx, &orderReservationsResult, client.MatchingFields{ownerReferencesUID: string(auctioneerResult.UID)})

	// One reservation with those specifications
	assert.Equal(t, len(orderReservationsResult.Items), 1)
	for i, res := range orderReservationsResult.Items {
		if i == 1 {
			assert.Equal(t, res.Spec.OrderRequest.Lgnum, "1710")
			assert.Equal(t, res.Spec.OrderRequest.Rsrctype, "RB01")
			assert.Equal(t, res.Spec.OrderRequest.Rsrcgrp, "RB01")
			assert.Equal(t, res.Spec.OrderRequest.Quantity, 3)

			assert.Contains(t, res.Spec.OrderAssignments, ewm.OrderAssignment{Lgnum: "1710", Who: "2000003", Rsrc: "ROBOT-5"})
			assert.Contains(t, res.Spec.OrderAssignments, ewm.OrderAssignment{Lgnum: "1710", Who: "2000002", Rsrc: "ROBOT-6"})
		}
	}

	// Expected OrderAuctions
	var orderAuctionsResult ewm.OrderAuctionList
	a.client.List(ctx, &orderAuctionsResult)

	// Four OrderAuctions with those specifications
	assert.Equal(t, len(orderAuctionsResult.Items), 4)

	var robotsWithAuctions []string
	for _, auction := range orderAuctionsResult.Items {
		robotsWithAuctions = append(robotsWithAuctions, auction.GetLabels()[robotLabel])
		assert.Equal(t, auction.Spec.AuctionStatus, ewm.OrderAuctionAuctionStatusClosed)
	}
	assert.Contains(t, robotsWithAuctions, "robot-4")
	assert.Contains(t, robotsWithAuctions, "robot-5")
	assert.Contains(t, robotsWithAuctions, "robot-6")
	assert.Contains(t, robotsWithAuctions, "robot-7")

}
