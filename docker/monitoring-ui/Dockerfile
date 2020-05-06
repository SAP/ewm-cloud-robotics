###############################################################################
# STEP 1 build executable binary
FROM golang:1.14-alpine as builder
# Install SSL ca certificates
RUN apk update && apk add git && apk add ca-certificates && apk add wget && apk add unzip
# Build OpenUI5 SDK
RUN mkdir -p /openui5-sdk
RUN wget https://github.com/SAP/openui5/releases/download/1.75.0/openui5-runtime-1.75.0.zip -P /openui5-sdk
RUN unzip -o /openui5-sdk/openui5-runtime-1.75.0.zip -d /openui5-sdk
# Build Go app
COPY ./go/pkg/zerologconfig $GOPATH/src/pkg/zerologconfig
COPY ./go/cmd/nginx-odata-auth $GOPATH/src/cmd/nginx-odata-auth
WORKDIR $GOPATH/src/cmd/nginx-odata-auth
# Build the binary
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /go/bin/nginx-odata-auth
###############################################################################
# STEP 2 nginx image
FROM nginx:1.17-alpine
# Install SSL ca certificates
RUN apk update && apk add ca-certificates
# Copy openui5 resources
COPY --from=builder /openui5-sdk/resources /app/openui5-resources
# Prepare nginx configuration environment
RUN mkdir -p /cmd && mkdir -p /odata && touch /odata/location.conf
# Copy Go static executable
COPY --from=builder /go/bin/nginx-odata-auth /cmd/nginx-odata-auth
RUN chmod +x /cmd/nginx-odata-auth
# Copy openui5 app
COPY docker/monitoring-ui/app /app

ENTRYPOINT ["/cmd/nginx-odata-auth"]