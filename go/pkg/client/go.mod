module github.com/SAP/ewm-cloud-robotics/go/pkg/client

go 1.15

require (
	github.com/SAP/ewm-cloud-robotics/go/pkg/apis v0.0.0
	k8s.io/apimachinery v0.20.6
	k8s.io/client-go v0.20.6
)

replace github.com/SAP/ewm-cloud-robotics/go/pkg/apis => ../../pkg/apis
