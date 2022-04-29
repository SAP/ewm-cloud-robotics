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

// GetStatus returns data from MiR GET /status endpoint
func (c *Client) GetStatus() (*apiv2.GetStatus, error) {

	endpoint := "./status"

	respBody := &apiv2.GetStatus{}
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
