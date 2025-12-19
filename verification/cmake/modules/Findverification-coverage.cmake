#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
# This module finds the LLVM coverage tools required for source-based code coverage.
# It provides llvm-cov and llvm-profdata for generating coverage reports.
#
# See: https://clang.llvm.org/docs/SourceBasedCodeCoverage.html
#

find_program(LLVM_COV llvm-cov)
find_program(LLVM_PROFDATA llvm-profdata)

if(LLVM_COV AND LLVM_PROFDATA)
    message(STATUS "Found LLVM coverage tools:")
    message(STATUS "  llvm-cov:      ${LLVM_COV}")
    message(STATUS "  llvm-profdata: ${LLVM_PROFDATA}")
endif()

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(verification-coverage
    REQUIRED_VARS
        LLVM_COV
        LLVM_PROFDATA
)
