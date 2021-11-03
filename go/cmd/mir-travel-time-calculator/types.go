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
	ewm "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	mirapisv2 "github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface/apis/v2"
	"k8s.io/apimachinery/pkg/watch"
)

type travelTimeCalculationEvent struct {
	eventType             watch.EventType
	travelTimeCalculation *ewm.TravelTimeCalculation
}

// Map positions to their MiR GUIDs and the other way round
type positionMaps struct {
	posToGUID map[string]string
	guidToPos map[string]string
}

// Lookup table for ewm.Path
type ewmPathLookup map[ewm.Path]bool

// newPathLookup returns a new lookup table for a slice of paths
func newPathLookup(paths []ewm.Path) ewmPathLookup {
	lookup := make(ewmPathLookup)
	for _, path := range paths {
		lookup[path] = true
	}
	return lookup
}

// newPathLookupForPosMaps return a new lookup table for an entire posMap
func newPathLookupForPosMaps(posMaps *positionMaps) ewmPathLookup {
	lookup := make(ewmPathLookup)
	for path1 := range posMaps.posToGUID {
		for path2 := range posMaps.posToGUID {
			if path1 == path2 {
				continue
			}
			ewmpath := ewm.Path{Start: path1, Goal: path2}
			lookup[ewmpath] = true
		}
	}
	return lookup
}

// Map ewm.Path to MiR Path
type ewmPathToMiR map[ewm.Path]mirapisv2.GetPath

type mirPaths struct {
	knownPaths   ewmPathToMiR
	unknownPaths ewmPathLookup
}

func newMirPaths() *mirPaths {
	mirPaths := &mirPaths{knownPaths: make(ewmPathToMiR), unknownPaths: make(ewmPathLookup)}
	return mirPaths
}

// Modes for MiR Fleet Management
type mirFleetConfigMode string

const (
	mirFleetConfigFleet mirFleetConfigMode = "FLEET"
	mirFleetConfigRobot mirFleetConfigMode = "ROBOT"
	mirFleetConfigNone  mirFleetConfigMode = ""
)
