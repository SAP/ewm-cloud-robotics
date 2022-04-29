// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
//

// Code generated by client-gen. DO NOT EDIT.

package v1alpha1

import (
	"context"
	"time"

	v1alpha1 "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	scheme "github.com/SAP/ewm-cloud-robotics/go/pkg/client/clientset/versioned/scheme"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	types "k8s.io/apimachinery/pkg/types"
	watch "k8s.io/apimachinery/pkg/watch"
	rest "k8s.io/client-go/rest"
)

// AuctioneersGetter has a method to return a AuctioneerInterface.
// A group's client should implement this interface.
type AuctioneersGetter interface {
	Auctioneers(namespace string) AuctioneerInterface
}

// AuctioneerInterface has methods to work with Auctioneer resources.
type AuctioneerInterface interface {
	Create(ctx context.Context, auctioneer *v1alpha1.Auctioneer, opts v1.CreateOptions) (*v1alpha1.Auctioneer, error)
	Update(ctx context.Context, auctioneer *v1alpha1.Auctioneer, opts v1.UpdateOptions) (*v1alpha1.Auctioneer, error)
	UpdateStatus(ctx context.Context, auctioneer *v1alpha1.Auctioneer, opts v1.UpdateOptions) (*v1alpha1.Auctioneer, error)
	Delete(ctx context.Context, name string, opts v1.DeleteOptions) error
	DeleteCollection(ctx context.Context, opts v1.DeleteOptions, listOpts v1.ListOptions) error
	Get(ctx context.Context, name string, opts v1.GetOptions) (*v1alpha1.Auctioneer, error)
	List(ctx context.Context, opts v1.ListOptions) (*v1alpha1.AuctioneerList, error)
	Watch(ctx context.Context, opts v1.ListOptions) (watch.Interface, error)
	Patch(ctx context.Context, name string, pt types.PatchType, data []byte, opts v1.PatchOptions, subresources ...string) (result *v1alpha1.Auctioneer, err error)
	AuctioneerExpansion
}

// auctioneers implements AuctioneerInterface
type auctioneers struct {
	client rest.Interface
	ns     string
}

// newAuctioneers returns a Auctioneers
func newAuctioneers(c *EwmV1alpha1Client, namespace string) *auctioneers {
	return &auctioneers{
		client: c.RESTClient(),
		ns:     namespace,
	}
}

// Get takes name of the auctioneer, and returns the corresponding auctioneer object, and an error if there is any.
func (c *auctioneers) Get(ctx context.Context, name string, options v1.GetOptions) (result *v1alpha1.Auctioneer, err error) {
	result = &v1alpha1.Auctioneer{}
	err = c.client.Get().
		Namespace(c.ns).
		Resource("auctioneers").
		Name(name).
		VersionedParams(&options, scheme.ParameterCodec).
		Do(ctx).
		Into(result)
	return
}

// List takes label and field selectors, and returns the list of Auctioneers that match those selectors.
func (c *auctioneers) List(ctx context.Context, opts v1.ListOptions) (result *v1alpha1.AuctioneerList, err error) {
	var timeout time.Duration
	if opts.TimeoutSeconds != nil {
		timeout = time.Duration(*opts.TimeoutSeconds) * time.Second
	}
	result = &v1alpha1.AuctioneerList{}
	err = c.client.Get().
		Namespace(c.ns).
		Resource("auctioneers").
		VersionedParams(&opts, scheme.ParameterCodec).
		Timeout(timeout).
		Do(ctx).
		Into(result)
	return
}

// Watch returns a watch.Interface that watches the requested auctioneers.
func (c *auctioneers) Watch(ctx context.Context, opts v1.ListOptions) (watch.Interface, error) {
	var timeout time.Duration
	if opts.TimeoutSeconds != nil {
		timeout = time.Duration(*opts.TimeoutSeconds) * time.Second
	}
	opts.Watch = true
	return c.client.Get().
		Namespace(c.ns).
		Resource("auctioneers").
		VersionedParams(&opts, scheme.ParameterCodec).
		Timeout(timeout).
		Watch(ctx)
}

// Create takes the representation of a auctioneer and creates it.  Returns the server's representation of the auctioneer, and an error, if there is any.
func (c *auctioneers) Create(ctx context.Context, auctioneer *v1alpha1.Auctioneer, opts v1.CreateOptions) (result *v1alpha1.Auctioneer, err error) {
	result = &v1alpha1.Auctioneer{}
	err = c.client.Post().
		Namespace(c.ns).
		Resource("auctioneers").
		VersionedParams(&opts, scheme.ParameterCodec).
		Body(auctioneer).
		Do(ctx).
		Into(result)
	return
}

// Update takes the representation of a auctioneer and updates it. Returns the server's representation of the auctioneer, and an error, if there is any.
func (c *auctioneers) Update(ctx context.Context, auctioneer *v1alpha1.Auctioneer, opts v1.UpdateOptions) (result *v1alpha1.Auctioneer, err error) {
	result = &v1alpha1.Auctioneer{}
	err = c.client.Put().
		Namespace(c.ns).
		Resource("auctioneers").
		Name(auctioneer.Name).
		VersionedParams(&opts, scheme.ParameterCodec).
		Body(auctioneer).
		Do(ctx).
		Into(result)
	return
}

// UpdateStatus was generated because the type contains a Status member.
// Add a +genclient:noStatus comment above the type to avoid generating UpdateStatus().
func (c *auctioneers) UpdateStatus(ctx context.Context, auctioneer *v1alpha1.Auctioneer, opts v1.UpdateOptions) (result *v1alpha1.Auctioneer, err error) {
	result = &v1alpha1.Auctioneer{}
	err = c.client.Put().
		Namespace(c.ns).
		Resource("auctioneers").
		Name(auctioneer.Name).
		SubResource("status").
		VersionedParams(&opts, scheme.ParameterCodec).
		Body(auctioneer).
		Do(ctx).
		Into(result)
	return
}

// Delete takes name of the auctioneer and deletes it. Returns an error if one occurs.
func (c *auctioneers) Delete(ctx context.Context, name string, opts v1.DeleteOptions) error {
	return c.client.Delete().
		Namespace(c.ns).
		Resource("auctioneers").
		Name(name).
		Body(&opts).
		Do(ctx).
		Error()
}

// DeleteCollection deletes a collection of objects.
func (c *auctioneers) DeleteCollection(ctx context.Context, opts v1.DeleteOptions, listOpts v1.ListOptions) error {
	var timeout time.Duration
	if listOpts.TimeoutSeconds != nil {
		timeout = time.Duration(*listOpts.TimeoutSeconds) * time.Second
	}
	return c.client.Delete().
		Namespace(c.ns).
		Resource("auctioneers").
		VersionedParams(&listOpts, scheme.ParameterCodec).
		Timeout(timeout).
		Body(&opts).
		Do(ctx).
		Error()
}

// Patch applies the patch and returns the patched auctioneer.
func (c *auctioneers) Patch(ctx context.Context, name string, pt types.PatchType, data []byte, opts v1.PatchOptions, subresources ...string) (result *v1alpha1.Auctioneer, err error) {
	result = &v1alpha1.Auctioneer{}
	err = c.client.Patch(pt).
		Namespace(c.ns).
		Resource("auctioneers").
		Name(name).
		SubResource(subresources...).
		VersionedParams(&opts, scheme.ParameterCodec).
		Body(data).
		Do(ctx).
		Into(result)
	return
}
