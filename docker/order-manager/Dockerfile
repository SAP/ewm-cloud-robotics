# Dockerfile order-manager
# Meant to be build from root directory of repository (!), in order to enable installing local modules,
# due to:
#    "The <src> path must be inside the context of the build; you cannot COPY ../something /something, 
#     because the first step of a docker build is to send the context directory (and subdirectories) 
#     to the docker daemon." - https://docs.docker.com/engine/reference/builder/#copy

FROM python:3.9-slim

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

COPY ./python-modules/robcoewmordermanager /robcoewmordermanager
RUN pip3 install /robcoewmordermanager && \
    rm -rf /robcoewmordermanager && \
    python3 -c "import robcoewmordermanager"

STOPSIGNAL SIGTERM
ENTRYPOINT ["python3", "-m", "robcoewmordermanager"]

# Create & use appuser
RUN adduser --disabled-password --gecos "" appuser
USER appuser