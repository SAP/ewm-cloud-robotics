# Dockerfile robot-configurator
# Meant to be build from root directory of repository (!), in order to enable installing local modules,
# due to:
#    "The <src> path must be inside the context of the build; you cannot COPY ../something /something, 
#     because the first step of a docker build is to send the context directory (and subdirectories) 
#     to the docker daemon." - https://docs.docker.com/engine/reference/builder/#copy

FROM python:3.7.6-slim-stretch

RUN pip3 install -U wss_plugin

COPY ./python-modules/k8scrhandler /k8scrhandler
RUN pip3 install /k8scrhandler && \
    rm -rf /k8scrhandler && \
    python3 -c "import k8scrhandler"

COPY ./python-modules/robcoewmtypes /robcoewmtypes
RUN pip3 install /robcoewmtypes && \
    rm -rf /robcoewmtypes && \
    python3 -c "import robcoewmtypes"

COPY ./python-modules/robcoewminterface /robcoewminterface
RUN pip3 install /robcoewminterface && \
    rm -rf /robcoewminterface && \
    python3 -c "import robcoewminterface"

COPY ./python-modules/robcoewmrobotconfigurator /robcoewmrobotconfigurator
RUN pip3 install /robcoewmrobotconfigurator && \
    rm -rf /robcoewmrobotconfigurator && \
    python3 -c "import robcoewmrobotconfigurator"

## TODO: replace with Volume mapping to ConfigMap & Helm value
# COPY docker/order-manager/cert /cert
# ENV REQUESTS_CA_BUNDLE="/cert/ca.crt"

COPY docker/robot-configurator/app /app
WORKDIR /app

RUN pip3 install -r ./requirements.txt

STOPSIGNAL SIGTERM
ENTRYPOINT [ "python3", "main.py" ]