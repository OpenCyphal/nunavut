#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# C, CXX, LD, and AS flags for native targets.
#

#
# Flags for C and C++
#

include(${CMAKE_SOURCE_DIR}/cmake/compiler_flag_sets/native.cmake)

list(APPEND C_AND_CXX_FLAG_SET
        "-fprofile-arcs"
        "-ftest-coverage"
)
