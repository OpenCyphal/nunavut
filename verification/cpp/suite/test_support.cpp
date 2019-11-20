/*
 * Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests of the Nunavut support header.
 */
#include "gmock/gmock.h"
#include "nunavut/support.hpp"
#include <vector>

template <typename SIZE_TYPE_FOR_TEST, typename BYTE_TYPE_FOR_TEST>
struct SupportTestTypes
{
    using SIZE_TYPE = SIZE_TYPE_FOR_TEST;
    using BYTE_TYPE = BYTE_TYPE_FOR_TEST;
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
    ::testing::Types<SupportTestTypes<std::size_t, std::uint8_t>, SupportTestTypes<std::size_t, std::uint16_t>>;

TYPED_TEST_SUITE(SupportTest, MyTypes, );

/**
 * Temporary test as a placeholder while we wire up the build.
 */
TYPED_TEST(SupportTest, UnalignedCopy)
{
    std::vector<typename TypeParam::BYTE_TYPE> test_pattern;
    test_pattern.reserve(sizeof(typename TypeParam::BYTE_TYPE));
    memset(test_pattern.data(), 0xAA, test_pattern.capacity());
    std::vector<typename TypeParam::BYTE_TYPE> test_buffer;
    test_buffer.reserve(test_pattern.capacity() + 1);
    auto copied_bits = nunavut::copyBitsAlignedToUnaligned<typename TypeParam::SIZE_TYPE,
                                                           typename TypeParam::BYTE_TYPE>(test_pattern.data(),
                                                                                          test_buffer.data(),
                                                                                          0,
                                                                                          test_pattern.capacity());
    ASSERT_EQ(test_pattern.capacity(), copied_bits);
    ASSERT_EQ(static_cast<unsigned>(test_buffer[0] & 0xFF), 0xAAU);
}
