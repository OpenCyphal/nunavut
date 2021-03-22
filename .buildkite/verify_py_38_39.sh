#!/bin/bash

set -o errexit
cd "${0%/*}/.."

tox -e lint,mypy,docs
tox -e py38-nnvg
tox -e py39-test,py39-nnvg,py39-doctest,py39-rstdoctest
tox -e noyaml
tox -e report
