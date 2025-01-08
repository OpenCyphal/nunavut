#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
cmake_minimum_required(VERSION 3.22.0)

# +---------------------------------------------------------------------------+
# | PROJECT DEFINITION
# +---------------------------------------------------------------------------+
project(nunavut_verification C CXX)

include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/utils.cmake)

# +-[GLOBAL DEFINITIONS]------------------------------------------------------+
handle_nunavut_verification_language_and_standard(
     REQUIRED
     PRINT_STATUS
     OUT_LOCAL_VERIFICATION_TARGET_LANGUAGE LOCAL_NUNAVUT_VERIFICATION_TARGET_LANG
     OUT_VERIFICATION_TARGET_PLATFORM LOCAL_VERIFICATION_TARGET_PLATFORM
     OUT_VERIFICATION_LANGUAGE_STANDARD_C LOCAL_VERIFICATION_LANGUAGE_STANDARD_C
     OUT_VERIFICATION_LANGUAGE_STANDARD_CPP LOCAL_VERIFICATION_LANGUAGE_STANDARD_CPP
)

if(NOT DEFINED LOCAL_PROJECT_ROOT)
     get_filename_component(LOCAL_PROJECT_ROOT
          "${CMAKE_CURRENT_SOURCE_DIR}/../"
          REALPATH BASE_DIR
          "${CMAKE_CURRENT_BINARY_DIR}")
     message(STATUS "Setting LOCAL_PROJECT_ROOT = ${LOCAL_PROJECT_ROOT}")
else()
     message(STATUS "Using ${LOCAL_PROJECT_ROOT} for LOCAL_PROJECT_ROOT")
endif()

#
# For now we only compile for the native environment. In the future we may cross
# compile some verifications as well.
#
include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/compiler_flag_sets/native.cmake")

#
# Tell cmake where to find our custom scripts.
#
set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/modules")

#
# Tell cmake where to find the Nunavut configuration package.
#
set(CMAKE_PREFIX_PATH ${LOCAL_PROJECT_ROOT})

#
# All test binaries and reports will be created under this directory.
#
set(NUNAVUT_VERIFICATIONS_BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/$<CONFIG>")

# +-[DEPENDENCIES]------------------------------------------------------------+
#
# Load the Nunavut cmake integration.
#
find_package(Nunavut 3.0 REQUIRED)

#
# We generate coverage reports. Please look at them (It wasn't easy to get this to work).
#
find_package(verification-coverage REQUIRED)
find_package(genhtml REQUIRED)

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
# Pull in some stuff we need for testing C++
#
find_package(o1heap REQUIRED)

# +-[DSDL FILES]--------------------------------------------------------------+

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

set(LOCAL_NAMESPACE_TEST0_REGULATED ${CMAKE_CURRENT_SOURCE_DIR}/nunavut_test_types/test0/regulated)
file(GLOB_RECURSE LOCAL_TEST_TYPES_TEST0_REGULATED CONFIGURE_DEPENDS ${LOCAL_NAMESPACE_TEST0_REGULATED}/*.dsdl)

set(LOCAL_NAMESPACE_NESTED_ARRAY_TYPES ${CMAKE_CURRENT_SOURCE_DIR}/nunavut_test_types/nested_array_types/mymsgs)
file(GLOB_RECURSE LOCAL_NESTED_ARRAY_TYPES CONFIGURE_DEPENDS ${LOCAL_NAMESPACE_NESTED_ARRAY_TYPES}/*.dsdl)

# +-[C-TYPES]-----------------------------------------------------------------+
#
# Generate additional types for verification
#

add_cyphal_library(
     NAME dsdl-test-c
     LANGUAGE c
     LANGUAGE_STANDARD ${LOCAL_VERIFICATION_LANGUAGE_STANDARD_C}
     OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR}/$<CONFIG>/generated
     DSDL_FILES
     ${LOCAL_TEST_TYPES_TEST0_REGULATED}
     ${LOCAL_NESTED_ARRAY_TYPES}
     ${LOCAL_TEST_TYPES_PUBLIC_REGULATED}
     DSDL_NAMESPACES
     ${LOCAL_NAMESPACE_TEST0_REGULATED}
     ${LOCAL_NAMESPACE_NESTED_ARRAY_TYPES}
     EXPORT_CONFIGURE_MANIFEST ${CMAKE_CURRENT_BINARY_DIR}
     EXPORT_GENERATE_MANIFEST ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
     EXTRA_GENERATOR_ARGS "$<$<CONFIG:Debug,DebugAsan,DebugCov>:--enable-serialization-asserts>"
     OUT_LIBRARY_TARGET LOCAL_TEST_TYPES_C_LIBRARY
)

# +-[CPP-TYPES]---------------------------------------------------------------+
if(LOCAL_NUNAVUT_VERIFICATION_TARGET_LANG STREQUAL "cpp")
     add_cyphal_library(
          NAME dsdl-test-cpp
          LANGUAGE ${LOCAL_NUNAVUT_VERIFICATION_TARGET_LANG}
          LANGUAGE_STANDARD ${LOCAL_VERIFICATION_LANGUAGE_STANDARD_CPP}
          OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR}/$<CONFIG>/generated
          DSDL_FILES
          ${LOCAL_TEST_TYPES_TEST0_REGULATED}
          ${LOCAL_NESTED_ARRAY_TYPES}
          ${LOCAL_TEST_TYPES_PUBLIC_REGULATED}
          DSDL_NAMESPACES
          ${LOCAL_NAMESPACE_TEST0_REGULATED}
          ${LOCAL_NAMESPACE_NESTED_ARRAY_TYPES}
          EXTRA_GENERATOR_ARGS "$<$<CONFIG:Debug,DebugAsan,DebugCov>:--enable-serialization-asserts>"
          EXPORT_CONFIGURE_MANIFEST ${CMAKE_CURRENT_BINARY_DIR}
          EXPORT_GENERATE_MANIFEST ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
          ALLOW_EXPERIMENTAL_LANGUAGES
          OUT_LIBRARY_TARGET LOCAL_TEST_TYPES_CPP_LIBRARY
     )

     target_compile_definitions(${LOCAL_TEST_TYPES_C_LIBRARY} INTERFACE "$<$<CONFIG:Debug,DebugAsan,DebugCov>:-DNUNAVUT_ASSERT=EXPECT_TRUE>")
     target_compile_definitions(${LOCAL_TEST_TYPES_CPP_LIBRARY} INTERFACE "$<$<CONFIG:Debug,DebugAsan,DebugCov>:-DNUNAVUT_ASSERT=EXPECT_TRUE>")
else()
     target_compile_definitions(${LOCAL_TEST_TYPES_C_LIBRARY} INTERFACE "$<$<CONFIG:Debug,DebugAsan,DebugCov>:-DNUNAVUT_ASSERT=TEST_ASSERT_TRUE>")
endif()

# +---------------------------------------------------------------------------+
# | VERIFICATION SUITE
# +---------------------------------------------------------------------------+
# We generate individual test binaires so we can record which test generated
# what coverage. We also allow test authors to generate coverage reports for
# just one test allowing for faster iteration.

set(ALL_TEST_RUNS "")
set(ALL_TEST_INFO_FILES "")
# Don't allow tests to run in parallel
set_property(GLOBAL PROPERTY JOB_POOLS coverage_test_runs=1)

function(runTestCpp)
     set(options "")
     set(oneValueArgs TEST_FILE)
     set(multiValueArgs LINK LANGUAGE_FLAVORS)
     cmake_parse_arguments(runTestCpp "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

     # Skip tests not relevant to the specified language standard
     list(FIND runTestCpp_LANGUAGE_FLAVORS "${LOCAL_VERIFICATION_LANGUAGE_STANDARD_CPP}" FIND_INDEX)

     if(${FIND_INDEX} EQUAL -1)
          message(STATUS "Skipping ${runTestCpp_TEST_FILE}")
          return()
     endif()

     set(NATIVE_TEST "${CMAKE_CURRENT_SOURCE_DIR}/cpp/suite/${runTestCpp_TEST_FILE}")
     get_filename_component(NATIVE_TEST_NAME ${NATIVE_TEST} NAME_WE)

     define_native_unit_test(
          FRAMEWORK "gtest"
          NAME ${NATIVE_TEST_NAME}
          SOURCE ${NATIVE_TEST}
          OUTDIR ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
          DSDL_TARGETS
          ${runTestCpp_LINK}
     )

     if(LOCAL_NUNAVUT_VERIFICATION_TARGET_LANG STREQUAL "c")
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
     target_include_directories(${NATIVE_TEST_NAME} PUBLIC "${NUNAVUT_SUBMODULES_DIR}/CETL/include")
     define_native_test_run(
          NAME ${NATIVE_TEST_NAME}
          OUTDIR ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
          OUT_CUSTOM_TARGET LOCAL_TEST_RUN_TARGET
     )
     define_coverage_native_test_run(
          NAME ${NATIVE_TEST_NAME}
          JOB_POOL coverage_test_runs
          OUTDIR ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
          SOURCE_FILTER_DIR ${CMAKE_CURRENT_SOURCE_DIR}/\\*
          OUT_INFO_FILE LOCAL_TEST_INFO_FILE
     )
     define_native_test_coverage(${NATIVE_TEST_NAME} ${NUNAVUT_VERIFICATIONS_BINARY_DIR})
     list(APPEND ALL_TEST_RUNS "${LOCAL_TEST_RUN_TARGET}")
     list(APPEND ALL_TEST_INFO_FILES "${LOCAL_TEST_INFO_FILE}")
     set(ALL_TEST_RUNS ${ALL_TEST_RUNS} PARENT_SCOPE)
     set(ALL_TEST_INFO_FILES ${ALL_TEST_INFO_FILES} PARENT_SCOPE)
endfunction()

if(LOCAL_NUNAVUT_VERIFICATION_TARGET_LANG STREQUAL "cpp")
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
     list(FIND runTestC_LANGUAGE_FLAVORS "${LOCAL_VERIFICATION_LANGUAGE_STANDARD_C}" FIND_INDEX)

     if(${FIND_INDEX} EQUAL -1)
          message(STATUS "Skipping ${runTestC_TEST_FILE}")
          return()
     endif()

     set(NATIVE_TEST "${CMAKE_CURRENT_SOURCE_DIR}/c/suite/${runTestC_TEST_FILE}")
     get_filename_component(NATIVE_TEST_NAME ${NATIVE_TEST} NAME_WE)

     define_native_unit_test(
          FRAMEWORK ${runTestC_FRAMEWORK}
          NAME ${NATIVE_TEST_NAME}
          SOURCE ${NATIVE_TEST}
          OUTDIR ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
          DSDL_TARGETS
          ${runTestC_LINK}
     )
     define_native_test_run(
          NAME ${NATIVE_TEST_NAME}
          OUTDIR ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
          OUT_CUSTOM_TARGET LOCAL_TEST_RUN_TARGET
     )
     define_coverage_native_test_run(
          NAME ${NATIVE_TEST_NAME}
          JOB_POOL coverage_test_runs
          OUTDIR ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
          SOURCE_FILTER_DIR ${CMAKE_CURRENT_SOURCE_DIR}/\\*
          OUT_INFO_FILE LOCAL_TEST_INFO_FILE
     )
     define_native_test_coverage(${NATIVE_TEST_NAME} ${NUNAVUT_VERIFICATIONS_BINARY_DIR})
     list(APPEND ALL_TEST_RUNS "${LOCAL_TEST_RUN_TARGET}")
     list(APPEND ALL_TEST_INFO_FILES "${LOCAL_TEST_INFO_FILE}")
     set(ALL_TEST_RUNS ${ALL_TEST_RUNS} PARENT_SCOPE)
     set(ALL_TEST_INFO_FILES ${ALL_TEST_INFO_FILES} PARENT_SCOPE)
endfunction()

if(LOCAL_NUNAVUT_VERIFICATION_TARGET_LANG STREQUAL "c")
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
define_coverage_summary(
     INFO_FILES ${ALL_TEST_INFO_FILES}
     OUTDIR ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
     OUT_INFO_FILE LOCAL_INFO_SUMMARY
)

# This just gives us a utility to clean things up manually. You don't need to hook it up to anything.
define_coverage_zero_all(OUTDIR ${NUNAVUT_VERIFICATIONS_BINARY_DIR})

add_custom_target(
     cov_all
     ${GENHTML}
          --title "${PROJECT_NAME} native test coverage"
          --output-directory ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage/all
          --demangle-cpp
          --sort
          --num-spaces 4
          --function-coverage
          --branch-coverage
          --legend
          --highlight
          --show-details
          ${LOCAL_INFO_SUMMARY}
     DEPENDS ${LOCAL_INFO_SUMMARY}
     COMMENT "Build and run all tests and generate an overall html coverage report."
)

add_custom_target(test_all DEPENDS ${ALL_TEST_RUNS})
