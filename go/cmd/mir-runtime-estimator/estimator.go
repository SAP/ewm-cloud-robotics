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
	crPathGuidesName string = "zz-cloudrobotics-path-guide"
)

type mirEstimator struct {
	robotName          string
	mirClient          *mirclientv2.Client
	clientset          *crclient.Clientset
	eventChan          <-chan runtimeEstimationEvent
	moveBaseChecker    *mirMoveBaseChecker
	preservePathGuides bool
	ewmPathQueue       ewmPathLookup
}

// Lookup table with position type IDs which can be added to path guides
var posTypeIDForPathGuides = map[int]bool{
	0: true, 1: true, 5: true, 8: true, 10: true, 12: true, 14: true, 15: true, 19: true, 21: true, 22: true, 23: true, 42: true,
}

// newMirEstimator returns a new instance of mirEstimator
func newMirEstimator(robotName string, mirClient *mirclientv2.Client, clientset *crclient.Clientset, eventChan <-chan runtimeEstimationEvent) *mirEstimator {

	estimator := &mirEstimator{robotName: robotName, mirClient: mirClient, clientset: clientset, eventChan: eventChan, preservePathGuides: false}
	estimator.moveBaseChecker = newMirMoveBaseChecker(mirClient)
	estimator.ewmPathQueue = make(ewmPathLookup)
	return estimator
}

// Set flag if path guides created on MiR robot should be preserved for debugging
func (m *mirEstimator) setPreservePathGuides(p bool) *mirEstimator {
	m.preservePathGuides = p
	return m
}

// Run the estimator until done channel closes
func (m *mirEstimator) run(done <-chan struct{}, precalcPathsWhenIdle bool) {
	// Main loop
	log.Info().Msg("Starting MiR estimator")

	precalcPathWhenIdleChan := make(chan struct{})
	if precalcPathsWhenIdle {
		log.Info().Msg("Path precalculation when robot is charging or idle is enabled")
		go func() { precalcPathWhenIdleChan <- struct{}{} }()
	}

	for running := true; running == true; {
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
				if e.eventType == watch.Added && e.runtimeEstimation.Status.Status != ewm.RunTimeEstimationStatusProcessed {
					m.processCRAdded(e.runtimeEstimation)
				}
			case <-precalcPathWhenIdleChan:
				m.precalcPathsWhenIdle(precalcPathWhenIdleChan)
			}
		}
	}
	log.Info().Msg("MiR estimator stopped")
}

func (m *mirEstimator) processCRAdded(rte *ewm.RunTimeEstimation) {
	// Prepare context and CR interface
	ctx := context.Background()
	crInterface := m.clientset.EwmV1alpha1().RunTimeEstimations(rte.GetNamespace())

	log.Info().Msgf("Start runtime estimation for CR %q", rte.GetName())

	var err error

	// Set status RUNNING if not done yet
	if rte.Status.Status == "" {
		rte.Status.Status = ewm.RunTimeEstimationStatusRunning
		rte, err = crInterface.UpdateStatus(ctx, rte, metav1.UpdateOptions{})
		if err != nil {
			log.Error().Err(err).Msgf("Updating status of RunTimeEstimation %q failed", rte.GetName())
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
	reqEwmPaths := newPathLookup(rte.Spec.Paths)
	mirPaths, err := m.collectMirPaths(mirStatus.MapID, posMaps, reqEwmPaths)
	if err != nil {
		log.Error().Err(err).Msgf("Error getting paths from active map on robot %q", m.robotName)
		return
	}

	// In case there are unknown paths
	if len(mirPaths.unknownPaths) > 0 {
		// Update status of RunTimeEstimation with preliminary results, because precalculation could take a while
		m.updateCRWithResult(rte, mirPaths)
		rte, err = crInterface.UpdateStatus(ctx, rte, metav1.UpdateOptions{})
		if err != nil {
			log.Error().Err(err).Msgf("Updating status with preliminary results of RunTimeEstimation %q failed", rte.GetName())
		}

		// Precalculate paths which are unknown
		m.precalculatePaths(mirStatus.MapID, posMaps, mirPaths.unknownPaths, metav1.Time{rte.Spec.ValidUntil.Add(time.Second * -10)})

		// Collect precalculated paths
		mirPathsPrec, err := m.collectMirPaths(mirStatus.MapID, posMaps, mirPaths.unknownPaths)
		if err != nil {
			log.Error().Err(err).Msgf("Error getting paths from active map on robot %q", m.robotName)
			return
		}

		// Aggregate both maps
		for k, v := range mirPathsPrec.validPaths {
			mirPaths.validPaths[k] = v
		}
		mirPaths.unknownPaths = mirPathsPrec.unknownPaths
	}

	// Update status of RunTimeEstimation
	m.updateCRWithResult(rte, mirPaths)
	rte.Status.Status = ewm.RunTimeEstimationStatusProcessed
	rte, err = crInterface.UpdateStatus(ctx, rte, metav1.UpdateOptions{})
	if err != nil {
		log.Error().Err(err).Msgf("Updating status with results of RunTimeEstimation %q failed", rte.GetName())
	}

	log.Info().Msgf("Finished runtime estimation for CR %q", rte.GetName())

}

func (m *mirEstimator) getPosMaps(mapID string) (*posMaps, error) {
	posMaps := &posMaps{
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

func (m *mirEstimator) collectMirPaths(mapID string, posMaps *posMaps, reqEwmPaths ewmPathLookup) (*mirPaths, error) {

	mirPaths := newMirPaths()

	// Get all paths for the active map from MiR API
	paths, err := m.mirClient.GetMapsIDPaths(mapID)
	if err != nil {
		return nil, errors.Wrap(err, "Get paths for mapID")
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
			// Save valid path and remove it from requested paths
			if path.Valid {
				log.Debug().Msgf("Path %+v found in cache", ewmPath)
				mirPaths.validPaths[ewmPath] = *path
				delete(reqEwmPaths, ewmPath)
				// Remove path from queue too to prevent that it is calculated again when robot is charging or idling
				delete(m.ewmPathQueue, ewmPath)
			} else {
				log.Info().Msgf("Path %+v found but in status invalid", ewmPath)
			}
		}
	}

	// The remaining paths are unknown and need to be created
	mirPaths.unknownPaths = reqEwmPaths

	log.Info().Msgf("Found %v valid paths in MiR path cache. %v paths are not known yet", len(mirPaths.validPaths), len(mirPaths.unknownPaths))

	return mirPaths, nil

}

func (m *mirEstimator) precalculatePaths(mapID string, posMaps *posMaps, unknownPaths ewmPathLookup, stopAt metav1.Time) {

	// precalculation does not work when the robot is moving

	// Create a new path guide on MiR robot for each missing path
	log.Info().Msgf("Start creating path guides for %v paths", len(unknownPaths))
	for ewmPath := range unknownPaths {
		if ewmPath.Start == ewmPath.Goal {
			log.Info().Msgf("Skip path %+v because start and goal positions are equal", ewmPath)
			continue
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
		pathGuide, err := prepareMirPathGuide(m.mirClient, mapID, posMaps.posToGUID[ewmPath.Start], posMaps.posToGUID[ewmPath.Goal])
		if err != nil {
			log.Error().Err(err).Msg("Creating PathGuide")
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
					log.Info().Msg("Running out of time, cannot wait for result of precalculation")
					break
				} else {
					time.Sleep(1 * time.Second)
				}
			}
			// Delete path from precalculation queue if it is listed
			delete(m.ewmPathQueue, ewmPath)
		}
	}

	// Cleanup automatically created path guides
	if !m.preservePathGuides {
		pathGuides, err := m.mirClient.GetPathGuides()
		if err != nil {
			log.Error().Err(err).Msg("Error getting path guides for cleanup, continue anyway")
			return
		}
		var i int
		for _, pathGuide := range *pathGuides {
			if pathGuide.Name == crPathGuidesName {
				err := m.mirClient.DeletePathGuidesGUID(pathGuide.GUID)
				if err != nil {
					log.Error().Err(err).Msg("Error cleaning up path guide, continue anyway")
				} else {
					i++
				}
			}
		}
		log.Info().Msgf("Cleaned up %v path guides", i)
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
			// Path found and valid
			if path.Valid {
				log.Debug().Msgf("Path found")
				return true
			}
			log.Info().Msg("Path found but in status invalid")
		}
	}
	return false
}

func (m *mirEstimator) updateCRWithResult(rte *ewm.RunTimeEstimation, mirPaths *mirPaths) {
	// Empty slice first
	rte.Status.RunTimes = nil
	// Append run times of all valid paths to CR status
	for _, ewmPath := range rte.Spec.Paths {
		if path, ok := mirPaths.validPaths[ewmPath]; ok {
			ewmRuntime := ewm.RunTime{Start: ewmPath.Start, Goal: ewmPath.Goal, Time: path.Time}
			rte.Status.RunTimes = append(rte.Status.RunTimes, ewmRuntime)
		}
	}
	log.Info().Msgf("Found results for %v of %v run time estimation requests", len(rte.Status.RunTimes), len(rte.Spec.Paths))
}

func (m *mirEstimator) precalcPathsWhenIdle(precalcPathWhenIdleChan chan<- struct{}) {

	// Send message to channel of main loop
	requeue := func(t time.Duration) {
		go func(t time.Duration) {
			time.Sleep(t)
			precalcPathWhenIdleChan <- struct{}{}
		}(t)
	}

	// Fill queue in background if empty
	if len(m.ewmPathQueue) == 0 {
		go func() {
			defer requeue(time.Second * 10)

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
