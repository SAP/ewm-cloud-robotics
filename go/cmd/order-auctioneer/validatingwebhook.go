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
	"fmt"
	"net/http"
	"reflect"

	ewm "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission"
)

// podValidator validates Auctioneers
type auctioneerValidator struct {
	Client  client.Client
	decoder *admission.Decoder
}

// Handle checks if the given auctioneer is valid
func (v *auctioneerValidator) Handle(ctx context.Context, req admission.Request) admission.Response {
	var auctioneer ewm.Auctioneer
	err := v.decoder.Decode(req, &auctioneer)
	if err != nil {
		return admission.Errored(http.StatusBadRequest, err)
	}

	var auctioneers ewm.AuctioneerList
	err = v.Client.List(ctx, &auctioneers)
	if err != nil {
		return admission.Errored(http.StatusBadRequest, err)
	}

	// Check if there are no other auctioneers with the same scope
	for _, a := range auctioneers.Items {
		if a.GetName() != auctioneer.GetName() || a.GetNamespace() != auctioneer.GetNamespace() {
			if reflect.DeepEqual(a.Spec.Scope, auctioneer.Spec.Scope) {
				return admission.Errored(http.StatusBadRequest, fmt.Errorf("auctioneer %q has the same spec.scope", a.GetName()))
			}
		}
	}

	// Check if Configuration is valid
	if auctioneer.Spec.Configuration.MaxOrdersPerRobot < auctioneer.Spec.Configuration.MinOrdersPerRobot {
		return admission.Errored(http.StatusBadRequest, fmt.Errorf("spec.configuration.maxOrdersPerRobot %v < spec.configuration.minOrdersPerRobot %v",
			auctioneer.Spec.Configuration.MaxOrdersPerRobot, auctioneer.Spec.Configuration.MinOrdersPerRobot))
	}

	return admission.Allowed("")
}

// InjectDecoder injects the decoder.
func (v *auctioneerValidator) InjectDecoder(d *admission.Decoder) error {
	v.decoder = d
	return nil
}
