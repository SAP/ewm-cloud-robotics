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
	"strings"

	ewm "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	"github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig"
	"github.com/SAP/ewm-cloud-robotics/go/pkg/zerologr"
	registry "github.com/googlecloudrobotics/core/src/go/pkg/apis/registry/v1alpha1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/kubernetes/scheme"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client/config"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/manager/signals"
	"sigs.k8s.io/controller-runtime/pkg/webhook"
)

const (
	webhookPort = 9876
	certDir     = "/tls"
)

var log = zerologconfig.GetGlobalLogger()

func main() {
	// Get robot names for which the order-auction app was deployed
	deployedRobotsStr := os.Getenv("DEPLOYED_ROBOTS")
	deployedRobotsStr = strings.ReplaceAll(deployedRobotsStr, " ", "")
	deployedRobotsList := strings.Split(deployedRobotsStr, ",")
	deployedRobots := make(map[string]bool)
	for _, r := range deployedRobotsList {
		if r != "" {
			deployedRobots[r] = true
		}
	}
	log.Info().Msgf("Order-Auction app is deployed for these robots: %v", deployedRobotsList)

	// Context
	ctx := context.Background()

	// Prepare new scheme for manager
	sc := runtime.NewScheme()
	scheme.AddToScheme(sc)
	ewm.AddToScheme(sc)
	registry.AddToScheme(sc)

	// Create new manager
	ctrl.SetLogger(zerologr.NewLogger(log))
	mgr, err := manager.New(config.GetConfigOrDie(), manager.Options{Scheme: sc, Port: webhookPort})
	if err != nil {
		log.Fatal().Err(err).Msg("Unable to create controller manager")
	}

	// Add the auctioneer-controller
	log.Info().Msg("Setting up auctioneer-controller")
	err = addAuctioneerController(ctx, mgr, deployedRobots)
	if err != nil {
		log.Fatal().Err(err).Msg("Unable to add auctioneer-controller to manager")
	}

	// Setup webhooks
	log.Info().Msg("Setting up webhook server")
	hookServer := mgr.GetWebhookServer()
	hookServer.CertDir = certDir

	log.Info().Msg("Registering webhooks to the webhook server")
	hookServer.Register("/auctioneer/validate", &webhook.Admission{Handler: &auctioneerValidator{Client: mgr.GetClient()}})

	// Start controller
	log.Info().Msg("Starting controller manager")
	err = mgr.Start(signals.SetupSignalHandler())
	if err != nil {
		log.Fatal().Err(err).Msg("Unable to start controller manager")
	} else {
		log.Info().Msg("Shutting down")
	}
}
