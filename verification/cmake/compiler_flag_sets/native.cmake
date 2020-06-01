#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# C, CXX, LD, and AS flags for building verification tests using only
# generic settings.
#
include(${CMAKE_SOURCE_DIR}/cmake/compiler_flag_sets/native_common.cmake)

list(APPEND CXX_FLAG_SET ${C_FLAG_SET})
list(APPEND ASM_FLAG_SET ${C_FLAG_SET})
