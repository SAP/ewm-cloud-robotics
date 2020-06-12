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
	"os/signal"
	"strings"
	"syscall"

	ewm "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	crclient "github.com/SAP/ewm-cloud-robotics/go/pkg/client/clientset/versioned"
	crfactory "github.com/SAP/ewm-cloud-robotics/go/pkg/client/informers/externalversions"
	mirv2 "github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface/client/v2"
	"github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig"
	"github.com/pkg/errors"
	"k8s.io/apimachinery/pkg/watch"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/cache"
)

const (
	robotLabel string = "cloudrobotics.com/robot-name"
)

var log = zerologconfig.GetGlobalLogger()

func getMirClient() (*mirv2.Client, error) {

	mirHost := os.Getenv("MIR_HOST")
	if mirHost == "" {
		return nil, errors.New("Environment variable MIR_HOST is not set")
	}
	log.Info().Msgf("Connecting to MiR robot on host %v", mirHost)

	mirUser := os.Getenv("MIR_USER")
	if mirUser == "" {
		return nil, errors.New("Environment variable MIR_USER is not set")
	}
	mirPassword := os.Getenv("MIR_PASSWORD")
	if mirPassword == "" {
		return nil, errors.New("Environment variable MIR_PASSWORD is not set")
	}

	mirClient, err := mirv2.NewClient(mirHost, mirUser, mirPassword, "mir-runtime-estimator", 5.0)
	if err != nil {
		return nil, errors.Wrapf(err, "NewClient")
	}

	return mirClient, nil
}

func getClientset() (*crclient.Clientset, error) {

	kubeConfig, err := rest.InClusterConfig()
	if err != nil {
		return nil, errors.Wrapf(err, "Could not get K8S InClusterConfig")
	}

	clientset, err := crclient.NewForConfig(kubeConfig)
	if err != nil {
		return nil, errors.Wrapf(err, "Could not create new clientset")
	}

	return clientset, nil
}

func initInformer(done <-chan struct{}, clientset *crclient.Clientset, robotName string) (<-chan runtimeEstimationEvent, error) {

	factory := crfactory.NewSharedInformerFactory(clientset, 0)
	informer := factory.Ewm().V1alpha1().RunTimeEstimations().Informer()

	// Add event handler
	eventChan := make(chan runtimeEstimationEvent)
	informer.AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			rte := obj.(*ewm.RunTimeEstimation)
			if rte.GetLabels()[robotLabel] == robotName {
				eventChan <- runtimeEstimationEvent{eventType: watch.Added, runtimeEstimation: rte}
			}
		},
	})

	// Start informer
	go informer.Run(done)

	if !cache.WaitForCacheSync(done, informer.HasSynced) {
		return nil, errors.New("WaitForCacheSync failed")
	}

	return eventChan, nil
}

func main() {
	// App close
	done := make(chan struct{})
	interruptChan := make(chan os.Signal, 1)
	signal.Notify(interruptChan, os.Interrupt, syscall.SIGINT, syscall.SIGTERM)

	// Get robot name for which the app is deployed
	robotName := os.Getenv("ROBCO_ROBOT_NAME")
	if robotName == "" {
		log.Fatal().Msg("No name in environment variable ROBCO_ROBOT_NAME")
	}

	log.Info().Msgf("mir-runtime-estimator app started on robot %q", robotName)

	// Initialize MiR interface
	mirClient, err := getMirClient()
	if err != nil {
		log.Fatal().Err(err).Msg("Error initializing client for MiR robot")
	}

	// Initialize CR Watchers
	clientset, err := getClientset()
	eventChan, err := initInformer(done, clientset, robotName)
	if err != nil {
		log.Fatal().Err(err).Msg("Error initializing informer for CRs")
	}

	precalcPathsWhenIdle := false
	if strings.ToLower(os.Getenv("PRECALC_PATHS_WHEN_IDLE")) == "true" {
		precalcPathsWhenIdle = true
	}

	// Initialize MiR estimator
	estimator := newMirEstimator(robotName, mirClient, clientset, eventChan)
	go estimator.run(done, precalcPathsWhenIdle)

	// Enable preserving pathguides if requested (debugging only)
	mirPreservPathGuides := os.Getenv("MIR_PERSERVE_PATHGUIDES")
	if strings.ToLower(mirPreservPathGuides) == "true" {
		estimator.setPreservePathGuides(true)
	}

	// Wait for interrupt signal
	<-interruptChan

	// Shutting down
	log.Info().Msg("Shutting down")
	close(done)
}
