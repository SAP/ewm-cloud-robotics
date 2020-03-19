###############################################################################
# STEP 1 build executable binary
FROM golang:alpine as builder
# Install SSL ca certificates
RUN apk update && apk add git && apk add ca-certificates
# Create appuser
RUN adduser -D -g '' appuser
COPY ./go/cmd/nginx-odata-auth $GOPATH/src/
WORKDIR $GOPATH/src/
# build the binary
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /go/bin/main
###############################################################################
# STEP 2 nginx image
FROM nginx

# Prepare nginx configuration environment
RUN mkdir -p /cmd && mkdir -p /odata && touch /odata/location.conf

# Copy certificates and static executable
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /go/bin/main /cmd/nginx-odata-auth
RUN chmod +x /cmd/nginx-odata-auth

# Copy openui5 app
COPY docker/monitoring-ui/app /app

ENTRYPOINT ["/cmd/nginx-odata-auth"]