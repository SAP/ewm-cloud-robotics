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

// GetPathGuides returns data from MiR GET /path_guides endpoint
func (c *Client) GetPathGuides() (*apiv2.GetPathGuides, error) {

	endpoint := "./path_guides"

	respBody := &apiv2.GetPathGuides{}
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

// GetPathGuidesGUIDPositions returns data from MiR GET /path_guides/{path_guide_guid}/positions endpoint
func (c *Client) GetPathGuidesGUIDPositions(guid string) (*apiv2.GetPathGuidePositions, error) {

	endpoint := fmt.Sprintf("./path_guides/%s/positions", guid)

	respBody := &apiv2.GetPathGuidePositions{}
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

// GetPathGuidesGUIDPositionsGUID returns data from MiR GET /path_guides/{path_guide_guid}/positions/{guid} endpoint
func (c *Client) GetPathGuidesGUIDPositionsGUID(pathGuideGUID, positionGUID string) (*apiv2.GetPathGuidePosition, error) {

	endpoint := fmt.Sprintf("./path_guides/%s/positions/%s", pathGuideGUID, positionGUID)

	respBody := &apiv2.GetPathGuidePosition{}
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

// PostPathGuides returns data from MiR POST /path_guides endpoint
func (c *Client) PostPathGuides(reqBody *apiv2.PostPathGuides) (*apiv2.GetPathGuidesItem, error) {

	endpoint := "./path_guides"

	respBody := &apiv2.GetPathGuidesItem{}
	mirError := &apiv2.Error{}

	resp, err := c.Post(endpoint, reqBody, respBody, mirError)

	if err == nil && (resp.StatusCode <= 199 || resp.StatusCode >= 300) {
		if mirError != nil {
			err = errors.Wrapf(mirError, "POST %s returned status code %v", endpoint, resp.StatusCode)
		} else {
			err = errors.New(fmt.Sprintf("POST %s returned status code %v", endpoint, resp.StatusCode))
		}
	}

	return respBody, err
}

// DeletePathGuidesGUID returns data from MiR DELETE /path_guides/{guid} endpoint
func (c *Client) DeletePathGuidesGUID(guid string) error {

	endpoint := fmt.Sprintf("./path_guides/%s", guid)

	mirError := &apiv2.Error{}

	resp, err := c.Delete(endpoint, mirError)

	if err == nil && (resp.StatusCode <= 199 || resp.StatusCode >= 300) {
		if mirError != nil {
			err = errors.Wrapf(mirError, "DELETE %s returned status code %v", endpoint, resp.StatusCode)
		} else {
			err = errors.New(fmt.Sprintf("DELETE %s returned status code %v", endpoint, resp.StatusCode))
		}
	}

	return err
}

// PostPathGuidesPositions returns data from MiR POST /path_guides endpoint
func (c *Client) PostPathGuidesPositions(pathGuideGUID string, reqBody *apiv2.PostPathGuidesPositions) (*apiv2.GetPathGuidePosition, error) {

	endpoint := fmt.Sprintf("./path_guides/%s/positions", pathGuideGUID)

	respBody := &apiv2.GetPathGuidePosition{}
	mirError := &apiv2.Error{}

	resp, err := c.Post(endpoint, reqBody, respBody, mirError)

	if err == nil && (resp.StatusCode <= 199 || resp.StatusCode >= 300) {
		if mirError != nil {
			err = errors.Wrapf(mirError, "POST %s returned status code %v", endpoint, resp.StatusCode)
		} else {
			err = errors.New(fmt.Sprintf("POST %s returned status code %v", endpoint, resp.StatusCode))
		}
	}

	return respBody, err
}
