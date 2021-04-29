# Dockerfile fetch-mission-controller
# Meant to be build from root directory of repository (!), in order to enable installing local modules,
# due to:
#    "The <src> path must be inside the context of the build; you cannot COPY ../something /something, 
#     because the first step of a docker build is to send the context directory (and subdirectories) 
#     to the docker daemon." - https://docs.docker.com/engine/reference/builder/#copy

FROM python:3.8-slim

COPY ./python-modules/k8scrhandler /k8scrhandler
RUN pip3 install /k8scrhandler && \
    rm -rf /k8scrhandler && \
    python3 -c "import k8scrhandler"

COPY ./python-modules/fetchcontroller /fetchcontroller
RUN pip3 install /fetchcontroller && \
    rm -rf /fetchcontroller && \
    python3 -c "import fetchcontroller"

STOPSIGNAL SIGTERM
ENTRYPOINT ["python3", "-m", "fetchcontroller"]