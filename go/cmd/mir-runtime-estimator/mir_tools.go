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
	"fmt"
	mirclientv2 "github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface/client/v2"
	"strings"
)

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

	// If robot is idle(3), paused(4), docked(8), docking(9) or error(12), move base is idle
	if stateIDsMoveBaseIdle[status.StateID] {
		log.Debug().Msgf("Robot is state %q, move base is idle", status.StateText)
		return true
	}

	// If there is no running mission at all, move base is idling
	if status.MissionQueueID == 0 {
		log.Debug().Msg("No mission in queue, move base is idle")
		return true
	}

	// If missionQueueID or actionID are initial they are not
	if m.missionQueueID != status.MissionQueueID {
		log.Debug().Msg("Cached MissionQueue ID is different than the current one from MiR GET /status endpoint")

		// Refresh missionQueueID from result of GET /status endpoint
		m.missionQueueID = status.MissionQueueID
		m.actionID = 0

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
