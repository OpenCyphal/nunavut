#!/bin/bash

set -o errexit
cd "${0%/*}/.."

function run()
{
    .buildkite/verify.py --verbose --remove-first --force --language c --platform native64 --toolchain-family clang --no-coverage $*
}

run  --endianness little --build-type Debug
run  --endianness little --build-type Release
run  --endianness little --build-type MinSizeRel  --disable-asserts
run  --endianness little --build-type Debug       --enable-ovr-var-array
run  --endianness little --build-type Release     --enable-ovr-var-array
run  --endianness little --build-type MinSizeRel  --enable-ovr-var-array
