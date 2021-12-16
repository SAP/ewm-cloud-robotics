module github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface

go 1.17

require (
	github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig v0.0.0
	github.com/pkg/errors v0.9.1
)

require github.com/rs/zerolog v1.26.1 // indirect

replace github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig => ../../pkg/zerologconfig
