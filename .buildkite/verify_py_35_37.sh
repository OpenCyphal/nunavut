#!/bin/bash

set -o errexit
cd "${0%/*}/.."

tox -e py35-test,py35-nnvg
tox -e py36-nnvg
tox -e py37-nnvg
