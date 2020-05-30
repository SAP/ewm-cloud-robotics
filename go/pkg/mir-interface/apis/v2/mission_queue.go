// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package v2

// GetMissionQueueActionsItem represents an item from result array of GET /mission_queue/{mission_queue_id}/actions endpoint
type GetMissionQueueActionsItem struct {
	ID  int    `json:"id,omitempty"`
	URL string `json:"url,omitempty"`
}

// GetMissionQueueActions represents the result array of GET /mission_queue/{mission_queue_id}/actions endpoint
type GetMissionQueueActions []GetMissionQueueActionsItem

// MirResponse identifies data type as MiR response
func (p *GetMissionQueueActions) MirResponse() {}

// GetMissionQueueAction represents the result of GET /mission_queue/{mission_queue_id}/actions/{id} endpoint
type GetMissionQueueAction struct {
	ActionID       string                 `json:"action_id,omitempty"`
	ActionType     string                 `json:"action_type,omitempty"`
	Finished       Time                   `json:"finished,omitempty"`
	ID             int                    `json:"id,omitempty"`
	Message        string                 `json:"message,omitempty"`
	MissionQueueID int                    `json:"mission_queue_id,omitempty"`
	Parameters     map[string]interface{} `json:"parameters"`
	Started        Time                   `json:"started,omitempty"`
	State          string                 `json:"state,omitempty"`
	URL            string                 `json:"url,omitempty"`
}

// MirResponse identifies data type as MiR response
func (p *GetMissionQueueAction) MirResponse() {}
