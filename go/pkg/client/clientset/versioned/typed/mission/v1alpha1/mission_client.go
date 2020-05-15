// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

// Code generated by client-gen. DO NOT EDIT.

package v1alpha1

import (
	v1alpha1 "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/mission/v1alpha1"
	"github.com/SAP/ewm-cloud-robotics/go/pkg/client/clientset/versioned/scheme"
	rest "k8s.io/client-go/rest"
)

type MissionV1alpha1Interface interface {
	RESTClient() rest.Interface
	MissionsGetter
}

// MissionV1alpha1Client is used to interact with features provided by the mission.cloudrobotics.com group.
type MissionV1alpha1Client struct {
	restClient rest.Interface
}

func (c *MissionV1alpha1Client) Missions(namespace string) MissionInterface {
	return newMissions(c, namespace)
}

// NewForConfig creates a new MissionV1alpha1Client for the given config.
func NewForConfig(c *rest.Config) (*MissionV1alpha1Client, error) {
	config := *c
	if err := setConfigDefaults(&config); err != nil {
		return nil, err
	}
	client, err := rest.RESTClientFor(&config)
	if err != nil {
		return nil, err
	}
	return &MissionV1alpha1Client{client}, nil
}

// NewForConfigOrDie creates a new MissionV1alpha1Client for the given config and
// panics if there is an error in the config.
func NewForConfigOrDie(c *rest.Config) *MissionV1alpha1Client {
	client, err := NewForConfig(c)
	if err != nil {
		panic(err)
	}
	return client
}

// New creates a new MissionV1alpha1Client for the given RESTClient.
func New(c rest.Interface) *MissionV1alpha1Client {
	return &MissionV1alpha1Client{c}
}

func setConfigDefaults(config *rest.Config) error {
	gv := v1alpha1.SchemeGroupVersion
	config.GroupVersion = &gv
	config.APIPath = "/apis"
	config.NegotiatedSerializer = scheme.Codecs.WithoutConversion()

	if config.UserAgent == "" {
		config.UserAgent = rest.DefaultKubernetesUserAgent()
	}

	return nil
}

// RESTClient returns a RESTClient that is used to communicate
// with API server by this client implementation.
func (c *MissionV1alpha1Client) RESTClient() rest.Interface {
	if c == nil {
		return nil
	}
	return c.restClient
}
