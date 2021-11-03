//go:build !ignore_autogenerated
// +build !ignore_autogenerated

// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

// Code generated by deepcopy-gen. DO NOT EDIT.

package v1alpha1

import (
	runtime "k8s.io/apimachinery/pkg/runtime"
)

// DeepCopyInto is an autogenerated deepcopy function, copying the receiver, writing into out. in must be non-nil.
func (in *ActiveAction) DeepCopyInto(out *ActiveAction) {
	*out = *in
	return
}

// DeepCopy is an autogenerated deepcopy function, copying the receiver, creating a new ActiveAction.
func (in *ActiveAction) DeepCopy() *ActiveAction {
	if in == nil {
		return nil
	}
	out := new(ActiveAction)
	in.DeepCopyInto(out)
	return out
}

// DeepCopyInto is an autogenerated deepcopy function, copying the receiver, writing into out. in must be non-nil.
func (in *Charge) DeepCopyInto(out *Charge) {
	*out = *in
	return
}

// DeepCopy is an autogenerated deepcopy function, copying the receiver, creating a new Charge.
func (in *Charge) DeepCopy() *Charge {
	if in == nil {
		return nil
	}
	out := new(Charge)
	in.DeepCopyInto(out)
	return out
}

// DeepCopyInto is an autogenerated deepcopy function, copying the receiver, writing into out. in must be non-nil.
func (in *ChargeAction) DeepCopyInto(out *ChargeAction) {
	*out = *in
	out.Charge = in.Charge
	return
}

// DeepCopy is an autogenerated deepcopy function, copying the receiver, creating a new ChargeAction.
func (in *ChargeAction) DeepCopy() *ChargeAction {
	if in == nil {
		return nil
	}
	out := new(ChargeAction)
	in.DeepCopyInto(out)
	return out
}

// DeepCopyInto is an autogenerated deepcopy function, copying the receiver, writing into out. in must be non-nil.
func (in *Dock) DeepCopyInto(out *Dock) {
	*out = *in
	return
}

// DeepCopy is an autogenerated deepcopy function, copying the receiver, creating a new Dock.
func (in *Dock) DeepCopy() *Dock {
	if in == nil {
		return nil
	}
	out := new(Dock)
	in.DeepCopyInto(out)
	return out
}

// DeepCopyInto is an autogenerated deepcopy function, copying the receiver, writing into out. in must be non-nil.
func (in *GetTrolleyAction) DeepCopyInto(out *GetTrolleyAction) {
	*out = *in
	out.GetTrolley = in.GetTrolley
	return
}

// DeepCopy is an autogenerated deepcopy function, copying the receiver, creating a new GetTrolleyAction.
func (in *GetTrolleyAction) DeepCopy() *GetTrolleyAction {
	if in == nil {
		return nil
	}
	out := new(GetTrolleyAction)
	in.DeepCopyInto(out)
	return out
}

// DeepCopyInto is an autogenerated deepcopy function, copying the receiver, writing into out. in must be non-nil.
func (in *Mission) DeepCopyInto(out *Mission) {
	*out = *in
	out.TypeMeta = in.TypeMeta
	in.ObjectMeta.DeepCopyInto(&out.ObjectMeta)
	in.Spec.DeepCopyInto(&out.Spec)
	in.Status.DeepCopyInto(&out.Status)
	return
}

// DeepCopy is an autogenerated deepcopy function, copying the receiver, creating a new Mission.
func (in *Mission) DeepCopy() *Mission {
	if in == nil {
		return nil
	}
	out := new(Mission)
	in.DeepCopyInto(out)
	return out
}

// DeepCopyObject is an autogenerated deepcopy function, copying the receiver, creating a new runtime.Object.
func (in *Mission) DeepCopyObject() runtime.Object {
	if c := in.DeepCopy(); c != nil {
		return c
	}
	return nil
}

// DeepCopyInto is an autogenerated deepcopy function, copying the receiver, writing into out. in must be non-nil.
func (in *MissionList) DeepCopyInto(out *MissionList) {
	*out = *in
	out.TypeMeta = in.TypeMeta
	in.ListMeta.DeepCopyInto(&out.ListMeta)
	if in.Items != nil {
		in, out := &in.Items, &out.Items
		*out = make([]Mission, len(*in))
		for i := range *in {
			(*in)[i].DeepCopyInto(&(*out)[i])
		}
	}
	return
}

// DeepCopy is an autogenerated deepcopy function, copying the receiver, creating a new MissionList.
func (in *MissionList) DeepCopy() *MissionList {
	if in == nil {
		return nil
	}
	out := new(MissionList)
	in.DeepCopyInto(out)
	return out
}

// DeepCopyObject is an autogenerated deepcopy function, copying the receiver, creating a new runtime.Object.
func (in *MissionList) DeepCopyObject() runtime.Object {
	if c := in.DeepCopy(); c != nil {
		return c
	}
	return nil
}

// DeepCopyInto is an autogenerated deepcopy function, copying the receiver, writing into out. in must be non-nil.
func (in *MissionSpec) DeepCopyInto(out *MissionSpec) {
	*out = *in
	if in.Actions != nil {
		in, out := &in.Actions, &out.Actions
		*out = make([]Action, len(*in))
		for i := range *in {
			if (*in)[i] != nil {
				(*out)[i] = (*in)[i].DeepCopyAction()
			}
		}
	}
	return
}

// DeepCopy is an autogenerated deepcopy function, copying the receiver, creating a new MissionSpec.
func (in *MissionSpec) DeepCopy() *MissionSpec {
	if in == nil {
		return nil
	}
	out := new(MissionSpec)
	in.DeepCopyInto(out)
	return out
}

// DeepCopyInto is an autogenerated deepcopy function, copying the receiver, writing into out. in must be non-nil.
func (in *MissionStatus) DeepCopyInto(out *MissionStatus) {
	*out = *in
	out.ActiveAction = in.ActiveAction
	in.TimeOfActuation.DeepCopyInto(&out.TimeOfActuation)
	return
}

// DeepCopy is an autogenerated deepcopy function, copying the receiver, creating a new MissionStatus.
func (in *MissionStatus) DeepCopy() *MissionStatus {
	if in == nil {
		return nil
	}
	out := new(MissionStatus)
	in.DeepCopyInto(out)
	return out
}

// DeepCopyInto is an autogenerated deepcopy function, copying the receiver, writing into out. in must be non-nil.
func (in *MoveToNamedPositionAction) DeepCopyInto(out *MoveToNamedPositionAction) {
	*out = *in
	out.MoveToNamedPosition = in.MoveToNamedPosition
	return
}

// DeepCopy is an autogenerated deepcopy function, copying the receiver, creating a new MoveToNamedPositionAction.
func (in *MoveToNamedPositionAction) DeepCopy() *MoveToNamedPositionAction {
	if in == nil {
		return nil
	}
	out := new(MoveToNamedPositionAction)
	in.DeepCopyInto(out)
	return out
}

// DeepCopyInto is an autogenerated deepcopy function, copying the receiver, writing into out. in must be non-nil.
func (in *ReturnTrolleyAction) DeepCopyInto(out *ReturnTrolleyAction) {
	*out = *in
	out.ReturnTrolley = in.ReturnTrolley
	return
}

// DeepCopy is an autogenerated deepcopy function, copying the receiver, creating a new ReturnTrolleyAction.
func (in *ReturnTrolleyAction) DeepCopy() *ReturnTrolleyAction {
	if in == nil {
		return nil
	}
	out := new(ReturnTrolleyAction)
	in.DeepCopyInto(out)
	return out
}

// DeepCopyInto is an autogenerated deepcopy function, copying the receiver, writing into out. in must be non-nil.
func (in *Target) DeepCopyInto(out *Target) {
	*out = *in
	return
}

// DeepCopy is an autogenerated deepcopy function, copying the receiver, creating a new Target.
func (in *Target) DeepCopy() *Target {
	if in == nil {
		return nil
	}
	out := new(Target)
	in.DeepCopyInto(out)
	return out
}
