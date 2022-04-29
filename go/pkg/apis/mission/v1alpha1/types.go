// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
//

package v1alpha1

import (
	"encoding/json"
	"fmt"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// Mission represents the Mission CRD
type Mission struct {
	metav1.TypeMeta `json:",inline"`
	// +optional
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec MissionSpec `json:"spec"`
	// +optional
	Status MissionStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// MissionList represents the array of Mission CRD
type MissionList struct {
	metav1.TypeMeta `json:",inline"`
	// +optional
	metav1.ListMeta `json:"metadata,omitempty"`

	Items []Mission `json:"items"`
}

// MissionSpec represents the spec of Mission CRD
type MissionSpec struct {
	Actions    []Action `json:"actions"`
	TimeOutSec int      `json:"timeOutSec,omitempty"`
}

// UnmarshalJSON is a JSON Unmarshaller supporting the polimorphic Actions array
func (m *MissionSpec) UnmarshalJSON(data []byte) error {
	// Ignore null, like in the main JSON package.
	if string(data) == "null" || string(data) == `""` {
		return nil
	}

	var objMap map[string]*json.RawMessage

	err := json.Unmarshal(data, &objMap)

	if err != nil {
		return err
	}

	// Unmarshal TimeOutSec if present
	if timeoutRaw, ok := objMap["timeOutSec"]; ok {
		err = json.Unmarshal(*timeoutRaw, &m.TimeOutSec)
		if err != nil {
			return err
		}
	}

	// Unmarshal Actions
	var rawActions []*json.RawMessage
	err = json.Unmarshal(*objMap["actions"], &rawActions)
	if err != nil {
		return err
	}

	m.Actions = make([]Action, len(rawActions))

	// Check the data type of each rawAction in array
	for i, rawAction := range rawActions {

		var a map[string]interface{}
		err = json.Unmarshal(*rawAction, &a)
		if err != nil {
			return err
		}

		if _, ok := a["charge"]; ok {
			var action ChargeAction
			err = json.Unmarshal(*rawAction, &action)
			if err != nil {
				return err
			}
			m.Actions[i] = &action
		} else if _, ok := a["moveToNamedPosition"]; ok {
			var action MoveToNamedPositionAction
			err = json.Unmarshal(*rawAction, &action)
			if err != nil {
				return err
			}
			m.Actions[i] = &action
		} else if _, ok := a["getTrolley"]; ok {
			var action GetTrolleyAction
			err = json.Unmarshal(*rawAction, &action)
			if err != nil {
				return err
			}
			m.Actions[i] = &action
		} else if _, ok := a["returnTrolley"]; ok {
			var action ReturnTrolleyAction
			err = json.Unmarshal(*rawAction, &action)
			if err != nil {
				return err
			}
			m.Actions[i] = &action
		} else {
			return fmt.Errorf("%v is an unknown action", a)
		}

	}

	return nil
}

// MissionStatus represents the status of Mission CRD
type MissionStatus struct {
	ActiveAction    ActiveAction        `json:"activeAction,omitempty"`
	Message         string              `json:"message,omitempty"`
	Status          MissionStatusStatus `json:"status,omitempty"`
	TimeOfActuation metav1.Time         `json:"timeOfActuation,omitempty"`
}

// Action is an interface to represent polymorphic array of actions in MissionSpec
type Action interface {
	isMissionSpecAction()
	DeepCopyAction() Action
}

// ChargeAction of MissionSpec.Actions
type ChargeAction struct {
	Charge Charge `json:"charge"`
}

func (*ChargeAction) isMissionSpecAction() {}

// DeepCopyAction represents the deepcopy method of the Action interface
func (a *ChargeAction) DeepCopyAction() Action {
	return a.DeepCopy()
}

// Charge structure of corresponding action
type Charge struct {
	ChargerName             string `json:"chargerName"`
	ThresholdBatteryPercent int    `json:"thresholdBatteryPercent"`
	TargetBatteryPercent    int    `json:"targetBatteryPercent"`
}

// MoveToNamedPositionAction of MissionSpec.Actions
type MoveToNamedPositionAction struct {
	MoveToNamedPosition Target `json:"moveToNamedPosition"`
}

func (*MoveToNamedPositionAction) isMissionSpecAction() {}

// DeepCopyAction represents the deepcopy method of the Action interface
func (a *MoveToNamedPositionAction) DeepCopyAction() Action {
	return a.DeepCopy()
}

// Target structure of corresponding action
type Target struct {
	TargetName string `json:"targetName"`
}

// GetTrolleyAction of MissionSpec.Actions
type GetTrolleyAction struct {
	GetTrolley Dock `json:"getTrolley"`
}

func (*GetTrolleyAction) isMissionSpecAction() {}

// DeepCopyAction represents the deepcopy method of the Action interface
func (a *GetTrolleyAction) DeepCopyAction() Action {
	return a.DeepCopy()
}

// ReturnTrolleyAction of MissionSpec.Actions
type ReturnTrolleyAction struct {
	ReturnTrolley Dock `json:"returnTrolley"`
}

func (*ReturnTrolleyAction) isMissionSpecAction() {}

// DeepCopyAction represents the deepcopy method of the Action interface
func (a *ReturnTrolleyAction) DeepCopyAction() Action {
	return a.DeepCopy()
}

// Dock structure of corresponding action
type Dock struct {
	DockName string `json:"dockName"`
}

// ActiveAction represents the ActiveAction of a Mission
type ActiveAction struct {
	Status ActiveActionStatus `json:"status,omitempty"`
}

// ActiveActionStatus describes the status of ActiveAction
type ActiveActionStatus string

// Values for ActiveActionStatus
const (
	ActiveActionSpace   ActiveActionStatus = ""
	ActiveActionMoving  ActiveActionStatus = "MOVING"
	ActiveActionDocking ActiveActionStatus = "DOCKING"
)

// MissionStatusStatus describes the status of a Mission
type MissionStatusStatus string

// Values for MissionStatusStatus
const (
	// initial state
	MissionStatusCreated MissionStatusStatus = "CREATED"
	// mission has been validated on
	MissionStatusAccepted MissionStatusStatus = "ACCEPTED"
	// active state (processing)
	MissionStatusRunning MissionStatusStatus = "RUNNING"
	// terminal states
	MissionStatusSucceeded MissionStatusStatus = "SUCCEEDED"
	MissionStatusCanceled  MissionStatusStatus = "CANCELED"
	MissionStatusFailed    MissionStatusStatus = "FAILED"
)
