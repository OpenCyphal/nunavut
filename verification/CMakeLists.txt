#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#

cmake_minimum_required(VERSION 3.22.0)

# +---------------------------------------------------------------------------+
# | LANGUAGE DEFINITIONS
# +---------------------------------------------------------------------------+
if(DEFINED ENV{NUNAVUT_VERIFICATION_LANG})
     message(STATUS "Getting NUNAVUT_VERIFICATION_LANG from the environment ($ENV{NUNAVUT_VERIFICATION_LANG})")
     set(NUNAVUT_VERIFICATION_LANG "$ENV{NUNAVUT_VERIFICATION_LANG}" CACHE STRING "The Nunavut output language to verify.")
else()
     set(NUNAVUT_VERIFICATION_LANG "unspecified" CACHE STRING "The Nunavut output language to verify.")
endif()

if(NUNAVUT_VERIFICATION_LANG STREQUAL "cpp")
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

# Ensure NUNAVUT_VERIFICATION_LANG_STANDARD has a default
if(NUNAVUT_VERIFICATION_LANG STREQUAL "cpp" AND NUNAVUT_VERIFICATION_LANG_STANDARD)
     set(NUNAVUT_VERIFICATION_LANG_CPP_STANDARD ${NUNAVUT_VERIFICATION_LANG_STANDARD})
else()
     set(NUNAVUT_VERIFICATION_LANG_CPP_STANDARD "c++20")
endif()

if(NUNAVUT_VERIFICATION_LANG STREQUAL "c" AND NUNAVUT_VERIFICATION_LANG_STANDARD)
     set(NUNAVUT_VERIFICATION_LANG_C_STANDARD ${NUNAVUT_VERIFICATION_LANG_STANDARD})
else()
     set(NUNAVUT_VERIFICATION_LANG_C_STANDARD "c11")
endif()

string(REGEX REPLACE "c-?([0-9]*).*" "\\1" LOCAL_VERIFICATION_LANG_C_MATCH ${NUNAVUT_VERIFICATION_LANG_C_STANDARD})

if(NOT LOCAL_VERIFICATION_LANG_C_MATCH)
     message(FATAL_ERROR "NUNAVUT_VERIFICATION_LANG_C_STANDARD (${NUNAVUT_VERIFICATION_LANG_C_STANDARD}) is in an unexpected format.")
endif()

set(CMAKE_C_STANDARD ${LOCAL_VERIFICATION_LANG_C_MATCH})
set(CMAKE_C_STANDARD_REQUIRED ON)

string(REGEX REPLACE "c[pPxX\+][pPxX\+]-?([0-9]*).*" "\\1" LOCAL_VERIFICATION_LANG_CPP_MATCH ${NUNAVUT_VERIFICATION_LANG_CPP_STANDARD})

if(NOT LOCAL_VERIFICATION_LANG_CPP_MATCH)
     message(FATAL_ERROR "NUNAVUT_VERIFICATION_LANG_CPP_STANDARD (${NUNAVUT_VERIFICATION_LANG_CPP_STANDARD}) is in an unexpected format.")
endif()

set(CMAKE_CXX_STANDARD ${LOCAL_VERIFICATION_LANG_CPP_MATCH})
set(CMAKE_CXX_STANDARD_REQUIRED ON)

message(STATUS "NUNAVUT_VERIFICATION_LANG_C_STANDARD is ${NUNAVUT_VERIFICATION_LANG_C_STANDARD}")
message(STATUS "CMAKE_C_STANDARD is ${CMAKE_C_STANDARD}")
message(STATUS "NUNAVUT_VERIFICATION_LANG_CPP_STANDARD is ${NUNAVUT_VERIFICATION_LANG_CPP_STANDARD}")
message(STATUS "CMAKE_CXX_STANDARD is ${CMAKE_CXX_STANDARD}")

# +---------------------------------------------------------------------------+
# | PROJECT DEFINITION
# +---------------------------------------------------------------------------+
project(nunavut_verification C CXX)

include(${CMAKE_SOURCE_DIR}/cmake/utils.cmake)

# +---------------------------------------------------------------------------+
# | GLOBAL DEFINITIONS
# +---------------------------------------------------------------------------+
if(NOT DEFINED NUNAVUT_PROJECT_ROOT)
     get_filename_component(NUNAVUT_PROJECT_ROOT
          "${CMAKE_SOURCE_DIR}/../"
          REALPATH BASE_DIR
          "${CMAKE_CURRENT_BINARY_DIR}")
     message(STATUS "Setting NUNAVUT_PROJECT_ROOT = ${NUNAVUT_PROJECT_ROOT}")
else()
     message(STATUS "Using ${NUNAVUT_PROJECT_ROOT} for NUNAVUT_PROJECT_ROOT")
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

if(DEFINED ENV{NUNAVUT_FLAGSET})
     set(NUNAVUT_FLAGSET "$ENV{NUNAVUT_FLAGSET}")
     message(STATUS "Using ${NUNAVUT_FLAGSET} from environment for NUNAVUT_FLAGSET")
elseif(DEFINED NUNAVUT_FLAGSET)
     message(STATUS "Using override NUNAVUT_FLAGSET = ${NUNAVUT_FLAGSET}")
else()
     set(NUNAVUT_FLAGSET "${CMAKE_SOURCE_DIR}/cmake/compiler_flag_sets/native.cmake")
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
set(NUNAVUT_GENERATED_ROOT ${CMAKE_CURRENT_BINARY_DIR}/generated)

#
# All test binaries and reports will be created under this directory.
#
set(NUNAVUT_VERIFICATIONS_BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/suite/$<CONFIG>")

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
find_package(Nunavut 3.0 REQUIRED)

#
# Pull in some stuff we need for testing C++
#
find_package(o1heap REQUIRED)

# +-[ARGUMENT TRANSLATION]----------------------------------------------------+
#
# Translate local arguments into the form needed by add_cyphal_library
#
if(NUNAVUT_VERIFICATION_SER_ASSERT)
     if(NUNAVUT_VERIFICATION_LANG STREQUAL "cpp")
          set(LOCAL_SERIALIZATION_ASSERT_VALUE "EXPECT_TRUE")
     else()
          set(LOCAL_SERIALIZATION_ASSERT_VALUE "TEST_ASSERT_TRUE")
     endif()
else()
     set(LOCAL_SERIALIZATION_ASSERT_VALUE)
endif()

set(LOCAL_EXTRA_NUNAVUT_ARGS)

if(NUNAVUT_VERIFICATION_SER_FP_DISABLE)
     list(APPEND LOCAL_EXTRA_NUNAVUT_ARGS "--omit-float-serialization-support")
endif()

if(NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE)
     list(APPEND LOCAL_EXTRA_NUNAVUT_ARGS "--enable-override-variable-array-capacity")
endif()

if(${NUNAVUT_VERIFICATION_TARGET_ENDIANNESS} STREQUAL "any")
     set(LOCAL_NUNAVUT_VERIFICATION_TARGET_ENDIANNESS_OPTION "ENDIAN_ANY")
elseif(${NUNAVUT_VERIFICATION_TARGET_ENDIANNESS} STREQUAL "little")
     set(LOCAL_NUNAVUT_VERIFICATION_TARGET_ENDIANNESS_OPTION "ENDIAN_LITTLE")
elseif(${NUNAVUT_VERIFICATION_TARGET_ENDIANNESS} STREQUAL "big")
     set(LOCAL_NUNAVUT_VERIFICATION_TARGET_ENDIANNESS_OPTION "ENDIAN_BIG")
else()
     message(FATAL_ERROR "NUNAVUT_VERIFICATION_TARGET_ENDIANNESS value \"${NUNAVUT_VERIFICATION_TARGET_ENDIANNESS}\" is invalid.")
endif()

# +-[DISCOVER DSDL FILES]-----------------------------------------------------+

# add_cyphal_library automatically adds the public_regulated_data_types/uavcan namespace
# (unless OMIT_PUBLIC_REGULATED_NAMESPACE is set) so we can use relative paths for these.
# Nunavut also finds all dependencies of the test types so we only add public regulated
# types where we've specifically included them in a test.
set(LOCAL_TEST_TYPES_PUBLIC_REGULATED
     uavcan/pnp/8165.NodeIDAllocationData.2.0.dsdl
     uavcan/time/TimeSystem.0.1.dsdl
     uavcan/node/port/SubjectIDList.1.0.dsdl
     uavcan/register/Value.1.0.dsdl
     uavcan/node/port/SubjectIDList.0.1.dsdl
     uavcan/metatransport/can/ArbitrationID.0.1.dsdl
)

set(LOCAL_NAMESPACE_TEST0_REGULATED ${CMAKE_SOURCE_DIR}/nunavut_test_types/test0/regulated)
file(GLOB_RECURSE LOCAL_TEST_TYPES_TEST0_REGULATED CONFIGURE_DEPENDS ${LOCAL_NAMESPACE_TEST0_REGULATED}/*.dsdl)

set(LOCAL_NAMESPACE_NESTED_ARRAY_TYPES ${CMAKE_SOURCE_DIR}/nunavut_test_types/nested_array_types/mymsgs)
file(GLOB_RECURSE LOCAL_NESTED_ARRAY_TYPES CONFIGURE_DEPENDS ${LOCAL_NAMESPACE_NESTED_ARRAY_TYPES}/*.dsdl)

# +-[C-TYPES]-----------------------------------------------------------------+
#
# Generate additional types for verification
#
add_cyphal_library(
     NAME dsdl-test-c
     LANGUAGE c
     LANGUAGE_STANDARD ${NUNAVUT_VERIFICATION_LANG_C_STANDARD}
     DSDL_FILES
     ${LOCAL_TEST_TYPES_TEST0_REGULATED}
     ${LOCAL_NESTED_ARRAY_TYPES}
     ${LOCAL_TEST_TYPES_PUBLIC_REGULATED}
     DSDL_NAMESPACES
     ${LOCAL_NAMESPACE_TEST0_REGULATED}
     ${LOCAL_NAMESPACE_NESTED_ARRAY_TYPES}
     SERIALIZATION_ASSERT ${LOCAL_SERIALIZATION_ASSERT_VALUE}
     EXTRA_GENERATOR_ARGS ${LOCAL_EXTRA_NUNAVUT_ARGS}
     ${LOCAL_NUNAVUT_VERIFICATION_TARGET_ENDIANNESS_OPTION}
     EXPORT_MANIFEST
     ALLOW_EXPERIMENTAL_LANGUAGES
     OUT_LIBRARY_TARGET LOCAL_TEST_TYPES_C_LIBRARY
)

# +-[CPP-TYPES]---------------------------------------------------------------+
if(NUNAVUT_VERIFICATION_LANG STREQUAL "cpp")
     add_cyphal_library(
          NAME dsdl-test-cpp
          LANGUAGE ${NUNAVUT_VERIFICATION_LANG}
          LANGUAGE_STANDARD ${NUNAVUT_VERIFICATION_LANG_CPP_STANDARD}
          DSDL_FILES
          ${LOCAL_TEST_TYPES_TEST0_REGULATED}
          ${LOCAL_NESTED_ARRAY_TYPES}
          ${LOCAL_TEST_TYPES_PUBLIC_REGULATED}
          DSDL_NAMESPACES
          ${LOCAL_NAMESPACE_TEST0_REGULATED}
          ${LOCAL_NAMESPACE_NESTED_ARRAY_TYPES}
          SERIALIZATION_ASSERT ${LOCAL_SERIALIZATION_ASSERT_VALUE}
          EXTRA_GENERATOR_ARGS ${LOCAL_EXTRA_NUNAVUT_ARGS}
          ${LOCAL_NUNAVUT_VERIFICATION_TARGET_ENDIANNESS_OPTION}
          EXPORT_MANIFEST
          ALLOW_EXPERIMENTAL_LANGUAGES
          OUT_LIBRARY_TARGET LOCAL_TEST_TYPES_CPP_LIBRARY
     )
endif()

# +---------------------------------------------------------------------------+
# | VERIFICATION SUITE
# +---------------------------------------------------------------------------+
# We generate individual test binaires so we can record which test generated
# what coverage. We also allow test authors to generate coverage reports for
# just one test allowing for faster iteration.
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
     list(FIND runTestCpp_LANGUAGE_FLAVORS "${NUNAVUT_VERIFICATION_LANG_CPP_STANDARD}" FIND_INDEX)

     if(${FIND_INDEX} EQUAL -1)
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

if(NUNAVUT_VERIFICATION_LANG STREQUAL "cpp")
     runTestCpp(TEST_FILE test_serialization.cpp     LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_array_c++17-pmr.cpp   LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS                         c++17-pmr       c++20-pmr)
     runTestCpp(TEST_FILE test_array_cetl++14-17.cpp LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS       cetl++14-17                                )
     runTestCpp(TEST_FILE test_bitarray.cpp          LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_compiles.cpp          LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_large_bitset.cpp      LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_unionant.cpp          LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14 cetl++14-17 c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_constant.cpp          LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
endif()

function(runTestC)
     set(options "")
     set(oneValueArgs TEST_FILE FRAMEWORK)
     set(multiValueArgs LINK LANGUAGE_FLAVORS)
     cmake_parse_arguments(runTestC "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

     # Skip tests not relevant to the specified language standard
     list(FIND runTestC_LANGUAGE_FLAVORS "${NUNAVUT_VERIFICATION_LANG_C_STANDARD}" FIND_INDEX)

     if(${FIND_INDEX} EQUAL -1)
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

if(NUNAVUT_VERIFICATION_LANG STREQUAL "c")
     runTestCpp(TEST_FILE test_canard.cpp                         LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11)
     runTestCpp(TEST_FILE test_support_assert.cpp                 LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11)
     runTestC(  TEST_FILE test_constant.c                         LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11 FRAMEWORK "unity")
     runTestC(  TEST_FILE test_override_variable_array_capacity.c LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11 FRAMEWORK "unity")
     runTestC(  TEST_FILE test_serialization.c                    LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11 FRAMEWORK "unity")
     runTestC(  TEST_FILE test_support.c                          LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11 FRAMEWORK "unity")
     runTestC(  TEST_FILE test_simple.c                           LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11 FRAMEWORK "none")
endif()

# +---------------------------------------------------------------------------+
# Finally, we setup an overall report. the coverage.info should be uploaded
# to a coverage reporting service as part of the CI pipeline.
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
