module github.com/SAP/ewm-cloud-robotics/go/pkg/client

go 1.14

require (
	github.com/SAP/ewm-cloud-robotics/go/pkg/apis v0.0.0
	k8s.io/apimachinery v0.17.5
	k8s.io/client-go v0.17.5
)

replace github.com/SAP/ewm-cloud-robotics/go/pkg/apis => ../../pkg/apis
