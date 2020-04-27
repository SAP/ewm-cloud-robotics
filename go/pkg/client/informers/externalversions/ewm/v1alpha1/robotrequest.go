// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

// Code generated by informer-gen. DO NOT EDIT.

package v1alpha1

import (
	"context"
	time "time"

	ewmv1alpha1 "github.com/SAP/ewm-cloud-robotics/go/pkg/apis/ewm/v1alpha1"
	versioned "github.com/SAP/ewm-cloud-robotics/go/pkg/client/clientset/versioned"
	internalinterfaces "github.com/SAP/ewm-cloud-robotics/go/pkg/client/informers/externalversions/internalinterfaces"
	v1alpha1 "github.com/SAP/ewm-cloud-robotics/go/pkg/client/listers/ewm/v1alpha1"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	runtime "k8s.io/apimachinery/pkg/runtime"
	watch "k8s.io/apimachinery/pkg/watch"
	cache "k8s.io/client-go/tools/cache"
)

// RobotRequestInformer provides access to a shared informer and lister for
// RobotRequests.
type RobotRequestInformer interface {
	Informer() cache.SharedIndexInformer
	Lister() v1alpha1.RobotRequestLister
}

type robotRequestInformer struct {
	factory          internalinterfaces.SharedInformerFactory
	tweakListOptions internalinterfaces.TweakListOptionsFunc
	namespace        string
}

// NewRobotRequestInformer constructs a new informer for RobotRequest type.
// Always prefer using an informer factory to get a shared informer instead of getting an independent
// one. This reduces memory footprint and number of connections to the server.
func NewRobotRequestInformer(client versioned.Interface, namespace string, resyncPeriod time.Duration, indexers cache.Indexers) cache.SharedIndexInformer {
	return NewFilteredRobotRequestInformer(client, namespace, resyncPeriod, indexers, nil)
}

// NewFilteredRobotRequestInformer constructs a new informer for RobotRequest type.
// Always prefer using an informer factory to get a shared informer instead of getting an independent
// one. This reduces memory footprint and number of connections to the server.
func NewFilteredRobotRequestInformer(client versioned.Interface, namespace string, resyncPeriod time.Duration, indexers cache.Indexers, tweakListOptions internalinterfaces.TweakListOptionsFunc) cache.SharedIndexInformer {
	return cache.NewSharedIndexInformer(
		&cache.ListWatch{
			ListFunc: func(options v1.ListOptions) (runtime.Object, error) {
				if tweakListOptions != nil {
					tweakListOptions(&options)
				}
				return client.EwmV1alpha1().RobotRequests(namespace).List(context.TODO(), options)
			},
			WatchFunc: func(options v1.ListOptions) (watch.Interface, error) {
				if tweakListOptions != nil {
					tweakListOptions(&options)
				}
				return client.EwmV1alpha1().RobotRequests(namespace).Watch(context.TODO(), options)
			},
		},
		&ewmv1alpha1.RobotRequest{},
		resyncPeriod,
		indexers,
	)
}

func (f *robotRequestInformer) defaultInformer(client versioned.Interface, resyncPeriod time.Duration) cache.SharedIndexInformer {
	return NewFilteredRobotRequestInformer(client, f.namespace, resyncPeriod, cache.Indexers{cache.NamespaceIndex: cache.MetaNamespaceIndexFunc}, f.tweakListOptions)
}

func (f *robotRequestInformer) Informer() cache.SharedIndexInformer {
	return f.factory.InformerFor(&ewmv1alpha1.RobotRequest{}, f.defaultInformer)
}

func (f *robotRequestInformer) Lister() v1alpha1.RobotRequestLister {
	return v1alpha1.NewRobotRequestLister(f.Informer().GetIndexer())
}
