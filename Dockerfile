#
# Builds a docker image to use for tox runs.
#
FROM ubuntu:18.04

VOLUME /repo

WORKDIR /repo

COPY provision.sh /

RUN /provision.sh

