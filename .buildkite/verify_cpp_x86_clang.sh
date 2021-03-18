#!/bin/bash

set -o errexit
cd "${0%/*}/.."

function run()
{
    .buildkite/verify.py --verbose --force --language cpp --platform native32 --toolchain-family clang --no-coverage $*
}

run  --endianness any --build-type Debug
run  --endianness any --build-type Release
run  --endianness any --build-type MinSizeRel  --disable-asserts
run  --endianness any --build-type Debug       --enable-ovr-var-array
run  --endianness any --build-type Release     --enable-ovr-var-array
run  --endianness any --build-type MinSizeRel  --enable-ovr-var-array
