/*
 * @copyright
 * Copyright (C) OpenCyphal Development Team  <opencyphal.org>
 * Copyright Amazon.com Inc. or its affiliates.
 * SPDX-License-Identifier: MIT
 * Authors: Scott Dixon <dixonsco@amazon.com>, Pavel Pletenev <cpp.create@gmail.com>
 * Sanity tests.
 */

#include "gmock/gmock.h"
#include "uavcan/file/Path_1_0.hpp"
#include "uavcan/file/Write_1_1.hpp"
#include "uavcan/file/Modify_1_1.hpp"
#include "uavcan/file/List_0_2.hpp"
#include "uavcan/file/GetInfo_0_2.hpp"
#include "uavcan/file/Modify_1_0.hpp"
#include "uavcan/file/Write_1_0.hpp"
#include "uavcan/file/GetInfo_0_1.hpp"
#include "uavcan/file/Path_2_0.hpp"
#include "uavcan/file/List_0_1.hpp"
#include "uavcan/file/Error_1_0.hpp"
#include "uavcan/file/Read_1_1.hpp"
#include "uavcan/file/Read_1_0.hpp"
#include "uavcan/diagnostic/Record_1_1.hpp"
#include "uavcan/diagnostic/Severity_1_0.hpp"
#include "uavcan/diagnostic/Record_1_0.hpp"
#include "uavcan/primitive/array/Integer32_1_0.hpp"
#include "uavcan/primitive/array/Bit_1_0.hpp"
#include "uavcan/primitive/array/Real16_1_0.hpp"
#include "uavcan/primitive/array/Integer16_1_0.hpp"
#include "uavcan/primitive/array/Real32_1_0.hpp"
#include "uavcan/primitive/array/Natural64_1_0.hpp"
#include "uavcan/primitive/array/Integer64_1_0.hpp"
#include "uavcan/primitive/array/Natural8_1_0.hpp"
#include "uavcan/primitive/array/Natural16_1_0.hpp"
#include "uavcan/primitive/array/Integer8_1_0.hpp"
#include "uavcan/primitive/array/Real64_1_0.hpp"
#include "uavcan/primitive/array/Natural32_1_0.hpp"
#include "uavcan/primitive/Empty_1_0.hpp"
#include "uavcan/primitive/String_1_0.hpp"
#include "uavcan/primitive/Unstructured_1_0.hpp"
#include "uavcan/primitive/scalar/Integer32_1_0.hpp"
#include "uavcan/primitive/scalar/Bit_1_0.hpp"
#include "uavcan/primitive/scalar/Real16_1_0.hpp"
#include "uavcan/primitive/scalar/Integer16_1_0.hpp"
#include "uavcan/primitive/scalar/Real32_1_0.hpp"
#include "uavcan/primitive/scalar/Natural64_1_0.hpp"
#include "uavcan/primitive/scalar/Integer64_1_0.hpp"
#include "uavcan/primitive/scalar/Natural8_1_0.hpp"
#include "uavcan/primitive/scalar/Natural16_1_0.hpp"
#include "uavcan/primitive/scalar/Integer8_1_0.hpp"
#include "uavcan/primitive/scalar/Real64_1_0.hpp"
#include "uavcan/primitive/scalar/Natural32_1_0.hpp"
#include "uavcan/time/TAIInfo_0_1.hpp"
#include "uavcan/time/Synchronization_1_0.hpp"
#include "uavcan/time/TimeSystem_0_1.hpp"
#include "uavcan/time/SynchronizedTimestamp_1_0.hpp"
#include "uavcan/time/GetSynchronizationMasterInfo_0_1.hpp"
#include "uavcan/_register/List_1_0.hpp"
#include "uavcan/_register/Name_1_0.hpp"
#include "uavcan/_register/Value_1_0.hpp"
#include "uavcan/_register/Access_1_0.hpp"
#include "uavcan/internet/udp/OutgoingPacket_0_2.hpp"
#include "uavcan/internet/udp/HandleIncomingPacket_0_2.hpp"
#include "uavcan/internet/udp/HandleIncomingPacket_0_1.hpp"
#include "uavcan/internet/udp/OutgoingPacket_0_1.hpp"
#include "uavcan/si/unit/power/Scalar_1_0.hpp"
#include "uavcan/si/unit/electric_current/Scalar_1_0.hpp"
#include "uavcan/si/unit/acceleration/Vector3_1_0.hpp"
#include "uavcan/si/unit/acceleration/Scalar_1_0.hpp"
#include "uavcan/si/unit/mass/Scalar_1_0.hpp"
#include "uavcan/si/unit/voltage/Scalar_1_0.hpp"
#include "uavcan/si/unit/magnetic_field_strength/Vector3_1_1.hpp"
#include "uavcan/si/unit/magnetic_field_strength/Vector3_1_0.hpp"
#include "uavcan/si/unit/magnetic_field_strength/Scalar_1_0.hpp"
#include "uavcan/si/unit/magnetic_field_strength/Scalar_1_1.hpp"
#include "uavcan/si/unit/frequency/Scalar_1_0.hpp"
#include "uavcan/si/unit/angle/Scalar_1_0.hpp"
#include "uavcan/si/unit/angle/Quaternion_1_0.hpp"
#include "uavcan/si/unit/energy/Scalar_1_0.hpp"
#include "uavcan/si/unit/volumetric_flow_rate/Scalar_1_0.hpp"
#include "uavcan/si/unit/length/Vector3_1_0.hpp"
#include "uavcan/si/unit/length/Scalar_1_0.hpp"
#include "uavcan/si/unit/length/WideScalar_1_0.hpp"
#include "uavcan/si/unit/length/WideVector3_1_0.hpp"
#include "uavcan/si/unit/velocity/Vector3_1_0.hpp"
#include "uavcan/si/unit/velocity/Scalar_1_0.hpp"
#include "uavcan/si/unit/angular_velocity/Vector3_1_0.hpp"
#include "uavcan/si/unit/angular_velocity/Scalar_1_0.hpp"
#include "uavcan/si/unit/pressure/Scalar_1_0.hpp"
#include "uavcan/si/unit/magnetic_flux_density/Vector3_1_0.hpp"
#include "uavcan/si/unit/magnetic_flux_density/Scalar_1_0.hpp"
#include "uavcan/si/unit/luminance/Scalar_1_0.hpp"
#include "uavcan/si/unit/torque/Vector3_1_0.hpp"
#include "uavcan/si/unit/torque/Scalar_1_0.hpp"
#include "uavcan/si/unit/force/Vector3_1_0.hpp"
#include "uavcan/si/unit/force/Scalar_1_0.hpp"
#include "uavcan/si/unit/temperature/Scalar_1_0.hpp"
#include "uavcan/si/unit/duration/Scalar_1_0.hpp"
#include "uavcan/si/unit/duration/WideScalar_1_0.hpp"
#include "uavcan/si/unit/angular_acceleration/Vector3_1_0.hpp"
#include "uavcan/si/unit/angular_acceleration/Scalar_1_0.hpp"
#include "uavcan/si/unit/volume/Scalar_1_0.hpp"
#include "uavcan/si/unit/electric_charge/Scalar_1_0.hpp"
#include "uavcan/si/sample/power/Scalar_1_0.hpp"
#include "uavcan/si/sample/electric_current/Scalar_1_0.hpp"
#include "uavcan/si/sample/acceleration/Vector3_1_0.hpp"
#include "uavcan/si/sample/acceleration/Scalar_1_0.hpp"
#include "uavcan/si/sample/mass/Scalar_1_0.hpp"
#include "uavcan/si/sample/voltage/Scalar_1_0.hpp"
#include "uavcan/si/sample/magnetic_field_strength/Vector3_1_1.hpp"
#include "uavcan/si/sample/magnetic_field_strength/Vector3_1_0.hpp"
#include "uavcan/si/sample/magnetic_field_strength/Scalar_1_0.hpp"
#include "uavcan/si/sample/magnetic_field_strength/Scalar_1_1.hpp"
#include "uavcan/si/sample/frequency/Scalar_1_0.hpp"
#include "uavcan/si/sample/angle/Scalar_1_0.hpp"
#include "uavcan/si/sample/angle/Quaternion_1_0.hpp"
#include "uavcan/si/sample/energy/Scalar_1_0.hpp"
#include "uavcan/si/sample/volumetric_flow_rate/Scalar_1_0.hpp"
#include "uavcan/si/sample/length/Vector3_1_0.hpp"
#include "uavcan/si/sample/length/Scalar_1_0.hpp"
#include "uavcan/si/sample/length/WideScalar_1_0.hpp"
#include "uavcan/si/sample/length/WideVector3_1_0.hpp"
#include "uavcan/si/sample/velocity/Vector3_1_0.hpp"
#include "uavcan/si/sample/velocity/Scalar_1_0.hpp"
#include "uavcan/si/sample/angular_velocity/Vector3_1_0.hpp"
#include "uavcan/si/sample/angular_velocity/Scalar_1_0.hpp"
#include "uavcan/si/sample/pressure/Scalar_1_0.hpp"
#include "uavcan/si/sample/magnetic_flux_density/Vector3_1_0.hpp"
#include "uavcan/si/sample/magnetic_flux_density/Scalar_1_0.hpp"
#include "uavcan/si/sample/luminance/Scalar_1_0.hpp"
#include "uavcan/si/sample/torque/Vector3_1_0.hpp"
#include "uavcan/si/sample/torque/Scalar_1_0.hpp"
#include "uavcan/si/sample/force/Vector3_1_0.hpp"
#include "uavcan/si/sample/force/Scalar_1_0.hpp"
#include "uavcan/si/sample/temperature/Scalar_1_0.hpp"
#include "uavcan/si/sample/duration/Scalar_1_0.hpp"
#include "uavcan/si/sample/duration/WideScalar_1_0.hpp"
#include "uavcan/si/sample/angular_acceleration/Vector3_1_0.hpp"
#include "uavcan/si/sample/angular_acceleration/Scalar_1_0.hpp"
#include "uavcan/si/sample/volume/Scalar_1_0.hpp"
#include "uavcan/si/sample/electric_charge/Scalar_1_0.hpp"
// TODO #377
// #include "uavcan/metatransport/can/ArbitrationID_0_1.hpp"
// #include "uavcan/metatransport/can/Frame_0_2.hpp"
// #include "uavcan/metatransport/can/DataFD_0_1.hpp"
// #include "uavcan/metatransport/can/Error_0_1.hpp"
// #include "uavcan/metatransport/can/DataClassic_0_1.hpp"
// #include "uavcan/metatransport/can/Frame_0_1.hpp"
// #include "uavcan/metatransport/can/Manifestation_0_1.hpp"
// #include "uavcan/metatransport/can/RTR_0_1.hpp"
// #include "uavcan/metatransport/can/BaseArbitrationID_0_1.hpp"
// #include "uavcan/metatransport/can/ExtendedArbitrationID_0_1.hpp"
#include "uavcan/metatransport/udp/Frame_0_1.hpp"
#include "uavcan/metatransport/udp/Endpoint_0_1.hpp"
#include "uavcan/metatransport/ethernet/EtherType_0_1.hpp"
#include "uavcan/metatransport/ethernet/Frame_0_1.hpp"
#include "uavcan/metatransport/serial/Fragment_0_2.hpp"
#include "uavcan/metatransport/serial/Fragment_0_1.hpp"
#include "uavcan/node/ExecuteCommand_1_0.hpp"
#include "uavcan/node/GetInfo_1_0.hpp"
#include "uavcan/node/ExecuteCommand_1_1.hpp"
#include "uavcan/node/ID_1_0.hpp"
#include "uavcan/node/IOStatistics_0_1.hpp"
#include "uavcan/node/GetTransportStatistics_0_1.hpp"
#include "uavcan/node/Mode_1_0.hpp"
#include "uavcan/node/port/ServiceIDList_1_0.hpp"
#include "uavcan/node/port/SubjectIDList_0_1.hpp"
#include "uavcan/node/port/List_1_0.hpp"
#include "uavcan/node/port/ID_1_0.hpp"
#include "uavcan/node/port/List_0_1.hpp"
#include "uavcan/node/port/ServiceIDList_0_1.hpp"
#include "uavcan/node/port/SubjectIDList_1_0.hpp"
#include "uavcan/node/port/ServiceID_1_0.hpp"
#include "uavcan/node/port/SubjectID_1_0.hpp"
#include "uavcan/node/ExecuteCommand_1_2.hpp"
#include "uavcan/node/Heartbeat_1_0.hpp"
#include "uavcan/node/ExecuteCommand_1_3.hpp"
#include "uavcan/node/Health_1_0.hpp"
#include "uavcan/node/Version_1_0.hpp"
#include "uavcan/pnp/cluster/AppendEntries_1_0.hpp"
#include "uavcan/pnp/cluster/RequestVote_1_0.hpp"
#include "uavcan/pnp/cluster/Entry_1_0.hpp"
#include "uavcan/pnp/cluster/Discovery_1_0.hpp"
#include "uavcan/pnp/NodeIDAllocationData_2_0.hpp"
#include "uavcan/pnp/NodeIDAllocationData_1_0.hpp"

/**
 * Compile a default Path_1_0 object.
 */
TEST(CompileTest, testCompileUavcanfilePath_1_0) {
    uavcan::file::Path_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Write_1_1 object.
 */
TEST(CompileTest, testCompileUavcanfileWrite_1_1) {
    uavcan::file::Write_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Modify_1_1 object.
 */
TEST(CompileTest, testCompileUavcanfileModify_1_1) {
    uavcan::file::Modify_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default List_0_2 object.
 */
TEST(CompileTest, testCompileUavcanfileList_0_2) {
    uavcan::file::List_0_2 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default GetInfo_0_2 object.
 */
TEST(CompileTest, testCompileUavcanfileGetInfo_0_2) {
    uavcan::file::GetInfo_0_2 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Modify_1_0 object.
 */
TEST(CompileTest, testCompileUavcanfileModify_1_0) {
    uavcan::file::Modify_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Write_1_0 object.
 */
TEST(CompileTest, testCompileUavcanfileWrite_1_0) {
    uavcan::file::Write_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default GetInfo_0_1 object.
 */
TEST(CompileTest, testCompileUavcanfileGetInfo_0_1) {
    uavcan::file::GetInfo_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Path_2_0 object.
 */
TEST(CompileTest, testCompileUavcanfilePath_2_0) {
    uavcan::file::Path_2_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default List_0_1 object.
 */
TEST(CompileTest, testCompileUavcanfileList_0_1) {
    uavcan::file::List_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Error_1_0 object.
 */
TEST(CompileTest, testCompileUavcanfileError_1_0) {
    uavcan::file::Error_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Read_1_1 object.
 */
TEST(CompileTest, testCompileUavcanfileRead_1_1) {
    uavcan::file::Read_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Read_1_0 object.
 */
TEST(CompileTest, testCompileUavcanfileRead_1_0) {
    uavcan::file::Read_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Record_1_1 object.
 */
TEST(CompileTest, testCompileUavcandiagnosticRecord_1_1) {
    uavcan::diagnostic::Record_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Severity_1_0 object.
 */
TEST(CompileTest, testCompileUavcandiagnosticSeverity_1_0) {
    uavcan::diagnostic::Severity_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Record_1_0 object.
 */
TEST(CompileTest, testCompileUavcandiagnosticRecord_1_0) {
    uavcan::diagnostic::Record_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer32_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivearrayInteger32_1_0) {
    uavcan::primitive::array::Integer32_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Bit_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivearrayBit_1_0) {
    uavcan::primitive::array::Bit_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Real16_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivearrayReal16_1_0) {
    uavcan::primitive::array::Real16_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer16_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivearrayInteger16_1_0) {
    uavcan::primitive::array::Integer16_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Real32_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivearrayReal32_1_0) {
    uavcan::primitive::array::Real32_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural64_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivearrayNatural64_1_0) {
    uavcan::primitive::array::Natural64_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer64_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivearrayInteger64_1_0) {
    uavcan::primitive::array::Integer64_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural8_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivearrayNatural8_1_0) {
    uavcan::primitive::array::Natural8_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural16_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivearrayNatural16_1_0) {
    uavcan::primitive::array::Natural16_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer8_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivearrayInteger8_1_0) {
    uavcan::primitive::array::Integer8_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Real64_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivearrayReal64_1_0) {
    uavcan::primitive::array::Real64_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural32_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivearrayNatural32_1_0) {
    uavcan::primitive::array::Natural32_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Empty_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitiveEmpty_1_0) {
    uavcan::primitive::Empty_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default String_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitiveString_1_0) {
    uavcan::primitive::String_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Unstructured_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitiveUnstructured_1_0) {
    uavcan::primitive::Unstructured_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer32_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivescalarInteger32_1_0) {
    uavcan::primitive::scalar::Integer32_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Bit_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivescalarBit_1_0) {
    uavcan::primitive::scalar::Bit_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Real16_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivescalarReal16_1_0) {
    uavcan::primitive::scalar::Real16_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer16_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivescalarInteger16_1_0) {
    uavcan::primitive::scalar::Integer16_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Real32_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivescalarReal32_1_0) {
    uavcan::primitive::scalar::Real32_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural64_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivescalarNatural64_1_0) {
    uavcan::primitive::scalar::Natural64_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer64_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivescalarInteger64_1_0) {
    uavcan::primitive::scalar::Integer64_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural8_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivescalarNatural8_1_0) {
    uavcan::primitive::scalar::Natural8_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural16_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivescalarNatural16_1_0) {
    uavcan::primitive::scalar::Natural16_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer8_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivescalarInteger8_1_0) {
    uavcan::primitive::scalar::Integer8_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Real64_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivescalarReal64_1_0) {
    uavcan::primitive::scalar::Real64_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural32_1_0 object.
 */
TEST(CompileTest, testCompileUavcanprimitivescalarNatural32_1_0) {
    uavcan::primitive::scalar::Natural32_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default TAIInfo_0_1 object.
 */
TEST(CompileTest, testCompileUavcantimeTAIInfo_0_1) {
    uavcan::time::TAIInfo_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Synchronization_1_0 object.
 */
TEST(CompileTest, testCompileUavcantimeSynchronization_1_0) {
    uavcan::time::Synchronization_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default TimeSystem_0_1 object.
 */
TEST(CompileTest, testCompileUavcantimeTimeSystem_0_1) {
    uavcan::time::TimeSystem_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default SynchronizedTimestamp_1_0 object.
 */
TEST(CompileTest, testCompileUavcantimeSynchronizedTimestamp_1_0) {
    uavcan::time::SynchronizedTimestamp_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default GetSynchronizationMasterInfo_0_1 object.
 */
TEST(CompileTest, testCompileUavcantimeGetSynchronizationMasterInfo_0_1) {
    uavcan::time::GetSynchronizationMasterInfo_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default List_1_0 object.
 */
TEST(CompileTest, testCompileUavcan_registerList_1_0) {
    uavcan::_register::List_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Name_1_0 object.
 */
TEST(CompileTest, testCompileUavcan_registerName_1_0) {
    uavcan::_register::Name_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Value_1_0 object.
 */
TEST(CompileTest, testCompileUavcan_registerValue_1_0) {
    uavcan::_register::Value_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Access_1_0 object.
 */
TEST(CompileTest, testCompileUavcan_registerAccess_1_0) {
    uavcan::_register::Access_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default OutgoingPacket_0_2 object.
 */
TEST(CompileTest, testCompileUavcaninternetudpOutgoingPacket_0_2) {
    uavcan::internet::udp::OutgoingPacket_0_2 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default HandleIncomingPacket_0_2 object.
 */
TEST(CompileTest, testCompileUavcaninternetudpHandleIncomingPacket_0_2) {
    uavcan::internet::udp::HandleIncomingPacket_0_2 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default HandleIncomingPacket_0_1 object.
 */
TEST(CompileTest, testCompileUavcaninternetudpHandleIncomingPacket_0_1) {
    uavcan::internet::udp::HandleIncomingPacket_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default OutgoingPacket_0_1 object.
 */
TEST(CompileTest, testCompileUavcaninternetudpOutgoingPacket_0_1) {
    uavcan::internet::udp::OutgoingPacket_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitpowerScalar_1_0) {
    uavcan::si::unit::power::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitelectric_currentScalar_1_0) {
    uavcan::si::unit::electric_current::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitaccelerationVector3_1_0) {
    uavcan::si::unit::acceleration::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitaccelerationScalar_1_0) {
    uavcan::si::unit::acceleration::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitmassScalar_1_0) {
    uavcan::si::unit::mass::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitvoltageScalar_1_0) {
    uavcan::si::unit::voltage::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_1 object.
 */
TEST(CompileTest, testCompileUavcansiunitmagnetic_field_strengthVector3_1_1) {
    uavcan::si::unit::magnetic_field_strength::Vector3_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitmagnetic_field_strengthVector3_1_0) {
    uavcan::si::unit::magnetic_field_strength::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitmagnetic_field_strengthScalar_1_0) {
    uavcan::si::unit::magnetic_field_strength::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_1 object.
 */
TEST(CompileTest, testCompileUavcansiunitmagnetic_field_strengthScalar_1_1) {
    uavcan::si::unit::magnetic_field_strength::Scalar_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitfrequencyScalar_1_0) {
    uavcan::si::unit::frequency::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitangleScalar_1_0) {
    uavcan::si::unit::angle::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Quaternion_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitangleQuaternion_1_0) {
    uavcan::si::unit::angle::Quaternion_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitenergyScalar_1_0) {
    uavcan::si::unit::energy::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitvolumetric_flow_rateScalar_1_0) {
    uavcan::si::unit::volumetric_flow_rate::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitlengthVector3_1_0) {
    uavcan::si::unit::length::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitlengthScalar_1_0) {
    uavcan::si::unit::length::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default WideScalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitlengthWideScalar_1_0) {
    uavcan::si::unit::length::WideScalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default WideVector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitlengthWideVector3_1_0) {
    uavcan::si::unit::length::WideVector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitvelocityVector3_1_0) {
    uavcan::si::unit::velocity::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitvelocityScalar_1_0) {
    uavcan::si::unit::velocity::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitangular_velocityVector3_1_0) {
    uavcan::si::unit::angular_velocity::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitangular_velocityScalar_1_0) {
    uavcan::si::unit::angular_velocity::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitpressureScalar_1_0) {
    uavcan::si::unit::pressure::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitmagnetic_flux_densityVector3_1_0) {
    uavcan::si::unit::magnetic_flux_density::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitmagnetic_flux_densityScalar_1_0) {
    uavcan::si::unit::magnetic_flux_density::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitluminanceScalar_1_0) {
    uavcan::si::unit::luminance::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunittorqueVector3_1_0) {
    uavcan::si::unit::torque::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunittorqueScalar_1_0) {
    uavcan::si::unit::torque::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitforceVector3_1_0) {
    uavcan::si::unit::force::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitforceScalar_1_0) {
    uavcan::si::unit::force::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunittemperatureScalar_1_0) {
    uavcan::si::unit::temperature::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitdurationScalar_1_0) {
    uavcan::si::unit::duration::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default WideScalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitdurationWideScalar_1_0) {
    uavcan::si::unit::duration::WideScalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitangular_accelerationVector3_1_0) {
    uavcan::si::unit::angular_acceleration::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitangular_accelerationScalar_1_0) {
    uavcan::si::unit::angular_acceleration::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitvolumeScalar_1_0) {
    uavcan::si::unit::volume::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansiunitelectric_chargeScalar_1_0) {
    uavcan::si::unit::electric_charge::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplepowerScalar_1_0) {
    uavcan::si::sample::power::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleelectric_currentScalar_1_0) {
    uavcan::si::sample::electric_current::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleaccelerationVector3_1_0) {
    uavcan::si::sample::acceleration::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleaccelerationScalar_1_0) {
    uavcan::si::sample::acceleration::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplemassScalar_1_0) {
    uavcan::si::sample::mass::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplevoltageScalar_1_0) {
    uavcan::si::sample::voltage::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_1 object.
 */
TEST(CompileTest, testCompileUavcansisamplemagnetic_field_strengthVector3_1_1) {
    uavcan::si::sample::magnetic_field_strength::Vector3_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplemagnetic_field_strengthVector3_1_0) {
    uavcan::si::sample::magnetic_field_strength::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplemagnetic_field_strengthScalar_1_0) {
    uavcan::si::sample::magnetic_field_strength::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_1 object.
 */
TEST(CompileTest, testCompileUavcansisamplemagnetic_field_strengthScalar_1_1) {
    uavcan::si::sample::magnetic_field_strength::Scalar_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplefrequencyScalar_1_0) {
    uavcan::si::sample::frequency::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleangleScalar_1_0) {
    uavcan::si::sample::angle::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Quaternion_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleangleQuaternion_1_0) {
    uavcan::si::sample::angle::Quaternion_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleenergyScalar_1_0) {
    uavcan::si::sample::energy::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplevolumetric_flow_rateScalar_1_0) {
    uavcan::si::sample::volumetric_flow_rate::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplelengthVector3_1_0) {
    uavcan::si::sample::length::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplelengthScalar_1_0) {
    uavcan::si::sample::length::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default WideScalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplelengthWideScalar_1_0) {
    uavcan::si::sample::length::WideScalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default WideVector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplelengthWideVector3_1_0) {
    uavcan::si::sample::length::WideVector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplevelocityVector3_1_0) {
    uavcan::si::sample::velocity::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplevelocityScalar_1_0) {
    uavcan::si::sample::velocity::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleangular_velocityVector3_1_0) {
    uavcan::si::sample::angular_velocity::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleangular_velocityScalar_1_0) {
    uavcan::si::sample::angular_velocity::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplepressureScalar_1_0) {
    uavcan::si::sample::pressure::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplemagnetic_flux_densityVector3_1_0) {
    uavcan::si::sample::magnetic_flux_density::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplemagnetic_flux_densityScalar_1_0) {
    uavcan::si::sample::magnetic_flux_density::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleluminanceScalar_1_0) {
    uavcan::si::sample::luminance::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampletorqueVector3_1_0) {
    uavcan::si::sample::torque::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampletorqueScalar_1_0) {
    uavcan::si::sample::torque::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleforceVector3_1_0) {
    uavcan::si::sample::force::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleforceScalar_1_0) {
    uavcan::si::sample::force::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampletemperatureScalar_1_0) {
    uavcan::si::sample::temperature::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampledurationScalar_1_0) {
    uavcan::si::sample::duration::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default WideScalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampledurationWideScalar_1_0) {
    uavcan::si::sample::duration::WideScalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleangular_accelerationVector3_1_0) {
    uavcan::si::sample::angular_acceleration::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleangular_accelerationScalar_1_0) {
    uavcan::si::sample::angular_acceleration::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisamplevolumeScalar_1_0) {
    uavcan::si::sample::volume::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcansisampleelectric_chargeScalar_1_0) {
    uavcan::si::sample::electric_charge::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
// TODO #377
// /**
//  * Compile a default ArbitrationID_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanmetatransportcanArbitrationID_0_1) {
//     uavcan::metatransport::can::ArbitrationID_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default Frame_0_2 object.
//  */
// TEST(CompileTest, testCompileUavcanmetatransportcanFrame_0_2) {
//     uavcan::metatransport::can::Frame_0_2 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default DataFD_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanmetatransportcanDataFD_0_1) {
//     uavcan::metatransport::can::DataFD_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default Error_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanmetatransportcanError_0_1) {
//     uavcan::metatransport::can::Error_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default DataClassic_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanmetatransportcanDataClassic_0_1) {
//     uavcan::metatransport::can::DataClassic_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default Frame_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanmetatransportcanFrame_0_1) {
//     uavcan::metatransport::can::Frame_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default Manifestation_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanmetatransportcanManifestation_0_1) {
//     uavcan::metatransport::can::Manifestation_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default RTR_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanmetatransportcanRTR_0_1) {
//     uavcan::metatransport::can::RTR_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default BaseArbitrationID_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanmetatransportcanBaseArbitrationID_0_1) {
//     uavcan::metatransport::can::BaseArbitrationID_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default ExtendedArbitrationID_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanmetatransportcanExtendedArbitrationID_0_1) {
//     uavcan::metatransport::can::ExtendedArbitrationID_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
/**
 * Compile a default Frame_0_1 object.
 */
TEST(CompileTest, testCompileUavcanmetatransportudpFrame_0_1) {
    uavcan::metatransport::udp::Frame_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Endpoint_0_1 object.
 */
TEST(CompileTest, testCompileUavcanmetatransportudpEndpoint_0_1) {
    uavcan::metatransport::udp::Endpoint_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default EtherType_0_1 object.
 */
TEST(CompileTest, testCompileUavcanmetatransportethernetEtherType_0_1) {
    uavcan::metatransport::ethernet::EtherType_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Frame_0_1 object.
 */
TEST(CompileTest, testCompileUavcanmetatransportethernetFrame_0_1) {
    uavcan::metatransport::ethernet::Frame_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Fragment_0_2 object.
 */
TEST(CompileTest, testCompileUavcanmetatransportserialFragment_0_2) {
    uavcan::metatransport::serial::Fragment_0_2 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Fragment_0_1 object.
 */
TEST(CompileTest, testCompileUavcanmetatransportserialFragment_0_1) {
    uavcan::metatransport::serial::Fragment_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ExecuteCommand_1_0 object.
 */
TEST(CompileTest, testCompileUavcannodeExecuteCommand_1_0) {
    uavcan::node::ExecuteCommand_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default GetInfo_1_0 object.
 */
TEST(CompileTest, testCompileUavcannodeGetInfo_1_0) {
    uavcan::node::GetInfo_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ExecuteCommand_1_1 object.
 */
TEST(CompileTest, testCompileUavcannodeExecuteCommand_1_1) {
    uavcan::node::ExecuteCommand_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ID_1_0 object.
 */
TEST(CompileTest, testCompileUavcannodeID_1_0) {
    uavcan::node::ID_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default IOStatistics_0_1 object.
 */
TEST(CompileTest, testCompileUavcannodeIOStatistics_0_1) {
    uavcan::node::IOStatistics_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default GetTransportStatistics_0_1 object.
 */
TEST(CompileTest, testCompileUavcannodeGetTransportStatistics_0_1) {
    uavcan::node::GetTransportStatistics_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Mode_1_0 object.
 */
TEST(CompileTest, testCompileUavcannodeMode_1_0) {
    uavcan::node::Mode_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ServiceIDList_1_0 object.
 */
TEST(CompileTest, testCompileUavcannodeportServiceIDList_1_0) {
    uavcan::node::port::ServiceIDList_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default SubjectIDList_0_1 object.
 */
TEST(CompileTest, testCompileUavcannodeportSubjectIDList_0_1) {
    uavcan::node::port::SubjectIDList_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default List_1_0 object.
 */
TEST(CompileTest, testCompileUavcannodeportList_1_0) {
    uavcan::node::port::List_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ID_1_0 object.
 */
TEST(CompileTest, testCompileUavcannodeportID_1_0) {
    uavcan::node::port::ID_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default List_0_1 object.
 */
TEST(CompileTest, testCompileUavcannodeportList_0_1) {
    uavcan::node::port::List_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ServiceIDList_0_1 object.
 */
TEST(CompileTest, testCompileUavcannodeportServiceIDList_0_1) {
    uavcan::node::port::ServiceIDList_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default SubjectIDList_1_0 object.
 */
TEST(CompileTest, testCompileUavcannodeportSubjectIDList_1_0) {
    uavcan::node::port::SubjectIDList_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ServiceID_1_0 object.
 */
TEST(CompileTest, testCompileUavcannodeportServiceID_1_0) {
    uavcan::node::port::ServiceID_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default SubjectID_1_0 object.
 */
TEST(CompileTest, testCompileUavcannodeportSubjectID_1_0) {
    uavcan::node::port::SubjectID_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ExecuteCommand_1_2 object.
 */
TEST(CompileTest, testCompileUavcannodeExecuteCommand_1_2) {
    uavcan::node::ExecuteCommand_1_2 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Heartbeat_1_0 object.
 */
TEST(CompileTest, testCompileUavcannodeHeartbeat_1_0) {
    uavcan::node::Heartbeat_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ExecuteCommand_1_3 object.
 */
TEST(CompileTest, testCompileUavcannodeExecuteCommand_1_3) {
    uavcan::node::ExecuteCommand_1_3 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Health_1_0 object.
 */
TEST(CompileTest, testCompileUavcannodeHealth_1_0) {
    uavcan::node::Health_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Version_1_0 object.
 */
TEST(CompileTest, testCompileUavcannodeVersion_1_0) {
    uavcan::node::Version_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default AppendEntries_1_0 object.
 */
TEST(CompileTest, testCompileUavcanpnpclusterAppendEntries_1_0) {
    uavcan::pnp::cluster::AppendEntries_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default RequestVote_1_0 object.
 */
TEST(CompileTest, testCompileUavcanpnpclusterRequestVote_1_0) {
    uavcan::pnp::cluster::RequestVote_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Entry_1_0 object.
 */
TEST(CompileTest, testCompileUavcanpnpclusterEntry_1_0) {
    uavcan::pnp::cluster::Entry_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Discovery_1_0 object.
 */
TEST(CompileTest, testCompileUavcanpnpclusterDiscovery_1_0) {
    uavcan::pnp::cluster::Discovery_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default NodeIDAllocationData_2_0 object.
 */
TEST(CompileTest, testCompileUavcanpnpNodeIDAllocationData_2_0) {
    uavcan::pnp::NodeIDAllocationData_2_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default NodeIDAllocationData_1_0 object.
 */
TEST(CompileTest, testCompileUavcanpnpNodeIDAllocationData_1_0) {
    uavcan::pnp::NodeIDAllocationData_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
