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

func TestMinInt(t *testing.T) {

	type testCase struct {
		name     string
		args     []int
		expected int
	}

	tests := []testCase{
		{
			name:     "minInt test 1",
			args:     []int{1, 3, 5},
			expected: 1,
		},
		{
			name:     "minInt test 2",
			args:     []int{1, 0, 5},
			expected: 0,
		},
		{
			name:     "minInt test 3",
			args:     []int{0, -1, -3},
			expected: -3,
		},
		{
			name:     "minInt test 4",
			args:     []int{-5, -1, -3},
			expected: -5,
		},
		{
			name:     "minInt test 5",
			args:     []int{},
			expected: 0,
		},
	}

	for _, test := range tests {
		t.Run(
			test.name,
			func(t *testing.T) {
				assert.Equal(t, test.expected, minInt(test.args...))
			})
	}

}

func TestMaxInt(t *testing.T) {

	type testCase struct {
		name     string
		args     []int
		expected int
	}

	tests := []testCase{
		{
			name:     "maxInt test 1",
			args:     []int{1, 3, 5},
			expected: 5,
		},
		{
			name:     "maxInt test 2",
			args:     []int{1, 0, 5},
			expected: 5,
		},
		{
			name:     "maxInt test 3",
			args:     []int{0, -1, -3},
			expected: 0,
		},
		{
			name:     "maxInt test 4",
			args:     []int{-5, -1, -3},
			expected: -1,
		},
		{
			name:     "maxInt test 5",
			args:     []int{},
			expected: 0,
		},
	}

	for _, test := range tests {
		t.Run(
			test.name,
			func(t *testing.T) {
				assert.Equal(t, test.expected, maxInt(test.args...))
			})
	}

}
