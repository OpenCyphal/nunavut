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
# Load common compiler flags
#
include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/compiler_flag_sets/common.cmake")

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
set(LOCAL_TEST_TYPES_PUBLIC_REGULATED
     uavcan/file/Path.1.0.dsdl
     uavcan/file/409.Write.1.1.dsdl
     uavcan/file/407.Modify.1.1.dsdl
     uavcan/file/406.List.0.2.dsdl
     uavcan/file/405.GetInfo.0.2.dsdl
     uavcan/file/407.Modify.1.0.dsdl
     uavcan/file/409.Write.1.0.dsdl
     uavcan/file/405.GetInfo.0.1.dsdl
     uavcan/file/Path.2.0.dsdl
     uavcan/file/406.List.0.1.dsdl
     uavcan/file/Error.1.0.dsdl
     uavcan/file/408.Read.1.1.dsdl
     uavcan/file/408.Read.1.0.dsdl
     uavcan/diagnostic/8184.Record.1.1.dsdl
     uavcan/diagnostic/Severity.1.0.dsdl
     uavcan/diagnostic/8184.Record.1.0.dsdl
     uavcan/primitive/array/Integer32.1.0.dsdl
     uavcan/primitive/array/Bit.1.0.dsdl
     uavcan/primitive/array/Real16.1.0.dsdl
     uavcan/primitive/array/Integer16.1.0.dsdl
     uavcan/primitive/array/Real32.1.0.dsdl
     uavcan/primitive/array/Natural64.1.0.dsdl
     uavcan/primitive/array/Integer64.1.0.dsdl
     uavcan/primitive/array/Natural8.1.0.dsdl
     uavcan/primitive/array/Natural16.1.0.dsdl
     uavcan/primitive/array/Integer8.1.0.dsdl
     uavcan/primitive/array/Real64.1.0.dsdl
     uavcan/primitive/array/Natural32.1.0.dsdl
     uavcan/primitive/Empty.1.0.dsdl
     uavcan/primitive/String.1.0.dsdl
     uavcan/primitive/Unstructured.1.0.dsdl
     uavcan/primitive/scalar/Integer32.1.0.dsdl
     uavcan/primitive/scalar/Bit.1.0.dsdl
     uavcan/primitive/scalar/Real16.1.0.dsdl
     uavcan/primitive/scalar/Integer16.1.0.dsdl
     uavcan/primitive/scalar/Real32.1.0.dsdl
     uavcan/primitive/scalar/Natural64.1.0.dsdl
     uavcan/primitive/scalar/Integer64.1.0.dsdl
     uavcan/primitive/scalar/Natural8.1.0.dsdl
     uavcan/primitive/scalar/Natural16.1.0.dsdl
     uavcan/primitive/scalar/Integer8.1.0.dsdl
     uavcan/primitive/scalar/Real64.1.0.dsdl
     uavcan/primitive/scalar/Natural32.1.0.dsdl
     uavcan/time/TAIInfo.0.1.dsdl
     uavcan/time/7168.Synchronization.1.0.dsdl
     uavcan/time/TimeSystem.0.1.dsdl
     uavcan/time/SynchronizedTimestamp.1.0.dsdl
     uavcan/time/510.GetSynchronizationMasterInfo.0.1.dsdl
     uavcan/register/385.List.1.0.dsdl
     uavcan/register/Name.1.0.dsdl
     uavcan/register/Value.1.0.dsdl
     uavcan/register/384.Access.1.0.dsdl
     uavcan/internet/udp/8174.OutgoingPacket.0.2.dsdl
     uavcan/internet/udp/500.HandleIncomingPacket.0.2.dsdl
     uavcan/internet/udp/500.HandleIncomingPacket.0.1.dsdl
     uavcan/internet/udp/8174.OutgoingPacket.0.1.dsdl
     uavcan/si/unit/power/Scalar.1.0.dsdl
     uavcan/si/unit/electric_current/Scalar.1.0.dsdl
     uavcan/si/unit/acceleration/Vector3.1.0.dsdl
     uavcan/si/unit/acceleration/Scalar.1.0.dsdl
     uavcan/si/unit/mass/Scalar.1.0.dsdl
     uavcan/si/unit/voltage/Scalar.1.0.dsdl
     uavcan/si/unit/magnetic_field_strength/Vector3.1.1.dsdl
     uavcan/si/unit/magnetic_field_strength/Vector3.1.0.dsdl
     uavcan/si/unit/magnetic_field_strength/Scalar.1.0.dsdl
     uavcan/si/unit/magnetic_field_strength/Scalar.1.1.dsdl
     uavcan/si/unit/frequency/Scalar.1.0.dsdl
     uavcan/si/unit/angle/Scalar.1.0.dsdl
     uavcan/si/unit/angle/Quaternion.1.0.dsdl
     uavcan/si/unit/energy/Scalar.1.0.dsdl
     uavcan/si/unit/volumetric_flow_rate/Scalar.1.0.dsdl
     uavcan/si/unit/length/Vector3.1.0.dsdl
     uavcan/si/unit/length/Scalar.1.0.dsdl
     uavcan/si/unit/length/WideScalar.1.0.dsdl
     uavcan/si/unit/length/WideVector3.1.0.dsdl
     uavcan/si/unit/velocity/Vector3.1.0.dsdl
     uavcan/si/unit/velocity/Scalar.1.0.dsdl
     uavcan/si/unit/angular_velocity/Vector3.1.0.dsdl
     uavcan/si/unit/angular_velocity/Scalar.1.0.dsdl
     uavcan/si/unit/pressure/Scalar.1.0.dsdl
     uavcan/si/unit/magnetic_flux_density/Vector3.1.0.dsdl
     uavcan/si/unit/magnetic_flux_density/Scalar.1.0.dsdl
     uavcan/si/unit/luminance/Scalar.1.0.dsdl
     uavcan/si/unit/torque/Vector3.1.0.dsdl
     uavcan/si/unit/torque/Scalar.1.0.dsdl
     uavcan/si/unit/force/Vector3.1.0.dsdl
     uavcan/si/unit/force/Scalar.1.0.dsdl
     uavcan/si/unit/temperature/Scalar.1.0.dsdl
     uavcan/si/unit/duration/Scalar.1.0.dsdl
     uavcan/si/unit/duration/WideScalar.1.0.dsdl
     uavcan/si/unit/angular_acceleration/Vector3.1.0.dsdl
     uavcan/si/unit/angular_acceleration/Scalar.1.0.dsdl
     uavcan/si/unit/volume/Scalar.1.0.dsdl
     uavcan/si/unit/electric_charge/Scalar.1.0.dsdl
     uavcan/si/sample/power/Scalar.1.0.dsdl
     uavcan/si/sample/electric_current/Scalar.1.0.dsdl
     uavcan/si/sample/acceleration/Vector3.1.0.dsdl
     uavcan/si/sample/acceleration/Scalar.1.0.dsdl
     uavcan/si/sample/mass/Scalar.1.0.dsdl
     uavcan/si/sample/voltage/Scalar.1.0.dsdl
     uavcan/si/sample/magnetic_field_strength/Vector3.1.1.dsdl
     uavcan/si/sample/magnetic_field_strength/Vector3.1.0.dsdl
     uavcan/si/sample/magnetic_field_strength/Scalar.1.0.dsdl
     uavcan/si/sample/magnetic_field_strength/Scalar.1.1.dsdl
     uavcan/si/sample/frequency/Scalar.1.0.dsdl
     uavcan/si/sample/angle/Scalar.1.0.dsdl
     uavcan/si/sample/angle/Quaternion.1.0.dsdl
     uavcan/si/sample/energy/Scalar.1.0.dsdl
     uavcan/si/sample/volumetric_flow_rate/Scalar.1.0.dsdl
     uavcan/si/sample/length/Vector3.1.0.dsdl
     uavcan/si/sample/length/Scalar.1.0.dsdl
     uavcan/si/sample/length/WideScalar.1.0.dsdl
     uavcan/si/sample/length/WideVector3.1.0.dsdl
     uavcan/si/sample/velocity/Vector3.1.0.dsdl
     uavcan/si/sample/velocity/Scalar.1.0.dsdl
     uavcan/si/sample/angular_velocity/Vector3.1.0.dsdl
     uavcan/si/sample/angular_velocity/Scalar.1.0.dsdl
     uavcan/si/sample/pressure/Scalar.1.0.dsdl
     uavcan/si/sample/magnetic_flux_density/Vector3.1.0.dsdl
     uavcan/si/sample/magnetic_flux_density/Scalar.1.0.dsdl
     uavcan/si/sample/luminance/Scalar.1.0.dsdl
     uavcan/si/sample/torque/Vector3.1.0.dsdl
     uavcan/si/sample/torque/Scalar.1.0.dsdl
     uavcan/si/sample/force/Vector3.1.0.dsdl
     uavcan/si/sample/force/Scalar.1.0.dsdl
     uavcan/si/sample/temperature/Scalar.1.0.dsdl
     uavcan/si/sample/duration/Scalar.1.0.dsdl
     uavcan/si/sample/duration/WideScalar.1.0.dsdl
     uavcan/si/sample/angular_acceleration/Vector3.1.0.dsdl
     uavcan/si/sample/angular_acceleration/Scalar.1.0.dsdl
     uavcan/si/sample/volume/Scalar.1.0.dsdl
     uavcan/si/sample/electric_charge/Scalar.1.0.dsdl
     uavcan/metatransport/can/ArbitrationID.0.1.dsdl
     uavcan/metatransport/can/Frame.0.2.dsdl
     uavcan/metatransport/can/DataFD.0.1.dsdl
     uavcan/metatransport/can/Error.0.1.dsdl
     uavcan/metatransport/can/DataClassic.0.1.dsdl
     uavcan/metatransport/can/Frame.0.1.dsdl
     uavcan/metatransport/can/Manifestation.0.1.dsdl
     uavcan/metatransport/can/RTR.0.1.dsdl
     uavcan/metatransport/can/BaseArbitrationID.0.1.dsdl
     uavcan/metatransport/can/ExtendedArbitrationID.0.1.dsdl
     uavcan/metatransport/udp/Frame.0.1.dsdl
     uavcan/metatransport/udp/Endpoint.0.1.dsdl
     uavcan/metatransport/ethernet/EtherType.0.1.dsdl
     uavcan/metatransport/ethernet/Frame.0.1.dsdl
     uavcan/metatransport/serial/Fragment.0.2.dsdl
     uavcan/metatransport/serial/Fragment.0.1.dsdl
     uavcan/node/435.ExecuteCommand.1.0.dsdl
     uavcan/node/430.GetInfo.1.0.dsdl
     uavcan/node/435.ExecuteCommand.1.1.dsdl
     uavcan/node/ID.1.0.dsdl
     uavcan/node/IOStatistics.0.1.dsdl
     uavcan/node/434.GetTransportStatistics.0.1.dsdl
     uavcan/node/Mode.1.0.dsdl
     uavcan/node/port/ServiceIDList.1.0.dsdl
     uavcan/node/port/SubjectIDList.0.1.dsdl
     uavcan/node/port/7510.List.1.0.dsdl
     uavcan/node/port/ID.1.0.dsdl
     uavcan/node/port/7510.List.0.1.dsdl
     uavcan/node/port/ServiceIDList.0.1.dsdl
     uavcan/node/port/SubjectIDList.1.0.dsdl
     uavcan/node/port/ServiceID.1.0.dsdl
     uavcan/node/port/SubjectID.1.0.dsdl
     uavcan/node/435.ExecuteCommand.1.2.dsdl
     uavcan/node/7509.Heartbeat.1.0.dsdl
     uavcan/node/435.ExecuteCommand.1.3.dsdl
     uavcan/node/Health.1.0.dsdl
     uavcan/node/Version.1.0.dsdl
     uavcan/pnp/cluster/390.AppendEntries.1.0.dsdl
     uavcan/pnp/cluster/391.RequestVote.1.0.dsdl
     uavcan/pnp/cluster/Entry.1.0.dsdl
     uavcan/pnp/cluster/8164.Discovery.1.0.dsdl
     uavcan/pnp/8165.NodeIDAllocationData.2.0.dsdl
     uavcan/pnp/8166.NodeIDAllocationData.1.0.dsdl
)

set(LOCAL_NAMESPACE_TEST0_REGULATED ${CMAKE_CURRENT_SOURCE_DIR}/nunavut_test_types/test0/regulated)
set(LOCAL_TEST_TYPES_TEST0_REGULATED
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/CombinatorialExplosion.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/RGB888_3840x2748.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/basics/300.Service.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/basics/7000.Struct_.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/basics/DelimitedFixedSize.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/basics/DelimitedVariableSize.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/basics/Primitive.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/basics/PrimitiveArrayFixed.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/basics/PrimitiveArrayVariable.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/basics/Union.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/basics/UnionWithSameTypes.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/delimited/A.1.0.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/delimited/A.1.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/delimited/BDelimited.1.0.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/delimited/BDelimited.1.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/delimited/BSealed.1.0.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/delimited/CFixed.1.0.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/delimited/CFixed.1.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/delimited/CVariable.1.0.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/delimited/CVariable.1.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/drone/sensor/BMSInfo.1.0.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/drone/sensor/BMSStatus.1.0.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/drone/sensor/BMSStatusValue.1.0.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/drone/sensor/BatteryChemistry.1.0.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/zubax/actuator/esc/AngVelSetpoint.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/zubax/actuator/esc/RatiometricSetpoint.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/zubax/actuator/esc/Status.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/zubax/sensor/bms/BatteryPackParams.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/zubax/sensor/bms/BatteryPackStatus.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/zubax/sensor/bms/Technology.0.1.dsdl
     ${LOCAL_NAMESPACE_TEST0_REGULATED}/zubax/sensor/wattmeter/DCSample.0.1.dsdl
)

set(LOCAL_NAMESPACE_NESTED_ARRAY_TYPES ${CMAKE_CURRENT_SOURCE_DIR}/nunavut_test_types/nested_array_types/mymsgs)
set(LOCAL_NESTED_ARRAY_TYPES
     ${LOCAL_NAMESPACE_NESTED_ARRAY_TYPES}/Inner.1.0.dsdl
     ${LOCAL_NAMESPACE_NESTED_ARRAY_TYPES}/InnerMore.1.0.dsdl
     ${LOCAL_NAMESPACE_NESTED_ARRAY_TYPES}/Outer.1.0.dsdl
     ${LOCAL_NAMESPACE_NESTED_ARRAY_TYPES}/OuterMore.1.0.dsdl
     ${LOCAL_NAMESPACE_NESTED_ARRAY_TYPES}/Simple.1.0.dsdl
)

# +-[C-TYPES]-----------------------------------------------------------------+
#
# Generate additional types for verification
#

if(LOCAL_NUNAVUT_VERIFICATION_TARGET_LANG STREQUAL "cpp")
     set(LOCAL_C_ONLY_GENERATOR_ARGS "--option" "cpp_safe_c=true")
else()
     set(LOCAL_C_ONLY_GENERATOR_ARGS "--option" "cpp_safe_c=false")
endif()

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
     EXTRA_GENERATOR_ARGS
          ${LOCAL_C_ONLY_GENERATOR_ARGS}
          "$<$<CONFIG:Debug,DebugAsan,DebugCov>:--enable-serialization-asserts>"
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

     if(${CMAKE_CROSSCOMPILING})
          set(LOCAL_CPP_ASSERT_FUNCTION "assert")
     else()
          set(LOCAL_CPP_ASSERT_FUNCTION "EXPECT_TRUE")
     endif()
     target_compile_definitions(${LOCAL_TEST_TYPES_C_LIBRARY} INTERFACE "$<$<CONFIG:Debug,DebugAsan,DebugCov>:-DNUNAVUT_ASSERT=${LOCAL_CPP_ASSERT_FUNCTION}>")
     target_compile_definitions(${LOCAL_TEST_TYPES_CPP_LIBRARY} INTERFACE "$<$<CONFIG:Debug,DebugAsan,DebugCov>:-DNUNAVUT_ASSERT=${LOCAL_CPP_ASSERT_FUNCTION}>")
else()
     if(${CMAKE_CROSSCOMPILING})
          set(LOCAL_C_ASSERT_FUNCTION "assert")
     else()
          set(LOCAL_C_ASSERT_FUNCTION "TEST_ASSERT_TRUE")
     endif()
     target_compile_definitions(${LOCAL_TEST_TYPES_C_LIBRARY} INTERFACE
          "$<$<CONFIG:Debug,DebugCov>:-DNUNAVUT_ASSERT=${LOCAL_C_ASSERT_FUNCTION}>"
          "$<$<CONFIG:DebugAsan>:-DNUNAVUT_ASSERT=assert>"
     )
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


function(compileTestMcu)
     set(options "")
     set(oneValueArgs TEST_FILE)
     set(multiValueArgs LINK LANGUAGE_FLAVORS)
     cmake_parse_arguments(compileTestBinary "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

     # Skip tests not relevant to the specified language standard
     list(FIND compileTestBinary_LANGUAGE_FLAVORS "${LOCAL_VERIFICATION_LANGUAGE_STANDARD_CPP}" FIND_INDEX)

     if(${FIND_INDEX} EQUAL -1)
          list(FIND compileTestBinary_LANGUAGE_FLAVORS "${LOCAL_VERIFICATION_LANGUAGE_STANDARD_C}" FIND_INDEX)

          if(${FIND_INDEX} EQUAL -1)
               message(STATUS "Skipping ${compileTestBinary_TEST_FILE}")
               return()
          endif()
     endif()

     set(NATIVE_TEST "${CMAKE_CURRENT_SOURCE_DIR}/${LOCAL_NUNAVUT_VERIFICATION_TARGET_LANG}/suite/${compileTestBinary_TEST_FILE}")
     get_filename_component(NATIVE_TEST_NAME ${NATIVE_TEST} NAME_WE)

     add_executable(${NATIVE_TEST_NAME}
          ${NATIVE_TEST}
          ${CMAKE_CURRENT_SOURCE_DIR}/cmake/dummysys.c
     )

     target_link_libraries(${NATIVE_TEST_NAME} PUBLIC ${compileTestBinary_LINK})

     set_target_properties(${NATIVE_TEST_NAME} PROPERTIES SUFFIX ".elf")

     target_link_options(${NATIVE_TEST_NAME} PUBLIC
          "-T" "${CMAKE_CURRENT_SOURCE_DIR}/cmake/samd21g18a.ld"
          "LINKER:-Map=${CMAKE_CURRENT_BINARY_DIR}/$<CONFIG>/${NATIVE_TEST_NAME}.map,--cref"
     )

     add_custom_command(OUTPUT $<CONFIG>/${NATIVE_TEST_NAME}-disassembly.S
          DEPENDS ${NATIVE_TEST_NAME}
          COMMAND ${CMAKE_OBJDUMP} -d $<TARGET_FILE:${NATIVE_TEST_NAME}>
               -marm
               --demangle
               --disassemble-zeroes
               --disassembler-options=reg-names-std
               --syms
               --special-syms
               --all-headers
               --wide > $<CONFIG>/${NATIVE_TEST_NAME}-disassembly.S
          COMMENT "Creating disassembly from ${NATIVE_TEST_NAME}.elf"
     )

     add_custom_target(${NATIVE_TEST_NAME}-disassembly DEPENDS $<CONFIG>/${NATIVE_TEST_NAME}-disassembly.S)

     add_custom_target(
          build_mcu_tests
          DEPENDS ${NATIVE_TEST_NAME}
     )

     # Some tests use deprecated DSDLs
     target_compile_options(${NATIVE_TEST_NAME} PRIVATE "-Wno-deprecated-declarations")
     target_link_libraries(${NATIVE_TEST_NAME} PUBLIC o1heap)
     target_include_directories(${NATIVE_TEST_NAME} PUBLIC "${NUNAVUT_SUBMODULES_DIR}/CETL/include")
endfunction()


if(LOCAL_NUNAVUT_VERIFICATION_TARGET_LANG STREQUAL "cpp")
if(NOT ${CMAKE_CROSSCOMPILING})
     runTestCpp(TEST_FILE test_serialization.cpp     LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_array_c++17-pmr.cpp   LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS                         c++17-pmr       c++20-pmr)
     runTestCpp(TEST_FILE test_array_cetl++14-17.cpp LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS       cetl++14-17                                )
     runTestCpp(TEST_FILE test_bitarray.cpp          LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_compiles.cpp          LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14             c++17           c++20          )
     runTestCpp(TEST_FILE test_large_bitset.cpp      LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_unionant.cpp          LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14 cetl++14-17 c++17 c++17-pmr c++20 c++20-pmr)
     runTestCpp(TEST_FILE test_unionant_c++14.cpp    LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14                                            )
     runTestCpp(TEST_FILE test_unionant_pmr.cpp      LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS       cetl++14-17       c++17-pmr       c++20-pmr)
     runTestCpp(TEST_FILE test_constant.cpp          LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14             c++17 c++17-pmr c++20 c++20-pmr)
else()
     compileTestMcu(TEST_FILE test_armv7m.cpp        LINK ${LOCAL_TEST_TYPES_C_LIBRARY} ${LOCAL_TEST_TYPES_CPP_LIBRARY} LANGUAGE_FLAVORS c++14 cetl++14-17 c++17 c++17-pmr c++20 c++20-pmr)
endif()
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
if(NOT ${CMAKE_CROSSCOMPILING})
     runTestCpp(TEST_FILE test_canard.cpp                         LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11 c17 c23)
     runTestCpp(TEST_FILE test_support_assert.cpp                 LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11 c17 c23)
     runTestC(  TEST_FILE test_constant.c                         LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11 c17 c23 FRAMEWORK "unity")
     runTestC(  TEST_FILE test_override_variable_array_capacity.c LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11 c17 c23 FRAMEWORK "unity")
     runTestC(  TEST_FILE test_serialization.c                    LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11 c17 c23 FRAMEWORK "unity")
     runTestC(  TEST_FILE test_support.c                          LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11 c17 c23 FRAMEWORK "unity")
     runTestC(  TEST_FILE test_simple.c                           LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11 c17 c23 FRAMEWORK "none")
else()
     compileTestMcu(TEST_FILE test_armv7m.c                       LINK ${LOCAL_TEST_TYPES_C_LIBRARY} LANGUAGE_FLAVORS c11 c17 c23)
endif()
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
