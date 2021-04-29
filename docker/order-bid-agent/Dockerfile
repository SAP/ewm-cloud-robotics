###############################################################################
# STEP 1 build executable binary
FROM golang:1.15-alpine as builder
# Install SSL ca certificates
RUN apk add --no-cache git ca-certificates
# Build Go app
COPY ./go/pkg/zerologconfig $GOPATH/src/pkg/zerologconfig
COPY ./go/pkg/zerologr $GOPATH/src/pkg/zerologr
COPY ./go/pkg/apis $GOPATH/src/pkg/apis
COPY ./go/cmd/order-bid-agent $GOPATH/src/cmd/order-bid-agent
WORKDIR $GOPATH/src/cmd/order-bid-agent
# Run tests
RUN CGO_ENABLED=0 GOOS=linux go test -v
# Build the binary
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /go/bin/order-bid-agent
###############################################################################
# STEP 2 nginx image
FROM alpine:latest
# Install SSL ca certificates
RUN apk add --no-cache ca-certificates
# Copy Go static executable
COPY --from=builder /go/bin/order-bid-agent /cmd/order-bid-agent
RUN chmod +x /cmd/order-bid-agent

ENTRYPOINT ["/cmd/order-bid-agent"]