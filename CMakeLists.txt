#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
# This top-level CMakeLists.txt is added for symmetry with the python environment. All C/C++ build
# for testing Nunavut is located under the verification folder.

cmake_minimum_required(VERSION 3.20)

project(nunavut)

add_subdirectory("verification")
