// Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
//
// This file is part of ewm-cloud-robotics
// (see https://github.com/SAP/ewm-cloud-robotics).
//
// This file is licensed under the Apache Software License, v. 2 except as noted
// otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
//

package apis

// MirResponse represents data types MiR APIs return in their HTTP body on success
type MirResponse interface {
	MirResponse()
}

// MirRequest represents data types which could be sent to MiR API in POST, PUT, PATCH HTTP body
type MirRequest interface {
	MirRequest()
}

// MirError represents data types MiR APIs return in their HTTP body in error cases
type MirError interface {
	MirError()
}
