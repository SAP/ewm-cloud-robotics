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
	"strconv"
	"strings"
	"syscall"

	ewm "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	crclient "github.com/SAP/ewm-cloud-robotics/go/pkg/client/clientset/versioned"
	crfactory "github.com/SAP/ewm-cloud-robotics/go/pkg/client/informers/externalversions"
	mirv2 "github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface/client/v2"
	"github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig"
	"github.com/pkg/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
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
	log.Info().Msgf("Connecting to MiR on host %v", mirHost)

	mirUser := os.Getenv("MIR_USER")
	if mirUser == "" {
		return nil, errors.New("Environment variable MIR_USER is not set")
	}
	mirPassword := os.Getenv("MIR_PASSWORD")
	if mirPassword == "" {
		return nil, errors.New("Environment variable MIR_PASSWORD is not set")
	}

	mirHTTPTimeout := os.Getenv("MIR_HTTP_TIMEOUT")

	httpTimeout, err := strconv.ParseFloat(mirHTTPTimeout, 64)
	if err != nil {
		// Big default timeout because GET /paths endpoint could get slow
		httpTimeout = 60
	}
	log.Info().Msgf("Timeout for MiR HTTP API set to %v seconds", httpTimeout)

	mirClient, err := mirv2.NewClient(mirHost, mirUser, mirPassword, "mir-travel-time-calculator", httpTimeout)
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

func initInformer(done <-chan struct{}, clientset *crclient.Clientset, namespace, robotName string) (<-chan travelTimeCalculationEvent, error) {

	factory := crfactory.NewSharedInformerFactoryWithOptions(clientset, 0, crfactory.WithNamespace(namespace))
	informer := factory.Ewm().V1alpha1().TravelTimeCalculations().Informer()

	// Add event handler
	eventChan := make(chan travelTimeCalculationEvent)
	informer.AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			ttc := obj.(*ewm.TravelTimeCalculation)
			if ttc.GetLabels()[robotLabel] == robotName {
				eventChan <- travelTimeCalculationEvent{eventType: watch.Added, travelTimeCalculation: ttc}
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

	// Get namespace of custom resources to be watched
	namespace := os.Getenv("K8S_NAMESPACE")
	if namespace == "" {
		namespace = metav1.NamespaceDefault
	}

	// If MIR_FLEET_CONFIG is enabled pathg uides are preserved and calculated in advance on MiR Fleet instance, but no path guides are created on the robots
	// MiR Fleet is unstable in case path guides are deleted on robot side or the same path guides are created at different robots at about the same time
	mirFleetConfig := strings.ToUpper(os.Getenv("MIR_FLEET_CONFIG"))
	var mirFleetConfigMode mirFleetConfigMode
	switch mirFleetConfig {
	case string(mirFleetConfigRobot):
		log.Info().Msg("Starting in MiR Fleet mode: robot")
		mirFleetConfigMode = mirFleetConfigRobot
	case string(mirFleetConfigFleet):
		log.Info().Msg("Starting in MiR Fleet mode: fleet")
		mirFleetConfigMode = mirFleetConfigFleet
	case string(mirFleetConfigNone):
		log.Info().Msg("MiR Fleet mode disabled")
		mirFleetConfigMode = mirFleetConfigNone
	default:
		log.Panic().Msgf("Value %s for environment variable MIR_FLEET_CONFIG is invalid", mirFleetConfig)
	}

	log.Info().Msgf("Watch custom resources of namespace %v", namespace)

	// Get robot name for which the app is deployed
	robotName := os.Getenv("ROBCO_ROBOT_NAME")
	if robotName == "" && mirFleetConfigMode != mirFleetConfigFleet {
		log.Fatal().Msg("No name in environment variable ROBCO_ROBOT_NAME")
	} else if mirFleetConfigMode == mirFleetConfigFleet {
		log.Info().Msg("mir-travel-time-calculator app started on MiR Fleet")
	} else {
		log.Info().Msgf("mir-travel-time-calculator app started on robot %q", robotName)
	}

	// Initialize MiR interface
	mirClient, err := getMirClient()
	if err != nil {
		log.Fatal().Err(err).Msg("Error initializing client for MiR robot")
	}

	// Create clientset and event channel for CR
	var clientset *crclient.Clientset
	var eventChan <-chan travelTimeCalculationEvent
	precalcPathsWhenIdle := false

	// MiR Fleet instance does not need to listen to runtime estimation CRs because it cannot create paths
	if mirFleetConfigMode != mirFleetConfigFleet {
		// Initialize CR Watchers
		clientset, err = getClientset()
		if err != nil {
			log.Fatal().Err(err).Msg("Error getting ClientSet for CRs")
		}
		eventChan, err = initInformer(done, clientset, namespace, robotName)
		if err != nil {
			log.Fatal().Err(err).Msg("Error initializing informer for CRs")
		}
		if strings.ToLower(os.Getenv("PRECALC_PATHS_WHEN_IDLE")) == "true" {
			precalcPathsWhenIdle = true
		}
	}

	// Initialize MiR estimator
	estimator := newMirEstimator(robotName, mirClient, clientset, eventChan)

	mirPreservPathGuides := bool(strings.ToLower(os.Getenv("MIR_PERSERVE_PATHGUIDES")) == "true")

	// Precalculate paths when robot move base is idle
	if precalcPathsWhenIdle {
		estimator.setPrecalcPathsWhenIdle(true)
	}

	// Enable preserving pathguides if requested
	if mirPreservPathGuides {
		estimator.setPreservePathGuides(true)
	}

	// Enable MiR Fleet mode if requested
	estimator.setMirFleetConfigMode(mirFleetConfigMode)

	// Run the estimator
	go estimator.run(done)

	// Wait for interrupt signal
	<-interruptChan

	// Shutting down
	log.Info().Msg("Shutting down")
	close(done)
}
