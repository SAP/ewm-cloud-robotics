// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package v2

// GetMapsItem represents an item from result array of GET /maps endpoint
type GetMapsItem struct {
	GUID string `json:"guid,omitempty"`
	Name string `json:"name,omitempty"`
	URL  string `json:"url,omitempty"`
}

// MirResponse identifies data type as MiR response
func (m *GetMapsItem) MirResponse() {}

// GetMaps represents the result array of GET /maps endpoint
type GetMaps []GetMapsItem

// MirResponse identifies data type as MiR response
func (m *GetMaps) MirResponse() {}
