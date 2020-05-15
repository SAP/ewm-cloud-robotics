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
	"context"
	"os"

	ewm "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	mis "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/mission/v1alpha1"
	"github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/kubernetes/scheme"
	"sigs.k8s.io/controller-runtime/pkg/client/config"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/manager/signals"
)

var log = zerologconfig.GetGlobalLogger()

func main() {
	// Get robot name for which the app is deployed
	robotName := os.Getenv("ROBCO_ROBOT_NAME")

	if robotName == "" {
		log.Fatal().Msg("No name in environment variable ROBCO_ROBOT_NAME")
	}

	log.Info().Msgf("Order-Bid-Agent app started on robot: %v", robotName)

	// Context
	ctx := context.Background()

	// Prepare new scheme for manager
	sc := runtime.NewScheme()
	scheme.AddToScheme(sc)
	ewm.AddToScheme(sc)
	mis.AddToScheme(sc)

	// Create new manager
	mgr, err := manager.New(config.GetConfigOrDie(), manager.Options{Scheme: sc})
	if err != nil {
		log.Fatal().Err(err).Msg("Unable to create controller manager")
	}

	// Add the bid-agent-controller
	log.Info().Msg("Setting up bid-agent-controller")
	err = addBidAgentController(ctx, mgr, robotName)
	if err != nil {
		log.Fatal().Err(err).Msg("Unable to add bid-agent-controller to manager")
	}

	// Start controller
	log.Info().Msg("Starting controller manager")
	err = mgr.Start(signals.SetupSignalHandler())
	if err != nil {
		log.Fatal().Err(err).Msg("Unable to start controller manager")
	} else {
		log.Info().Msg("Shutting down")
	}
}
