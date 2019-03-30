#
# Builds a docker image to use for tox runs.
#
FROM ubuntu:18.04

VOLUME /pydsdlgen

WORKDIR /pydsdlgen

COPY provision.sh /

RUN /provision.sh
