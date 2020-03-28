module github.com/SAP/ewm-cloud-robotics/go/cmd/nginx-odata-auth

go 1.14

require (
	github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig v0.0.0
	golang.org/x/oauth2 v0.0.0-20200107190931-bf48bf16ab8d
)

replace github.com/SAP/ewm-cloud-robotics/go/pkg/zerologconfig => ../../pkg/zerologconfig
