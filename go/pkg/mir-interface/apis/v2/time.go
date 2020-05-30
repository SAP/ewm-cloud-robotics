// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package v2

import (
	"strings"
	"time"
)

// Time formats used in some MiR interfaces
const (
	ISO8601LocalTime = "2006-01-02T15:04:05"
	ISO8601          = "2006-01-02T15:04:05Z"
)

// Time is a custom MiR time format without time zone
type Time struct {
	time.Time
}

// UnmarshalJSON unmarshals MiR Time format
func (t *Time) UnmarshalJSON(data []byte) error {
	// Ignore null, like in the main JSON package.
	if string(data) == "null" || string(data) == `""` {
		return nil
	}

	// Trim ""
	str := strings.Trim(string(data), "\"")
	// Identify time format
	var format string
	if len(str) == len(ISO8601LocalTime) {
		format = ISO8601LocalTime
	} else if len(str) == len(ISO8601) {
		format = ISO8601
	} else {
		format = time.RFC3339
	}

	pt, err := time.Parse(format, str)
	if err != nil {
		return err
	}

	t.Time = pt.Local()

	return err
}
