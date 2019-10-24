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

pushd verification/cpp
if [ ! -d build ]; then
    mkdir build
fi
cd build
cmake -DNUNAVUT_CPP_FLAG_SET=linux -DVIRTUALENV_OUTPUT="$PWD/.pyenv" ..
cmake --build . --target all -- -j4
cmake --build . --target cov_all
