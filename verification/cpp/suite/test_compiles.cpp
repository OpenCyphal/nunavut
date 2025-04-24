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
TEST(CompileTest, testCompileUavcanFilePath_1_0)
{
    uavcan::file::Path_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Write_1_1 object.
 */
TEST(CompileTest, testCompileUavcanFileWrite_1_1)
{
    ASSERT_TRUE(uavcan::file::Write_1_1::_traits_::IsServiceType);
    uavcan::file::Write_1_1::Request  request{};
    uavcan::file::Write_1_1::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default Modify_1_1 object.
 */
TEST(CompileTest, testCompileUavcanFileModify_1_1)
{
    ASSERT_TRUE(uavcan::file::Modify_1_1::_traits_::IsServiceType);
    uavcan::file::Modify_1_1::Request  request{};
    uavcan::file::Modify_1_1::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default List_0_2 object.
 */
TEST(CompileTest, testCompileUavcanFileList_0_2)
{
    ASSERT_TRUE(uavcan::file::List_0_2::_traits_::IsServiceType);
    uavcan::file::List_0_2::Request  request{};
    uavcan::file::List_0_2::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default GetInfo_0_2 object.
 */
TEST(CompileTest, testCompileUavcanFileGetInfo_0_2)
{
    ASSERT_TRUE(uavcan::file::GetInfo_0_2::_traits_::IsServiceType);
    uavcan::file::GetInfo_0_2::Request  request{};
    uavcan::file::GetInfo_0_2::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default Modify_1_0 object.
 */
TEST(CompileTest, testCompileUavcanFileModify_1_0)
{
    ASSERT_TRUE(uavcan::file::Modify_1_0::_traits_::IsServiceType);
    uavcan::file::Modify_1_0::Request  request{};
    uavcan::file::Modify_1_0::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default Write_1_0 object.
 */
TEST(CompileTest, testCompileUavcanFileWrite_1_0)
{
    ASSERT_TRUE(uavcan::file::Write_1_0::_traits_::IsServiceType);
    uavcan::file::Write_1_0::Request  request{};
    uavcan::file::Write_1_0::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default GetInfo_0_1 object.
 */
TEST(CompileTest, testCompileUavcanFileGetInfo_0_1)
{
    ASSERT_TRUE(uavcan::file::GetInfo_0_1::_traits_::IsServiceType);
    uavcan::file::GetInfo_0_1::Request  request{};
    uavcan::file::GetInfo_0_1::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default Path_2_0 object.
 */
TEST(CompileTest, testCompileUavcanFilePath_2_0)
{
    uavcan::file::Path_2_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default List_0_1 object.
 */
TEST(CompileTest, testCompileUavcanFileList_0_1)
{
    ASSERT_TRUE(uavcan::file::List_0_1::_traits_::IsServiceType);
    uavcan::file::List_0_1::Request  request{};
    uavcan::file::List_0_1::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default Error_1_0 object.
 */
TEST(CompileTest, testCompileUavcanFileError_1_0)
{
    uavcan::file::Error_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Read_1_1 object.
 */
TEST(CompileTest, testCompileUavcanFileRead_1_1)
{
    ASSERT_TRUE(uavcan::file::Read_1_1::_traits_::IsServiceType);
    uavcan::file::Read_1_1::Request  request{};
    uavcan::file::Read_1_1::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default Read_1_0 object.
 */
TEST(CompileTest, testCompileUavcanFileRead_1_0)
{
    ASSERT_TRUE(uavcan::file::Read_1_0::_traits_::IsServiceType);
    uavcan::file::Read_1_0::Request  request{};
    uavcan::file::Read_1_0::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default Record_1_1 object.
 */
TEST(CompileTest, testCompileUavcanDiagnosticRecord_1_1)
{
    uavcan::diagnostic::Record_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Severity_1_0 object.
 */
TEST(CompileTest, testCompileUavcanDiagnosticSeverity_1_0)
{
    uavcan::diagnostic::Severity_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Record_1_0 object.
 */
TEST(CompileTest, testCompileUavcanDiagnosticRecord_1_0)
{
    uavcan::diagnostic::Record_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer32_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivearrayInteger32_1_0)
{
    uavcan::primitive::array::Integer32_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Bit_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivearrayBit_1_0)
{
    uavcan::primitive::array::Bit_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Real16_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivearrayREAL16_1_0)
{
    uavcan::primitive::array::Real16_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer16_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivearrayInteger16_1_0)
{
    uavcan::primitive::array::Integer16_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Real32_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivearrayReal32_1_0)
{
    uavcan::primitive::array::Real32_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural64_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivearrayNatural64_1_0)
{
    uavcan::primitive::array::Natural64_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer64_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivearrayInteger64_1_0)
{
    uavcan::primitive::array::Integer64_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural8_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivearrayNatural8_1_0)
{
    uavcan::primitive::array::Natural8_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural16_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivearrayNatural16_1_0)
{
    uavcan::primitive::array::Natural16_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer8_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivearrayInteger8_1_0)
{
    uavcan::primitive::array::Integer8_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Real64_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivearrayReal64_1_0)
{
    uavcan::primitive::array::Real64_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural32_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivearrayNatural32_1_0)
{
    uavcan::primitive::array::Natural32_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Empty_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitiveEmpty_1_0)
{
    uavcan::primitive::Empty_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default String_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitiveString_1_0)
{
    uavcan::primitive::String_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Unstructured_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitiveUnstructured_1_0)
{
    uavcan::primitive::Unstructured_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer32_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivescalarInteger32_1_0)
{
    uavcan::primitive::scalar::Integer32_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Bit_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivescalarBit_1_0)
{
    uavcan::primitive::scalar::Bit_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Real16_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivescalarReal16_1_0)
{
    uavcan::primitive::scalar::Real16_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer16_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivescalarInteger16_1_0)
{
    uavcan::primitive::scalar::Integer16_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Real32_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivescalarReal32_1_0)
{
    uavcan::primitive::scalar::Real32_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural64_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivescalarNatural64_1_0)
{
    uavcan::primitive::scalar::Natural64_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer64_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivescalarInteger64_1_0)
{
    uavcan::primitive::scalar::Integer64_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural8_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivescalarNatural8_1_0)
{
    uavcan::primitive::scalar::Natural8_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural16_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivescalarNatural16_1_0)
{
    uavcan::primitive::scalar::Natural16_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Integer8_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivescalarInteger8_1_0)
{
    uavcan::primitive::scalar::Integer8_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Real64_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivescalarReal64_1_0)
{
    uavcan::primitive::scalar::Real64_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Natural32_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPrimitivescalarNatural32_1_0)
{
    uavcan::primitive::scalar::Natural32_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default TAIInfo_0_1 object.
 */
TEST(CompileTest, testCompileUavcanTimeTAIInfo_0_1)
{
    uavcan::time::TAIInfo_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Synchronization_1_0 object.
 */
TEST(CompileTest, testCompileUavcanTimeSynchronization_1_0)
{
    uavcan::time::Synchronization_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default TimeSystem_0_1 object.
 */
TEST(CompileTest, testCompileUavcanTimeTimeSystem_0_1)
{
    uavcan::time::TimeSystem_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default SynchronizedTimestamp_1_0 object.
 */
TEST(CompileTest, testCompileUavcanTimeSynchronizedTimestamp_1_0)
{
    uavcan::time::SynchronizedTimestamp_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default GetSynchronizationMasterInfo_0_1 object.
 */
TEST(CompileTest, testCompileUavcanTimeGetSynchronizationMasterInfo_0_1)
{
    ASSERT_TRUE(uavcan::time::GetSynchronizationMasterInfo_0_1::_traits_::IsServiceType);
    uavcan::time::GetSynchronizationMasterInfo_0_1::Request  request{};
    uavcan::time::GetSynchronizationMasterInfo_0_1::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default List_1_0 object.
 */
TEST(CompileTest, testCompileUavcan_registerList_1_0)
{
    ASSERT_TRUE(uavcan::_register::List_1_0::_traits_::IsServiceType);
    uavcan::_register::List_1_0::Request  request{};
    uavcan::_register::List_1_0::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default Name_1_0 object.
 */
TEST(CompileTest, testCompileUavcan_registerName_1_0)
{
    uavcan::_register::Name_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Value_1_0 object.
 */
TEST(CompileTest, testCompileUavcan_registerValue_1_0)
{
    uavcan::_register::Value_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Access_1_0 object.
 */
TEST(CompileTest, testCompileUavcan_registerAccess_1_0)
{
    ASSERT_TRUE(uavcan::_register::Access_1_0::_traits_::IsServiceType);
    uavcan::_register::Access_1_0::Request  request{};
    uavcan::_register::Access_1_0::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default OutgoingPacket_0_2 object.
 */
TEST(CompileTest, testCompileUavcanInternetudpOutgoingPacket_0_2)
{
    uavcan::internet::udp::OutgoingPacket_0_2 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default HandleIncomingPacket_0_2 object.
 */
TEST(CompileTest, testCompileUavcanInternetudpHandleIncomingPacket_0_2)
{
    ASSERT_TRUE(uavcan::internet::udp::HandleIncomingPacket_0_2::_traits_::IsServiceType);
    uavcan::internet::udp::HandleIncomingPacket_0_2::Request  request{};
    uavcan::internet::udp::HandleIncomingPacket_0_2::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default HandleIncomingPacket_0_1 object.
 */
TEST(CompileTest, testCompileUavcanInternetudpHandleIncomingPacket_0_1)
{
    ASSERT_TRUE(uavcan::internet::udp::HandleIncomingPacket_0_1::_traits_::IsServiceType);
    uavcan::internet::udp::HandleIncomingPacket_0_1::Request  request{};
    uavcan::internet::udp::HandleIncomingPacket_0_1::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default OutgoingPacket_0_1 object.
 */
TEST(CompileTest, testCompileUavcanInternetudpOutgoingPacket_0_1)
{
    uavcan::internet::udp::OutgoingPacket_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitPowerScalar_1_0)
{
    uavcan::si::unit::power::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitElectric_currentScalar_1_0)
{
    uavcan::si::unit::electric_current::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitAccelerationVector3_1_0)
{
    uavcan::si::unit::acceleration::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitAccelerationScalar_1_0)
{
    uavcan::si::unit::acceleration::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitMassScalar_1_0)
{
    uavcan::si::unit::mass::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitVoltageScalar_1_0)
{
    uavcan::si::unit::voltage::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_1 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitMagnetic_field_strengthVector3_1_1)
{
    uavcan::si::unit::magnetic_field_strength::Vector3_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitMagnetic_field_strengthVector3_1_0)
{
    uavcan::si::unit::magnetic_field_strength::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitMagnetic_field_strengthScalar_1_0)
{
    uavcan::si::unit::magnetic_field_strength::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_1 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitMagnetic_field_strengthScalar_1_1)
{
    uavcan::si::unit::magnetic_field_strength::Scalar_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitFrequencyScalar_1_0)
{
    uavcan::si::unit::frequency::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitAngleScalar_1_0)
{
    uavcan::si::unit::angle::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Quaternion_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitAngleQuaternion_1_0)
{
    uavcan::si::unit::angle::Quaternion_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitEnergyScalar_1_0)
{
    uavcan::si::unit::energy::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitVolumetric_flow_rateScalar_1_0)
{
    uavcan::si::unit::volumetric_flow_rate::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitLengthVector3_1_0)
{
    uavcan::si::unit::length::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitLengthScalar_1_0)
{
    uavcan::si::unit::length::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default WideScalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitLengthWideScalar_1_0)
{
    uavcan::si::unit::length::WideScalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default WideVector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitLengthWideVector3_1_0)
{
    uavcan::si::unit::length::WideVector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitVelocityVector3_1_0)
{
    uavcan::si::unit::velocity::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitVelocityScalar_1_0)
{
    uavcan::si::unit::velocity::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitAngular_velocityVector3_1_0)
{
    uavcan::si::unit::angular_velocity::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitAngular_velocityScalar_1_0)
{
    uavcan::si::unit::angular_velocity::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitPressureScalar_1_0)
{
    uavcan::si::unit::pressure::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitMagnetic_flux_densityVector3_1_0)
{
    uavcan::si::unit::magnetic_flux_density::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitMagnetic_flux_densityScalar_1_0)
{
    uavcan::si::unit::magnetic_flux_density::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitLuminanceScalar_1_0)
{
    uavcan::si::unit::luminance::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitTorqueVector3_1_0)
{
    uavcan::si::unit::torque::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitTorqueScalar_1_0)
{
    uavcan::si::unit::torque::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitForceVector3_1_0)
{
    uavcan::si::unit::force::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitForceScalar_1_0)
{
    uavcan::si::unit::force::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitTemperatureScalar_1_0)
{
    uavcan::si::unit::temperature::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitDurationScalar_1_0)
{
    uavcan::si::unit::duration::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default WideScalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitDurationWideScalar_1_0)
{
    uavcan::si::unit::duration::WideScalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitAngular_accelerationVector3_1_0)
{
    uavcan::si::unit::angular_acceleration::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitAngular_accelerationScalar_1_0)
{
    uavcan::si::unit::angular_acceleration::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitVolumeScalar_1_0)
{
    uavcan::si::unit::volume::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSiUnitElectric_chargeScalar_1_0)
{
    uavcan::si::unit::electric_charge::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplepowerScalar_1_0)
{
    uavcan::si::sample::power::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleelectric_currentScalar_1_0)
{
    uavcan::si::sample::electric_current::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleaccelerationVector3_1_0)
{
    uavcan::si::sample::acceleration::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleaccelerationScalar_1_0)
{
    uavcan::si::sample::acceleration::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplemassScalar_1_0)
{
    uavcan::si::sample::mass::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplevoltageScalar_1_0)
{
    uavcan::si::sample::voltage::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_1 object.
 */
TEST(CompileTest, testCompileUavcanSisamplemagnetic_field_strengthVector3_1_1)
{
    uavcan::si::sample::magnetic_field_strength::Vector3_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplemagnetic_field_strengthVector3_1_0)
{
    uavcan::si::sample::magnetic_field_strength::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplemagnetic_field_strengthScalar_1_0)
{
    uavcan::si::sample::magnetic_field_strength::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_1 object.
 */
TEST(CompileTest, testCompileUavcanSisamplemagnetic_field_strengthScalar_1_1)
{
    uavcan::si::sample::magnetic_field_strength::Scalar_1_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplefrequencyScalar_1_0)
{
    uavcan::si::sample::frequency::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleangleScalar_1_0)
{
    uavcan::si::sample::angle::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Quaternion_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleangleQuaternion_1_0)
{
    uavcan::si::sample::angle::Quaternion_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleenergyScalar_1_0)
{
    uavcan::si::sample::energy::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplevolumetric_flow_rateScalar_1_0)
{
    uavcan::si::sample::volumetric_flow_rate::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplelengthVector3_1_0)
{
    uavcan::si::sample::length::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplelengthScalar_1_0)
{
    uavcan::si::sample::length::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default WideScalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplelengthWideScalar_1_0)
{
    uavcan::si::sample::length::WideScalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default WideVector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplelengthWideVector3_1_0)
{
    uavcan::si::sample::length::WideVector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplevelocityVector3_1_0)
{
    uavcan::si::sample::velocity::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplevelocityScalar_1_0)
{
    uavcan::si::sample::velocity::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleangular_velocityVector3_1_0)
{
    uavcan::si::sample::angular_velocity::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleangular_velocityScalar_1_0)
{
    uavcan::si::sample::angular_velocity::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplepressureScalar_1_0)
{
    uavcan::si::sample::pressure::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplemagnetic_flux_densityVector3_1_0)
{
    uavcan::si::sample::magnetic_flux_density::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplemagnetic_flux_densityScalar_1_0)
{
    uavcan::si::sample::magnetic_flux_density::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleluminanceScalar_1_0)
{
    uavcan::si::sample::luminance::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampletorqueVector3_1_0)
{
    uavcan::si::sample::torque::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampletorqueScalar_1_0)
{
    uavcan::si::sample::torque::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleforceVector3_1_0)
{
    uavcan::si::sample::force::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleforceScalar_1_0)
{
    uavcan::si::sample::force::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampletemperatureScalar_1_0)
{
    uavcan::si::sample::temperature::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampledurationScalar_1_0)
{
    uavcan::si::sample::duration::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default WideScalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampledurationWideScalar_1_0)
{
    uavcan::si::sample::duration::WideScalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Vector3_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleangular_accelerationVector3_1_0)
{
    uavcan::si::sample::angular_acceleration::Vector3_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleangular_accelerationScalar_1_0)
{
    uavcan::si::sample::angular_acceleration::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisamplevolumeScalar_1_0)
{
    uavcan::si::sample::volume::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Scalar_1_0 object.
 */
TEST(CompileTest, testCompileUavcanSisampleelectric_chargeScalar_1_0)
{
    uavcan::si::sample::electric_charge::Scalar_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
// TODO #377
// /**
//  * Compile a default ArbitrationID_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanMetatransportcanArbitrationID_0_1) {
//     uavcan::metatransport::can::ArbitrationID_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default Frame_0_2 object.
//  */
// TEST(CompileTest, testCompileUavcanMetatransportcanFrame_0_2) {
//     uavcan::metatransport::can::Frame_0_2 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default DataFD_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanMetatransportcanDataFD_0_1) {
//     uavcan::metatransport::can::DataFD_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default Error_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanMetatransportcanError_0_1) {
//     uavcan::metatransport::can::Error_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default DataClassic_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanMetatransportcanDataClassic_0_1) {
//     uavcan::metatransport::can::DataClassic_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default Frame_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanMetatransportcanFrame_0_1) {
//     uavcan::metatransport::can::Frame_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default Manifestation_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanMetatransportcanManifestation_0_1) {
//     uavcan::metatransport::can::Manifestation_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default RTR_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanMetatransportcanRTR_0_1) {
//     uavcan::metatransport::can::RTR_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default BaseArbitrationID_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanMetatransportcanBaseArbitrationID_0_1) {
//     uavcan::metatransport::can::BaseArbitrationID_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
// /**
//  * Compile a default ExtendedArbitrationID_0_1 object.
//  */
// TEST(CompileTest, testCompileUavcanMetatransportcanExtendedArbitrationID_0_1) {
//     uavcan::metatransport::can::ExtendedArbitrationID_0_1 a{};
//     ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
// }
/**
 * Compile a default Frame_0_1 object.
 */
TEST(CompileTest, testCompileUavcanMetatransportudpFrame_0_1)
{
    uavcan::metatransport::udp::Frame_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Endpoint_0_1 object.
 */
TEST(CompileTest, testCompileUavcanMetatransportudpEndpoint_0_1)
{
    uavcan::metatransport::udp::Endpoint_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default EtherType_0_1 object.
 */
TEST(CompileTest, testCompileUavcanMetatransportethernetEtherType_0_1)
{
    uavcan::metatransport::ethernet::EtherType_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Frame_0_1 object.
 */
TEST(CompileTest, testCompileUavcanMetatransportethernetFrame_0_1)
{
    uavcan::metatransport::ethernet::Frame_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Fragment_0_2 object.
 */
TEST(CompileTest, testCompileUavcanMetatransportserialFragment_0_2)
{
    uavcan::metatransport::serial::Fragment_0_2 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Fragment_0_1 object.
 */
TEST(CompileTest, testCompileUavcanMetatransportserialFragment_0_1)
{
    uavcan::metatransport::serial::Fragment_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ExecuteCommand_1_0 object.
 */
TEST(CompileTest, testCompileUavcanNodeExecuteCommand_1_0)
{
    ASSERT_TRUE(uavcan::node::ExecuteCommand_1_0::_traits_::IsServiceType);
    uavcan::node::ExecuteCommand_1_0::Request  request{};
    uavcan::node::ExecuteCommand_1_0::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default GetInfo_1_0 object.
 */
TEST(CompileTest, testCompileUavcanNodeGetInfo_1_0)
{
    ASSERT_TRUE(uavcan::node::GetInfo_1_0::_traits_::IsServiceType);
    uavcan::node::GetInfo_1_0::Request  request{};
    uavcan::node::GetInfo_1_0::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default ExecuteCommand_1_1 object.
 */
TEST(CompileTest, testCompileUavcanNodeExecuteCommand_1_1)
{
    ASSERT_TRUE(uavcan::node::ExecuteCommand_1_1::_traits_::IsServiceType);
    uavcan::node::ExecuteCommand_1_1::Request  request{};
    uavcan::node::ExecuteCommand_1_1::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default ID_1_0 object.
 */
TEST(CompileTest, testCompileUavcanNodeID_1_0)
{
    uavcan::node::ID_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default IOStatistics_0_1 object.
 */
TEST(CompileTest, testCompileUavcanNodeIOStatistics_0_1)
{
    uavcan::node::IOStatistics_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default GetTransportStatistics_0_1 object.
 */
TEST(CompileTest, testCompileUavcanNodeGetTransportStatistics_0_1)
{
    ASSERT_TRUE(uavcan::node::GetTransportStatistics_0_1::_traits_::IsServiceType);
    uavcan::node::GetTransportStatistics_0_1::Request  request{};
    uavcan::node::GetTransportStatistics_0_1::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default Mode_1_0 object.
 */
TEST(CompileTest, testCompileUavcanNodeMode_1_0)
{
    uavcan::node::Mode_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ServiceIDList_1_0 object.
 */
TEST(CompileTest, testCompileUavcanNodeportServiceIDList_1_0)
{
    uavcan::node::port::ServiceIDList_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default SubjectIDList_0_1 object.
 */
TEST(CompileTest, testCompileUavcanNodeportSubjectIDList_0_1)
{
    uavcan::node::port::SubjectIDList_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default List_1_0 object.
 */
TEST(CompileTest, testCompileUavcanNodeportList_1_0)
{
    uavcan::node::port::List_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ID_1_0 object.
 */
TEST(CompileTest, testCompileUavcanNodeportID_1_0)
{
    uavcan::node::port::ID_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default List_0_1 object.
 */
TEST(CompileTest, testCompileUavcanNodeportList_0_1)
{
    uavcan::node::port::List_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ServiceIDList_0_1 object.
 */
TEST(CompileTest, testCompileUavcanNodeportServiceIDList_0_1)
{
    uavcan::node::port::ServiceIDList_0_1 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default SubjectIDList_1_0 object.
 */
TEST(CompileTest, testCompileUavcanNodeportSubjectIDList_1_0)
{
    uavcan::node::port::SubjectIDList_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ServiceID_1_0 object.
 */
TEST(CompileTest, testCompileUavcanNodeportServiceID_1_0)
{
    uavcan::node::port::ServiceID_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default SubjectID_1_0 object.
 */
TEST(CompileTest, testCompileUavcanNodeportSubjectID_1_0)
{
    uavcan::node::port::SubjectID_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ExecuteCommand_1_2 object.
 */
TEST(CompileTest, testCompileUavcanNodeExecuteCommand_1_2)
{
    ASSERT_TRUE(uavcan::node::ExecuteCommand_1_2::_traits_::IsServiceType);
    uavcan::node::ExecuteCommand_1_2::Request  request{};
    uavcan::node::ExecuteCommand_1_2::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default Heartbeat_1_0 object.
 */
TEST(CompileTest, testCompileUavcanNodeHeartbeat_1_0)
{
    uavcan::node::Heartbeat_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default ExecuteCommand_1_3 object.
 */
TEST(CompileTest, testCompileUavcanNodeExecuteCommand_1_3)
{
    ASSERT_TRUE(uavcan::node::ExecuteCommand_1_3::_traits_::IsServiceType);
    uavcan::node::ExecuteCommand_1_3::Request  request{};
    uavcan::node::ExecuteCommand_1_3::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default Health_1_0 object.
 */
TEST(CompileTest, testCompileUavcanNodeHealth_1_0)
{
    uavcan::node::Health_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Version_1_0 object.
 */
TEST(CompileTest, testCompileUavcanNodeVersion_1_0)
{
    uavcan::node::Version_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default AppendEntries_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPnpClusterAppendEntries_1_0)
{
    ASSERT_TRUE(uavcan::pnp::cluster::AppendEntries_1_0::_traits_::IsServiceType);
    uavcan::pnp::cluster::AppendEntries_1_0::Request  request{};
    uavcan::pnp::cluster::AppendEntries_1_0::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default RequestVote_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPnpClusterRequestVote_1_0)
{
    ASSERT_TRUE(uavcan::pnp::cluster::RequestVote_1_0::_traits_::IsServiceType);
    uavcan::pnp::cluster::RequestVote_1_0::Request  request{};
    uavcan::pnp::cluster::RequestVote_1_0::Response response{};
    static_cast<void>(request);
    static_cast<void>(response);
}
/**
 * Compile a default Entry_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPnpClusterEntry_1_0)
{
    uavcan::pnp::cluster::Entry_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default Discovery_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPnpClusterDiscovery_1_0)
{
    uavcan::pnp::cluster::Discovery_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default NodeIDAllocationData_2_0 object.
 */
TEST(CompileTest, testCompileUavcanPnpNodeIDAllocationData_2_0)
{
    uavcan::pnp::NodeIDAllocationData_2_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}
/**
 * Compile a default NodeIDAllocationData_1_0 object.
 */
TEST(CompileTest, testCompileUavcanPnpNodeIDAllocationData_1_0)
{
    uavcan::pnp::NodeIDAllocationData_1_0 a{};
    ASSERT_FALSE(decltype(a)::_traits_::IsServiceType);
}

#if __cplusplus >= 201402L
namespace uavcan
{

namespace time
{
constexpr const bool GetSynchronizationMasterInfo_0_1::_traits_::IsServiceType;
}

namespace pnp
{
namespace cluster
{
constexpr const bool AppendEntries_1_0::_traits_::IsServiceType;
constexpr const bool RequestVote_1_0::_traits_::IsServiceType;
}  // namespace cluster
}  // namespace pnp

namespace file
{
constexpr const bool Write_1_1::_traits_::IsServiceType;
constexpr const bool Write_1_0::_traits_::IsServiceType;
constexpr const bool Modify_1_1::_traits_::IsServiceType;
constexpr const bool Modify_1_0::_traits_::IsServiceType;
constexpr const bool List_0_2::_traits_::IsServiceType;
constexpr const bool List_0_1::_traits_::IsServiceType;
constexpr const bool GetInfo_0_2::_traits_::IsServiceType;
constexpr const bool GetInfo_0_1::_traits_::IsServiceType;
constexpr const bool Read_1_1::_traits_::IsServiceType;
constexpr const bool Read_1_0::_traits_::IsServiceType;
}  // namespace file

namespace _register
{
constexpr const bool List_1_0::_traits_::IsServiceType;
constexpr const bool Access_1_0::_traits_::IsServiceType;
}  // namespace _register

namespace internet
{
namespace udp
{
constexpr const bool HandleIncomingPacket_0_2::_traits_::IsServiceType;
constexpr const bool HandleIncomingPacket_0_1::_traits_::IsServiceType;
}  // namespace udp
}  // namespace internet

namespace node
{
constexpr const bool ExecuteCommand_1_0::_traits_::IsServiceType;
constexpr const bool ExecuteCommand_1_1::_traits_::IsServiceType;
constexpr const bool ExecuteCommand_1_2::_traits_::IsServiceType;
constexpr const bool ExecuteCommand_1_3::_traits_::IsServiceType;
constexpr const bool GetInfo_1_0::_traits_::IsServiceType;
constexpr const bool GetTransportStatistics_0_1::_traits_::IsServiceType;
}  // namespace node
}  // namespace uavcan
#endif
