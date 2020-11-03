/*
 * Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * Copyright (c) 2016-2020 UAVCAN Development Team.
 *
 * This software is distributed under the terms of the MIT License.
 *
 * Contains tests pulled from libcanard.
 */
#include "gmock/gmock.h"
#include "nunavut/support/serialization.h"

#include <cmath>
#include <limits>

TEST(CanardTests, float16Pack)
{
    EXPECT_TRUE(0b0000000000000000 == nunavutFloat16Pack(0.0F));
    EXPECT_TRUE(0b0011110000000000 == nunavutFloat16Pack(1.0F));
    EXPECT_TRUE(0b1100000000000000 == nunavutFloat16Pack(-2.0F));
    EXPECT_TRUE(0b0111110000000000 == nunavutFloat16Pack(999999.0F));      // +inf
    EXPECT_TRUE(0b1111101111111111 == nunavutFloat16Pack(-65519.0F));      // -max
    EXPECT_TRUE(0b1100000000000000 == nunavutFloat16Pack(-2.0F));
    EXPECT_TRUE(0b0111110000000000 == nunavutFloat16Pack(999999.0F));      // +inf
    EXPECT_TRUE(0b1111101111111111 == nunavutFloat16Pack(-65519.0F));      // -max
    EXPECT_TRUE(std::isnan(nunavutFloat16Unpack(nunavutFloat16Pack(std::nanf("")))));  // nan
    // These are intrusive tests, they make assumptions about the specific implementation of the conversion logic.
    // Normally, one wouldn't be able to compare a NaN against a particular number because there are many ways to
    // represent it. We do not differentiate between sNaN and qNaN because there is no platform-agnostic way to do
    // that; see https://github.com/UAVCAN/nunavut/pull/115#issuecomment-704185463
    EXPECT_TRUE(0b0111111000000000 == nunavutFloat16Pack(+std::numeric_limits<float>::quiet_NaN()));
    EXPECT_TRUE(0b1111111000000000 == nunavutFloat16Pack(-std::numeric_limits<float>::quiet_NaN()));
    EXPECT_TRUE(0b0111111000000000 == nunavutFloat16Pack(+std::numeric_limits<float>::signaling_NaN()));
    EXPECT_TRUE(0b1111111000000000 == nunavutFloat16Pack(-std::numeric_limits<float>::signaling_NaN()));
}

TEST(CanardTests, float16Unpack)
{
    ASSERT_FLOAT_EQ(0.0, (float)nunavutFloat16Unpack(0b0000000000000000));
    ASSERT_FLOAT_EQ(1.0, (float)nunavutFloat16Unpack(0b0011110000000000));
    ASSERT_FLOAT_EQ(-2.0, (float)nunavutFloat16Unpack(0b1100000000000000));
    ASSERT_FLOAT_EQ(-65504.0, (float)nunavutFloat16Unpack(0b1111101111111111));
    EXPECT_TRUE(std::isinf(nunavutFloat16Unpack(0b0111110000000000)));
    EXPECT_TRUE(bool(std::isnan(nunavutFloat16Unpack(0b0111111111111111))));  // quiet
    EXPECT_TRUE(bool(std::isnan(nunavutFloat16Unpack(0b0111111000000000))));  // quiet
    EXPECT_TRUE(bool(std::isnan(nunavutFloat16Unpack(0b0111110111111111))));  // signaling
    EXPECT_TRUE(bool(std::isnan(nunavutFloat16Unpack(0b0111110000000001))));  // signaling
}

TEST(CanardTests, canardDSDLFloat16)
{
    float x = -1000.0F;
    while (x <= 1000.0F)
    {
        ASSERT_FLOAT_EQ(x, nunavutFloat16Unpack(nunavutFloat16Pack(x)));
        x += 0.5F;
    }
    EXPECT_TRUE(0b0111110000000000 == nunavutFloat16Pack(nunavutFloat16Unpack(0b0111110000000000)));  // +inf
    EXPECT_TRUE(0b1111110000000000 == nunavutFloat16Pack(nunavutFloat16Unpack(0b1111110000000000)));  // -inf
    EXPECT_TRUE(0b0111111000000000 == nunavutFloat16Pack(nunavutFloat16Unpack(0b0111111111111111)));  // qNaN

    EXPECT_TRUE(0b0111110000000000 == nunavutFloat16Pack(nunavutFloat16Unpack(0b0111110000000000)));  // +inf
    EXPECT_TRUE(0b1111110000000000 == nunavutFloat16Pack(nunavutFloat16Unpack(0b1111110000000000)));  // -inf

    // These are intrusive tests, they make assumptions about the specific implementation of the conversion logic.
    // Normally, one wouldn't be able to compare a NaN against a particular number because there are many ways to
    // represent it. We do not differentiate between sNaN and qNaN because there is no platform-agnostic way to do
    // that; see https://github.com/UAVCAN/nunavut/pull/115#issuecomment-704185463
    EXPECT_TRUE(0b0111111000000000 == nunavutFloat16Pack(nunavutFloat16Unpack(0b0111111111111111)));  // +qNaN
    EXPECT_TRUE(0b0111111000000000 == nunavutFloat16Pack(nunavutFloat16Unpack(0b0111110111111111)));  // +sNaN
    EXPECT_TRUE(0b1111111000000000 == nunavutFloat16Pack(nunavutFloat16Unpack(0b1111111111111111)));  // -qNaN
    EXPECT_TRUE(0b1111111000000000 == nunavutFloat16Pack(nunavutFloat16Unpack(0b1111110111111111)));  // -sNaN
}
