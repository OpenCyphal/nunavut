#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# C, CXX, LD, and AS flags for native targets.
#

#
# Flags for C and C++
#

include(${CMAKE_CURRENT_LIST_DIR}/common.cmake)

list(APPEND C_AND_CXX_FLAG_SET
        "-fprofile-arcs"
        "-ftest-coverage"
)

list(APPEND C_FLAG_SET ${C_AND_CXX_FLAG_SET})
list(APPEND CXX_FLAG_SET ${C_AND_CXX_FLAG_SET})
list(APPEND ASM_FLAG_SET ${C_AND_CXX_FLAG_SET})
