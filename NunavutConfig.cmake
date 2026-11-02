#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#

# The Nunavut CMake package lives in the Python package (src/nunavut/cmake) so the wheel ships it. This file lets
# find_package() find it in a source checkout, and tells it to run Nunavut and its submodules from this checkout.
set(_NUNAVUT_SOURCE_CHECKOUT_ROOT "${CMAKE_CURRENT_LIST_DIR}")
include("${CMAKE_CURRENT_LIST_DIR}/src/nunavut/cmake/NunavutConfig.cmake")
