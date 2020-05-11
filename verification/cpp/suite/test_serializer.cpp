/*
 * Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests of the Nunavut support header.
 */
#include "gmock/gmock.h"
#include "nunavut/support/serialization.hpp"
#include <vector>

template <typename ByteType_FOR_TEST, std::size_t static_capacity_bits_value>
struct SupportTestTypes
{
    using ByteType = ByteType_FOR_TEST;
    static constexpr std::size_t static_capacity_bits = static_capacity_bits_value;
};

/**
 * Test fixture for testing the nunavut C++ support headers against various configurations.
 * See https://github.com/google/googletest/blob/master/googletest/docs/advanced.md for
 * more information about typed gtests.
 *
 * @tparam T    The allocator type under test.
 */
template <typename T>
class SupportTest : public testing::TestWithParam<int>
{};

using MyTypes =
    ::testing::Types<SupportTestTypes<std::uint8_t, 0x10000>, SupportTestTypes<std::uint16_t, 0x10000>>;

TYPED_TEST_SUITE(SupportTest, MyTypes, );

/**
 * Temporary test as a placeholder while we wire up the build.
 */
TYPED_TEST(SupportTest, AlignedCopy)
{
    std::vector<typename TypeParam::ByteType> test_pattern;
    test_pattern.reserve(sizeof(typename TypeParam::ByteType));
    memset(test_pattern.data(), 0xAA, test_pattern.capacity());
    std::vector<typename TypeParam::ByteType> test_buffer;
    nunavut::support::LittleEndianSerializer<typename TypeParam::ByteType, TypeParam::static_capacity_bits> test_subject(
        test_buffer,
        0
    );
    test_subject.add_aligned_bytes(test_pattern.data(), test_pattern.capacity());
    ASSERT_EQ(test_pattern.capacity(), test_subject.get_current_bit_length());
    ASSERT_EQ(static_cast<unsigned>(test_buffer[0] & 0xFF), 0xAAU);
}
