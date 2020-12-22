module github.com/SAP/ewm-cloud-robotics/go/cmd/order-auctioneer

go 1.15

require (
	github.com/SAP/ewm-cloud-robotics/go/pkg/apis v0.0.0
	github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig v0.0.0
	github.com/SAP/ewm-cloud-robotics/go/pkg/zerologr v0.0.0
	github.com/googlecloudrobotics/core v0.0.0-20200626124521-e2d1b816f510
	github.com/pkg/errors v0.9.1
	k8s.io/apimachinery v0.20.1
	k8s.io/client-go v0.20.1
	sigs.k8s.io/controller-runtime v0.7.0
)

replace (
	github.com/SAP/ewm-cloud-robotics/go/pkg/apis => ../../pkg/apis
	github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig => ../../pkg/zerologconfig
	github.com/SAP/ewm-cloud-robotics/go/pkg/zerologr => ../../pkg/zerologr
)
