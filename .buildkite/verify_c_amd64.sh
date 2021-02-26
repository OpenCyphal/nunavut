#!/bin/bash

set -o errexit
cd "${0%/*}/.."

function run()
{
    .buildkite/verify.py --verbose --force --language c $*
}

run  --endianness little  --platform native64  --build-type Debug
run  --endianness little  --platform native64  --build-type Release
run  --endianness little  --platform native64  --build-type MinSizeRel  --disable-asserts
run  --endianness little  --platform native64  --build-type Debug       --enable-ovr-var-array
run  --endianness little  --platform native64  --build-type Release     --enable-ovr-var-array
run  --endianness little  --platform native64  --build-type MinSizeRel  --enable-ovr-var-array
