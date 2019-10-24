#
# Copyright (C) 2014 Pavel Kirienko <pavel.kirienko@gmail.com>
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

cmake_minimum_required(VERSION 3.6.0)

project(nunavut_verification CXX)

include(${CMAKE_SOURCE_DIR}/cmake/utils.cmake)


# +---------------------------------------------------------------------------+
# | GLOBAL DEFINITIONS
# +---------------------------------------------------------------------------+

if (NOT DEFINED NUNAVUT_PROJECT_ROOT)
    get_filename_component(NUNAVUT_PROJECT_ROOT
                           "${CMAKE_SOURCE_DIR}/../../"
                           REALPATH BASE_DIR
                           "${CMAKE_BINARY_DIR}")
    message(STATUS "Setting NUNAVUT_PROJECT_ROOT = ${NUNAVUT_PROJECT_ROOT}")
else()
    message(STATUS "Using ${NUNAVUT_PROJECT_ROOT} for NUNAVUT_PROJECT_ROOT")
endif()

if (NOT DEFINED NUNAVUT_SUBMODULES_ROOT)
    set(NUNAVUT_SUBMODULES_ROOT "${NUNAVUT_PROJECT_ROOT}/submodules")
    message(STATUS "Setting NUNAVUT_SUBMODULES_ROOT = ${NUNAVUT_SUBMODULES_ROOT}")
else()
    message(STATUS "Using ${NUNAVUT_SUBMODULES_ROOT} for NUNAVUT_SUBMODULES_ROOT")
endif()

if (NOT DEFINED NUNAVUT_VERIFICATION_CPP_ROOT)
    set(NUNAVUT_VERIFICATION_CPP_ROOT "${NUNAVUT_PROJECT_ROOT}/verification/cpp")
    message(STATUS "Setting NUNAVUT_VERIFICATION_CPP_ROOT = ${NUNAVUT_VERIFICATION_CPP_ROOT}")
else()
    message(STATUS "Using ${NUNAVUT_VERIFICATION_CPP_ROOT} for NUNAVUT_VERIFICATION_CPP_ROOT")
endif()

if(NOT NUNAVUT_CPP_FLAG_SET)
    message(STATUS "NUNAVUT_CPP_FLAG_SET was not defined. Setting to \"native\" as a default")
    set(NUNAVUT_CPP_FLAG_SET ${CMAKE_SOURCE_DIR}/cmake/compiler_flag_sets/native.cmake)
else()
    set(NUNAVUT_CPP_FLAG_SET ${CMAKE_SOURCE_DIR}/cmake/compiler_flag_sets/${NUNAVUT_CPP_FLAG_SET}.cmake)
endif()

#
# Tell cmake where to find our custom scripts.
#
set(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake/modules")

#
# All generated source can be found under this directory.
#
set(NUNAVUT_GENERATED_ROOT ${CMAKE_CURRENT_BINARY_DIR}/generated)

#
# All test binaries and reports will be created under this directory.
#
set(NUNAVUT_VERIFICATIONS_BINARY_DIR ${CMAKE_CURRENT_BINARY_DIR}/suite)

#
# Write a README to create the tests folder.
#
file(WRITE ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/README.txt
     "All test binaries and output will appear under here.")


# +---------------------------------------------------------------------------+
# | BUILD ENVIRONMENT
# +---------------------------------------------------------------------------+

#
# We generate coverage reports. Please look at them (It wasn't easy to get this to work).
#
find_package(lcov REQUIRED)

#
# We need python, of course.
#
find_package(python3 REQUIRED)

#
# We need virtualenv to enable a reproducable python environment.
#
find_package(virtualenv REQUIRED)

#
# Install Nunavut into our local environment.
#
execute_process(COMMAND ${PIP} --isolated --disable-pip-version-check install --editable ${NUNAVUT_PROJECT_ROOT}
                WORKING_DIRECTORY ${NUNAVUT_PROJECT_ROOT})


# +---------------------------------------------------------------------------+
# | SOURCE GENERATION
# +---------------------------------------------------------------------------+
#
# We require googletest to run the verification suite.
#
find_package(gtest REQUIRED)

#
# Make sure nnvg was installed correctly.
#
find_package(nnvg REQUIRED)

#
# Generate all types defined in the UAVCAN v1 public_regulated_data_types set.
#
create_dsdl_target(dsdl-regulated
                   ${NUNAVUT_GENERATED_ROOT}
                   ${NUNAVUT_SUBMODULES_ROOT}/public_regulated_data_types/uavcan
                   ON)


# +---------------------------------------------------------------------------+
# | FLAG SETS
# +---------------------------------------------------------------------------+
#
# Load all our compile flag sets into the appropriate places.
#
apply_flag_set(${NUNAVUT_CPP_FLAG_SET})


# +---------------------------------------------------------------------------+
# | VERIFICATION SUITE
# +---------------------------------------------------------------------------+
#   We generate individual test binaires so we can record which test generated
#   what coverage. We also allow test authors to generate coverage reports for
#   just one test allowing for faster iteration.
file(GLOB NATIVE_TESTS
     LIST_DIRECTORIES false
     RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
     ${CMAKE_CURRENT_SOURCE_DIR}/suite/test_*.cpp
)

add_custom_target(
     lcov_zero
     ${LCOV}
          ${NUNAVUT_GOV_TOOL_ARG}
          --zerocounters
          --directory ${CMAKE_CURRENT_BINARY_DIR}
     COMMENT "Resetting coverage counters."
)

set(ALL_TESTS "")
set(ALL_TESTS_WITH_LCOV "")
set(ALL_TEST_COVERAGE "")

foreach(NATIVE_TEST ${NATIVE_TESTS})
    get_filename_component(NATIVE_TEST_NAME ${NATIVE_TEST} NAME_WE)
    define_native_unit_test(${NATIVE_TEST_NAME} ${NATIVE_TEST} ${NUNAVUT_VERIFICATIONS_BINARY_DIR})
    define_native_test_run(${NATIVE_TEST_NAME} ${NUNAVUT_VERIFICATIONS_BINARY_DIR})
    define_native_test_run_with_lcov(${NATIVE_TEST_NAME} ${NUNAVUT_VERIFICATIONS_BINARY_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/\\*)
    define_natve_test_coverage(${NATIVE_TEST_NAME} ${NUNAVUT_VERIFICATIONS_BINARY_DIR})
    list(APPEND ALL_TESTS "run_${NATIVE_TEST_NAME}")
    list(APPEND ALL_TESTS_WITH_LCOV "run_${NATIVE_TEST_NAME}_with_lcov")
    list(APPEND ALL_TEST_COVERAGE "--add-tracefile")
    list(APPEND ALL_TEST_COVERAGE "${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.${NATIVE_TEST_NAME}.filtered.info")
endforeach()

# +---------------------------------------------------------------------------+
#   Finally, we setup an overall report. the coverage.info should be uploaded
#   to a coverage reporting service as part of the CI pipeline.

add_custom_command(
     OUTPUT ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.all.info
     COMMAND
          ${LCOV}
               ${NUNAVUT_GOV_TOOL_ARG}
               --rc lcov_branch_coverage=1
               ${ALL_TEST_COVERAGE}
               --output-file ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.all.info
     DEPENDS ${ALL_TESTS_WITH_LCOV}
)

add_custom_command(
     OUTPUT ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.info
     COMMAND
          ${LCOV}
               ${NUNAVUT_GOV_TOOL_ARG}
               --rc lcov_branch_coverage=1
               --extract ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.all.info
                         ${NUNAVUT_PROJECT_ROOT}/\\*
               --output-file ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.info
     DEPENDS ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.all.info
)

add_custom_target(
     cov_info
     DEPENDS ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.info
)

add_custom_target(
     cov_all
     ${GENHTML} --title "${PROJECT_NAME} native test coverage"
          --output-directory ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage/all
          --demangle-cpp
          --sort
          --num-spaces 4
          --function-coverage
          --branch-coverage
          --legend
          --highlight
          --show-details
          ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.info
     DEPENDS ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.info
     COMMENT "Build and run all tests and generate an overall html coverage report."
)

add_custom_target(
     test_all
     DEPENDS
          ${ALL_TESTS}
)
