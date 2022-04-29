// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
//

package v2

// GetPathGuidesPrecalc represents the result array of GET /path_guides_precalc endpoint
type GetPathGuidesPrecalc struct {
	Active        bool   `json:"active,omitempty"`
	FailCount     int    `json:"fail_count,omitempty"`
	Message       string `json:"message,omitempty"`
	PathGuideGUID string `json:"path_guide_guid,omitempty"`
	SuccessCount  int    `json:"success_count,omitempty"`
	TotalCount    int    `json:"total_count,omitempty"`
}

// MirResponse identifies data type as MiR response
func (p *GetPathGuidesPrecalc) MirResponse() {}

// PostPathGuidesPrecalc represents the request body of POST /path_guides_precalc endpoint
type PostPathGuidesPrecalc struct {
	// valid options: start, stop
	Command string `json:"command"`
	GUID    string `json:"guid"`
}

// MirRequest identifies data type as MiR request
func (p *PostPathGuidesPrecalc) MirRequest() {}
