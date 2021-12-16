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
	"strings"
	"time"

	ewm "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	crclient "github.com/SAP/ewm-cloud-robotics/go/pkg/client/clientset/versioned"
	mirapisv2 "github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface/apis/v2"
	mirclientv2 "github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface/client/v2"
	"github.com/pkg/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/watch"
)

const (
	pathGuidePrefix string = "mir-travel-time-calculator"
)

type mirEstimator struct {
	robotName            string
	mirClient            *mirclientv2.Client
	clientset            *crclient.Clientset
	eventChan            <-chan travelTimeCalculationEvent
	moveBaseChecker      *mirMoveBaseChecker
	precalcPathsWhenIdle bool
	preservePathGuides   bool
	mirFleetConfigMode   mirFleetConfigMode
	ewmPathQueue         ewmPathLookup
}

// Lookup table with position type IDs which can be added to path guides
var posTypeIDForPathGuides = map[int]bool{
	0: true, 1: true, 5: true, 8: true, 10: true, 12: true, 14: true, 15: true, 19: true, 21: true, 22: true, 23: true, 42: true,
}

// newMirEstimator returns a new instance of mirEstimator
func newMirEstimator(robotName string, mirClient *mirclientv2.Client, clientset *crclient.Clientset, eventChan <-chan travelTimeCalculationEvent) *mirEstimator {

	estimator := &mirEstimator{
		robotName:            robotName,
		mirClient:            mirClient,
		clientset:            clientset,
		eventChan:            eventChan,
		precalcPathsWhenIdle: false,
		preservePathGuides:   false,
		mirFleetConfigMode:   mirFleetConfigNone}
	estimator.moveBaseChecker = newMirMoveBaseChecker(mirClient)
	estimator.ewmPathQueue = make(ewmPathLookup)
	return estimator
}

// Set flag if all path guides should be created on startup
func (m *mirEstimator) setMirFleetConfigMode(cfg mirFleetConfigMode) *mirEstimator {
	m.mirFleetConfigMode = cfg
	return m
}

// Set flag if a MiR Robot should precalculate path guides when its move base is idle
func (m *mirEstimator) setPrecalcPathsWhenIdle(p bool) *mirEstimator {
	m.precalcPathsWhenIdle = p
	return m
}

// Set flag if path guides created on MiR robot should be preserved for debugging
func (m *mirEstimator) setPreservePathGuides(p bool) *mirEstimator {
	m.preservePathGuides = p
	return m
}

// Run the estimator until done channel closes
func (m *mirEstimator) run(done <-chan struct{}) {
	// Main loop
	log.Info().Msg("Starting MiR estimator")

	precalcPathsChan := make(chan struct{})
	if m.precalcPathsWhenIdle {
		log.Info().Msg("Path precalculation when robot is charging or idle is enabled")
		go func() { precalcPathsChan <- struct{}{} }()
	} else if m.mirFleetConfigMode == mirFleetConfigFleet {
		log.Info().Msg("Path guide precalculation on MiR Fleet is enabled")
		go func() { precalcPathsChan <- struct{}{} }()
	}

	for running := true; running; {
		select {
		// Handle app close with higher priority
		case <-done:
			running = false
		default:
			select {
			case <-done:
				running = false
			case e := <-m.eventChan:
				// Handle events from CR event channel
				if e.eventType == watch.Added && e.travelTimeCalculation.Status.Status != ewm.TravelTimeCalculationStatusProcessed {
					m.processCRAdded(e.travelTimeCalculation)
				}
			case <-precalcPathsChan:
				m.precalcPaths(precalcPathsChan)
			}
		}
	}
	log.Info().Msg("MiR estimator stopped")
}

func (m *mirEstimator) processCRAdded(ttc *ewm.TravelTimeCalculation) {
	// Prepare context and CR interface
	ctx := context.Background()
	crInterface := m.clientset.EwmV1alpha1().TravelTimeCalculations(ttc.GetNamespace())

	log.Info().Msgf("Start travel time calculation for CR %q", ttc.GetName())

	var err error

	// Set status RUNNING if not done yet
	if ttc.Status.Status == "" {
		ttc.Status.Status = ewm.TravelTimeCalculationStatusRunning
		ttc, err = crInterface.UpdateStatus(ctx, ttc, metav1.UpdateOptions{})
		if err != nil {
			log.Error().Err(err).Msgf("Updating status of TravelTimeCalculation %q failed", ttc.GetName())
		}
	}

	// Get Map ID from MiR API
	mirStatus, err := m.mirClient.GetStatus()
	if err != nil {
		log.Error().Err(err).Msgf("Error getting status of robot %q", m.robotName)
		return
	}

	// Get GUIDs for all positions on active map
	posMaps, err := m.getPosMaps(mirStatus.MapID)
	if err != nil {
		log.Error().Err(err).Msgf("Error getting positions from active map on robot %q", m.robotName)
		return
	}

	// Collect paths from MiR
	reqEwmPaths := newPathLookup(ttc.Spec.Paths)
	mirPaths, err := m.collectMirPaths(mirStatus.MapID, posMaps, reqEwmPaths)
	if err != nil {
		log.Error().Err(err).Msgf("Error getting paths from active map on robot %q", m.robotName)
		return
	}

	// In case there are unknown paths
	if len(mirPaths.unknownPaths) > 0 {
		// Update status of TravelTimeCalculation with preliminary results, because precalculation could take a while
		m.updateCRWithResult(ttc, mirPaths)
		ttc, err = crInterface.UpdateStatus(ctx, ttc, metav1.UpdateOptions{})
		if err != nil {
			log.Error().Err(err).Msgf("Updating status with preliminary results of TravelTimeCalculation %q failed", ttc.GetName())
		}

		// Precalculate paths which are unknown
		m.precalculatePaths(mirStatus.MapID, posMaps, mirPaths.unknownPaths, metav1.Time{ttc.Spec.ValidUntil.Add(time.Second * -10)})

		// Collect precalculated paths
		mirPathsPrec, err := m.collectMirPaths(mirStatus.MapID, posMaps, mirPaths.unknownPaths)
		if err != nil {
			log.Error().Err(err).Msgf("Error getting paths from active map on robot %q", m.robotName)
			return
		}

		// Aggregate both maps
		for k, v := range mirPathsPrec.knownPaths {
			mirPaths.knownPaths[k] = v
		}
		mirPaths.unknownPaths = mirPathsPrec.unknownPaths
	}

	// Update status of TravelTimeCalculation
	m.updateCRWithResult(ttc, mirPaths)
	ttc.Status.Status = ewm.TravelTimeCalculationStatusProcessed
	ttc, err = crInterface.UpdateStatus(ctx, ttc, metav1.UpdateOptions{})
	if err != nil {
		log.Error().Err(err).Msgf("Updating status with results of TravelTimeCalculation %q failed", ttc.GetName())
	}

	log.Info().Msgf("Finished travel time calculation for CR %q", ttc.GetName())

}

func (m *mirEstimator) getPosMaps(mapID string) (*positionMaps, error) {
	posMaps := &positionMaps{
		posToGUID: make(map[string]string),
		guidToPos: make(map[string]string),
	}

	mirPositions, err := m.mirClient.GetMapsIDPositions(mapID)
	if err != nil {
		return nil, errors.Wrap(err, "get MiR positions")
	}

	for _, p := range *mirPositions {
		// Skip positions which cannot be used for precalculation
		if !posTypeIDForPathGuides[p.TypeID] {
			continue
		}
		// GUIDs are always unique
		posMaps.guidToPos[p.GUID] = p.Name
		// Same name might occure several times
		if _, found := posMaps.posToGUID[p.Name]; found {
			log.Warn().Msgf("There are multiple positions with name %q. Continue with the first occurance", p.Name)
		} else {
			posMaps.posToGUID[p.Name] = p.GUID
		}
	}

	log.Debug().Msgf("Found %v positions", len(posMaps.guidToPos))
	log.Debug().Msgf("Found %v unique positions", len(posMaps.posToGUID))

	return posMaps, nil
}

func (m *mirEstimator) collectMirPaths(mapID string, posMaps *positionMaps, reqEwmPaths ewmPathLookup) (*mirPaths, error) {

	mirPaths := newMirPaths()

	// Get all paths for the active map from MiR API
	paths, err := m.mirClient.GetMapsIDPaths(mapID)
	if err != nil {
		return nil, errors.Wrap(err, "Get paths for mapID")
	}

	// Remove paths where start and goal positions are equal, because those cannot be calculated by MiR
	for ewmPath := range reqEwmPaths {
		if ewmPath.Start == ewmPath.Goal {
			log.Info().Msgf("Path has same start and goal position %v. Not looking for this path", ewmPath.Start)
			delete(reqEwmPaths, ewmPath)
		}
	}

	// Check if paths are in needs to be checked for this estimation
	for _, p := range *paths {
		// Check if path is in lookup table
		ewmPath := ewm.Path{
			Start: posMaps.guidToPos[pathPosToPosGUID(p.StartPos)],
			Goal:  posMaps.guidToPos[pathPosToPosGUID(p.GoalPos)],
		}
		if reqEwmPaths[ewmPath] {
			// Check MiR API if path is valid
			path, err := m.mirClient.GetPathsGUID(p.GUID)
			if err != nil {
				log.Error().Err(err).Msgf("Getting path GUID %s failed", p.GUID)
				continue
			}
			// Save path and remove it from requested paths
			if path.Valid {
				log.Debug().Msgf("Path %+v found in cache", ewmPath)
				mirPaths.knownPaths[ewmPath] = *path
				delete(reqEwmPaths, ewmPath)
				// Remove path from queue too to prevent that it is calculated again when robot is charging or idling
				delete(m.ewmPathQueue, ewmPath)
			} else {
				log.Warn().Msgf("Path %+v found but in status invalid. Try to recalculate it", ewmPath)
			}
		}
	}

	// The remaining paths are unknown and need to be created
	mirPaths.unknownPaths = reqEwmPaths

	log.Info().Msgf("Found %v paths in MiR path cache. %v paths are not known yet", len(mirPaths.knownPaths), len(mirPaths.unknownPaths))

	return mirPaths, nil

}

func (m *mirEstimator) precalculatePaths(mapID string, posMaps *positionMaps, unknownPaths ewmPathLookup, stopAt metav1.Time) {

	// precalculation does not work when the robot is moving

	// Create a new path guide on MiR robot for each missing path
	log.Info().Msgf("Start creating path guides for %v paths", len(unknownPaths))
	for ewmPath := range unknownPaths {
		if ewmPath.Start == ewmPath.Goal {
			log.Info().Msgf("Skip path %+v because start and goal positions are equal", ewmPath)
			continue
		} else {
			log.Info().Msgf("Precalculate path %+v", ewmPath)
		}

		if !m.moveBaseChecker.isIdle() {
			log.Info().Msg("Wait until robot is able to precalculate paths")

			// Wait until move base is idle or we are running out out time
			for !stopAt.UTC().Before(time.Now().UTC()) {
				if m.moveBaseChecker.isIdle() {
					log.Info().Msgf("Move base of robot %s is idle, start precalculating paths", m.robotName)
					break
				}
				time.Sleep(500 * time.Millisecond)
			}
		}

		// Break the loop when calculation must be finished
		if stopAt.UTC().Before(time.Now().UTC()) {
			log.Info().Msg("Running out of time, precalculation must be stopped")
			break
		}

		// Prepare path guide for precalculation. This is a) an existing one for these start and goal positions or a new temporary one
		pathGuide, err := prepareMirPathGuide(
			m.mirClient, mapID, ewmPath.Start, ewmPath.Goal, posMaps, bool(m.mirFleetConfigMode != mirFleetConfigRobot), !m.preservePathGuides)
		if err != nil {
			if errors.Is(err, PathGuideNotFoundError) && m.mirFleetConfigMode == mirFleetConfigRobot {
				log.Warn().Msgf("Path guide for path from start position %s to goal position %s not found, waiting for MiR Fleet to create it", ewmPath.Start, ewmPath.Goal)
			} else {
				log.Error().Err(err).Msg("Creating PathGuide")
			}
			continue
		}

		// Start precalculation for path guide
		preCalc, err := m.mirClient.PostPathGuidesPrecalc(&mirapisv2.PostPathGuidesPrecalc{Command: "start", GUID: pathGuide.GUID})
		if err != nil {
			log.Error().Err(err).Msg("Starting precalculation of PathGuide")
			delete(m.ewmPathQueue, ewmPath)
		} else {
			if preCalc.PathGuideGUID == "" {
				log.Error().Msgf("Precalculation not started: %q", preCalc.Message)
				delete(m.ewmPathQueue, ewmPath)
				continue
			} else if preCalc.PathGuideGUID != pathGuide.GUID {
				log.Info().Msg("Precalculation not started, a different precalculation is in process")
				continue
			}

			log.Info().Msgf("Precalculation of path guide started. Current status: %v total / %v successfull / %v failed",
				preCalc.TotalCount, preCalc.SuccessCount, preCalc.FailCount)

			// Check status of precalulation and wait until it is finished
			for {
				// Existance of path must be checked because GET path_guides_precalc endpoint does not give a helpful response when the robot is moving
				pathFound := m.checkPathCreated(mapID, posMaps.posToGUID[ewmPath.Start], posMaps.posToGUID[ewmPath.Goal])

				// Break the loop when path was found
				if pathFound {
					log.Info().Msgf("Precalculation of path guide finished. Path %+v found", ewmPath)
					break
				} else if stopAt.UTC().Before(time.Now().UTC()) {
					// Break the loop when calculation must be finished
					log.Info().Msgf("Running out of time, cannot wait for result of precalculation of path %+v", ewmPath)
					break
				} else {
					time.Sleep(1 * time.Second)
				}
			}
			// Delete path from precalculation queue if it is listed
			delete(m.ewmPathQueue, ewmPath)

			// Cleanup automatically created path guides in some cases
			if m.mirFleetConfigMode != mirFleetConfigRobot && !m.preservePathGuides && strings.HasPrefix(pathGuide.Name, pathGuidePrefix) {
				err := m.mirClient.DeletePathGuidesGUID(pathGuide.GUID)
				if err != nil {
					log.Error().Err(err).Msg("Error cleaning up path guide, continue anyway")
				} else {
					log.Info().Msgf("Cleaned up path guide %s", pathGuide.GUID)
				}

			}
		}
	}
}

func (m *mirEstimator) checkPathCreated(mapID, startPosGUID, goalPosGUID string) bool {
	// Get all paths for the active map from MiR API
	paths, err := m.mirClient.GetMapsIDPaths(mapID)
	if err != nil {
		log.Error().Err(err).Msg("Get paths for mapID")
		return false
	}

	// Try to find the with its start and goal positions
	for _, p := range *paths {
		if p.StartPos == posGUIDToPathPos(startPosGUID) && p.GoalPos == posGUIDToPathPos(goalPosGUID) {
			// Check MiR API if path is valid
			path, err := m.mirClient.GetPathsGUID(p.GUID)
			if err != nil {
				log.Error().Err(err).Msgf("Getting path GUID %s failed", p.GUID)
				continue
			}
			// Path found
			// MiR robots mark very short paths often as invalid, thus they are used until there is a better solution
			if path.Valid {
				log.Debug().Msg("Path found")
			} else {
				log.Warn().Msg("Path found but in status invalid. Use it anyway and recalculate it the next time")
			}
			return true
		}
	}
	return false
}

func (m *mirEstimator) updateCRWithResult(ttc *ewm.TravelTimeCalculation, mirPaths *mirPaths) {
	// Empty slice first
	ttc.Status.RunTimes = nil
	// Append run times of all known paths to CR status
	for _, ewmPath := range ttc.Spec.Paths {
		if path, ok := mirPaths.knownPaths[ewmPath]; ok {
			ewmRuntime := ewm.RunTime{Start: ewmPath.Start, Goal: ewmPath.Goal, Time: path.Time}
			ttc.Status.RunTimes = append(ttc.Status.RunTimes, ewmRuntime)
		}
	}
	log.Info().Msgf("Found results for %v of %v run time estimation requests", len(ttc.Status.RunTimes), len(ttc.Spec.Paths))
}

func (m *mirEstimator) precalcPaths(precalcPathsChan chan<- struct{}) {

	// Send message to channel of main loop
	requeue := func(t time.Duration) {
		go func(t time.Duration) {
			time.Sleep(t)
			precalcPathsChan <- struct{}{}
		}(t)
	}

	if m.mirFleetConfigMode == mirFleetConfigFleet {

		defer requeue(time.Second * 30)
		// Get Maps from MiR API
		mirMaps, err := m.mirClient.GetMaps()
		if err != nil {
			log.Error().Err(err).Msg("Error getting maps from MiR Fleet")
			return
		}

		for _, mirMapsItem := range *mirMaps {
			// Get GUIDs for all positions on each map
			posMaps, err := m.getPosMaps(mirMapsItem.GUID)
			if err != nil {
				log.Error().Err(err).Msgf("Error getting positions from map %s on MiR Fleet", mirMapsItem.Name)
				return
			}

			// Collect existing paths from MiR
			ewmPaths := newPathLookupForPosMaps(posMaps)

			// Create path guide
			m.createPathGuides(ewmPaths, mirMapsItem.GUID, posMaps)
		}

	} else {

		// Fill queue in background if empty
		if len(m.ewmPathQueue) == 0 {
			go func() {
				defer requeue(time.Second * 120)

				// Get Map ID from MiR API
				mirStatus, err := m.mirClient.GetStatus()
				if err != nil {
					log.Error().Err(err).Msgf("Error getting status of robot %q", m.robotName)
					return
				}

				// Get GUIDs for all positions on active map
				posMaps, err := m.getPosMaps(mirStatus.MapID)
				if err != nil {
					log.Error().Err(err).Msgf("Error getting positions from active map on robot %q", m.robotName)
					return
				}

				// Collect existing paths from MiR
				ewmPaths := newPathLookupForPosMaps(posMaps)
				mirPaths, err := m.collectMirPaths(mirStatus.MapID, posMaps, ewmPaths)
				if err != nil {
					log.Error().Err(err).Msgf("Error getting paths from active map on robot %q", m.robotName)
					return
				}
				m.ewmPathQueue = mirPaths.unknownPaths
				log.Info().Msgf("Queue with %v paths for precalculation created on robot %q", len(m.ewmPathQueue), m.robotName)
			}()
			log.Info().Msg("No queue for path precalculation when robot is charging or idling. Create queue in background")
			return
		}

		// Run only when move base is idle
		if !m.moveBaseChecker.isIdle() {
			// Check again 10 seconds after finishing
			requeue(time.Second * 10)
			return
		}
		// and the robot is charging or does not run a mission
		if m.moveBaseChecker.actionType != "charging" && m.moveBaseChecker.missionQueueID != 0 {
			// Check again 10 seconds after finishing
			requeue(time.Second * 10)
			return
		}

		// Start precalculation of the first path and requeue when finished
		defer requeue(time.Millisecond * 500)

		if m.moveBaseChecker.actionType == "charging" {
			log.Info().Msg("Robot is charging, precalculate random paths meanwhile")
		} else {
			log.Info().Msg("Robot is idling, precalculate random paths meanwhile")
		}

		// Get GUIDs for all positions on active map
		posMaps, err := m.getPosMaps(m.moveBaseChecker.mapID)
		if err != nil {
			log.Error().Err(err).Msgf("Error getting positions from active map on robot %q", m.robotName)
			return
		}

		for k, v := range m.ewmPathQueue {
			calculatePath := ewmPathLookup{k: v}
			m.precalculatePaths(m.moveBaseChecker.mapID, posMaps, calculatePath, metav1.Time{time.Now().Add(5 * time.Minute)})
			// Go back to main loop after each precalculation
			break
		}
		log.Info().Msgf("%v paths are still in queue for precalculation", len(m.ewmPathQueue))
	}
}

func (m *mirEstimator) createPathGuides(pathsLookup ewmPathLookup, mapID string, posMaps *positionMaps) {
	log.Info().Msg("Creating path guides")
	for p := range pathsLookup {
		_, err := prepareMirPathGuide(m.mirClient, mapID, p.Start, p.Goal, posMaps, true, false)
		if err != nil {
			log.Error().Err(err).Msgf("Error creating path guide from start position %s to goal position %s", p.Start, p.Goal)
		}
	}
	log.Info().Msg("Creating path guides finished")
}
