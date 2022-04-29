// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
//

package main

import (
	"context"
	"math/rand"
	"sort"
	"time"

	ewm "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	mis "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/mission/v1alpha1"
	"github.com/pkg/errors"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/event"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/predicate"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"sigs.k8s.io/controller-runtime/pkg/source"
)

const (
	ownerReferencesUID        string        = "metadata.ownerReferences.uid"
	warehouseOrderOrderStatus string        = "spec.order_status"
	robotLabel                string        = "cloudrobotics.com/robot-name"
	orderAuctionLabel         string        = "ewm.sap.com/order-auction"
	timeBufferOrderAuction    time.Duration = time.Second * 20
)

// Reconcile controller for bid agent
type reconcileBidAgent struct {
	client    client.Client
	scheme    *runtime.Scheme
	robotName string
	namespace string
}

// Implement reconcile.Reconciler so the controller can reconcile objects
var _ reconcile.Reconciler = &reconcileBidAgent{}

// fitsRobotLabelPredicate implements a default update predicate function on cloud robotics robot labels
type fitsRobotLabelPredicate struct {
	predicate.Funcs
	robotName string
}

func (f fitsRobotLabelPredicate) Create(e event.CreateEvent) bool {
	match := e.Object.GetLabels()[robotLabel] == f.robotName
	return match
}

func (f fitsRobotLabelPredicate) Update(e event.UpdateEvent) bool {
	match := e.ObjectNew.GetLabels()[robotLabel] == f.robotName
	return match
}

// Add a new instance of bid agent controller to a manager
func addBidAgentController(ctx context.Context, mgr manager.Manager, namespace, robotName string) error {

	// Create bid agent controller
	r := &reconcileBidAgent{client: mgr.GetClient(), scheme: mgr.GetScheme(), robotName: robotName, namespace: namespace}
	c, err := controller.New("bid-agent-controller", mgr, controller.Options{Reconciler: r})

	if err != nil {
		return errors.Wrap(err, "create controller")
	}

	// Cache for OwnerReferences.UID
	err = mgr.GetCache().IndexField(ctx, &ewm.TravelTimeCalculation{}, ownerReferencesUID, indexOwnerReferences)
	if err != nil {
		return errors.Wrap(err, "add IndexField TravelTimeCalculation")
	}
	// Cache for Warehouse Order Spec.OrderStatus
	err = mgr.GetCache().IndexField(ctx, &ewm.WarehouseOrder{}, warehouseOrderOrderStatus, indexWarehouseOrderOrderStatus)
	if err != nil {
		return errors.Wrap(err, "add IndexField WarehouseOrder")
	}

	// Watch OrderAuction CRs
	err = c.Watch(&source.Kind{Type: &ewm.OrderAuction{}}, &handler.EnqueueRequestForObject{},
		fitsRobotLabelPredicate{robotName: robotName})
	if err != nil {
		return errors.Wrap(err, "watch OrderAuction")
	}

	// Watch TravelTimeCalculation CRs
	err = c.Watch(&source.Kind{Type: &ewm.TravelTimeCalculation{}},
		&handler.EnqueueRequestForOwner{OwnerType: &ewm.OrderAuction{}, IsController: true})

	if err != nil {
		return errors.Wrap(err, "watch TravelTimeCalculation")
	}

	return err
}

// indexOwnerReferences indexes resources by the UIDs of their owner references.
func indexOwnerReferences(o client.Object) (refs []string) {
	switch obj := o.(type) {
	case *ewm.TravelTimeCalculation:
		for _, ref := range obj.OwnerReferences {
			refs = append(refs, string(ref.UID))
		}
	default:
		log.Panic().Msgf("Unknown type for indexOrderReferences %v", obj)
	}

	return refs
}

// indexWarehouseOrderOrderStatus indexes warehouse order CRs by their OrderStatus
func indexWarehouseOrderOrderStatus(o client.Object) (refs []string) {
	w, ok := o.(*ewm.WarehouseOrder)
	if !ok {
		log.Panic().Msgf("%v is not a WarehouseOrder CR", o)
	}
	refs = append(refs, string(w.Spec.OrderStatus))

	return refs
}

func (r *reconcileBidAgent) Reconcile(ctx context.Context, request reconcile.Request) (reconcile.Result, error) {

	log.Debug().Msgf("Starting reconcile for OrderAuction %+v", request.NamespacedName)

	// Get current version of OrderAuction CR
	var auction ewm.OrderAuction
	err := r.client.Get(ctx, request.NamespacedName, &auction)

	if k8serrors.IsNotFound(err) {
		// OrderAuction was already deleted, nothing to do.
		log.Debug().Msgf("Finished reconcile for OrderAuction %+v. OrderAuction was already deleted", request.NamespacedName)
		return reconcile.Result{}, nil
	} else if err != nil {
		log.Error().Err(err).Msgf("Error get OrderAuction %+v", request.NamespacedName)
		return reconcile.Result{}, errors.Wrapf(err, "get OrderAuction %+v", request.NamespacedName)
	}

	// There is nothing to do, if OrderAuction is not open anymore
	if auction.Spec.AuctionStatus != ewm.OrderAuctionAuctionStatusOpen {
		log.Debug().Msgf("Finished reconcile for OrderAuction %+v. AuctionStatus is not open", request.NamespacedName)
		return reconcile.Result{}, nil
	}

	// There is nothing to do, if bid was already sent
	if auction.Status.BidStatus == ewm.OrderAuctionBidStatusCompleted {
		log.Debug().Msgf("Finished reconcile for OrderAuction %+v. BidStatus is completed", request.NamespacedName)
		return reconcile.Result{}, nil
	}

	// Get TravelTimeCalculations for this OrderAuction
	var travelTimeCalculations ewm.TravelTimeCalculationList
	err = r.client.List(ctx, &travelTimeCalculations, client.MatchingFields{ownerReferencesUID: string(auction.UID)})
	if err != nil {
		log.Error().Err(err).Msg("Error get TravelTimeCalculations")
		return reconcile.Result{}, errors.Wrap(err, "get TravelTimeCalculations")
	}

	// If there is no TravelTimeCalculation request, create a new one
	if len(travelTimeCalculations.Items) == 0 {
		log.Info().Msgf("New OrderAuction %q with %v warehouse orders arrived", auction.GetName(), len(auction.Spec.WarehouseOrders))
		log.Info().Msgf("No TravelTimeCalculation CR for OrderAuction %q found, creating a new request", auction.GetName())
		err = r.requestTravelTimeCalculation(ctx, &auction)
		if err != nil {
			log.Error().Err(err).Msg("Error request TravelTimeCalculation")
			return reconcile.Result{}, errors.Wrap(err, "request TravelTimeCalculation")
		}

		// Reconcile latest some seconds before the auction closes
		requeueAfter := auction.Spec.ValidUntil.UTC().Sub(metav1.Now().UTC()) - timeBufferOrderAuction
		log.Debug().Msgf("Finished reconcile for OrderAuction %+v, requeue after %v", request.NamespacedName, requeueAfter)
		return reconcile.Result{RequeueAfter: requeueAfter}, nil
	}

	// Always try to close the bid some seconds before its validity ends
	closeBid := auction.Spec.ValidUntil.UTC().Before(metav1.Now().UTC().Add(-timeBufferOrderAuction))
	if closeBid {
		log.Info().Msgf("OrderAuction CR %q expires soon at %v, closing bid", auction.GetName(), auction.Spec.ValidUntil.Local())
	}
	// Collect run time estimations
	collectedEstimations := make(map[ewm.Path]float64)
	var startPosition string
	// There should be only one CR in this array
	for _, runT := range travelTimeCalculations.Items {
		if runT.Status.Status == ewm.TravelTimeCalculationStatusProcessed || closeBid {
			closeBid = true
			startPosition = runT.Spec.StartPosition
			for _, runTime := range runT.Status.RunTimes {
				path := ewm.Path{Start: runTime.Start, Goal: runTime.Goal}
				collectedEstimations[path] = runTime.Time
			}
		}
	}
	if closeBid {
		err = r.closeBid(ctx, &auction, startPosition, collectedEstimations)
		if err != nil {
			log.Error().Err(err).Msg("Error close bid")
			return reconcile.Result{}, errors.Wrap(err, "close bid")
		}
	}

	log.Debug().Msgf("Finished reconcile for OrderAuction %+v", request.NamespacedName)

	return reconcile.Result{}, nil
}

func (r *reconcileBidAgent) requestTravelTimeCalculation(ctx context.Context, auction *ewm.OrderAuction) error {
	// Estimate start position of the robot for this auction
	startPosition, err := r.estimateStartPosition(ctx)
	if err != nil {
		return errors.Wrap(err, "estimateStartPosition")
	}

	// Now request run times for every path from robot, which is:
	// - startPosition to source bin of first warehouse task from warehouse order
	// for each warehouse order in the auction
	// This approach optimizes warehouse order processing by reducing empty drives of the robots

	spec := ewm.TravelTimeCalculationSpec{StartPosition: startPosition}

	existingPaths := make(map[ewm.Path]bool)

	// Shuffle warehouse orders before determining paths that not all robots bid for the same orders
	// if there is not enough time for path calculation
	warehouseOrders := auction.Spec.WarehouseOrders
	rand.Seed(time.Now().UnixNano())
	rand.Shuffle(len(warehouseOrders), func(i, j int) { warehouseOrders[i], warehouseOrders[j] = warehouseOrders[j], warehouseOrders[i] })

	for _, w := range warehouseOrders {
		if len(w.Warehousetasks) > 0 {
			// Create potential path from startPosition to source bin of first warehouse task
			path := ewm.Path{Start: startPosition, Goal: w.Warehousetasks[0].Vlpla}
			// Append to spec if not appended yet
			if !existingPaths[path] {
				spec.Paths = append(spec.Paths, path)
				existingPaths[path] = true
			}
		}
	}

	// Bid agent closes bid some seconds before auction ends, so give it 10 seconds buffer time
	spec.ValidUntil = metav1.NewTime(auction.Spec.ValidUntil.UTC().Add(-(timeBufferOrderAuction + time.Second*10)))

	if len(spec.Paths) == 0 {
		log.Info().Msgf("No valid paths identified for OrderAuction %q", auction.GetName())
		return nil
	}

	// Create TravelTimeCalculation CR
	runT := ewm.TravelTimeCalculation{
		ObjectMeta: metav1.ObjectMeta{
			Name:      auction.GetName(),
			Namespace: r.namespace,
			Labels:    map[string]string{robotLabel: r.robotName, orderAuctionLabel: auction.GetLabels()[orderAuctionLabel]},
		},
		Spec: spec,
	}
	// Set Controller reference for CR
	controllerutil.SetControllerReference(auction, &runT, r.scheme)

	// Create CR
	err = r.client.Create(ctx, &runT)
	if err != nil {
		return errors.Wrap(err, "create TravelTimeCalculation")
	}

	// Update bid status
	newAuction := auction.DeepCopy()
	newAuction.Status.BidStatus = ewm.OrderAuctionBidStatusRunning
	err = r.client.Status().Patch(ctx, newAuction, client.MergeFrom(auction))
	if err != nil {
		return errors.Wrap(err, "update OrderAuctionStatus")
	}

	return nil
}

func (r *reconcileBidAgent) estimateStartPosition(ctx context.Context) (string, error) {
	var position string

	// If warehouse orders are in process, estimated start position is the destination of the last warehouse task
	var warehouseOrders ewm.WarehouseOrderList
	err := r.client.List(
		ctx, &warehouseOrders, client.MatchingLabels{robotLabel: r.robotName},
		client.MatchingFields{warehouseOrderOrderStatus: string(ewm.WarehouseOrderOrderStatusRunning)})
	if err != nil {
		return "", errors.Wrap(err, "get WarehouseOrders")
	}

	if len(warehouseOrders.Items) > 0 {
		// Sort warehouse orders by sequence (descending)
		sort.SliceStable(warehouseOrders.Items, func(i, j int) bool {
			return warehouseOrders.Items[i].Spec.Sequence > warehouseOrders.Items[j].Spec.Sequence
		})

		// Estimated position is the destination of the last warehouse task in the first warehouse order
		i := len(warehouseOrders.Items[0].Spec.Data.Warehousetasks) - 1
		position = warehouseOrders.Items[0].Spec.Data.Warehousetasks[i].Nlpla

		if position != "" {
			log.Info().Msgf("Found estimated start position %q in warehouse order %q", position, warehouseOrders.Items[0].GetName())
			return position, nil
		}
	}

	// If no position found yet, estimated start position is the target of the latest mission which is running or succeded
	var missions mis.MissionList
	err = r.client.List(ctx, &missions, client.MatchingLabels{robotLabel: r.robotName})
	if err != nil {
		return "", errors.Wrap(err, "get Missions")
	}

	if len(missions.Items) > 0 {
		// Sort missions by creation time (descending)
		sort.SliceStable(missions.Items, func(i, j int) bool {
			return missions.Items[i].GetCreationTimestamp().UTC().After(missions.Items[j].GetCreationTimestamp().UTC())
		})

		for _, mission := range missions.Items {
			missionValid := mission.Status.Status == mis.MissionStatusAccepted
			missionValid = missionValid || mission.Status.Status == mis.MissionStatusRunning
			missionValid = missionValid || mission.Status.Status == mis.MissionStatusSucceeded
			if missionValid && len(mission.Spec.Actions) > 0 {
				i := len(mission.Spec.Actions) - 1
				switch action := mission.Spec.Actions[i].(type) {
				case *mis.ChargeAction:
					position = action.Charge.ChargerName
				case *mis.MoveToNamedPositionAction:
					position = action.MoveToNamedPosition.TargetName
				case *mis.GetTrolleyAction:
					position = action.GetTrolley.DockName
				case *mis.ReturnTrolleyAction:
					position = action.ReturnTrolley.DockName
				default:
					log.Panic().Msgf("Action %v of mission %q is of unknown type", action, mission.GetName())
				}
				log.Info().Msgf("Found estimated start position %q in mission %q", position, mission.GetName())
				break
			}
		}
	}

	return position, nil
}

func (r *reconcileBidAgent) closeBid(ctx context.Context, auction *ewm.OrderAuction, startPosition string,
	travelTimeCalculations map[ewm.Path]float64) error {

	log.Info().Msgf("Starting to close bid process for OrderAuction CR %q", auction.GetName())
	var bidResults []ewm.WarehouseOrderBidding

	// Calculate bid results for each warehouse order in auction
	for _, w := range auction.Spec.WarehouseOrders {
		if len(w.Warehousetasks) > 0 {
			var bidding float64
			createBid := true
			// Create potential path from startPosition to source bin of first warehouse task
			path := ewm.Path{Start: startPosition, Goal: w.Warehousetasks[0].Vlpla}

			// Create bidding from runtime. If path is not found do not create a bid for this warehouse order
			if value, existing := travelTimeCalculations[path]; existing {
				log.Debug().Msgf("Path %+v of warehouse order %s.%s found with bidding %v", path, w.Lgnum, w.Who, value)
				bidding = value
			} else if path.Start == path.Goal {
				log.Debug().Msgf("Path %+v of warehouse order %s.%s not found, but start and goal are the same. Bidding set to 1",
					path, w.Lgnum, w.Who)
				bidding = 1
			} else {
				log.Debug().Msgf("Path %+v of warehouse order %s.%s not found", path, w.Lgnum, w.Who)
				createBid = false
			}
			if createBid {
				wBidding := ewm.WarehouseOrderBidding{Lgnum: w.Lgnum, Who: w.Who, Bidding: bidding}
				bidResults = append(bidResults, wBidding)
			}
		}
	}

	// Update the OrderAuction status and close the bid process
	newAuction := auction.DeepCopy()
	newAuction.Status.Biddings = bidResults
	newAuction.Status.BidStatus = ewm.OrderAuctionBidStatusCompleted

	err := r.client.Status().Patch(ctx, newAuction, client.MergeFrom(auction))
	if err != nil {
		return errors.Wrap(err, "update OrderAuctionStatus")
	}
	log.Info().Msgf("Bid process for OrderAuction CR %q completed with bids for %v warehouse orders",
		auction.GetName(), len(bidResults))

	return nil

}
