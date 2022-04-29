// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
//

package main

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestNewRobotStates(t *testing.T) {
	rs := newRobotStates()
	assert.NotNil(t, rs.isInScope, "isInScope map must be initialized")
	assert.NotNil(t, rs.isAvailable, "isAvailable map must be initialized")
}
