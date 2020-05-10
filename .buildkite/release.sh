#!/usr/bin/env bash
#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# This software is distributed under the terms of the MIT License.
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

if [ -z "${BUILDKITE+xxx}" ]; then
    echo "Not BUILDKITE. Skipping artifact download."
    mkdir -p test/build_native_gcc
else
    buildkite-agent artifact download ".tox/report/tmp/" .
fi

export NUNAVUT_FULL_VERSION=$(grep __version__ src/nunavut/version.py | awk '{print $3}' | sed -E "s/'([0-9]+\.[0-9]+\.[0-9]+)'/\1/g")
export NUNAVUT_MAJOR_MINOR_VERSION=$(echo $NUNAVUT_FULL_VERSION | sed -E "s/([0-9]+\.[0-9]+)\.[0-9]+/\1/g")
tox -e package
tox -e sonar | grep -v "sonar.login"
tox -e upload | grep -v "twine upload"
