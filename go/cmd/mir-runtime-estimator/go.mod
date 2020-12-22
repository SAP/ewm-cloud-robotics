module github.com/SAP/ewm-cloud-robotics/go/cmd/mir-runtime-estimator

go 1.15

require (
	github.com/SAP/ewm-cloud-robotics/go/pkg/apis v0.0.0
	github.com/SAP/ewm-cloud-robotics/go/pkg/client v0.0.0
	github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface v0.0.0
	github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig v0.0.0
	github.com/pkg/errors v0.9.1
	k8s.io/apimachinery v0.20.1
	k8s.io/client-go v0.20.1
)

replace (
	github.com/SAP/ewm-cloud-robotics/go/pkg/apis => ../../pkg/apis
	github.com/SAP/ewm-cloud-robotics/go/pkg/client => ../../pkg/client
	github.com/SAP/ewm-cloud-robotics/go/pkg/mir-interface => ../../pkg/mir-interface
	github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig => ../../pkg/zerologconfig
)
