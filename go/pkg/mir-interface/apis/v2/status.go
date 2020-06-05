// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package v2

// GetStatus represents the result of GET /status endpoint
type GetStatus struct {
	BatteryPercentage           float64              `json:"battery_percentage,omitempty"`
	BatteryTimeRemaining        int64                `json:"battery_time_remaining,omitempty"`
	DistanceToNextTarget        float64              `json:"distance_to_next_target,omitempty"`
	Errors                      []GetStatusErrors    `json:"errors,omitempty"`
	Footprint                   string               `json:"footprint,omitempty"`
	HookStatus                  *GetStatusHookStatus `json:"hook_status,omitempty"`
	JoystickLowSpeedModeEnabled bool                 `json:"joystick_low_speed_mode_enabled,omitempty"`
	JoystickWebSessionID        string               `json:"joystick_web_session_id,omitempty"`
	MapID                       string               `json:"map_id,omitempty"`
	MissionQueueID              int                  `json:"mission_queue_id,omitempty"`
	MissionQueueURL             string               `json:"mission_queue_url,omitempty"`
	MissionText                 string               `json:"mission_text,omitempty"`
	ModeID                      int                  `json:"mode_id,omitempty"`
	ModeKeyState                string               `json:"mode_key_state,omitempty"`
	ModeText                    string               `json:"mode_text,omitempty"`
	Moved                       float64              `json:"moved,omitempty"`
	Position                    *GetStatusPosition   `json:"position,omitempty"`
	RobotModel                  string               `json:"robot_model,omitempty"`
	RobotName                   string               `json:"robot_name,omitempty"`
	SafetySystemMuted           bool                 `json:"safety_system_muted,omitempty"`
	SerialNumber                string               `json:"serial_number,omitempty"`
	SessionID                   string               `json:"session_id,omitempty"`
	StateID                     int                  `json:"state_id,omitempty"`
	StateText                   string               `json:"state_text,omitempty"`
	UnloadedMapChanges          bool                 `json:"unloaded_map_changes,omitempty"`
	Uptime                      int64                `json:"uptime,omitempty"`
	UserPrompt                  *GetStatusUserPrompt `json:"user_prompt,omitempty"`
	Velocity                    *GetStatusVelocity   `json:"velocity,omitempty"`
}

// MirResponse identifies data type as MiR response
func (p *GetStatus) MirResponse() {}

// GetStatusPosition represents the corresponding structure of GET /status endpoint
type GetStatusPosition struct {
	Orientation float64 `json:"orientation,omitempty"`
	X           float64 `json:"x,omitempty"`
	Y           float64 `json:"y,omitempty"`
}

// GetStatusErrors represents an item of GetStatusErrors structure of GET /status endpoint
type GetStatusErrors struct {
	Code        int    `json:"code,omitempty"`
	Description string `json:"description,omitempty"`
	Module      string `json:"module,omitempty"`
}

// GetStatusVelocity represents the corresponding structure of GET /status endpoint
type GetStatusVelocity struct {
	Angular float64 `json:"angular,omitempty"`
	Linear  float64 `json:"linear,omitempty"`
}

// GetStatusUserPrompt represents the corresponding structure of GET /status endpoint
type GetStatusUserPrompt struct {
	GUID      string   `json:"guid,omitempty"`
	Options   []string `json:"options,omitempty"`
	Question  string   `json:"question,omitempty"`
	Timeout   float64  `json:"timeout,omitempty"`
	UserGroup string   `json:"user_group,omitempty"`
}

// GetStatusHookStatus represents the corresponding structure of GET /status endpoint
type GetStatusHookStatus struct {
	Angle        float64                  `json:"angle,omitempty"`
	Available    bool                     `json:"available,omitempty"`
	Braked       bool                     `json:"braked,omitempty"`
	Cart         *GetStatusHookStatusCart `json:"cart,omitempty"`
	CartAttached bool                     `json:"cart_attached,omitempty"`
	Height       float64                  `json:"height,omitempty"`
	Length       float64                  `json:"length,omitempty"`
}

// GetStatusHookStatusCart represents the corresponding structure of GetStatusHookStatus
type GetStatusHookStatusCart struct {
	Height             float64 `json:"height,omitempty"`
	ID                 float64 `json:"id,omitempty"`
	Length             float64 `json:"length,omitempty"`
	OffsetLockedWheels float64 `json:"offset_locked_wheels,omitempty"`
	Width              float64 `json:"width,omitempty"`
}
