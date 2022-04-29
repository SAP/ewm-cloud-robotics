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

// GetMaps returns data from MiR GET /maps
func (c *Client) GetMaps() (*apiv2.GetMaps, error) {

	endpoint := "./maps"

	respBody := &apiv2.GetMaps{}
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

// GetMapsIDPositions returns data from MiR GET /maps/{map_id}/positions endpoint
func (c *Client) GetMapsIDPositions(mapID string) (*apiv2.GetPositions, error) {

	endpoint := fmt.Sprintf("./maps/%s/positions", mapID)

	respBody := &apiv2.GetPositions{}
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

// GetMapsIDPaths returns data from MiR GET /maps/{map_id}/paths endpoint
func (c *Client) GetMapsIDPaths(mapID string) (*apiv2.GetPaths, error) {

	endpoint := fmt.Sprintf("./maps/%s/paths", mapID)

	respBody := &apiv2.GetPaths{}
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
