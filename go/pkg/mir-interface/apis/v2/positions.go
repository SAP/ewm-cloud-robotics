// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package v2

// GetPosition represents the result of GET /positions/{guid} endpoint
type GetPosition struct {
	CreatedBy      string  `json:"created_by,omitempty"`
	CreatedByID    string  `json:"created_by_id,omitempty"`
	DockingOffsets string  `json:"docking_offsets,omitempty"`
	GUID           string  `json:"guid,omitempty"`
	HelpPositions  string  `json:"help_positions,omitempty"`
	Map            string  `json:"map,omitempty"`
	MapID          string  `json:"map_id,omitempty"`
	Name           string  `json:"name,omitempty"`
	Orientation    float64 `json:"orientation,omitempty"`
	Parent         string  `json:"parent,omitempty"`
	ParentID       string  `json:"parent_id,omitempty"`
	PosX           float64 `json:"pos_x,omitempty"`
	PosY           float64 `json:"pos_y,omitempty"`
	Type           string  `json:"type,omitempty"`
	TypeID         int     `json:"type_id,omitempty"`
}

// MirResponse identifies data type as MiR response
func (p *GetPosition) MirResponse() {}

// GetPositionsItem represents an item from result array of GET /positions endpoint
type GetPositionsItem struct {
	GUID   string `json:"guid,omitempty"`
	Map    string `json:"map,omitempty"`
	Name   string `json:"name,omitempty"`
	TypeID int    `json:"type_id,omitempty"`
	URL    string `json:"url,omitempty"`
}

// GetPositions represents the result array of GET /positions endpoint
type GetPositions []GetPositionsItem

// MirResponse identifies data type as MiR response
func (p *GetPositions) MirResponse() {}
