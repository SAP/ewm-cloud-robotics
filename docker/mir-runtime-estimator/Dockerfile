###############################################################################
# STEP 1 build executable binary
FROM golang:1.15-alpine as builder
# Install SSL ca certificates
RUN apk add --no-cache git ca-certificates
# Build Go app
COPY ./go/pkg/zerologconfig $GOPATH/src/pkg/zerologconfig
COPY ./go/pkg/apis $GOPATH/src/pkg/apis
COPY ./go/pkg/client $GOPATH/src/pkg/client
COPY ./go/pkg/mir-interface $GOPATH/src/pkg/mir-interface
COPY ./go/cmd/mir-runtime-estimator $GOPATH/src/cmd/mir-runtime-estimator
WORKDIR $GOPATH/src/cmd/mir-runtime-estimator
# Build the binary
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /go/bin/mir-runtime-estimator
###############################################################################
# STEP 2 app image
FROM alpine:latest
# Install SSL ca certificates
RUN apk add --no-cache ca-certificates
# Copy Go static executable
COPY --from=builder /go/bin/mir-runtime-estimator /cmd/mir-runtime-estimator
RUN chmod +x /cmd/mir-runtime-estimator

ENTRYPOINT ["/cmd/mir-runtime-estimator"]

# Create & use appuser
RUN adduser -D appuser
USER appuser