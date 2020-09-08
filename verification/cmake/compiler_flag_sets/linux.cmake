#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# C, CXX, LD, and AS flags for building verification tests on linux platforms.
#
include(${CMAKE_SOURCE_DIR}/cmake/compiler_flag_sets/native_common.cmake)

list(APPEND C_FLAG_SET "-pthread")
list(APPEND CXX_FLAG_SET "-pthread")
list(APPEND ASM_FLAG_SET "-pthread")
