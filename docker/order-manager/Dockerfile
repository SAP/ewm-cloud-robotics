# Dockerfile order-manager
# Meant to be build from root directory of repository (!), in order to enable installing local modules,
# due to:
#    "The <src> path must be inside the context of the build; you cannot COPY ../something /something, 
#     because the first step of a docker build is to send the context directory (and subdirectories) 
#     to the docker daemon." - https://docs.docker.com/engine/reference/builder/#copy

FROM python:3.7.4-slim-stretch

RUN pip3 install -U wss_plugin

COPY ./python-modules/k8scrhandler /k8scrhandler
RUN pip3 install ./k8scrhandler
RUN rm -rf /k8scrhandler

COPY ./python-modules/robcoewmtypes /robcoewmtypes
RUN pip3 install ./robcoewmtypes
RUN rm -rf /robcoewmtypes

COPY ./python-modules/robcoewminterface /robcoewminterface
RUN pip3 install ./robcoewminterface
RUN rm -rf /robcoewminterface

COPY ./python-modules/robcoewmordermanager /robcoewmordermanager
RUN pip3 install ./robcoewmordermanager
RUN rm -rf /robcoewmordermanager

## TODO: replace with Volume mapping to ConfigMap & Helm value
# COPY docker/order-manager/cert /cert
# ENV REQUESTS_CA_BUNDLE="/cert/ca.crt"

COPY docker/order-manager/app /app
WORKDIR /app

RUN pip3 install -r ./requirements.txt

STOPSIGNAL SIGTERM
ENTRYPOINT [ "python3", "main.py" ]