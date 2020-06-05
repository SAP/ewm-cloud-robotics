module github.com/SAP/ewm-cloud-robotics/go/pkg/client

go 1.14

require (
	github.com/SAP/ewm-cloud-robotics/go/pkg/apis v0.0.0
	k8s.io/apimachinery v0.18.2
	k8s.io/client-go v0.18.2
)

replace github.com/SAP/ewm-cloud-robotics/go/pkg/apis => ../../pkg/apis
