#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#

cmake_minimum_required(VERSION 3.22.0)

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

string(TOLOWER ${NUNAVUT_VERIFICATION_LANG} LOCAL_VERIFICATION_LANG)

set(NUNAVUT_SUBMODULES_ROOT "${NUNAVUT_PROJECT_ROOT}/submodules" CACHE STRING "The path to git submodules for the project.")

if(NOT DEFINED NUNAVUT_VERIFICATION_LANG_STANDARD)
     set(NUNAVUT_VERIFICATION_LANG_STANDARD "c++20" CACHE STRING "A language standard for languages that support this concept.")
endif()
# Ensure NUNAVUT_VERIFICATION_LANG_STANDARD has a default
if (NUNAVUT_VERIFICATION_LANG STREQUAL "cpp" AND NOT NUNAVUT_VERIFICATION_LANG_STANDARD)
     set(NUNAVUT_VERIFICATION_LANG_STANDARD "c++20")
endif()

if (NUNAVUT_VERIFICATION_LANG STREQUAL "c" AND NOT NUNAVUT_VERIFICATION_LANG_STANDARD)
     set(NUNAVUT_VERIFICATION_LANG_STANDARD "c11")
endif()

message(STATUS "NUNAVUT_VERIFICATION_LANG_STANDARD is ${NUNAVUT_VERIFICATION_LANG_STANDARD}")

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

if(DEFINED ENV{NUNAVUT_FLAGSET})
    set(NUNAVUT_FLAGSET "$ENV{NUNAVUT_FLAGSET}")
    message(STATUS "Using ${NUNAVUT_FLAGSET} from environment for NUNAVUT_FLAGSET")
elseif (DEFINED NUNAVUT_FLAGSET)
     message(STATUS "Using override NUNAVUT_FLAGSET = ${NUNAVUT_FLAGSET}")
else()
    set(NUNAVUT_FLAGSET "${CMAKE_SOURCE_DIR}/cmake/compiler_flag_sets/native_w_cov.cmake")
    message(STATUS "Setting (default) NUNAVUT_FLAGSET = ${NUNAVUT_FLAGSET}")
endif()
include("${NUNAVUT_FLAGSET}")

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


# +---------------------------------------------------------------------------+
# | BUILD ENVIRONMENT
# +---------------------------------------------------------------------------+

#
# We generate coverage reports. Please look at them (It wasn't easy to get this to work).
#
find_package(lcov REQUIRED)
find_package(genhtml REQUIRED)

#
# We need tox to enable a reproducible python environment.
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

create_dsdl_library(
     NAME public_regulated_data_types
     LANGUAGE c
     ASSERT_TYPE_GTEST
     DSDL_FILES ${NUNAVUT_SUBMODULES_ROOT}/public_regulated_data_types/uavcan
)
#
# Generate serialization support headers
#
create_dsdl_target(nunavut-support
                   ${NUNAVUT_VERIFICATION_LANG}
                   "${NUNAVUT_VERIFICATION_LANG_STANDARD}"
                   ${NUNAVUT_GENERATED_ROOT}/${NUNAVUT_VERIFICATION_LANG}/default
                   ""
                   OFF
                   ${NUNAVUT_VERIFICATION_SER_ASSERT}
                   ${NUNAVUT_VERIFICATION_SER_FP_DISABLE}
                   ${NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE}
                   ON
                   "${NUNAVUT_VERIFICATION_TARGET_ENDIANNESS}"
                   "only")

#
# Generate types for the Cyphal v1 public_regulated_data_types set.
#
create_dsdl_target(dsdl-regulated
                   ${NUNAVUT_VERIFICATION_LANG}
                   "${NUNAVUT_VERIFICATION_LANG_STANDARD}"
                   ${NUNAVUT_GENERATED_ROOT}/${NUNAVUT_VERIFICATION_LANG}/default
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
                   "${NUNAVUT_VERIFICATION_LANG_STANDARD}"
                   ${NUNAVUT_GENERATED_ROOT}/${NUNAVUT_VERIFICATION_LANG}/default
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

if(LOCAL_VERIFICATION_LANG STREQUAL "cpp")
     # C++ tests including going back and forth between c and c++. We include
     # c serialization support when verifying c++ for this reason. Future versions of this
     # verification build might make this more generic allowing any language to test interoperability
     # with any other language.
     set(LOCAL_VERIFICATION_LANG_STANDARD_C "")
     set(LOCAL_VERIFICATION_LANG_STANDARD_CXX "${NUNAVUT_VERIFICATION_LANG_STANDARD}")
     list(APPEND LOCAL_ADDITIONAL_DSDL_LIBS dsdl-regulated-c dsdl-test-c)
     #
     # Generate serialization support headers
     #
     create_dsdl_target(nunavut-support-c
                        "c"
                        "${NUNAVUT_VERIFICATION_LANG_STANDARD}"
                        ${NUNAVUT_GENERATED_ROOT}/${NUNAVUT_VERIFICATION_LANG}/default
                        ""
                        OFF
                        ${NUNAVUT_VERIFICATION_SER_ASSERT}
                        ${NUNAVUT_VERIFICATION_SER_FP_DISABLE}
                        ${NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE}
                        ON
                        "${NUNAVUT_VERIFICATION_TARGET_ENDIANNESS}"
                        "only")

     #
     # Generate types for the Cyphal v1 public_regulated_data_types set.
     #
     create_dsdl_target(dsdl-regulated-c
                        "c"
                        "${NUNAVUT_VERIFICATION_LANG_STANDARD}"
                        ${NUNAVUT_GENERATED_ROOT}/${NUNAVUT_VERIFICATION_LANG}/default
                        ${NUNAVUT_SUBMODULES_ROOT}/public_regulated_data_types/uavcan
                        OFF
                        ${NUNAVUT_VERIFICATION_SER_ASSERT}
                        ${NUNAVUT_VERIFICATION_SER_FP_DISABLE}
                        ${NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE}
                        ON
                        "${NUNAVUT_VERIFICATION_TARGET_ENDIANNESS}"
                        "never")

     add_dependencies(dsdl-regulated-c nunavut-support-c)

     #
     # Generate additional types for verification
     #
     create_dsdl_target(dsdl-test-c
                        "c"
                        "${NUNAVUT_VERIFICATION_LANG_STANDARD}"
                        ${NUNAVUT_GENERATED_ROOT}/${NUNAVUT_VERIFICATION_LANG}/default
                        ${CMAKE_SOURCE_DIR}/nunavut_test_types/test0/regulated
                        OFF
                        ${NUNAVUT_VERIFICATION_SER_ASSERT}
                        ${NUNAVUT_VERIFICATION_SER_FP_DISABLE}
                        ${NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE}
                        ON
                        "${NUNAVUT_VERIFICATION_TARGET_ENDIANNESS}"
                        "never"
                        ${NUNAVUT_SUBMODULES_ROOT}/public_regulated_data_types/uavcan)

     add_dependencies(dsdl-test-c nunavut-support-c)
endif()


if(NUNAVUT_VERIFICATION_LANG_STANDARD STREQUAL "cetl++14-17"
OR NUNAVUT_VERIFICATION_LANG_STANDARD STREQUAL "c++17-pmr"
OR NUNAVUT_VERIFICATION_LANG_STANDARD STREQUAL "c++20-pmr")
     #
     # Generate serialization support headers with config matching the language standard
     #
     create_dsdl_target(nunavut-support-array-with-allocator
                    ${NUNAVUT_VERIFICATION_LANG}
                    "${NUNAVUT_VERIFICATION_LANG_STANDARD}"
                    ${NUNAVUT_GENERATED_ROOT}/${NUNAVUT_VERIFICATION_LANG}/array-with-allocator
                    ""
                    OFF
                    ${NUNAVUT_VERIFICATION_SER_ASSERT}
                    ${NUNAVUT_VERIFICATION_SER_FP_DISABLE}
                    ${NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE}
                    ON
                    "${NUNAVUT_VERIFICATION_TARGET_ENDIANNESS}"
                    "only")

     #
     # Generate additional types with config matching the language standard
     #
     create_dsdl_target(dsdl-test-array-with-allocator
                    ${NUNAVUT_VERIFICATION_LANG}
                    "${NUNAVUT_VERIFICATION_LANG_STANDARD}"
                    ${NUNAVUT_GENERATED_ROOT}/${NUNAVUT_VERIFICATION_LANG}/array-with-allocator
                    ${CMAKE_SOURCE_DIR}/nunavut_test_types/nested_array_types/mymsgs
                    OFF
                    ${NUNAVUT_VERIFICATION_SER_ASSERT}
                    ${NUNAVUT_VERIFICATION_SER_FP_DISABLE}
                    ${NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE}
                    ON
                    "${NUNAVUT_VERIFICATION_TARGET_ENDIANNESS}"
                    "never"
                    ${NUNAVUT_SUBMODULES_ROOT}/public_regulated_data_types/uavcan)

     add_dependencies(dsdl-test-array-with-allocator nunavut-support-array-with-allocator)
endif()

# +---------------------------------------------------------------------------+
# | FLAG SETS
# +---------------------------------------------------------------------------+

if (LOCAL_VERIFICATION_LANG STREQUAL "c")
     set(LOCAL_VERIFICATION_LANG_STANDARD_C "${NUNAVUT_VERIFICATION_LANG_STANDARD}")
     set(LOCAL_VERIFICATION_LANG_STANDARD_CXX "")
     list(APPEND LOCAL_ADDITIONAL_DSDL_LIBS "")
elseif(LOCAL_VERIFICATION_LANG STREQUAL "cpp")
     set(LOCAL_VERIFICATION_LANG_STANDARD_C "")
     set(LOCAL_VERIFICATION_LANG_STANDARD_CXX "${NUNAVUT_VERIFICATION_LANG_STANDARD}")
     list(APPEND LOCAL_ADDITIONAL_DSDL_LIBS "")
else()
    set(LOCAL_VERIFICATION_LANG_STANDARD_C "")
    set(LOCAL_VERIFICATION_LANG_STANDARD_CXX "")
    list(APPEND LOCAL_ADDITIONAL_DSDL_LIBS "")
endif()

# +---------------------------------------------------------------------------+
# | VERIFICATION SUITE
# +---------------------------------------------------------------------------+
#   We generate individual test binaires so we can record which test generated
#   what coverage. We also allow test authors to generate coverage reports for
#   just one test allowing for faster iteration.

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

function(runTestCpp)
    set(options "")
    set(oneValueArgs TEST_FILE)
    set(multiValueArgs LINK LANGUAGE_FLAVORS)
    cmake_parse_arguments(runTestCpp "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    # Skip tests not relevant to the specified language standard
    list(FIND runTestCpp_LANGUAGE_FLAVORS "${NUNAVUT_VERIFICATION_LANG_STANDARD}" FIND_INDEX)
    if (${FIND_INDEX} EQUAL -1)
        message(STATUS "Skipping ${runTestCpp_TEST_FILE}")
        return()
    endif()

    set(NATIVE_TEST "${NUNAVUT_VERIFICATION_LANG}/suite/${runTestCpp_TEST_FILE}")
    get_filename_component(NATIVE_TEST_NAME ${NATIVE_TEST} NAME_WE)

    define_native_unit_test(FRAMEWORK "gtest"
                            TEST_NAME ${NATIVE_TEST_NAME}
                            TEST_SOURCE ${NATIVE_TEST}
                            OUTDIR ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
                            DSDL_TARGETS
                                ${runTestCpp_LINK}
                                ${LOCAL_ADDITIONAL_DSDL_LIBS}
    )
    if(NUNAVUT_VERIFICATION_LANG STREQUAL "c")
        #
        # If we are testing C headers with C++ tests we have to disable
        # certain checks to allow the inline code to compile without
        # warnings.
        #
        target_compile_options(${NATIVE_TEST_NAME} PRIVATE "-Wno-old-style-cast")
    endif()
    # Some tests use deprecated DSDLs
    target_compile_options(${NATIVE_TEST_NAME} PRIVATE "-Wno-deprecated-declarations")
    target_link_libraries(${NATIVE_TEST_NAME} PUBLIC o1heap)
    target_include_directories(${NATIVE_TEST_NAME} PUBLIC "${NUNAVUT_PROJECT_ROOT}/submodules/CETL/include")
    define_native_test_run(TEST_NAME ${NATIVE_TEST_NAME} OUTDIR ${NUNAVUT_VERIFICATIONS_BINARY_DIR})
    define_native_test_run_with_lcov(${NATIVE_TEST_NAME} ${NUNAVUT_VERIFICATIONS_BINARY_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/\\*)
    define_native_test_coverage(${NATIVE_TEST_NAME} ${NUNAVUT_VERIFICATIONS_BINARY_DIR})
    list(APPEND ALL_TESTS "run_${NATIVE_TEST_NAME}")
    list(APPEND ALL_TESTS_WITH_LCOV "run_${NATIVE_TEST_NAME}_with_lcov")
    list(APPEND ALL_TEST_COVERAGE "--add-tracefile")
    list(APPEND ALL_TEST_COVERAGE "${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.${NATIVE_TEST_NAME}.filtered.info")
    set(ALL_TESTS ${ALL_TESTS} PARENT_SCOPE)
    set(ALL_TESTS_WITH_LCOV ${ALL_TESTS_WITH_LCOV} PARENT_SCOPE)
    set(ALL_TEST_COVERAGE ${ALL_TEST_COVERAGE} PARENT_SCOPE)
endfunction()

if (NUNAVUT_VERIFICATION_LANG STREQUAL "cpp")
     runTestCpp(TEST_FILE test_array_c++17-pmr.cpp   LINK dsdl-test-array-with-allocator LANGUAGE_FLAVORS                         c++17-pmr       c++20-pmr)
     runTestCpp(TEST_FILE test_array_cetl++14-17.cpp LINK dsdl-test-array-with-allocator LANGUAGE_FLAVORS       cetl++14-17                                )
     runTestCpp(TEST_FILE test_bitarray.cpp          LINK dsdl-regulated dsdl-test       LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_compiles.cpp          LINK dsdl-regulated dsdl-test       LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_large_bitset.cpp      LINK dsdl-regulated dsdl-test       LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_serialization.cpp     LINK dsdl-regulated dsdl-test       LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_unionant.cpp          LINK dsdl-regulated dsdl-test       LANGUAGE_FLAVORS c++14 cetl++14-17 c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_constant.cpp          LINK dsdl-regulated dsdl-test       LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
endif()

function(runTestC)
    set(options "")
    set(oneValueArgs TEST_FILE FRAMEWORK)
    set(multiValueArgs LINK LANGUAGE_FLAVORS)
    cmake_parse_arguments(runTestC "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    # Skip tests not relevant to the specified language standard
    list(FIND runTestC_LANGUAGE_FLAVORS "${NUNAVUT_VERIFICATION_LANG_STANDARD}" FIND_INDEX)
    if (${FIND_INDEX} EQUAL -1)
        message(STATUS "Skipping ${runTestC_TEST_FILE}")
        return()
    endif()

    set(NATIVE_TEST "${NUNAVUT_VERIFICATION_ROOT}/suite/${runTestC_TEST_FILE}")
    get_filename_component(NATIVE_TEST_NAME ${NATIVE_TEST} NAME_WE)

    define_native_unit_test(FRAMEWORK ${runTestC_FRAMEWORK}
                            TEST_NAME ${NATIVE_TEST_NAME}
                            TEST_SOURCE ${NATIVE_TEST}
                            OUTDIR ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
                            DSDL_TARGETS
                                ${runTestC_LINK}
    )
    define_native_test_run(TEST_NAME ${NATIVE_TEST_NAME} OUTDIR ${NUNAVUT_VERIFICATIONS_BINARY_DIR})
    define_native_test_run_with_lcov(${NATIVE_TEST_NAME} ${NUNAVUT_VERIFICATIONS_BINARY_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/\\*)
    define_native_test_coverage(${NATIVE_TEST_NAME} ${NUNAVUT_VERIFICATIONS_BINARY_DIR})
    list(APPEND ALL_TESTS "run_${NATIVE_TEST_NAME}")
    list(APPEND ALL_TESTS_WITH_LCOV "run_${NATIVE_TEST_NAME}_with_lcov")
    list(APPEND ALL_TEST_COVERAGE "--add-tracefile")
    list(APPEND ALL_TEST_COVERAGE "${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.${NATIVE_TEST_NAME}.filtered.info")
    set(ALL_TESTS ${ALL_TESTS} PARENT_SCOPE)
    set(ALL_TESTS_WITH_LCOV ${ALL_TESTS_WITH_LCOV} PARENT_SCOPE)
    set(ALL_TEST_COVERAGE ${ALL_TEST_COVERAGE} PARENT_SCOPE)
endfunction()

if (NUNAVUT_VERIFICATION_LANG STREQUAL "c")
     runTestCpp(TEST_FILE test_canard.cpp                         LINK dsdl-regulated dsdl-test LANGUAGE_FLAVORS c11)
     runTestCpp(TEST_FILE test_support_assert.cpp                 LINK dsdl-regulated dsdl-test LANGUAGE_FLAVORS c11)
     runTestC(  TEST_FILE test_constant.c                         LINK dsdl-regulated dsdl-test LANGUAGE_FLAVORS c11 FRAMEWORK "unity")
     runTestC(  TEST_FILE test_override_variable_array_capacity.c LINK dsdl-regulated dsdl-test LANGUAGE_FLAVORS c11 FRAMEWORK "unity")
     runTestC(  TEST_FILE test_serialization.c                    LINK dsdl-regulated dsdl-test LANGUAGE_FLAVORS c11 FRAMEWORK "unity")
     runTestC(  TEST_FILE test_support.c                          LINK dsdl-regulated dsdl-test LANGUAGE_FLAVORS c11 FRAMEWORK "unity")
     runTestC(  TEST_FILE test_simple.c                           LINK dsdl-regulated dsdl-test LANGUAGE_FLAVORS c11 FRAMEWORK "none")
endif()

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
