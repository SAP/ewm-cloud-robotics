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
)

// Error represents the error response type of HTTP endpoints
type Error struct {
	ErrorCode  string `json:"error_code,omitempty"`
	ErrorHuman string `json:"error_human,omitempty"`
}

// MirError identifies data type as MiR error response
func (e *Error) MirError() {}

// Error implements error interface
func (e *Error) Error() string {
	return fmt.Sprintf("ErrorCode: %s, ErrorHuman: %s", e.ErrorCode, e.ErrorHuman)
}

// NewMirError provides a fresh error instance
func NewMirError(errorCode, errorHuman string) error {
	return &Error{ErrorCode: errorCode, ErrorHuman: errorHuman}
}
