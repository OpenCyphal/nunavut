#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#

# Uses the CMake package from an installed Nunavut (#422). See check_installed_package.py.

cmake_minimum_required(VERSION 3.27.0 FATAL_ERROR)

project("Nunavut installed package check" LANGUAGES C)

find_package(Nunavut 3.0 REQUIRED)

add_cyphal_library(
    NAME smoke
    LANGUAGE c
    LANGUAGE_STANDARD c11
    DSDL_FILES ${CMAKE_CURRENT_SOURCE_DIR}/dsdl/smoke/Ping.1.0.dsdl
    DSDL_NAMESPACES ${CMAKE_CURRENT_SOURCE_DIR}/dsdl/smoke
    OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR}/include
    EXPORT_CONFIGURE_MANIFEST ${CMAKE_CURRENT_BINARY_DIR}
    EXPORT_GENERATE_MANIFEST ${CMAKE_CURRENT_BINARY_DIR}
    OUT_LIBRARY_TARGET SMOKE_TYPES
)

add_executable(smoke main.c)
target_link_libraries(smoke PRIVATE ${SMOKE_TYPES})
set_target_properties(smoke PROPERTIES C_STANDARD 11 C_STANDARD_REQUIRED ON)
