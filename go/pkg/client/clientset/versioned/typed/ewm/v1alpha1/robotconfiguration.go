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
	"time"

	v1alpha1 "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	scheme "github.com/SAP/ewm-cloud-robotics/go/pkg/client/clientset/versioned/scheme"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	types "k8s.io/apimachinery/pkg/types"
	watch "k8s.io/apimachinery/pkg/watch"
	rest "k8s.io/client-go/rest"
)

// RobotConfigurationsGetter has a method to return a RobotConfigurationInterface.
// A group's client should implement this interface.
type RobotConfigurationsGetter interface {
	RobotConfigurations(namespace string) RobotConfigurationInterface
}

// RobotConfigurationInterface has methods to work with RobotConfiguration resources.
type RobotConfigurationInterface interface {
	Create(*v1alpha1.RobotConfiguration) (*v1alpha1.RobotConfiguration, error)
	Update(*v1alpha1.RobotConfiguration) (*v1alpha1.RobotConfiguration, error)
	UpdateStatus(*v1alpha1.RobotConfiguration) (*v1alpha1.RobotConfiguration, error)
	Delete(name string, options *v1.DeleteOptions) error
	DeleteCollection(options *v1.DeleteOptions, listOptions v1.ListOptions) error
	Get(name string, options v1.GetOptions) (*v1alpha1.RobotConfiguration, error)
	List(opts v1.ListOptions) (*v1alpha1.RobotConfigurationList, error)
	Watch(opts v1.ListOptions) (watch.Interface, error)
	Patch(name string, pt types.PatchType, data []byte, subresources ...string) (result *v1alpha1.RobotConfiguration, err error)
	RobotConfigurationExpansion
}

// robotConfigurations implements RobotConfigurationInterface
type robotConfigurations struct {
	client rest.Interface
	ns     string
}

// newRobotConfigurations returns a RobotConfigurations
func newRobotConfigurations(c *EwmV1alpha1Client, namespace string) *robotConfigurations {
	return &robotConfigurations{
		client: c.RESTClient(),
		ns:     namespace,
	}
}

// Get takes name of the robotConfiguration, and returns the corresponding robotConfiguration object, and an error if there is any.
func (c *robotConfigurations) Get(name string, options v1.GetOptions) (result *v1alpha1.RobotConfiguration, err error) {
	result = &v1alpha1.RobotConfiguration{}
	err = c.client.Get().
		Namespace(c.ns).
		Resource("robotconfigurations").
		Name(name).
		VersionedParams(&options, scheme.ParameterCodec).
		Do().
		Into(result)
	return
}

// List takes label and field selectors, and returns the list of RobotConfigurations that match those selectors.
func (c *robotConfigurations) List(opts v1.ListOptions) (result *v1alpha1.RobotConfigurationList, err error) {
	var timeout time.Duration
	if opts.TimeoutSeconds != nil {
		timeout = time.Duration(*opts.TimeoutSeconds) * time.Second
	}
	result = &v1alpha1.RobotConfigurationList{}
	err = c.client.Get().
		Namespace(c.ns).
		Resource("robotconfigurations").
		VersionedParams(&opts, scheme.ParameterCodec).
		Timeout(timeout).
		Do().
		Into(result)
	return
}

// Watch returns a watch.Interface that watches the requested robotConfigurations.
func (c *robotConfigurations) Watch(opts v1.ListOptions) (watch.Interface, error) {
	var timeout time.Duration
	if opts.TimeoutSeconds != nil {
		timeout = time.Duration(*opts.TimeoutSeconds) * time.Second
	}
	opts.Watch = true
	return c.client.Get().
		Namespace(c.ns).
		Resource("robotconfigurations").
		VersionedParams(&opts, scheme.ParameterCodec).
		Timeout(timeout).
		Watch()
}

// Create takes the representation of a robotConfiguration and creates it.  Returns the server's representation of the robotConfiguration, and an error, if there is any.
func (c *robotConfigurations) Create(robotConfiguration *v1alpha1.RobotConfiguration) (result *v1alpha1.RobotConfiguration, err error) {
	result = &v1alpha1.RobotConfiguration{}
	err = c.client.Post().
		Namespace(c.ns).
		Resource("robotconfigurations").
		Body(robotConfiguration).
		Do().
		Into(result)
	return
}

// Update takes the representation of a robotConfiguration and updates it. Returns the server's representation of the robotConfiguration, and an error, if there is any.
func (c *robotConfigurations) Update(robotConfiguration *v1alpha1.RobotConfiguration) (result *v1alpha1.RobotConfiguration, err error) {
	result = &v1alpha1.RobotConfiguration{}
	err = c.client.Put().
		Namespace(c.ns).
		Resource("robotconfigurations").
		Name(robotConfiguration.Name).
		Body(robotConfiguration).
		Do().
		Into(result)
	return
}

// UpdateStatus was generated because the type contains a Status member.
// Add a +genclient:noStatus comment above the type to avoid generating UpdateStatus().

func (c *robotConfigurations) UpdateStatus(robotConfiguration *v1alpha1.RobotConfiguration) (result *v1alpha1.RobotConfiguration, err error) {
	result = &v1alpha1.RobotConfiguration{}
	err = c.client.Put().
		Namespace(c.ns).
		Resource("robotconfigurations").
		Name(robotConfiguration.Name).
		SubResource("status").
		Body(robotConfiguration).
		Do().
		Into(result)
	return
}

// Delete takes name of the robotConfiguration and deletes it. Returns an error if one occurs.
func (c *robotConfigurations) Delete(name string, options *v1.DeleteOptions) error {
	return c.client.Delete().
		Namespace(c.ns).
		Resource("robotconfigurations").
		Name(name).
		Body(options).
		Do().
		Error()
}

// DeleteCollection deletes a collection of objects.
func (c *robotConfigurations) DeleteCollection(options *v1.DeleteOptions, listOptions v1.ListOptions) error {
	var timeout time.Duration
	if listOptions.TimeoutSeconds != nil {
		timeout = time.Duration(*listOptions.TimeoutSeconds) * time.Second
	}
	return c.client.Delete().
		Namespace(c.ns).
		Resource("robotconfigurations").
		VersionedParams(&listOptions, scheme.ParameterCodec).
		Timeout(timeout).
		Body(options).
		Do().
		Error()
}

// Patch applies the patch and returns the patched robotConfiguration.
func (c *robotConfigurations) Patch(name string, pt types.PatchType, data []byte, subresources ...string) (result *v1alpha1.RobotConfiguration, err error) {
	result = &v1alpha1.RobotConfiguration{}
	err = c.client.Patch(pt).
		Namespace(c.ns).
		Resource("robotconfigurations").
		SubResource(subresources...).
		Name(name).
		Body(data).
		Do().
		Into(result)
	return
}