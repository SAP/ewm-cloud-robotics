// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package main

func minInt(args ...int) int {
	var min int
	for _, x := range args {
		if x < min {
			min = x
		}
	}
	return min
}

func maxInt(args ...int) int {
	var max int
	for _, x := range args {
		if x > max {
			max = x
		}
	}
	return max
}
