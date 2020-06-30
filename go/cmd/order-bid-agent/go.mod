module github.com/SAP/ewm-cloud-robotics/go/cmd/order-bid-agent

go 1.14

require (
	github.com/SAP/ewm-cloud-robotics/go/pkg/apis v0.0.0
	github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig v0.0.0
	github.com/SAP/ewm-cloud-robotics/go/pkg/zerologr v0.0.0
	github.com/pkg/errors v0.9.1
	k8s.io/apimachinery v0.18.2
	k8s.io/client-go v0.18.2
	sigs.k8s.io/controller-runtime v0.6.0
)

replace (
	github.com/SAP/ewm-cloud-robotics/go/pkg/apis => ../../pkg/apis
	github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig => ../../pkg/zerologconfig
	github.com/SAP/ewm-cloud-robotics/go/pkg/zerologr => ../../pkg/zerologr
)
