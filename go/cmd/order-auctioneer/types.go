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
)

// Number of running warehouse orders / auctions per robot
type ordersPerRobot map[string]int
type auctionsPerRobot map[string]int

// An order auction consists of n OrderAuction CRs where n is the number of robots taking part
// and one OrderReservation CR which includes the warehouse order reserved for this auction
type auction struct {
	orderAuction  string
	reservationCR ewm.OrderReservation
	auctionCRs    []ewm.OrderAuction
}

// Auctions classified into categories how they are processed
type classifiedAuctions struct {
	auctionsToCreate    []auction
	auctionsToClose     []auction
	auctionsToComplete  []auction
	auctionsRunning     []auction
	waitForOrderManager []auction
	inconsistent        []auction
}

// Lookup if robot is in scope and available
type robotStates struct {
	isInScope   map[string]bool
	isAvailable map[string]bool
}

func newRobotStates() *robotStates {
	var rs robotStates
	rs.isInScope = make(map[string]bool)
	rs.isAvailable = make(map[string]bool)
	return &rs
}
