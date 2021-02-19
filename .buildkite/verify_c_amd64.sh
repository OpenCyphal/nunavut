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
run  --endianness little  --platform native64  --build-type Debug       --enable-override-variable-array-capacity
run  --endianness little  --platform native64  --build-type Release     --enable-override-variable-array-capacity
run  --endianness little  --platform native64  --build-type MinSizeRel  --enable-override-variable-array-capacity
