// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

// Code generated by client-gen. DO NOT EDIT.

package fake

import (
	"context"

	v1alpha1 "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	labels "k8s.io/apimachinery/pkg/labels"
	schema "k8s.io/apimachinery/pkg/runtime/schema"
	types "k8s.io/apimachinery/pkg/types"
	watch "k8s.io/apimachinery/pkg/watch"
	testing "k8s.io/client-go/testing"
)

// FakeAuctioneers implements AuctioneerInterface
type FakeAuctioneers struct {
	Fake *FakeEwmV1alpha1
	ns   string
}

var auctioneersResource = schema.GroupVersionResource{Group: "ewm.sap.com", Version: "v1alpha1", Resource: "auctioneers"}

var auctioneersKind = schema.GroupVersionKind{Group: "ewm.sap.com", Version: "v1alpha1", Kind: "Auctioneer"}

// Get takes name of the auctioneer, and returns the corresponding auctioneer object, and an error if there is any.
func (c *FakeAuctioneers) Get(ctx context.Context, name string, options v1.GetOptions) (result *v1alpha1.Auctioneer, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewGetAction(auctioneersResource, c.ns, name), &v1alpha1.Auctioneer{})

	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha1.Auctioneer), err
}

// List takes label and field selectors, and returns the list of Auctioneers that match those selectors.
func (c *FakeAuctioneers) List(ctx context.Context, opts v1.ListOptions) (result *v1alpha1.AuctioneerList, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewListAction(auctioneersResource, auctioneersKind, c.ns, opts), &v1alpha1.AuctioneerList{})

	if obj == nil {
		return nil, err
	}

	label, _, _ := testing.ExtractFromListOptions(opts)
	if label == nil {
		label = labels.Everything()
	}
	list := &v1alpha1.AuctioneerList{ListMeta: obj.(*v1alpha1.AuctioneerList).ListMeta}
	for _, item := range obj.(*v1alpha1.AuctioneerList).Items {
		if label.Matches(labels.Set(item.Labels)) {
			list.Items = append(list.Items, item)
		}
	}
	return list, err
}

// Watch returns a watch.Interface that watches the requested auctioneers.
func (c *FakeAuctioneers) Watch(ctx context.Context, opts v1.ListOptions) (watch.Interface, error) {
	return c.Fake.
		InvokesWatch(testing.NewWatchAction(auctioneersResource, c.ns, opts))

}

// Create takes the representation of a auctioneer and creates it.  Returns the server's representation of the auctioneer, and an error, if there is any.
func (c *FakeAuctioneers) Create(ctx context.Context, auctioneer *v1alpha1.Auctioneer, opts v1.CreateOptions) (result *v1alpha1.Auctioneer, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewCreateAction(auctioneersResource, c.ns, auctioneer), &v1alpha1.Auctioneer{})

	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha1.Auctioneer), err
}

// Update takes the representation of a auctioneer and updates it. Returns the server's representation of the auctioneer, and an error, if there is any.
func (c *FakeAuctioneers) Update(ctx context.Context, auctioneer *v1alpha1.Auctioneer, opts v1.UpdateOptions) (result *v1alpha1.Auctioneer, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewUpdateAction(auctioneersResource, c.ns, auctioneer), &v1alpha1.Auctioneer{})

	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha1.Auctioneer), err
}

// UpdateStatus was generated because the type contains a Status member.
// Add a +genclient:noStatus comment above the type to avoid generating UpdateStatus().
func (c *FakeAuctioneers) UpdateStatus(ctx context.Context, auctioneer *v1alpha1.Auctioneer, opts v1.UpdateOptions) (*v1alpha1.Auctioneer, error) {
	obj, err := c.Fake.
		Invokes(testing.NewUpdateSubresourceAction(auctioneersResource, "status", c.ns, auctioneer), &v1alpha1.Auctioneer{})

	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha1.Auctioneer), err
}

// Delete takes name of the auctioneer and deletes it. Returns an error if one occurs.
func (c *FakeAuctioneers) Delete(ctx context.Context, name string, opts v1.DeleteOptions) error {
	_, err := c.Fake.
		Invokes(testing.NewDeleteAction(auctioneersResource, c.ns, name), &v1alpha1.Auctioneer{})

	return err
}

// DeleteCollection deletes a collection of objects.
func (c *FakeAuctioneers) DeleteCollection(ctx context.Context, opts v1.DeleteOptions, listOpts v1.ListOptions) error {
	action := testing.NewDeleteCollectionAction(auctioneersResource, c.ns, listOpts)

	_, err := c.Fake.Invokes(action, &v1alpha1.AuctioneerList{})
	return err
}

// Patch applies the patch and returns the patched auctioneer.
func (c *FakeAuctioneers) Patch(ctx context.Context, name string, pt types.PatchType, data []byte, opts v1.PatchOptions, subresources ...string) (result *v1alpha1.Auctioneer, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewPatchSubresourceAction(auctioneersResource, c.ns, name, pt, data, subresources...), &v1alpha1.Auctioneer{})

	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha1.Auctioneer), err
}
