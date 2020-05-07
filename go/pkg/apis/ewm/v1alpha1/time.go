// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package v1alpha1

import (
	"encoding/json"
	"strconv"
	"time"

	fuzz "github.com/google/gofuzz"
)

// This follows the approach of Time implementation in k8s.io/apimachinery/pkg/apis/meta/v1 for time format used in EWM
// It is in integer format follow this schema int(YYYYMMDDhhmmss) used for properties like Lsd (Latest start date)

// EwmTime is a timp stamp from EWM YYYYMMDDhhmmss. Const according to layout definition of time.Time.
const EwmTime = "20060102150405"

// Time is a wrapper around time.Time which supports correct
// marshaling to YAML and JSON.  Wrappers are provided for many
// of the factory methods that the time package offers.
//
// +protobuf.options.marshal=false
// +protobuf.as=Timestamp
// +protobuf.options.(gogoproto.goproto_stringer)=false
type Time struct {
	time.Time `protobuf:"-"`
}

// DeepCopyInto creates a deep-copy of the Time value.  The underlying time.Time
// type is effectively immutable in the time API, so it is safe to
// copy-by-assign, despite the presence of (unexported) Pointer fields.
func (t *Time) DeepCopyInto(out *Time) {
	*out = *t
}

// NewTime returns a wrapped instance of the provided time
func NewTime(time time.Time) Time {
	return Time{time}
}

// Date returns the Time corresponding to the supplied parameters
// by wrapping time.Date.
func Date(year int, month time.Month, day, hour, min, sec, nsec int, loc *time.Location) Time {
	return Time{time.Date(year, month, day, hour, min, sec, nsec, loc)}
}

// Now returns the current local time.
func Now() Time {
	return Time{time.Now()}
}

// IsZero returns true if the value is nil or time is zero.
func (t *Time) IsZero() bool {
	if t == nil {
		return true
	}
	return t.Time.IsZero()
}

// Before reports whether the time instant t is before u.
func (t *Time) Before(u *Time) bool {
	if t != nil && u != nil {
		return t.Time.Before(u.Time)
	}
	return false
}

// Equal reports whether the time instant t is equal to u.
func (t *Time) Equal(u *Time) bool {
	if t == nil && u == nil {
		return true
	}
	if t != nil && u != nil {
		return t.Time.Equal(u.Time)
	}
	return false
}

// Unix returns the local time corresponding to the given Unix time
// by wrapping time.Unix.
func Unix(sec int64, nsec int64) Time {
	return Time{time.Unix(sec, nsec)}
}

// Rfc3339Copy returns a copy of the Time at second-level precision.
func (t Time) Rfc3339Copy() Time {
	copied, _ := time.Parse(time.RFC3339, t.Format(time.RFC3339))
	return Time{copied}
}

// UnmarshalJSON implements the json.Unmarshaller interface.
func (t *Time) UnmarshalJSON(b []byte) error {
	// Ignore null, like in the main JSON package.
	if string(b) == "null" || string(b) == `""` {
		t.Time = time.Time{}
		return nil
	}

	var integer int
	err := json.Unmarshal(b, &integer)
	if err != nil {
		return err
	}

	if integer == 0 {
		t.Time = time.Time{}
		return nil
	}

	// str has format YYYYMMDDhhmmss now, which is EwmTime
	str := strconv.Itoa(integer)

	pt, err := time.Parse(EwmTime, str)
	if err != nil {
		return err
	}

	t.Time = pt.Local()
	return nil
}

// UnmarshalQueryParameter converts from a URL query parameter value to an object
func (t *Time) UnmarshalQueryParameter(str string) error {
	if len(str) == 0 || str == "0" {
		t.Time = time.Time{}
		return nil
	}

	// str has format YYYYMMDDhhmmss now, which is EwmTime
	pt, err := time.Parse(EwmTime, str)
	if err != nil {
		return err
	}

	t.Time = pt.Local()
	return nil
}

// MarshalJSON implements the json.Marshaler interface.
func (t Time) MarshalJSON() ([]byte, error) {
	if t.IsZero() {
		// Encode unset/nil objects as 0.
		return json.Marshal(0)
	}

	// Type in JSON is integer
	str := t.UTC().Format(EwmTime)
	integer, err := strconv.Atoi(str)

	if err != nil {
		return nil, err
	}

	return json.Marshal(integer)
}

// ToUnstructured implements the value.UnstructuredConverter interface.
func (t Time) ToUnstructured() interface{} {
	if t.IsZero() {
		return nil
	}

	str := t.UTC().Format(EwmTime)
	integer, err := strconv.Atoi(str)

	if err != nil {
		return nil
	}
	return integer
}

// OpenAPISchemaType is used by the kube-openapi generator when constructing
// the OpenAPI spec of this type.
//
// See: https://github.com/kubernetes/kube-openapi/tree/master/pkg/generators
func (_ Time) OpenAPISchemaType() []string { return []string{"integer"} }

// OpenAPISchemaFormat is used by the kube-openapi generator when constructing
// the OpenAPI spec of this type.
func (_ Time) OpenAPISchemaFormat() string { return "" }

// MarshalQueryParameter converts to a URL query parameter value
func (t Time) MarshalQueryParameter() (string, error) {
	if t.IsZero() {
		// Encode unset/nil objects as an empty string
		return "0", nil
	}

	return t.UTC().Format(EwmTime), nil
}

// Fuzz satisfies fuzz.Interface.
func (t *Time) Fuzz(c fuzz.Continue) {
	if t == nil {
		return
	}
	// Allow for about 1000 years of randomness.  Leave off nanoseconds
	// because JSON doesn't represent them so they can't round-trip
	// properly.
	t.Time = time.Unix(c.Rand.Int63n(1000*365*24*60*60), 0)
}

var _ fuzz.Interface = &Time{}
