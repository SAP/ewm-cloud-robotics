// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package v2

// GetPathGuidesItem represents an item from result array of GET /path_guides endpoint
type GetPathGuidesItem struct {
	GUID string `json:"guid,omitempty"`
	Name string `json:"name,omitempty"`
	URL  string `json:"url,omitempty"`
}

// MirResponse identifies data type as MiR response
func (p *GetPathGuidesItem) MirResponse() {}

// GetPathGuides represents the result array of GET /path_guides endpoint
type GetPathGuides []GetPathGuidesItem

// MirResponse identifies data type as MiR response
func (p *GetPathGuides) MirResponse() {}

// GetPathGuidePosition represents the result of GET /path_guides/{path_guide_guid}/positions/{guid} endpoint
type GetPathGuidePosition struct {
	GUID          string `json:"guid,omitempty"`
	PathGuideGUID string `json:"path_guide_guid,omitempty"`
	PosGUID       string `json:"pos_guid,omitempty"`
	PosType       string `json:"pos_type,omitempty"`
	Priority      int    `json:"priority,omitempty"`
}

// MirResponse identifies data type as MiR response
func (p *GetPathGuidePosition) MirResponse() {}

// GetPathGuidePositionsItem represents an item from result array of GET /path_guides/{path_guide_guid}/positions endpoint
type GetPathGuidePositionsItem struct {
	GUID          string `json:"guid,omitempty"`
	PathGuideGUID string `json:"path_guide_guid,omitempty"`
	PosType       string `json:"pos_type,omitempty"`
	URL           string `json:"url,omitempty"`
}

// GetPathGuidePositions represents the result array of GET /path_guides/{path_guide_guid}/positions endpoint
type GetPathGuidePositions []GetPathGuidePositionsItem

// MirResponse identifies data type as MiR response
func (p *GetPathGuidePositions) MirResponse() {}

// PostPathGuides represents the request body of POST /path_guides endpoint
type PostPathGuides struct {
	// optional
	CreatedByID string `json:"created_by_id,omitempty"`
	// optional
	GUID  string `json:"guid,omitempty"`
	MapID string `json:"map_id"`
	Name  string `json:"name"`
}

// MirRequest identifies data type as MiR request
func (p *PostPathGuides) MirRequest() {}

// PostPathGuidesPositions represents the request body of POST /path_guides/{path_guide_guid}/positions endpoint
type PostPathGuidesPositions struct {
	// optional
	GUID          string `json:"guid,omitempty"`
	PathGuideGUID string `json:"path_guide_guid"`
	PosGUID       string `json:"pos_guid"`
	PosType       string `json:"pos_type"`
	// optional
	Priority int `json:"priority,omitempty"`
}

// MirRequest identifies data type as MiR request
func (p *PostPathGuidesPositions) MirRequest() {}
