/*
 * Copyright (c) 2024 OpenCyphal Development Team.
 * Authors: Sergei Shirokov <sergei.shirokov@zubax.com>
 * This software is distributed under the terms of the MIT License.
 *
 * Tests of constant
 */

#include "gmock/gmock.h"
#include "regulated/basics/Struct__0_1.hpp"
#include "regulated/basics/Union_0_1.hpp"
#include "regulated/basics/Service_0_1.hpp"

#if __cplusplus == 201402L
const std::uint16_t regulated::basics::Struct__0_1::_traits_::FixedPortId;
const bool regulated::basics::Struct__0_1::_traits_::HasFixedPortID;
const std::size_t regulated::basics::Union_0_1::_traits_::ExtentBytes;
const std::size_t regulated::basics::Union_0_1::VariantType::MAX_INDEX;
const double regulated::basics::Struct__0_1::CONSTANT_MINUS_THREE;
const std::int64_t regulated::basics::Struct__0_1::CONSTANT_MINUS_MAX_OFFSET;
const std::uint8_t regulated::basics::Struct__0_1::CONSTANT_ZEE;
const bool regulated::basics::Struct__0_1::CONSTANT_TRUTH;
const float regulated::basics::Service::Response_0_1::ONE_TENTH;
const double regulated::basics::Service::Request_0_1::HALF;
const bool regulated::basics::Service::Request_0_1::_traits_::IsRequest;
const bool regulated::basics::Service::Request_0_1::_traits_::IsResponse;
const bool regulated::basics::Service::Request_0_1::_traits_::IsService;
const bool regulated::basics::Service::Request_0_1::_traits_::IsServiceType;
const bool regulated::basics::Service::Response_0_1::_traits_::IsResponse;
const bool regulated::basics::Service::Response_0_1::_traits_::IsServiceType;
const bool regulated::basics::Service_0_1::_traits_::IsService;
const bool regulated::basics::Service_0_1::_traits_::IsServiceType;
const bool regulated::basics::Service_0_1::_traits_::HasFixedPortID;
const std::uint16_t regulated::basics::Service_0_1::_traits_::FixedPortId;

const std::size_t regulated::basics::Struct__0_1::_traits_::ArrayCapacity::i10_4;
const std::size_t regulated::basics::Struct__0_1::_traits_::ArrayCapacity::f16_le2;
const std::size_t regulated::basics::Struct__0_1::_traits_::ArrayCapacity::unaligned_bitpacked_3;
const std::size_t regulated::basics::Struct__0_1::_traits_::ArrayCapacity::bytes_lt3;
const std::size_t regulated::basics::Struct__0_1::_traits_::ArrayCapacity::bytes_3;
const std::size_t regulated::basics::Struct__0_1::_traits_::ArrayCapacity::u2_le4;
const std::size_t regulated::basics::Struct__0_1::_traits_::ArrayCapacity::delimited_fix_le2;
const std::size_t regulated::basics::Struct__0_1::_traits_::ArrayCapacity::u16_2;
const std::size_t regulated::basics::Struct__0_1::_traits_::ArrayCapacity::aligned_bitpacked_3;
const std::size_t regulated::basics::Struct__0_1::_traits_::ArrayCapacity::unaligned_bitpacked_lt3;
const std::size_t regulated::basics::Struct__0_1::_traits_::ArrayCapacity::delimited_var_2;
const std::size_t regulated::basics::Struct__0_1::_traits_::ArrayCapacity::aligned_bitpacked_le3;

const std::size_t regulated::basics::Union_0_1::_traits_::ArrayCapacity::delimited_fix_le2;
const std::size_t regulated::basics::Union_0_1::_traits_::ArrayCapacity::delimited_var_le2;
#endif

using testing::Le;
using testing::StrEq;
using testing::FloatNear;
using testing::DoubleNear;

TEST(ConstantTests, Struct)
{
    // Type parameters.
    EXPECT_TRUE(regulated::basics::Struct__0_1::_traits_::HasFixedPortID);
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::FixedPortId, 7000);
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::FullNameAndVersion(), StrEq("regulated.basics.Struct_.0.1"));

    // Application constants.
    EXPECT_THAT(regulated::basics::Struct__0_1::CONSTANT_MINUS_THREE, DoubleNear(-3.0, 1e-9));
    EXPECT_THAT(regulated::basics::Struct__0_1::CONSTANT_ZEE, 'Z');
    EXPECT_THAT(-regulated::basics::Struct__0_1::CONSTANT_MINUS_MAX_OFFSET,
                Le(regulated::basics::Struct__0_1::_traits_::SerializationBufferSizeBytes * 8U));
    EXPECT_TRUE(regulated::basics::Struct__0_1::CONSTANT_TRUTH);

    // Field metadata. Expected values encoded in the field names.
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::ArrayCapacity::i10_4, 4);
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::ArrayCapacity::f16_le2, 2);
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::ArrayCapacity::unaligned_bitpacked_3, 3);
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::ArrayCapacity::bytes_lt3, 2);
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::ArrayCapacity::bytes_3, 3);
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::ArrayCapacity::u2_le4, 4);
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::ArrayCapacity::delimited_fix_le2, 2);
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::ArrayCapacity::u16_2, 2);
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::ArrayCapacity::aligned_bitpacked_3, 3);
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::ArrayCapacity::unaligned_bitpacked_lt3, 2);
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::ArrayCapacity::delimited_var_2, 2);
    EXPECT_THAT(regulated::basics::Struct__0_1::_traits_::ArrayCapacity::aligned_bitpacked_le3, 3);
}

TEST(ConstantTests, Union)
{
    // Type parameters.
    EXPECT_FALSE(regulated::basics::Union_0_1::_traits_::HasFixedPortID);
    EXPECT_THAT(regulated::basics::Union_0_1::_traits_::FullNameAndVersion(), StrEq("regulated.basics.Union.0.1"));
    EXPECT_THAT(regulated::basics::Union_0_1::_traits_::ExtentBytes,
                1U + regulated::basics::Struct__0_1::_traits_::ExtentBytes);  // Largest option + union tag field
    EXPECT_THAT(regulated::basics::Union_0_1::VariantType::MAX_INDEX, 3);

    // Field metadata. Expected values encoded in the field names.
    EXPECT_THAT(regulated::basics::Union_0_1::_traits_::ArrayCapacity::delimited_fix_le2, 2);
    EXPECT_THAT(regulated::basics::Union_0_1::_traits_::ArrayCapacity::delimited_var_le2, 2);
}

TEST(ConstantTests, Service)
{
    // Type parameters.
    EXPECT_TRUE(regulated::basics::Service_0_1::_traits_::IsService);
    EXPECT_TRUE(regulated::basics::Service_0_1::_traits_::IsServiceType);
    EXPECT_TRUE(regulated::basics::Service_0_1::_traits_::HasFixedPortID);
    EXPECT_THAT(regulated::basics::Service_0_1::_traits_::FixedPortId, 300);
    EXPECT_THAT(regulated::basics::Service_0_1::_traits_::FullNameAndVersion(),
                StrEq("regulated.basics.Service.0.1"));

    EXPECT_FALSE(regulated::basics::Service::Request_0_1::_traits_::IsService);
    EXPECT_TRUE(regulated::basics::Service::Request_0_1::_traits_::IsServiceType);
    EXPECT_TRUE(regulated::basics::Service::Request_0_1::_traits_::IsRequest);
    EXPECT_FALSE(regulated::basics::Service::Request_0_1::_traits_::IsResponse);
    EXPECT_THAT(regulated::basics::Service::Request_0_1::_traits_::FullNameAndVersion(),
                StrEq("regulated.basics.Service.Request.0.1"));

    EXPECT_FALSE(regulated::basics::Service::Response_0_1::_traits_::IsService);
    EXPECT_TRUE(regulated::basics::Service::Response_0_1::_traits_::IsServiceType);
    EXPECT_TRUE(regulated::basics::Service::Response_0_1::_traits_::IsResponse);
    EXPECT_FALSE(regulated::basics::Service::Response_0_1::_traits_::IsRequest);
    EXPECT_THAT(regulated::basics::Service::Response_0_1::_traits_::FullNameAndVersion(),
                StrEq("regulated.basics.Service.Response.0.1"));

    // Application constants.
    EXPECT_THAT(regulated::basics::Service::Request_0_1::HALF, DoubleNear(0.5, 1e-9));
    EXPECT_THAT(regulated::basics::Service::Response_0_1::ONE_TENTH, FloatNear(0.1f, 1e-9f));
}
