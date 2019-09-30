#!/usr/bin/env bash
#
# Provisioning script for Ubuntu 18 build environments. This should work with travis.ci
# as well as ubuntu:18.04 docker images or any other standard ubuntu 18.04 operating system.
#

# +----------------------------------------------------------+
# | BASH : Modifying Shell Behaviour
# |    (https://www.gnu.org/software/bash/manual)
# +----------------------------------------------------------+
# Treat unset variables and parameters other than the special
# parameters ‘@’ or ‘*’ as an error when performing parameter
# expansion. An error message will be written to the standard
# error, and a non-interactive shell will exit.
set -o nounset

# Exit immediately if a pipeline returns a non-zero status.
set -o errexit

# If set, the return value of a pipeline is the value of the
# last (rightmost) command to exit with a non-zero status, or
# zero if all commands in the pipeline exit successfully.
set -o pipefail

# +----------------------------------------------------------+
apt-get update
apt-get -y install software-properties-common
apt-get -y install git

# deadsnakes maintains a bunch of python versions for Ubuntu.
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get -y install python3.5
apt-get -y install python3.6
apt-get -y install python3.7
apt-get -y install python3.8
apt-get -y install python3.8-distutils
apt-get -y install python3-pip
pip3 install tox
