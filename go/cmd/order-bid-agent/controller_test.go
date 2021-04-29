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
	mis "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/mission/v1alpha1"
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

func createTestBidAgentController(initObjs ...client.Object) *reconcileBidAgent {
	sc := runtime.NewScheme()
	scheme.AddToScheme(sc)
	ewm.AddToScheme(sc)
	mis.AddToScheme(sc)
	client := fake.NewClientBuilder().WithScheme(sc).WithObjects(initObjs...).Build()
	r := &reconcileBidAgent{client: client, scheme: sc, robotName: "robot-1"}
	return r
}

func createTestOrderAuction(orderAuction string, auctionExpired bool, warehouseOrders []ewm.EWMWarehouseOrder, withStatus bool) *ewm.OrderAuction {

	var validUntil metav1.Time

	if auctionExpired {
		validUntil = testTimeExpired
	} else {
		validUntil = testTimeNotExpired
	}

	robot := fmt.Sprintf("robot-%v", 1)

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
	}

	if withStatus {
		oaStatus := ewm.OrderAuctionStatus{
			BidStatus: ewm.OrderAuctionBidStatusRunning,
		}
		oa.Status = oaStatus
	}

	return &oa
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

func createTestMission() *mis.Mission {
	m := mis.Mission{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-mission-1",
			Namespace: metav1.NamespaceDefault,
			Labels:    map[string]string{robotLabel: "robot-1"},
		},
		Spec: mis.MissionSpec{
			Actions: []mis.Action{
				&mis.MoveToNamedPositionAction{MoveToNamedPosition: mis.Target{TargetName: "Staging"}},
			},
		},
		Status: mis.MissionStatus{
			Status:          mis.MissionStatusRunning,
			TimeOfActuation: metav1.Time{time.Now()},
		},
	}

	return &m
}

func createTestRuntimeEstimation(estimatationExpired bool) *ewm.RunTimeEstimation {
	r := ewm.RunTimeEstimation{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "1710.12345-robot-1",
			Namespace: metav1.NamespaceDefault,
			Labels:    map[string]string{robotLabel: "robot-1"},
		},
		Spec: ewm.RunTimeEstimationSpec{
			StartPosition: "Staging",
			ValidUntil:    testTimeNotExpired,
			Paths: []ewm.Path{
				{Start: "Staging", Goal: "GR-YDI1"},
				{Start: "Staging", Goal: "GR-YDI2"},
				{Start: "Staging", Goal: "GR-YDI3"},
			},
		},
		Status: ewm.RunTimeEstimationStatus{
			Status: ewm.RunTimeEstimationStatusProcessed,
			RunTimes: []ewm.RunTime{
				{Start: "Staging", Goal: "GR-YDI1", Time: 1.1},
				{Start: "Staging", Goal: "GR-YDI2", Time: 2.2},
				{Start: "Staging", Goal: "GR-YDI3", Time: 3.3},
			},
		},
	}

	if estimatationExpired {
		r.Spec.ValidUntil = testTimeExpired
		r.Status.Status = ewm.RunTimeEstimationStatusRunning
		r.Status.RunTimes = r.Status.RunTimes[1:]
	}

	return &r
}

func createTestWarehouseOrder() *ewm.WarehouseOrder {
	w := ewm.WarehouseOrder{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "1710.2123456",
			Namespace: metav1.NamespaceDefault,
			Labels:    map[string]string{robotLabel: "robot-1"},
		},
		Spec: ewm.WarehouseOrderSpec{
			Sequence:    1,
			OrderStatus: ewm.WarehouseOrderOrderStatusRunning,
			Data: ewm.EWMWarehouseOrder{
				Lgnum: "1710",
				Who:   "2123456",
				Flgto: true,
				Queue: "ROBOTS",
				Lsd:   testEwmTimeNotExpired,
				Warehousetasks: []ewm.EWMWarehouseTask{
					{
						Lgnum: "1710",
						Tanum: "123456",
						Who:   "2123456",
						Vltyp: "Y021",
						Vlber: "YS01",
						Vlpla: "GR-YDI9",
						Nltyp: "Y920",
						Nlber: "YO01",
						Nlpla: "GI-YDO9",
					},
				},
			},
		},
	}

	return &w
}

func TestReconcileOne(t *testing.T) {

	ctx := context.Background()

	var clientObjects []client.Object

	// Test case: new OrderAuction, no WarehouseOrders in queue, one mission to Staging is running
	clientObjects = append(clientObjects, createTestMission())
	clientObjects = append(clientObjects, createTestOrderAuction("1710.12345", false, createTestEWMWarehouseOrders(), false))

	o := createTestBidAgentController(clientObjects...)

	reconcileRequest := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "1710.12345-robot-1",
			Namespace: metav1.NamespaceDefault,
		},
	}

	o.Reconcile(ctx, reconcileRequest)

	// Expected status of RuntimeEstimation
	var runtimeEstimationResult ewm.RunTimeEstimationList
	o.client.List(ctx, &runtimeEstimationResult)

	// One RuntimeEstimation with those specifications
	assert.Equal(t, len(runtimeEstimationResult.Items), 1)

	var runtimeEstimationNames []string
	var ewmPaths []ewm.Path
	for _, r := range runtimeEstimationResult.Items {
		runtimeEstimationNames = append(runtimeEstimationNames, r.GetName())
		ewmPaths = append(ewmPaths, r.Spec.Paths...)
		assert.Equal(t, r.Spec.StartPosition, "Staging")
	}
	assert.Contains(t, runtimeEstimationNames, "1710.12345-robot-1")
	assert.Contains(t, ewmPaths, ewm.Path{Start: "Staging", Goal: "GR-YDI1"})
	assert.Contains(t, ewmPaths, ewm.Path{Start: "Staging", Goal: "GR-YDI2"})
	assert.Contains(t, ewmPaths, ewm.Path{Start: "Staging", Goal: "GR-YDI3"})
}

func TestReconcileTwo(t *testing.T) {

	ctx := context.Background()

	var clientObjects []client.Object

	// Test case: new OrderAuction, one WarehouseOrder in queue, one mission to Staging is running
	clientObjects = append(clientObjects, createTestMission())
	clientObjects = append(clientObjects, createTestWarehouseOrder())
	clientObjects = append(clientObjects, createTestOrderAuction("1710.12345", false, createTestEWMWarehouseOrders(), false))

	o := createTestBidAgentController(clientObjects...)

	reconcileRequest := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "1710.12345-robot-1",
			Namespace: metav1.NamespaceDefault,
		},
	}

	o.Reconcile(ctx, reconcileRequest)

	// Expected status of RuntimeEstimation
	var runtimeEstimationResult ewm.RunTimeEstimationList
	o.client.List(ctx, &runtimeEstimationResult)

	// One RuntimeEstimation with those specifications
	assert.Equal(t, len(runtimeEstimationResult.Items), 1)

	var runtimeEstimationNames []string
	var ewmPaths []ewm.Path
	for _, r := range runtimeEstimationResult.Items {
		runtimeEstimationNames = append(runtimeEstimationNames, r.GetName())
		ewmPaths = append(ewmPaths, r.Spec.Paths...)
		assert.Equal(t, r.Spec.StartPosition, "GI-YDO9")
	}
	assert.Contains(t, runtimeEstimationNames, "1710.12345-robot-1")
	assert.Contains(t, ewmPaths, ewm.Path{Start: "GI-YDO9", Goal: "GR-YDI1"})
	assert.Contains(t, ewmPaths, ewm.Path{Start: "GI-YDO9", Goal: "GR-YDI2"})
	assert.Contains(t, ewmPaths, ewm.Path{Start: "GI-YDO9", Goal: "GR-YDI3"})
}

func TestReconcileThree(t *testing.T) {

	ctx := context.Background()

	var clientObjects []client.Object

	// Test case: existing OrderAuction, no WarehouseOrders in queue, one mission to Staging is running, RuntimeEstimation is completed
	clientObjects = append(clientObjects, createTestMission())
	clientObjects = append(clientObjects, createTestOrderAuction("1710.12345", false, createTestEWMWarehouseOrders(), false))
	clientObjects = append(clientObjects, createTestRuntimeEstimation(false))

	o := createTestBidAgentController(clientObjects...)

	reconcileRequest := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "1710.12345-robot-1",
			Namespace: metav1.NamespaceDefault,
		},
	}

	o.Reconcile(ctx, reconcileRequest)

	// Expected status of OrderAuction
	var auctionResult ewm.OrderAuction
	o.client.Get(ctx, reconcileRequest.NamespacedName, &auctionResult)

	assert.Equal(t, auctionResult.Status.BidStatus, ewm.OrderAuctionBidStatusCompleted)

	assert.Contains(t, auctionResult.Status.Biddings, ewm.WarehouseOrderBidding{Lgnum: "1710", Who: "2000001", Bidding: 1.1})
	assert.Contains(t, auctionResult.Status.Biddings, ewm.WarehouseOrderBidding{Lgnum: "1710", Who: "2000002", Bidding: 2.2})
	assert.Contains(t, auctionResult.Status.Biddings, ewm.WarehouseOrderBidding{Lgnum: "1710", Who: "2000003", Bidding: 3.3})
}

func TestReconcileFour(t *testing.T) {

	ctx := context.Background()

	var clientObjects []client.Object

	// Test case: existing expired OrderAuction, no WarehouseOrders in queue, one mission to Staging is running, RuntimeEstimation is not completed but expired
	clientObjects = append(clientObjects, createTestMission())
	clientObjects = append(clientObjects, createTestOrderAuction("1710.12345", true, createTestEWMWarehouseOrders(), false))
	clientObjects = append(clientObjects, createTestRuntimeEstimation(true))

	o := createTestBidAgentController(clientObjects...)

	reconcileRequest := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "1710.12345-robot-1",
			Namespace: metav1.NamespaceDefault,
		},
	}

	o.Reconcile(ctx, reconcileRequest)

	// Expected status of OrderAuction
	var auctionResult ewm.OrderAuction
	o.client.Get(ctx, reconcileRequest.NamespacedName, &auctionResult)

	assert.Equal(t, auctionResult.Status.BidStatus, ewm.OrderAuctionBidStatusCompleted)

	assert.NotContains(t, auctionResult.Status.Biddings, ewm.WarehouseOrderBidding{Lgnum: "1710", Who: "2000001", Bidding: 1.1})
	assert.Contains(t, auctionResult.Status.Biddings, ewm.WarehouseOrderBidding{Lgnum: "1710", Who: "2000002", Bidding: 2.2})
	assert.Contains(t, auctionResult.Status.Biddings, ewm.WarehouseOrderBidding{Lgnum: "1710", Who: "2000003", Bidding: 3.3})
}
