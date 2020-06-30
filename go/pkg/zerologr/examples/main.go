// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package main

import (
	"os"

	"github.com/SAP/ewm-cloud-robotics/go/pkg/zerologr"
	"github.com/rs/zerolog"
)

// E is a demo error type
type E struct {
	str string
}

func (e E) Error() string {
	return e.str
}

func main() {
	zerologger := zerolog.New(os.Stderr).Level(zerolog.DebugLevel)
	log := zerologr.NewLogger(&zerologger)
	log = log.WithName("MyName").WithName("MySubDomainName").WithValues("user", "you")
	log.Info("hello", "val1", 1, "val2", map[string]int{"k": 1})
	log.V(1).Info("you should see this")
	log.V(2).Info("you should NOT see this")
	// for v0.2.0
	// log.V(1).V(1).Info("you should NOT see this")
	log.Error(nil, "uh oh", "trouble", true, "reasons", []float64{0.1, 0.11, 3.14})
	log.Error(E{"an error occurred"}, "goodbye", "code", -1)
}
