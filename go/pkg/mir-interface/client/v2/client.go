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
	"github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface/http"
	"github.com/pkg/errors"
)

// Client represents a HTTP REST client for MiR API 2.0.0 interface
type Client struct {
	*http.Client
}

// NewClient returns a new client for MiR HTTP API 2.0.0 interface
func NewClient(host, username, password, userAgent string, timeoutSec float64) (*Client, error) {
	http, err := http.NewClient(host, "/api/v2.0.0/", username, password, userAgent, timeoutSec)

	if err != nil {
		return nil, errors.Wrap(err, "NewClient")
	}

	return &Client{http}, nil
}
