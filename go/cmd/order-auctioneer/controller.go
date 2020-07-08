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
	"reflect"
	"sort"
	"strings"
	"time"

	ewm "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	registry "github.com/googlecloudrobotics/core/src/go/pkg/apis/registry/v1alpha1"
	"github.com/pkg/errors"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/util/workqueue"
	"sigs.k8s.io/controller-runtime/pkg/client"
	ctrlclient "sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/event"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"sigs.k8s.io/controller-runtime/pkg/source"
)

const (
	ownerReferencesUID         string        = "metadata.ownerReferences.uid"
	robotLabel                 string        = "cloudrobotics.com/robot-name"
	orderAuctionLabel          string        = "ewm.sap.com/order-auction"
	timeBufferOrderReservation time.Duration = time.Second * 10
)

// Reconcile controller for auctioneer
type reconcileAuctioneer struct {
	client         client.Client
	scheme         *runtime.Scheme
	deployedRobots map[string]bool
}

// Implement reconcile.Reconciler so the controller can reconcile objects
var _ reconcile.Reconciler = &reconcileAuctioneer{}

// Available states from robot CRD
var robotAvailable = map[string]bool{
	string(registry.RobotStateAvailable): true,
}

// Unavailable states from ewm-robot-controller state machine
var statemachineUnavailable = map[string]bool{
	"moveTrolley_waitingForErrorRecovery":  true,
	"pickPackPass_waitingForErrorRecovery": true,
	"robotError":                           true,
	"charging":                             true,
}

// Add a new instance of auctioneer controller to a manager
func addAuctioneerController(ctx context.Context, mgr manager.Manager, deployedRobots map[string]bool) error {

	// Create auctioneer controller
	r := &reconcileAuctioneer{client: mgr.GetClient(), scheme: mgr.GetScheme(), deployedRobots: deployedRobots}
	c, err := controller.New("auctioneer-controller", mgr, controller.Options{Reconciler: r})

	if err != nil {
		return errors.Wrap(err, "create controller")
	}

	// Cache for OwnerReferences.UID
	err = mgr.GetCache().IndexField(ctx, &ewm.OrderReservation{}, ownerReferencesUID, indexOwnerReferences)
	if err != nil {
		return errors.Wrap(err, "add IndexField OrderReservation")
	}
	err = mgr.GetCache().IndexField(ctx, &ewm.OrderAuction{}, ownerReferencesUID, indexOwnerReferences)
	if err != nil {
		return errors.Wrap(err, "add IndexField OrderAuction")
	}

	// Watch Auctioneer CRs
	err = c.Watch(
		&source.Kind{Type: &ewm.Auctioneer{}}, &handler.EnqueueRequestForObject{},
	)
	if err != nil {
		return errors.Wrap(err, "watch Auctioneer")
	}

	// Watch OrderReservation CRs
	err = c.Watch(&source.Kind{Type: &ewm.OrderReservation{}},
		&handler.EnqueueRequestForOwner{OwnerType: &ewm.Auctioneer{}, IsController: true})

	if err != nil {
		return errors.Wrap(err, "watch OrderReservation")
	}

	// Watch OrderAuction CRs
	err = c.Watch(&source.Kind{Type: &ewm.OrderAuction{}},
		&handler.Funcs{
			UpdateFunc: func(e event.UpdateEvent, q workqueue.RateLimitingInterface) {
				log.Debug().Msgf("Auctioneer controller received update event for OrderAuction %q", e.MetaNew.GetName())
				r.enqueueFromLabel(e.MetaNew, q)
				if nameOrNamespaceChanged(e.MetaNew, e.MetaOld) {
					log.Debug().Msgf("Auctioneer controller received update event for OrderAuction %q", e.MetaOld.GetName())
					r.enqueueFromLabel(e.MetaOld, q)
				}
			},
		},
	)

	if err != nil {
		return errors.Wrap(err, "watch OrderAuction")
	}

	// Watch Robot CRs
	err = c.Watch(&source.Kind{Type: &registry.Robot{}},
		&handler.Funcs{
			UpdateFunc: func(e event.UpdateEvent, q workqueue.RateLimitingInterface) {
				// Check if status changed from unavailable to available or name changed
				rbStateOld := string(e.ObjectOld.(*registry.Robot).Status.Robot.State)
				rbStateNew := string(e.ObjectNew.(*registry.Robot).Status.Robot.State)
				change := !robotAvailable[rbStateOld] && robotAvailable[rbStateNew]
				change = change || nameOrNamespaceChanged(e.MetaNew, e.MetaOld)
				if change {
					log.Debug().Msgf("Auctioneer controller received update event for Robot %q", e.MetaNew.GetName())
					r.enqueueFromLabel(e.MetaNew, q)
					if nameOrNamespaceChanged(e.MetaNew, e.MetaOld) {
						log.Info().Msgf("Auctioneer controller received update event for Robot %q", e.MetaOld.GetName())
						r.enqueueFromLabel(e.MetaOld, q)
					}

				}
			},
		},
	)

	if err != nil {
		return errors.Wrap(err, "watch Robot")
	}

	// Watch RobotConfiguration CRs
	err = c.Watch(&source.Kind{Type: &ewm.RobotConfiguration{}},
		&handler.Funcs{
			CreateFunc: func(e event.CreateEvent, q workqueue.RateLimitingInterface) {
				// Only create events because of robots for which this app was deployed
				if !r.deployedRobots[e.Meta.GetName()] {
					return
				}
				log.Info().Msgf("Auctioneer controller received create event for RobotConfiguration %q", e.Meta.GetName())
				r.enqueueFromConfig(e.Object.(*ewm.RobotConfiguration).Spec, q)
			},
			UpdateFunc: func(e event.UpdateEvent, q workqueue.RateLimitingInterface) {
				// Only create events because of robots for which this app was deployed
				if !r.deployedRobots[e.MetaNew.GetName()] && !r.deployedRobots[e.MetaOld.GetName()] {
					return
				}
				// Check if Spec or name changed or status changed from unavailable to available
				rcOld := e.ObjectOld.(*ewm.RobotConfiguration)
				rcNew := e.ObjectNew.(*ewm.RobotConfiguration)
				change := !reflect.DeepEqual(rcOld.Spec, rcNew.Spec)
				change = change || statemachineUnavailable[rcOld.Status.Statemachine] && !statemachineUnavailable[rcNew.Status.Statemachine]
				change = change || nameOrNamespaceChanged(e.MetaNew, e.MetaOld)
				if change {
					log.Info().Msgf("Auctioneer controller received update event for RobotConfiguration %q", e.MetaNew.GetName())
					r.enqueueFromConfig(rcNew.Spec, q)
					if nameOrNamespaceChanged(e.MetaNew, e.MetaOld) {
						log.Info().Msgf("Auctioneer controller received update event for RobotConfiguration %q", e.MetaOld.GetName())
						r.enqueueFromConfig(rcOld.Spec, q)
					}
				}
			},
		},
	)

	if err != nil {
		return errors.Wrap(err, "watch RobotConfiguration")
	}

	// Watch WarehouseOrder CRs
	// Enqueue Reconcile when warehouse orders are finished
	err = c.Watch(&source.Kind{Type: &ewm.WarehouseOrder{}},
		&handler.Funcs{
			UpdateFunc: func(e event.UpdateEvent, q workqueue.RateLimitingInterface) {
				// Check if Spec.OrderStatus or name changed
				change := e.ObjectOld.(*ewm.WarehouseOrder).Spec.OrderStatus != e.ObjectNew.(*ewm.WarehouseOrder).Spec.OrderStatus
				change = change || nameOrNamespaceChanged(e.MetaNew, e.MetaOld)
				if change {
					log.Debug().Msgf("Auctioneer controller received update event for WarehouseOrder %q", e.MetaNew.GetName())
					r.enqueueFromLabel(e.MetaNew, q)
					if nameOrNamespaceChanged(e.MetaNew, e.MetaOld) {
						log.Info().Msgf("Auctioneer controller received update event for WarehouseOrder %q", e.MetaOld.GetName())
						r.enqueueFromLabel(e.MetaOld, q)
					}

				}
			},
			DeleteFunc: func(e event.DeleteEvent, q workqueue.RateLimitingInterface) {
				log.Debug().Msgf("Auctioneer controller received delete event for WarehouseOrder %q", e.Meta.GetName())
				r.enqueueFromLabel(e.Meta, q)
			},
		},
	)

	if err != nil {
		return errors.Wrap(err, "watch WarehouseOrder")
	}

	return err
}

// indexOwnerReferences indexes resources by the UIDs of their owner references.
func indexOwnerReferences(o runtime.Object) (refs []string) {
	switch obj := o.(type) {
	case *ewm.OrderReservation:
		for _, ref := range obj.OwnerReferences {
			refs = append(refs, string(ref.UID))
		}
	case *ewm.OrderAuction:
		for _, ref := range obj.OwnerReferences {
			refs = append(refs, string(ref.UID))
		}
	default:
		log.Panic().Msgf("Unknown type for indexOrderReferences %v", obj)
	}

	return refs
}

func nameOrNamespaceChanged(metaNew, metaOld metav1.Object) bool {
	change := metaNew.GetName() != metaOld.GetName()
	change = change || metaNew.GetNamespace() != metaOld.GetNamespace()
	return change
}

func (r *reconcileAuctioneer) enqueueFromConfig(c ewm.RobotConfigurationSpec, q workqueue.RateLimitingInterface) {
	// Lookup config in Auctioneer Status
	var auctioneers ewm.AuctioneerList
	err := r.client.List(context.Background(), &auctioneers)
	if err != nil {
		log.Error().Err(err).Msg("Unable to list Auctioneer CRs")
		return
	}

	// Request reconcile for all auctioneers sharing the same config
	for _, a := range auctioneers.Items {
		if a.Spec.Scope.Lgnum == c.Lgnum && a.Spec.Scope.Rsrcgrp == c.Rsrcgrp && a.Spec.Scope.Rsrctype == c.Rsrctype {
			log.Debug().Msgf("Reconcile of %q triggered by change of RobotConfiguration", a.GetName())
			q.Add(reconcile.Request{
				NamespacedName: types.NamespacedName{
					Name:      a.GetName(),
					Namespace: a.GetNamespace()},
			})
		}
	}
}

func (r *reconcileAuctioneer) enqueueFromLabel(m metav1.Object, q workqueue.RateLimitingInterface) {
	// Get robot name from label
	robot, ok := m.GetLabels()[robotLabel]

	if !ok {
		log.Error().Msgf("No label %q in CR %q", robotLabel, m.GetName())
		return
	}

	// Only create events because of robots for which this app was deployed
	if !r.deployedRobots[robot] {
		return
	}

	// Lookup robot name in Auctioneer Status
	var auctioneers ewm.AuctioneerList
	err := r.client.List(context.Background(), &auctioneers)
	if err != nil {
		log.Error().Err(err).Msg("Unable to list Auctioneer CRs")
		return
	}

	// Request reconcile for all auctioneers with robot label in RobotsInScope
	for _, auctioneer := range auctioneers.Items {
		for _, r := range auctioneer.Status.RobotsInScope {
			if r == robot {
				log.Debug().Msgf("Reconcile of %q triggered by change of CR %q", auctioneer.GetName(), m.GetName())
				q.Add(reconcile.Request{
					NamespacedName: types.NamespacedName{
						Name:      auctioneer.GetName(),
						Namespace: auctioneer.GetNamespace()},
				})
			}
		}
	}

}

func (r *reconcileAuctioneer) Reconcile(request reconcile.Request) (reconcile.Result, error) {

	log.Debug().Msgf("Starting reconcile for Auctioneer %+v", request.NamespacedName)

	// Context
	ctx := context.Background()

	// Get current version of Auctioneer CR
	var auctioneer ewm.Auctioneer
	err := r.client.Get(ctx, request.NamespacedName, &auctioneer)

	if k8serrors.IsNotFound(err) {
		// Auctioneer was already deleted, nothing to do.
		log.Debug().Msgf("Finished reconcile for Auctioneer %+v. Auctioneer was already deleted", request.NamespacedName)
		return reconcile.Result{}, nil
	} else if err != nil {
		log.Error().Err(err).Msgf("Error get Auctioneer %+v", request.NamespacedName)
		return reconcile.Result{}, errors.Wrapf(err, "get Auctioneer %+v", request.NamespacedName)
	}

	// Get robots for this Auctioneer
	robotStates, err := r.getRobots(ctx, &auctioneer)
	if err != nil {
		log.Error().Err(err).Msg("Error get robots")
		r.setErrorStatus(ctx, &auctioneer, err)
		return reconcile.Result{}, errors.Wrap(err, "get robots")
	}

	// Run auctions for this Auctioneer
	clres, opr, err := r.runAuctions(ctx, &auctioneer, robotStates)
	if err != nil {
		log.Error().Err(err).Msg("Error run auctions")
		r.setErrorStatus(ctx, &auctioneer, err)
		return reconcile.Result{}, errors.Wrap(err, "run auctions")
	}

	// Update status
	err = r.updateStatus(ctx, &auctioneer, robotStates, clres, opr)
	if err != nil {
		log.Error().Err(err).Msg("Error update auctioneer status")
		r.setErrorStatus(ctx, &auctioneer, err)
		return reconcile.Result{}, errors.Wrap(err, "update auctioneer status")
	}

	log.Debug().Msgf("Finished reconcile for Auctioneer %+v", request.NamespacedName)

	return r.getReconcileResult(&auctioneer, robotStates, opr, clres), nil
}

func (r *reconcileAuctioneer) updateStatus(ctx context.Context, a *ewm.Auctioneer, rs *robotStates, clAuc *classifiedAuctions, opr ordersPerRobot) error {

	var newStatus ewm.AuctioneerStatus

	// Collect robots
	newStatus.RobotsInScope = make([]string, 0)
	for robot := range rs.isInScope {
		newStatus.RobotsInScope = append(newStatus.RobotsInScope, robot)
	}
	sort.Strings(newStatus.RobotsInScope)
	newStatus.AvailableRobots = make([]string, 0)
	for robot := range rs.isAvailable {
		newStatus.AvailableRobots = append(newStatus.AvailableRobots, robot)
	}
	sort.Strings(newStatus.AvailableRobots)

	// Warehouse orders in process
	for _, wip := range opr {
		newStatus.WarehouseOrdersInProcess += wip
	}

	// Running auctions
	auctionsLookup := make(map[string]bool)
	for _, auc := range clAuc.auctionsToCreate {
		if !auctionsLookup[auc.reservationCR.GetLabels()[orderAuctionLabel]] {
			newStatus.RunningAuctions++
			auctionsLookup[auc.reservationCR.GetLabels()[orderAuctionLabel]] = true
		}
	}
	for _, auc := range clAuc.auctionsRunning {
		if !auctionsLookup[auc.reservationCR.GetLabels()[orderAuctionLabel]] {
			newStatus.RunningAuctions++
			auctionsLookup[auc.reservationCR.GetLabels()[orderAuctionLabel]] = true
		}
	}

	// Define new status
	if len(clAuc.auctionsRunning) > 0 {
		newStatus.Status = ewm.AuctioneerStatusAuction
	} else if len(clAuc.waitForOrderManager) > 0 || len(clAuc.auctionsToClose) > 0 {
		newStatus.Status = ewm.AuctioneerStatusWaiting
	} else {
		newStatus.Status = ewm.AuctioneerStatusWatching
	}

	// Message
	newStatus.Message = ""

	// Set equal timestamps for comparison of old and new status
	newStatus.UpdateTime = a.Status.UpdateTime
	newStatus.LastStatusChangeTime = a.Status.LastStatusChangeTime

	// Check if status changed
	if !reflect.DeepEqual(a.Status, newStatus) {
		// Set update times
		now := metav1.Now()
		newStatus.UpdateTime = now
		if a.Status.Status != newStatus.Status {
			newStatus.LastStatusChangeTime = now
		}
		a.Status = newStatus

		// Update status of  Auctioneer CR
		err := r.client.Status().Update(ctx, a)

		if err != nil {
			return errors.Wrap(err, "Auctioneer CR update")
		}

		log.Debug().Msgf("Status of Auctioneer %q updated", a.GetName())
	}

	return nil
}

func (r *reconcileAuctioneer) setErrorStatus(ctx context.Context, a *ewm.Auctioneer, err error) {
	a.Status.Status = ewm.AuctioneerStatusError
	a.Status.Message = fmt.Sprintln(err)
	// Update status of  Auctioneer CR
	r.client.Status().Update(ctx, a)
}

func (r *reconcileAuctioneer) getReconcileResult(a *ewm.Auctioneer, rs *robotStates, opr ordersPerRobot, clAuc *classifiedAuctions) reconcile.Result {

	var requeueAfter time.Duration = 0

	// Requeue frequently if robots do not have enough work
	for robot, orders := range opr {
		if rs.isAvailable[robot] && orders < a.Spec.Configuration.MinOrdersPerRobot {
			requeueAfter = time.Second * 30
			log.Debug().Msgf("Robot %q and maybe others are below spec.configuration.minOrdersPerRobot. Requeue in %v",
				robot, requeueAfter)
			break
		}
	}

	// Requeue several seconds before the earliest OrderReservation expires
	for _, auc := range clAuc.auctionsRunning {
		if !auc.reservationCR.Status.ValidUntil.IsZero() {
			d := auc.reservationCR.Status.ValidUntil.UTC().Sub(metav1.Now().UTC()) - timeBufferOrderReservation
			if requeueAfter == 0 || d < requeueAfter {
				requeueAfter = d
				log.Debug().Msgf("Running OrderReservation %q expires. Requeue in %v", auc.reservationCR.GetName(), requeueAfter)
			}
		}
	}

	return reconcile.Result{RequeueAfter: requeueAfter}
}

func (r *reconcileAuctioneer) getRobots(ctx context.Context, a *ewm.Auctioneer) (*robotStates, error) {

	robotStates := newRobotStates()

	// List Robots
	var robots registry.RobotList
	err := r.client.List(ctx, &robots)
	if err != nil {
		return nil, errors.Wrap(err, "get Robots")
	}

	// Check if robot is status available in robot CRD
	isRobotAvailable := make(map[string]bool)
	robotBattery := make(map[string]float64)
	for _, rb := range robots.Items {
		robotBattery[rb.GetName()] = rb.Status.Robot.BatteryPercentage
		state := string(rb.Status.Robot.State)
		if r.deployedRobots[rb.GetName()] && robotAvailable[state] {
			isRobotAvailable[rb.GetName()] = true
		}
	}

	// List RobotConfigurations
	var robotConfigurations ewm.RobotConfigurationList
	err = r.client.List(ctx, &robotConfigurations)
	if err != nil {
		return nil, errors.Wrap(err, "get RobotConfigurations")
	}

	for _, rc := range robotConfigurations.Items {
		// If robot fits to scope of Auctioneer and order-auction app is deployed on it, add it to status
		eq := r.deployedRobots[rc.GetName()]
		eq = eq && rc.Spec.Lgnum == a.Spec.Scope.Lgnum
		eq = eq && rc.Spec.Rsrctype == a.Spec.Scope.Rsrctype
		eq = eq && rc.Spec.Rsrcgrp == a.Spec.Scope.Rsrcgrp
		if eq {
			log.Debug().Msgf("Robot %q is in scope of Auctioneer %q", rc.GetName(), a.GetName())
			robotStates.isInScope[rc.GetName()] = true
			// Add robot to available robots if not unavailable according to ewm state machine and available in robot CR
			if rc.Spec.Mode == ewm.RobotConfigurationModeRun && isRobotAvailable[rc.GetName()] {
				if !statemachineUnavailable[rc.Status.Statemachine] {
					log.Debug().Msgf("Robot %q is available", rc.GetName())
					robotStates.isAvailable[rc.GetName()] = true
				}
				if rc.Status.Statemachine == "charging" && robotBattery[rc.GetName()] > rc.Spec.BatteryIdle {
					log.Debug().Msgf("Robot %q is available - charging but battery is above BatteryIdle level", rc.GetName())
					robotStates.isAvailable[rc.GetName()] = true
				}

			}
		}
	}

	return robotStates, nil
}

func (r *reconcileAuctioneer) mapWarehouseOrders(ctx context.Context, a *ewm.Auctioneer, rs *robotStates) (ordersPerRobot, error) {
	// List WarehouseOrders
	var warehouseOrders ewm.WarehouseOrderList
	err := r.client.List(ctx, &warehouseOrders)
	if err != nil {
		return nil, errors.Wrap(err, "get WarehouseOrders")
	}

	// Calculate the number of warehouse orders in process by the robots
	ordersPerRobot := make(ordersPerRobot)
	for _, w := range warehouseOrders.Items {
		// Save warehouse order if it is in process and assigned to a robot in scope
		if rs.isInScope[w.GetLabels()[robotLabel]] && w.Spec.OrderStatus == ewm.WarehouseOrderOrderStatusRunning {
			ordersPerRobot[w.GetLabels()[robotLabel]]++
		}
	}

	log.Debug().Msgf("Got this map of running warehouse orders per robot: %v", ordersPerRobot)

	return ordersPerRobot, nil
}

func (r *reconcileAuctioneer) collectAuctions(ctx context.Context, reservations *ewm.OrderReservationList) ([]auction, auctionsPerRobot, error) {

	// An OrderAuction consists of different CRs for each robot taking part. All CRs of an auction share the same label
	var auctions []auction

	auctionsPerRobot := make(auctionsPerRobot)

	for _, res := range reservations.Items {
		// Get OrderAuctions for this OrderReservation
		var orderAuctions ewm.OrderAuctionList
		err := r.client.List(ctx, &orderAuctions, ctrlclient.MatchingFields{ownerReferencesUID: string(res.UID)})
		if err != nil {
			return nil, nil, errors.Wrap(err, "get OrderAuctions")
		}
		auction := auction{orderAuction: res.GetLabels()[orderAuctionLabel], reservationCR: res}
		for _, oa := range orderAuctions.Items {

			auction.auctionCRs = append(auction.auctionCRs, oa)
			robot := oa.GetLabels()[robotLabel]
			// Increase counter if OrderAuction is not completed yet
			if oa.Spec.AuctionStatus != ewm.OrderAuctionAuctionStatusCompleted {
				auctionsPerRobot[robot]++
			}
		}
		auctions = append(auctions, auction)
	}

	log.Debug().Msgf("Got this map of running order auctions per robot: %v", auctionsPerRobot)

	return auctions, auctionsPerRobot, nil
}

func (r *reconcileAuctioneer) runAuctions(ctx context.Context, a *ewm.Auctioneer, rs *robotStates) (*classifiedAuctions, ordersPerRobot, error) {

	// Get data to run auctions
	// Get OrderReservations for this Auctioneer
	var orderReservations ewm.OrderReservationList
	err := r.client.List(ctx, &orderReservations, ctrlclient.MatchingFields{ownerReferencesUID: string(a.UID)})
	if err != nil {
		return nil, nil, errors.Wrap(err, "get OrderReservations")
	}

	// Collect auctions from OrderReservation and OrderAuction CRs
	auctions, auctionsPerRobot, err := r.collectAuctions(ctx, &orderReservations)
	if err != nil {
		return nil, nil, errors.Wrap(err, "collect auctions")
	}

	// Classify auctions to categories which decide what to to next
	classifiedAuctions := r.classifyAuctions(auctions, rs)

	// Map warehouse orders in process to robots in scope of this Auctioneer
	ordersPerRobot, err := r.mapWarehouseOrders(ctx, a, rs)
	if err != nil {
		return nil, nil, errors.Wrap(err, "map warehouse orders")
	}

	// Run Auctions
	// First complete auctions, second close auctions, third create auctions, forth reserve more warehouse orders if needed, fifth cleanup
	// First step
	r.doCompleteAuctions(ctx, classifiedAuctions, auctionsPerRobot)

	// Second step
	r.doCloseAuctions(ctx, classifiedAuctions, rs)

	// Third step
	r.doCreateAuctions(ctx, a, classifiedAuctions, auctionsPerRobot, ordersPerRobot, rs)

	// Fourth step
	r.doCreateReservations(ctx, a, classifiedAuctions, auctionsPerRobot, ordersPerRobot, rs)

	// Fifth step
	r.doCleanupReservations(ctx, classifiedAuctions)

	return classifiedAuctions, ordersPerRobot, nil
}

func (r *reconcileAuctioneer) classifyAuctions(auctions []auction, rs *robotStates) *classifiedAuctions {
	var clAuc classifiedAuctions
	for _, auc := range auctions {
		auctionAvailable := len(auc.auctionCRs) > 0
		switch auc.reservationCR.Status.Status {
		case ewm.OrderReservationStatusReservations:
			if !auctionAvailable {
				// Create case if no OrderAuction CRs exist for this OrderReservation
				clAuc.auctionsToCreate = append(clAuc.auctionsToCreate, auc)
			} else if len(auc.reservationCR.Spec.OrderAssignments) > 0 {
				// If there are Reservations with OrderAssigments, wait for the order manager to assign them
				clAuc.waitForOrderManager = append(clAuc.waitForOrderManager, auc)
			} else {
				// Close if all bids of the are completed or expired and wait otherwise. All CRs of an auction should have the same ValidUntil time
				toClose := true
				for _, auctionCR := range auc.auctionCRs {
					if rs.isAvailable[auctionCR.GetLabels()[robotLabel]] && auctionCR.Status.BidStatus != ewm.OrderAuctionBidStatusCompleted && auctionCR.Spec.ValidUntil.After(time.Now()) {
						toClose = false
					}
				}
				if toClose {
					clAuc.auctionsToClose = append(clAuc.auctionsToClose, auc)
				} else {
					clAuc.auctionsRunning = append(clAuc.auctionsRunning, auc)
				}
			}
		case ewm.OrderReservationStatusSucceeded, ewm.OrderReservationStatusTimeout:
			// Complete on success or timeout of the OrderReservation for this auction
			clAuc.auctionsToComplete = append(clAuc.auctionsToComplete, auc)
		case ewm.OrderReservationStatusNew, ewm.OrderReservationStatusAccepted, "":
			// New order auctions for which order manager did not create reservations yet
			clAuc.waitForOrderManager = append(clAuc.waitForOrderManager, auc)
		default:
			log.Error().Msgf("OrderReservation %q could not been classified", auc.reservationCR.GetName())
		}
	}

	log.Debug().Msgf("Classified OrderReservations: auctionsToCreate %v, auctionsRunning %v, auctionsToClose %v, auctionsToComplete %v, waitForOrderManager %v",
		len(clAuc.auctionsToCreate), len(clAuc.auctionsRunning), len(clAuc.auctionsToClose), len(clAuc.auctionsToComplete), len(clAuc.waitForOrderManager))

	return &clAuc
}

func (r *reconcileAuctioneer) doCompleteAuctions(ctx context.Context, clAuc *classifiedAuctions, apr auctionsPerRobot) {
	// Complete all auctions with the same label as the corresponding OrderReservation
	for _, auction := range clAuc.auctionsToComplete {
		for _, oa := range auction.auctionCRs {
			if oa.Spec.AuctionStatus != ewm.OrderAuctionAuctionStatusCompleted {
				log.Info().Msgf("OrderAuction %q is completed", oa.GetName())
				// Update AuctionStatus of this auction
				oa.Spec.AuctionStatus = ewm.OrderAuctionAuctionStatusCompleted
				err := r.client.Update(ctx, &oa)
				if err != nil {
					log.Error().Err(err).Msgf("Error updating OrderAuction %q", oa.GetName())
				} else {
					// Decrease the number of running order auctions for this robot
					apr[oa.GetLabels()[robotLabel]]--
				}
			}
		}
	}
}

func (r *reconcileAuctioneer) doCloseAuctions(ctx context.Context, clAuc *classifiedAuctions, rs *robotStates) {
	// Identify winners, then close all auctions with the same label as the corresponding OrderReservation
	for _, auction := range clAuc.auctionsToClose {

		log.Info().Msgf("Closing auction %q", auction.orderAuction)

		// Get order assignments for the OrderReservation by identifying auction winners
		orderAssignments := r.getAuctionWinners(auction.reservationCR, auction.auctionCRs, rs)

		// Don't close auction if there are no OrderAssignments
		if len(orderAssignments) == 0 {
			log.Info().Msgf("No order assignments. Stop closing auction %q", auction.orderAuction)
			continue
		}

		// Update OrderReservation Spec
		auction.reservationCR.Spec.OrderAssignments = orderAssignments
		log.Info().Msgf("Adding %v OrderAssignments to OrderReservation %q", len(orderAssignments), auction.reservationCR.GetName())
		err := r.client.Update(ctx, &auction.reservationCR)
		if err != nil {
			log.Error().Err(err).Msgf("Error updating OrderReservationSpec with OrderAssignments %q", auction.reservationCR.GetName())
			continue
		}

		for _, oa := range auction.auctionCRs {
			if oa.Spec.AuctionStatus != ewm.OrderAuctionAuctionStatusClosed {
				log.Info().Msgf("OrderAuction %q is closed", oa.GetName())
				// Update AuctionStatus of this auction
				oa.Spec.AuctionStatus = ewm.OrderAuctionAuctionStatusClosed
				err := r.client.Update(ctx, &oa)
				if err != nil {
					log.Error().Err(err).Msgf("Error updating OrderAuction %q", oa.GetName())
				}
			}
		}
	}
}

type biddingPlusRobot struct {
	robot   string
	bidding ewm.WarehouseOrderBidding
}

func (r *reconcileAuctioneer) getAuctionWinners(res ewm.OrderReservation, aucs []ewm.OrderAuction, rs *robotStates) []ewm.OrderAssignment {
	// Idea:
	//   - only robots which are in state available can win an auction
	//   - each robot is assigned to a maximum of one warehouse order
	//   - each warehouse order can be assigned just once
	//   - first ensure that warehouse order which have an overdue latest start date (Lsd) are assigned to the robot with the lowest bid. Warehouse order with Lsd = 0 are ignored in this step
	//   - secondly sort all bids by their value and start assigning the robot with the lowest overall bidding to the warehouse order

	// return variable
	var orderAssignments []ewm.OrderAssignment

	// Lookup maps for robots and warehouse orders with assignments
	robotsAssigned := make(map[string]bool)          // Key = robot-name
	robotsInAuction := make(map[string]bool)         // Key = robot-name
	warehouseOrdersAssigned := make(map[string]bool) // Key = Who; Safe here because we are planning just one warehouse

	// Collect all biddings from order auctions
	var biddings []biddingPlusRobot
	for _, auc := range aucs {
		robotsInAuction[auc.GetLabels()[robotLabel]] = true
		log.Info().Msgf("Robot %q created %v biddings for the %v warehouse orders of auction %q", auc.GetLabels()[robotLabel],
			len(auc.Status.Biddings), len(auc.Spec.WarehouseOrders), auc.GetName())
		for _, b := range auc.Status.Biddings {
			if !rs.isAvailable[auc.GetLabels()[robotLabel]] {
				log.Info().Msgf("Robot %q is not available, skipping its biddings of OrderAuction %q", auc.GetLabels()[robotLabel],
					auc.GetName())
				break
			}
			bidding := biddingPlusRobot{robot: auc.GetLabels()[robotLabel], bidding: b}
			biddings = append(biddings, bidding)
		}
	}
	// Sort biddings by lowest bidding
	sort.SliceStable(biddings, func(i, j int) bool {
		return biddings[i].bidding.Bidding < biddings[j].bidding.Bidding
	})

	// Collect warehouse orders with Lsd overdue
	var warehouseOrdersOverdue []ewm.EWMWarehouseOrder
	for _, who := range res.Status.WarehouseOrders {
		if !who.Lsd.IsZero() && time.Now().UTC().After(who.Lsd.UTC()) {
			log.Info().Msgf("Warehouse Order %q latest start date %v is overdue, prioritize its assignment", who.Who, who.Lsd.Local())
			warehouseOrdersOverdue = append(warehouseOrdersOverdue, who)
		}
	}

	// Sort warehouse orders by Lsd
	sort.SliceStable(warehouseOrdersOverdue, func(i, j int) bool {
		return warehouseOrdersOverdue[i].Lsd.UTC().Before(warehouseOrdersOverdue[j].Lsd.UTC())
	})

	// First assignments: overdue warehouse orders
	for _, who := range warehouseOrdersOverdue {
		for _, bidding := range biddings {
			// Skip bidding if warehouse order or robot are already assigned
			if warehouseOrdersAssigned[who.Who] || robotsAssigned[bidding.robot] {
				continue
			}
			if who.Who == bidding.bidding.Who && who.Lgnum == bidding.bidding.Lgnum {
				log.Info().Msgf("Assigning warehouse order \"%s.%s\" to Rsrc %q. Lsd overdue. The bidding was %v", bidding.bidding.Lgnum,
					bidding.bidding.Who, strings.ToUpper(bidding.robot), bidding.bidding.Bidding)
				orderAssignment := ewm.OrderAssignment{
					Lgnum: bidding.bidding.Lgnum,
					Who:   bidding.bidding.Who,
					Rsrc:  strings.ToUpper(bidding.robot),
				}
				orderAssignments = append(orderAssignments, orderAssignment)
				robotsAssigned[bidding.robot] = true
				warehouseOrdersAssigned[bidding.bidding.Who] = true
				// Assignment made, can continue with next warehouseOrdersOverdue
				break
			}
		}
		// If there is no bidding assign it to a random robot
		if !warehouseOrdersAssigned[who.Who] {
			for robot := range rs.isAvailable {
				if !robotsAssigned[robot] && robotsInAuction[robot] {
					log.Info().Msgf(
						"Assigning warehouse order \"%s.%s\" to Rsrc %q. Lsd overdue. No bidding, random robot selection.",
						who.Lgnum, who.Who, strings.ToUpper(robot))
					orderAssignment := ewm.OrderAssignment{
						Lgnum: who.Lgnum,
						Who:   who.Who,
						Rsrc:  strings.ToUpper(robot),
					}
					orderAssignments = append(orderAssignments, orderAssignment)
					robotsAssigned[robot] = true
					warehouseOrdersAssigned[who.Who] = true
					// Assignment made, can continue with next warehouseOrdersOverdue
					break
				}
			}
		}
	}

	// Second assignments: the remaining biddings
	for _, bidding := range biddings {
		// Assign bidding only if neither the warehouse order nor the robot are already assigned
		if !warehouseOrdersAssigned[bidding.bidding.Who] && !robotsAssigned[bidding.robot] {
			log.Info().Msgf("Assigning warehouse order \"%s.%s\" to Rsrc %q. The bidding was %v", bidding.bidding.Lgnum,
				bidding.bidding.Who, strings.ToUpper(bidding.robot), bidding.bidding.Bidding)
			orderAssignment := ewm.OrderAssignment{
				Lgnum: bidding.bidding.Lgnum,
				Who:   bidding.bidding.Who,
				Rsrc:  strings.ToUpper(bidding.robot),
			}
			orderAssignments = append(orderAssignments, orderAssignment)
			robotsAssigned[bidding.robot] = true
			warehouseOrdersAssigned[bidding.bidding.Who] = true
		}
	}

	return orderAssignments
}

func (r *reconcileAuctioneer) doCreateAuctions(ctx context.Context, a *ewm.Auctioneer, clAuc *classifiedAuctions, apr auctionsPerRobot, opr ordersPerRobot, rs *robotStates) {
	// Create OrderAuction CRs for auctions which only have a OrderReservation CR
	// Boundary conditions:
	//   - Each robot can only have one (running) OrderAuction which is not in state COMPLETED
	//   - maxOrdersPerRobot must be exceeded. Calculation "runningWarehouseOrders + runningAuctions"

	for _, auction := range clAuc.auctionsToCreate {
		for robot := range rs.isAvailable {
			if opr[robot] < a.Spec.Configuration.MaxOrdersPerRobot && apr[robot] == 0 {
				// Create OrderAuction CR
				oa := ewm.OrderAuction{
					ObjectMeta: metav1.ObjectMeta{
						Name:      fmt.Sprintf("%s-%s", auction.orderAuction, robot),
						Namespace: metav1.NamespaceDefault,
						Labels:    map[string]string{robotLabel: robot, orderAuctionLabel: auction.orderAuction},
					},
					Spec: ewm.OrderAuctionSpec{
						WarehouseOrders: auction.reservationCR.Status.WarehouseOrders,
						AuctionStatus:   ewm.OrderAuctionAuctionStatusOpen,
						ValidUntil:      metav1.Time{auction.reservationCR.Status.ValidUntil.Add(-timeBufferOrderReservation)},
					},
				}
				// Set Controller reference for CR
				controllerutil.SetControllerReference(&auction.reservationCR, &oa, r.scheme)

				// Create CR
				err := r.client.Create(ctx, &oa)
				if err != nil {
					log.Error().Err(err).Msgf("Error creating CRs for OrderAuction %q", auction.orderAuction)
				} else {
					log.Debug().Msgf("OrderAuction CR %q created", oa.GetName())
					auction.auctionCRs = append(auction.auctionCRs, oa)
					apr[robot]++
				}
			}
		}
		log.Info().Msgf("%v OrderAuction CRs created for order auction %q", len(auction.auctionCRs),
			auction.orderAuction)
	}
}

func (r *reconcileAuctioneer) doCreateReservations(ctx context.Context, a *ewm.Auctioneer, clAuc *classifiedAuctions, apr auctionsPerRobot, opr ordersPerRobot, rs *robotStates) {
	// Request more warehouse orders from order manager when one available robot is below its minimum number of warehouse orders

	for _, auction := range clAuc.waitForOrderManager {
		eq := auction.reservationCR.Spec.OrderRequest.Lgnum == a.Spec.Scope.Lgnum
		eq = eq && auction.reservationCR.Spec.OrderRequest.Rsrctype == a.Spec.Scope.Rsrctype
		eq = eq && auction.reservationCR.Spec.OrderRequest.Rsrcgrp == a.Spec.Scope.Rsrcgrp
		if eq {
			log.Debug().Msgf("There is already an open reservation %q in status %q awaiting response from order manager",
				auction.reservationCR.GetName(), auction.reservationCR.Status.Status)
			return
		}
	}

	var robotMightWork []string
	createReservations := false

	for robot := range rs.isAvailable {
		// First check if robot might request work, because is below maximum number of warehouse orders
		if opr[robot] < a.Spec.Configuration.MaxOrdersPerRobot && apr[robot] == 0 {
			robotMightWork = append(robotMightWork, robot)
			// Create OrderReservation only if at least one robot is below minimum number of warehouse orders
			if opr[robot] < a.Spec.Configuration.MinOrdersPerRobot {
				log.Info().Msgf("Only %v warehouse orders assigned to robot %q. This is below the minimum of %v. Starting a new order auction",
					opr[robot], robot, a.Spec.Configuration.MinOrdersPerRobot)
				createReservations = true
			}
		}
	}

	if createReservations {
		// Try to reserve more orders than robots, that there is space for optimization
		x := len(robotMightWork) * 3
		numberOfOrders := maxInt(x, a.Spec.Configuration.MinOrdersPerAuction)

		// Create OrderReservation CR
		orderAuctionName := fmt.Sprintf("%s.%v", a.Spec.Scope.Lgnum, time.Now().Unix())
		or := ewm.OrderReservation{
			ObjectMeta: metav1.ObjectMeta{
				Name:      orderAuctionName,
				Namespace: metav1.NamespaceDefault,
				Labels:    map[string]string{orderAuctionLabel: orderAuctionName},
			},
			Spec: ewm.OrderReservationSpec{
				OrderRequest: ewm.OrderRequest{
					Lgnum:    a.Spec.Scope.Lgnum,
					Rsrctype: a.Spec.Scope.Rsrctype,
					Rsrcgrp:  a.Spec.Scope.Rsrcgrp,
					Quantity: numberOfOrders,
				},
			},
		}
		// Set Controller reference for CR
		controllerutil.SetControllerReference(a, &or, r.scheme)

		err := r.client.Create(ctx, &or)
		if err != nil {
			log.Error().Err(err).Msgf("Error creating CR for OrderReservation %q", orderAuctionName)
		} else {
			log.Info().Msgf("Created CR for OrderReservation %q, requesting reservation for %v warehouse orders",
				orderAuctionName, numberOfOrders)
		}
	}
}

func (r *reconcileAuctioneer) doCleanupReservations(ctx context.Context, clAuc *classifiedAuctions) {
	// Sort reservations by creation time (descending)
	sort.SliceStable(clAuc.auctionsToComplete, func(i, j int) bool {
		return clAuc.auctionsToComplete[i].reservationCR.GetCreationTimestamp().UTC().After(clAuc.auctionsToComplete[j].reservationCR.GetCreationTimestamp().UTC())
	})

	// Keep a maximum of 50 OrderReservations. Corresponding OrderAuction CRs will be deleted by garbage collector based on OwnerReferences
	for i, auction := range clAuc.auctionsToComplete {
		if i > 49 {
			policy := metav1.DeletePropagationBackground
			err := r.client.Delete(ctx, &auction.reservationCR, &ctrlclient.DeleteOptions{PropagationPolicy: &policy})
			if err != nil {
				log.Error().Err(err).Msgf("Error cleaning up OrderReservation %q", auction.reservationCR.GetName())
			} else {
				log.Info().Msgf("Cleaned up OrderReservation %q", auction.reservationCR.GetName())
			}
		}
	}
}
