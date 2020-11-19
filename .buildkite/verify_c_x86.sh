#!/bin/bash

set -o errexit
set -o nounset
set -o xtrace

cd "${0%/*}/.."

function run()
{
    .buildkite/verify.py --verbose --force --language c $*
}

# x86
run  --endianness any     --platform native32  --build-type Debug
run  --endianness any     --platform native32  --build-type Release
run  --endianness any     --platform native32  --build-type MinSizeRel  --disable-asserts

# TODO: ARM
# TODO: a big-endian architecture
# TODO: an 8-bit architecture
