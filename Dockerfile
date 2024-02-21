FROM keppel.eu-de-1.cloud.sap/ccloud-dockerhub-mirror/library/alpine:latest

ARG BININFO_BUILD_DATE BININFO_COMMIT_HASH BININFO_VERSION
LABEL source_repository="https://github.com/sapcc/vrops-exporter" \
  org.opencontainers.image.url="https://github.com/sapcc/vrops-exporter" \
  org.opencontainers.image.created=${BININFO_BUILD_DATE} \
  org.opencontainers.image.revision=${BININFO_COMMIT_HASH} \
  org.opencontainers.image.version=${BININFO_VERSION}

RUN apk --update add python3 openssl ca-certificates bash python3-dev  git py3-pip && \
    apk --update add --virtual build-dependencies libffi-dev openssl-dev libxml2 libxml2-dev libxslt libxslt-dev build-base
RUN apk upgrade -U 
RUN git config --global http.sslVerify false
RUN git clone https://github.com/sapcc/vrops-exporter.git
RUN python3 -m venv /opt/vrops-env
RUN . /opt/vrops-env/bin/activate
ENV PATH /opt/vrops-env/bin:$PATH
RUN pip3 install --upgrade pip
RUN pip3 install --ignore-installed six
RUN pip install --upgrade cffi

ADD . vrops-exporter/
RUN pip3 install --upgrade -r vrops-exporter/requirements.txt
RUN pip3 install --upgrade setuptools

WORKDIR vrops-exporter/
