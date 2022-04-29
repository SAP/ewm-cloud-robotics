// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
//

package v2

import (
	"fmt"

	apiv2 "github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface/apis/v2"
	"github.com/pkg/errors"
)

// GetMissionQueueIDActionID returns data from MiR GET /mission_queue/{mission_queue_id}/actions/{id} endpoint
func (c *Client) GetMissionQueueIDActionID(missionQueueID, actionID int) (*apiv2.GetMissionQueueAction, error) {

	endpoint := fmt.Sprintf("./mission_queue/%d/actions/%d", missionQueueID, actionID)

	respBody := &apiv2.GetMissionQueueAction{}
	mirError := &apiv2.Error{}

	resp, err := c.Get(endpoint, respBody, mirError)

	if err == nil && (resp.StatusCode <= 199 || resp.StatusCode >= 300) {
		if mirError != nil {
			err = errors.Wrapf(mirError, "GET %s returned status code %v", endpoint, resp.StatusCode)
		} else {
			err = errors.New(fmt.Sprintf("GET %s returned status code %v", endpoint, resp.StatusCode))
		}
	}

	return respBody, err
}

// GetMissionQueueIDActions returns data from MiR GET /mission_queue/{mission_queue_id}/actions endpoint
func (c *Client) GetMissionQueueIDActions(missionQueueID int) (*apiv2.GetMissionQueueActions, error) {

	endpoint := fmt.Sprintf("./mission_queue/%d/actions", missionQueueID)

	respBody := &apiv2.GetMissionQueueActions{}
	mirError := &apiv2.Error{}

	resp, err := c.Get(endpoint, respBody, mirError)

	if err == nil && (resp.StatusCode <= 199 || resp.StatusCode >= 300) {
		if mirError != nil {
			err = errors.Wrapf(mirError, "GET %s returned status code %v", endpoint, resp.StatusCode)
		} else {
			err = errors.New(fmt.Sprintf("GET %s returned status code %v", endpoint, resp.StatusCode))
		}
	}

	return respBody, err
}
