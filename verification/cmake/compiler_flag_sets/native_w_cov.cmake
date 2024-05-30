#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#

#
# Enable code coverage instrumentation for C and C++ code
#

include(${CMAKE_CURRENT_LIST_DIR}/common.cmake)

add_compile_options(
        "-fprofile-arcs"
        "-ftest-coverage"
)

add_link_options(
        "-fprofile-arcs"
        "-ftest-coverage"
)
