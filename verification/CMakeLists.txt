#
# Copyright (C) 2014 Pavel Kirienko <pavel.kirienko@gmail.com>
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

cmake_minimum_required(VERSION 3.6.0)

project(nunavut_verification C CXX)

include(${CMAKE_SOURCE_DIR}/cmake/utils.cmake)


# +---------------------------------------------------------------------------+
# | GLOBAL DEFINITIONS
# +---------------------------------------------------------------------------+
if(NOT CMAKE_BUILD_TYPE)
     set(CMAKE_BUILD_TYPE Release)
endif()

message(STATUS "Configuring with CMAKE_BUILD_TYPE=\"${CMAKE_BUILD_TYPE}\"")

if (NOT DEFINED NUNAVUT_PROJECT_ROOT)
    get_filename_component(NUNAVUT_PROJECT_ROOT
                           "${CMAKE_SOURCE_DIR}/../"
                           REALPATH BASE_DIR
                           "${CMAKE_BINARY_DIR}")
    message(STATUS "Setting NUNAVUT_PROJECT_ROOT = ${NUNAVUT_PROJECT_ROOT}")
else()
    message(STATUS "Using ${NUNAVUT_PROJECT_ROOT} for NUNAVUT_PROJECT_ROOT")
endif()

if(DEFINED ENV{NUNAVUT_VERIFICATION_LANG})
     message(STATUS "Getting NUNAVUT_VERIFICATION_LANG from the environment ($ENV{NUNAVUT_VERIFICATION_LANG})")
     set(NUNAVUT_VERIFICATION_LANG "$ENV{NUNAVUT_VERIFICATION_LANG}" CACHE STRING "The Nunavut output language to verify.")
else()
     set(NUNAVUT_VERIFICATION_LANG "unspecified" CACHE STRING "The Nunavut output language to verify.")
endif()

set(NUNAVUT_SUBMODULES_ROOT "${NUNAVUT_PROJECT_ROOT}/submodules" CACHE STRING "The path to git submodules for the project.")

if(NOT DEFINED NUNAVUT_VERIFICATION_TARGET_ENDIANNESS)
     set(NUNAVUT_VERIFICATION_TARGET_ENDIANNESS "any" CACHE STRING "The endianess for the target verification architecture.")
endif()

if(NOT DEFINED NUNAVUT_VERIFICATION_SER_ASSERT)
     set(NUNAVUT_VERIFICATION_SER_ASSERT ON CACHE BOOL "Enable or disable serialization asserts in generated code.")
endif()

if(NOT DEFINED NUNAVUT_VERIFICATION_SER_FP_DISABLE)
     set(NUNAVUT_VERIFICATION_SER_FP_DISABLE OFF CACHE BOOL "Enable or disable floating point support in generated support code.")
endif()

if(NOT DEFINED NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE)
     set(NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE OFF CACHE BOOL "Enable or disable override variable array capacity in generated support code.")
endif()

if (NUNAVUT_VERIFICATION_LANG STREQUAL "cpp")
    set(NUNAVUT_VERIFICATION_ROOT "${CMAKE_SOURCE_DIR}/cpp")
    message(STATUS "NUNAVUT_VERIFICATION_LANG is C++ (${NUNAVUT_VERIFICATION_LANG})")
    message(STATUS "Setting NUNAVUT_VERIFICATION_ROOT = ${NUNAVUT_VERIFICATION_ROOT}")
elseif(NUNAVUT_VERIFICATION_LANG STREQUAL "c")
    set(NUNAVUT_VERIFICATION_ROOT "${CMAKE_SOURCE_DIR}/c")
    message(STATUS "NUNAVUT_VERIFICATION_LANG is C (${NUNAVUT_VERIFICATION_LANG})")
    message(STATUS "Setting NUNAVUT_VERIFICATION_ROOT = ${NUNAVUT_VERIFICATION_ROOT}")
else()
    message(FATAL_ERROR "Unknown or no verification language (${NUNAVUT_VERIFICATION_LANG}). Try cmake -DNUNAVUT_VERIFICATION_LANG:string=[cpp|c]")
endif()

if(DEFINED ENV{NUNAVUT_FLAGSET})
    set(NUNAVUT_FLAGSET "$ENV{NUNAVUT_FLAGSET}")
    message(STATUS "Using ${NUNAVUT_FLAGSET} from environment for NUNAVUT_FLAGSET")
elseif (DEFINED NUNAVUT_FLAGSET)
     message(STATUS "Using override NUNAVUT_FLAGSET = ${NUNAVUT_FLAGSET}")
else()
    set(NUNAVUT_FLAGSET "${CMAKE_SOURCE_DIR}/cmake/compiler_flag_sets/native_w_cov.cmake")
    message(STATUS "Setting (default) NUNAVUT_FLAGSET = ${NUNAVUT_FLAGSET}")
endif()

#
# Tell cmake where to find our custom scripts.
#
set(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake/modules")

#
# All generated source can be found under this directory.
#
set(NUNAVUT_GENERATED_ROOT ${CMAKE_BINARY_DIR}/generated)

#
# All test binaries and reports will be created under this directory.
#
set(NUNAVUT_VERIFICATIONS_BINARY_DIR ${CMAKE_BINARY_DIR}/suite)

#
# Write a README to create the tests folder.
#
file(WRITE ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/README.txt
     "All test binaries and output will appear under here.")

#
# Handle other inputs that translate to compiler flags.
#
set(NUNAVUT_VERIFICATION_EXTRA_COMPILE_FLAGS "")

if(DEFINED NUNAVUT_VERIFICATION_TARGET_PLATFORM)
     if(${NUNAVUT_VERIFICATION_TARGET_PLATFORM} STREQUAL "native32")
          list(APPEND NUNAVUT_VERIFICATION_EXTRA_COMPILE_FLAGS "-m32")
          message(STATUS "Configuring for native32 platform.")
     elseif(${NUNAVUT_VERIFICATION_TARGET_PLATFORM} STREQUAL "native64")
          list(APPEND NUNAVUT_VERIFICATION_EXTRA_COMPILE_FLAGS "-m64")
          message(STATUS "Configuring for native64 platform.")
     else()
          message(FATAL_ERROR "\"${NUNAVUT_VERIFICATION_TARGET_PLATFORM}\" is not a supported value.")
     endif()
endif()

# +---------------------------------------------------------------------------+
# | BUILD ENVIRONMENT
# +---------------------------------------------------------------------------+

#
# We generate coverage reports. Please look at them (It wasn't easy to get this to work).
#
find_package(lcov REQUIRED)
find_package(genhtml REQUIRED)

#
# We need tox to enable a reproducable python environment.
#
find_package(tox REQUIRED)

# +---------------------------------------------------------------------------+
# | SOURCE GENERATION
# +---------------------------------------------------------------------------+

#
# We require googletest to run the verification suite.
#
find_package(gtest REQUIRED)

#
# We also require unity to run c-specific tests as part of the verification suite.
# Configuration docs: https://github.com/ThrowTheSwitch/Unity/blob/master/docs/UnityConfigurationGuide.md
#
find_package(unity REQUIRED)
add_definitions(-DUNITY_SUPPORT_64=1
                -DUNITY_INCLUDE_FLOAT=1
                -DUNITY_INCLUDE_DOUBLE=1)

#
# Make sure nnvg was installed correctly.
#
find_package(nnvg REQUIRED)

#
# Pull in some stuff we need for testing C++
#
find_package(o1heap REQUIRED)

#
# Generate serialization support headers
#
create_dsdl_target(nunavut-support
                   ${NUNAVUT_VERIFICATION_LANG}
                   ${NUNAVUT_GENERATED_ROOT}/${NUNAVUT_VERIFICATION_LANG}
                   ""
                   OFF
                   ${NUNAVUT_VERIFICATION_SER_ASSERT}
                   ${NUNAVUT_VERIFICATION_SER_FP_DISABLE}
                   ${NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE}
                   ON
                   "${NUNAVUT_VERIFICATION_TARGET_ENDIANNESS}"
                   "only")

#
# Generate types for the UAVCAN v1 public_regulated_data_types set.
#
create_dsdl_target(dsdl-regulated
                   ${NUNAVUT_VERIFICATION_LANG}
                   ${NUNAVUT_GENERATED_ROOT}/${NUNAVUT_VERIFICATION_LANG}
                   ${NUNAVUT_SUBMODULES_ROOT}/public_regulated_data_types/uavcan
                   OFF
                   ${NUNAVUT_VERIFICATION_SER_ASSERT}
                   ${NUNAVUT_VERIFICATION_SER_FP_DISABLE}
                   ${NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE}
                   ON
                   "${NUNAVUT_VERIFICATION_TARGET_ENDIANNESS}"
                   "never")

add_dependencies(dsdl-regulated nunavut-support)

#
# Generate additional types for verification
#
create_dsdl_target(dsdl-test
                   ${NUNAVUT_VERIFICATION_LANG}
                   ${NUNAVUT_GENERATED_ROOT}/${NUNAVUT_VERIFICATION_LANG}
                   ${CMAKE_SOURCE_DIR}/nunavut_test_types/test0/regulated
                   OFF
                   ${NUNAVUT_VERIFICATION_SER_ASSERT}
                   ${NUNAVUT_VERIFICATION_SER_FP_DISABLE}
                   ${NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE}
                   ON
                   "${NUNAVUT_VERIFICATION_TARGET_ENDIANNESS}"
                   "never"
                   ${NUNAVUT_SUBMODULES_ROOT}/public_regulated_data_types/uavcan)

add_dependencies(dsdl-test nunavut-support)

# +---------------------------------------------------------------------------+
# | FLAG SETS
# +---------------------------------------------------------------------------+
#
# Load all our compile flag sets into the appropriate places.
#
apply_flag_set("${NUNAVUT_FLAGSET}")


# +---------------------------------------------------------------------------+
# | VERIFICATION SUITE
# +---------------------------------------------------------------------------+
#   We generate individual test binaires so we can record which test generated
#   what coverage. We also allow test authors to generate coverage reports for
#   just one test allowing for faster iteration.
file(GLOB NATIVE_TESTS_CPP
     LIST_DIRECTORIES false
     RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
     ${NUNAVUT_VERIFICATION_ROOT}/suite/test_*.cpp
)

file(GLOB NATIVE_TESTS_C
     LIST_DIRECTORIES false
     RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
     ${NUNAVUT_VERIFICATION_ROOT}/suite/test_*.c
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

foreach(NATIVE_TEST ${NATIVE_TESTS_CPP})
    get_filename_component(NATIVE_TEST_NAME ${NATIVE_TEST} NAME_WE)
    set(${NATIVE_TEST_NAME}_CPP_EXTRA_FLAGS, "")
    list(APPEND ${NATIVE_TEST_NAME}_CPP_EXTRA_FLAGS ${NUNAVUT_VERIFICATION_EXTRA_COMPILE_FLAGS})

    if(NUNAVUT_VERIFICATION_LANG STREQUAL "c")
          #
          # If we are testing C headers with C++ tests we have to disable
          # certain checks to allow the inline code to compile without
          # warnings.
          #
          list(APPEND ${NATIVE_TEST_NAME}_CPP_EXTRA_FLAGS "-Wno-old-style-cast")
    endif()

    define_native_unit_test("gtest"
                            ${NATIVE_TEST_NAME}
                            ${NATIVE_TEST}
                            ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
                            "${${NATIVE_TEST_NAME}_CPP_EXTRA_FLAGS}"
                            dsdl-regulated
                            dsdl-test
                            o1heap)
    define_native_test_run(${NATIVE_TEST_NAME} ${NUNAVUT_VERIFICATIONS_BINARY_DIR})
    define_native_test_run_with_lcov(${NATIVE_TEST_NAME} ${NUNAVUT_VERIFICATIONS_BINARY_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/\\*)
    define_natve_test_coverage(${NATIVE_TEST_NAME} ${NUNAVUT_VERIFICATIONS_BINARY_DIR})
    list(APPEND ALL_TESTS "run_${NATIVE_TEST_NAME}")
    list(APPEND ALL_TESTS_WITH_LCOV "run_${NATIVE_TEST_NAME}_with_lcov")
    list(APPEND ALL_TEST_COVERAGE "--add-tracefile")
    list(APPEND ALL_TEST_COVERAGE "${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.${NATIVE_TEST_NAME}.filtered.info")
endforeach()

foreach(NATIVE_TEST ${NATIVE_TESTS_C})
    get_filename_component(NATIVE_TEST_NAME ${NATIVE_TEST} NAME_WE)
    set(${NATIVE_TEST_NAME}_C_EXTRA_FLAGS, "")
    list(APPEND ${NATIVE_TEST_NAME}_C_EXTRA_FLAGS ${NUNAVUT_VERIFICATION_EXTRA_COMPILE_FLAGS})

    define_native_unit_test("unity"
                            ${NATIVE_TEST_NAME}
                            ${NATIVE_TEST}
                            ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
                            "${${NATIVE_TEST_NAME}_C_EXTRA_FLAGS}"
                            dsdl-regulated
                            dsdl-test)
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

add_custom_target(
     cov_all_archive
     COMMAND
     ${CMAKE_COMMAND}
          -E tar
          "cfv"
          "coverage_all.zip"
          --format=zip
          "${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage/all"
     DEPENDS
          cov_all
     BYPRODUCTS
          "${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage_all.zip"
     COMMENT
          "Build and run all tests and generate an overall html coverage report as a zip archive."
)
