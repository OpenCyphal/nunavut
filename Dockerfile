#
# Builds a docker image to use for tox runs.
#
FROM ubuntu:18.04

VOLUME /repo

WORKDIR /repo

ENV SONAR_SCANNER_VERSION 4.0.0.1744

ENV PATH="sonar-scanner-${SONAR_SCANNER_VERSION}-linux/bin:${PATH}"

ADD sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux.tar.gz /

COPY provision.sh /

RUN /provision.sh

