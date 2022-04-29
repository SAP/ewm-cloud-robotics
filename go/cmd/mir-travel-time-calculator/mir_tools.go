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
	"fmt"
	mirapisv2 "github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface/apis/v2"
	mirclientv2 "github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface/client/v2"
	"github.com/pkg/errors"
	"strings"
)

// Path guide was not found
var PathGuideNotFoundError = errors.New("Path guide not found")

// Action types move base is idle when executing them
var actionTypesMoveBaseIdle = map[string]bool{
	"charging":              true,
	"docking":               true,
	"pickup_cart":           true,
	"place_cart":            true,
	"pickup_shelf":          true,
	"place_shelf":           true,
	"wait_for_plc_register": true,
	"prompt_user":           true,
	"wait":                  true,
}

// If robot is idle(3), paused(4), docked(8), docking(9) or error(12), move base is idle
var stateIDsMoveBaseIdle = map[int]bool{
	3:  true,
	4:  true,
	8:  true,
	9:  true,
	12: true,
}

// posGUIDToPathPos converts position GUID from /positions endpoint to format used in start_pos, goal_pos of /paths endpoint
func posGUIDToPathPos(posGUID string) string {
	return fmt.Sprintf("/v2.0.0/positions/%s", posGUID)
}

// pathPosToPosGUID is the reverse operation of posGUIDToPathPos
func pathPosToPosGUID(pathPos string) string {
	return strings.TrimPrefix(pathPos, "/v2.0.0/positions/")
}

// mirMoveBaseChecker can check if move base on the MiR robot is currently idle, that it could be used for tasks like path guide precalculation
type mirMoveBaseChecker struct {
	mirClient      *mirclientv2.Client
	missionQueueID int
	actionID       int
	actionType     string
	stateID        int
	mapID          string
}

// newMirMoveBaseChecker return a new instance of mirMoveBaseChecker
func newMirMoveBaseChecker(mirClient *mirclientv2.Client) *mirMoveBaseChecker {
	m := &mirMoveBaseChecker{mirClient: mirClient}
	return m
}

// isIdle checks if move base is currently idle. This is the case when the robot is idling, charging and docking
func (m *mirMoveBaseChecker) isIdle() bool {

	status, err := m.mirClient.GetStatus()
	if err != nil {
		log.Error().Err(err).Msg("Error getting MiR status")
		return false
	}

	m.mapID = status.MapID
	m.stateID = status.StateID

	// If there is no running mission at all, move base is idling
	if status.MissionQueueID == 0 {
		log.Debug().Msg("No mission in queue, move base is idle")
		m.missionQueueID = 0
		m.actionID = 0
		m.actionType = ""
		return true
	}

	// If robot is idle(3), paused(4), docked(8), docking(9) or error(12), move base is idle
	if stateIDsMoveBaseIdle[status.StateID] {
		log.Debug().Msgf("Robot is state %q, move base is idle", status.StateText)
		return true
	}

	// If missionQueueID or actionID are initial they are not
	if m.missionQueueID != status.MissionQueueID {
		log.Debug().Msg("Cached MissionQueue ID is different than the current one from MiR GET /status endpoint")

		// Refresh missionQueueID from result of GET /status endpoint
		m.missionQueueID = status.MissionQueueID
		m.actionID = 0
		m.actionType = ""

		// If there is a mission running, check which action is active at the moment
		actions, err := m.mirClient.GetMissionQueueIDActions(m.missionQueueID)
		if err != nil {
			log.Error().Err(err).Msgf("Error getting MiR mission queue ID %v", m.missionQueueID)
			m.missionQueueID = 0
			return false
		}

		// Last action is the action in state "Executing"
		if len(*actions) == 0 {
			log.Debug().Msg("No actions in running mission, this should not happen. Reset missionQueueID and action")
			m.missionQueueID = 0
			return false
		}
		a := *actions
		m.actionID = a[len(a)-1].ID
	}

	// Check type and state of the actionID
	action, err := m.mirClient.GetMissionQueueIDActionID(m.missionQueueID, m.actionID)
	if err != nil {
		log.Error().Err(err).Msgf("Error getting MiR action ID %v of mission queue ID %v", m.actionID, m.missionQueueID)
		m.missionQueueID = 0
		m.actionID = 0
		return false
	}

	m.actionType = action.ActionType

	if action.State != "Executing" {
		log.Debug().Msgf("Action ID %v of mission queue ID %v is in state %v, starting all over again", m.actionID, m.missionQueueID, action.State)
		m.missionQueueID = 0
		m.actionID = 0
		return m.isIdle()
	}

	if actionTypesMoveBaseIdle[action.ActionType] {
		log.Debug().Msgf("Running Action ID %v of mission queue ID %v is of type %s, move base is idle", m.actionID, m.missionQueueID, action.ActionType)
		return true
	}

	return false
}

// checkExistingPathGuide checks if the path guide already exists. If a name is set, it filters by name before querying for Position GUIDs
func checkExistingPathGuide(m *mirclientv2.Client, name, startPosGUID, goalPosGUID string) (*mirapisv2.GetPathGuidesItem, error) {
	// Check for existing path guides with these positions
	pathGuides, err := m.GetPathGuides()
	if err != nil {
		return nil, errors.Wrap(err, "Get PathGuides")
	}

	// Check if existing path guides include start and goal positions
	for _, pathGuide := range *pathGuides {
		// If a name is set, filter by name first
		if name != "" && pathGuide.Name != name {
			continue
		}

		positions, err := m.GetPathGuidesGUIDPositions(pathGuide.GUID)
		if err != nil {
			log.Error().Err(err).Msg("Get PathGuidesGUIDPositions")
			continue
		}
		startPosFound := false
		goalPosFound := false
		for _, position := range *positions {
			if position.PosType == "start" && !startPosFound {
				p, err := m.GetPathGuidesGUIDPositionsGUID(pathGuide.GUID, position.GUID)
				if err != nil {
					log.Error().Err(err).Msg("Get PathGuidesGUIDPositionsGUID")
					continue
				}
				if p.PosGUID == startPosGUID {
					startPosFound = true
				}
			} else if position.PosType == "goal" && !goalPosFound {
				p, err := m.GetPathGuidesGUIDPositionsGUID(pathGuide.GUID, position.GUID)
				if err != nil {
					log.Error().Err(err).Msg("Get PathGuidesGUIDPositionsGUID")
					continue
				}
				if p.PosGUID == goalPosGUID {
					goalPosFound = true
				}
			}
		}
		// If start and goal positions are both found, return this path guide
		if startPosFound && goalPosFound {
			log.Debug().Msgf("Using existing path guide with name %s", pathGuide.Name)
			return &pathGuide, nil
		}
	}

	return nil, PathGuideNotFoundError
}

func prepareMirPathGuide(m *mirclientv2.Client, mapID string, ewmStart, ewmGoal string, posMaps *positionMaps, create, cleanup bool) (*mirapisv2.GetPathGuidesItem, error) {

	startPosGUID := posMaps.posToGUID[ewmStart]
	goalPosGUID := posMaps.posToGUID[ewmGoal]
	name := fmt.Sprintf("%s-%s-%s", pathGuidePrefix, ewmStart, ewmGoal)

	// Check for existing path guides by name
	pathGuide, err := checkExistingPathGuide(m, name, startPosGUID, goalPosGUID)
	if err == nil {
		return pathGuide, nil
	} else if errors.Is(err, PathGuideNotFoundError) {
		log.Debug().Msgf("Path guide from start %s to goal %s not found when searching for name", ewmStart, ewmGoal)
	} else {
		return nil, errors.Wrap(err, "Getting PathGuide by name")
	}

	if create {
		// Try to create new path guide before scanning all path guides for GUIDs. That would take too long.
		newPathGuide, err := m.PostPathGuides(&mirapisv2.PostPathGuides{MapID: mapID, Name: name})
		if err != nil {
			return nil, errors.Wrap(err, "Creating PathGuide")
		}

		// start pos
		startPos := &mirapisv2.PostPathGuidesPositions{
			PathGuideGUID: newPathGuide.GUID,
			PosGUID:       startPosGUID,
			PosType:       "start"}

		// goalPos
		goalPos := &mirapisv2.PostPathGuidesPositions{
			PathGuideGUID: newPathGuide.GUID,
			PosGUID:       goalPosGUID,
			PosType:       "goal"}

		_, err = m.PostPathGuidesPositions(newPathGuide.GUID, startPos)
		if err != nil {
			return nil, errors.Wrap(err, "Posting start position to PathGuide")
		}

		var returnDelete error
		var mirError *mirapisv2.Error
		_, err = m.PostPathGuidesPositions(newPathGuide.GUID, goalPos)
		if err == nil {
			log.Debug().Msgf("Using new temporary path guide %s", newPathGuide.Name)
			return newPathGuide, nil
		} else if errors.As(err, &mirError) {
			log.Debug().Msgf("There is already a path guide for start position %s to goal position %s. Start searching for that", ewmStart, ewmGoal)
			if cleanup {
				err := m.DeletePathGuidesGUID(newPathGuide.GUID)
				if err != nil {
					log.Error().Err(err).Msgf("Error deleting not needed path guide for start position %s to goal position %s. Continue anyway", ewmStart, ewmGoal)
				}
			}
		} else {
			returnDelete = err
		}

		if returnDelete != nil {
			if cleanup {
				err := m.DeletePathGuidesGUID(newPathGuide.GUID)
				if err != nil {
					log.Error().Err(err).Msgf("Error deleting not needed path guide for start position %s to goal position %s. Continue anyway", ewmStart, ewmGoal)
				}
			}
			return nil, errors.Wrap(returnDelete, "Posting goal position to PathGuide")
		}

	}

	// Search for existing path guides by GUID
	pathGuide, err = checkExistingPathGuide(m, "", startPosGUID, goalPosGUID)
	if errors.Is(err, PathGuideNotFoundError) {
		log.Debug().Msgf("Path guide from start %s to goal %s not found when searching for GUID", ewmStart, ewmGoal)
		return nil, err
	} else if err != nil {
		return nil, errors.Wrap(err, "Searching PathGuide by GUID")
	}

	return pathGuide, nil

}
