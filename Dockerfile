##
## Copyright (c) 2022 SAP SE or an SAP affiliate company. All rights reserved.
##
## This file is part of ewm-cloud-robotics
## (see https://github.com/SAP/ewm-cloud-robotics).
##
## This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/main/LICENSE)
##

# Base build image image containing packages required in all apps
FROM python:3.9-slim as python_base

COPY ./python-modules /python-modules
WORKDIR /python-modules

RUN python3 -m venv /app
ENV PATH="/app/bin:$PATH"

RUN pip3 install --no-cache-dir ./k8scrhandler ./robcoewmtypes && \
    python3 -c "import k8scrhandler; import robcoewmtypes"

# Base golang image containing all go applications
FROM golang:1.22 AS go_builder

ARG SKIP_TESTS=false
# Copy go code
COPY . /code

WORKDIR /code
# Run all unit tests unless SKIP_TESTS is true
RUN if [ "$SKIP_TESTS" = "false" ] ; then \
      echo "commencing tests..." && \
      go test ./go/pkg/... ./go/cmd/... ; \
    elif [ "$SKIP_TESTS" = "true" ] ; then \
      echo "unit tests skipped." ; \
    else \
      echo "SKIP_TESTS must be either 'true' or 'false'. Your input: SKIP_TESTS='$SKIP_TESTS'." && \
      exit 95 ; \
    fi
# Build go executables into binaries
RUN mkdir /build && GOBIN=/build \
    GO111MODULE=on CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go install -a ./...


FROM ubuntu:latest as openui5_builder
# Install SSL ca certificates
RUN apt -qq update && apt -qq install -y unzip wget

# Unpack OpenUI5 SDK
RUN mkdir -p /openui5-sdk
RUN wget https://github.com/SAP/openui5/releases/download/1.84.3/openui5-runtime-1.84.3.zip -P /openui5-sdk
RUN unzip -o /openui5-sdk/openui5-runtime-1.84.3.zip -d /openui5-sdk

# Build ewm-sim
FROM node:lts-alpine AS ewm-sim-builder

RUN apk add --no-cache python3 make g++

WORKDIR /usr/src/app
COPY /nodejs/ewm-sim/package*.json /usr/src/app/
RUN npm install --production

# Build dumm-mission-controller
FROM python_base as dummy-mission-controller-builder

RUN pip3 install --no-cache-dir ./dummycontroller && \
    python3 -c "import dummycontroller"

# Build fetch-mission-controller
FROM python_base as fetch-mission-controller-builder
RUN pip3 install --no-cache-dir ./fetchcontroller && \
    python3 -c "import fetchcontroller"

# Build mir-mission-controller
FROM python_base as mir-mission-controller-builder
RUN pip3 install --no-cache-dir ./mircontroller && \
    python3 -c "import mircontroller"

# Build order-manager
FROM python_base as order-manager-builder
RUN pip3 install --no-cache-dir ./robcoewminterface ./robcoewmordermanager && \
    python3 -c "import robcoewminterface; import robcoewmordermanager"

# Build robot-configurator
FROM python_base as robot-configurator-builder
RUN pip3 install --no-cache-dir ./robcoewminterface ./robcoewmrobotconfigurator && \
    python3 -c "import robcoewminterface; import robcoewmrobotconfigurator"

# Build robot-controller
FROM python_base as robot-controller-builder
RUN pip3 install --no-cache-dir ./robcoewmrobotcontroller && \
    python3 -c "import robcoewmrobotcontroller"

# Executable container bases
# --------------------------
FROM python:3.9-slim as python_runner

STOPSIGNAL SIGTERM
RUN adduser --disabled-password --gecos "" appuser
USER appuser
ENV PATH="/app/bin:$PATH"

FROM alpine:3.15 AS ssl_runner
# Install SSL ca certificates
RUN apk add --no-cache ca-certificates
# Create user to be used in executable containers
# Add a non-root user matching the nonroot user from the main container
RUN addgroup -g 65532 -S nonroot && adduser -u 65532 -S nonroot -G nonroot
# Set the uid as an integer for compatibility with runAsNonRoot in Kubernetes
USER 65532

# Executables
# -----------------

FROM python_runner as dummy-mission-controller
COPY --from=dummy-mission-controller-builder /app /app
ENTRYPOINT ["python3", "-m", "dummycontroller"]

FROM python_runner as fetch-mission-controller
COPY --from=fetch-mission-controller-builder /app /app
ENTRYPOINT ["python3", "-m", "fetchcontroller"]

FROM python_runner as mir-mission-controller
COPY --from=mir-mission-controller-builder /app /app
ENTRYPOINT ["python3", "-m", "mircontroller"]

FROM python_runner as order-manager
COPY --from=order-manager-builder /app /app
ENTRYPOINT ["python3", "-m", "robcoewmordermanager"]

FROM python_runner as robot-configurator
COPY --from=robot-configurator-builder /app /app
ENTRYPOINT ["python3", "-m", "robcoewmrobotconfigurator"]

FROM python_runner as robot-controller
COPY --from=robot-controller-builder /app /app
ENTRYPOINT ["python3", "-m", "robcoewmrobotcontroller"]

FROM ssl_runner AS order-auctioneer
WORKDIR /
COPY --from=go_builder /build/order-auctioneer /order-auctioneer
ENTRYPOINT [ "./order-auctioneer" ]

FROM ssl_runner AS order-bid-agent
WORKDIR /
COPY --from=go_builder /build/order-bid-agent /order-bid-agent
ENTRYPOINT [ "./order-bid-agent" ]

FROM ssl_runner AS mir-travel-time-calculator
WORKDIR /
COPY --from=go_builder /build/mir-travel-time-calculator /mir-travel-time-calculator
ENTRYPOINT [ "./mir-travel-time-calculator" ]

FROM nginx:1.25-alpine as monitoring-ui
WORKDIR /
# Install SSL ca certificates
RUN apk add --no-cache ca-certificates
# Copy openui5 resources
COPY --from=openui5_builder /openui5-sdk/resources /app/openui5-resources
# Prepare nginx configuration environment
RUN mkdir -p /odata && touch /odata/location.conf
# Copy Go static executable
COPY --from=go_builder /build/nginx-odata-auth /nginx-odata-auth
# Copy openui5 app
COPY openui5/monitoring-ui /app
ENTRYPOINT ["./nginx-odata-auth"]

FROM node:lts-alpine as ewm-sim
WORKDIR /usr/src/app
COPY /nodejs/ewm-sim /usr/src/app
COPY --from=ewm-sim-builder /usr/src/app/node_modules /usr/src/app/node_modules

EXPOSE 8080
CMD [ "npm", "start" ]