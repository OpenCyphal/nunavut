/*
 * Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests the common functionality provided by the Nunavut support headers.
 */
#include "unity.h"
#include "nunavut/support/serialization.h"

// +--------------------------------------------------------------------------+
// | nunavutCopyBits
// +--------------------------------------------------------------------------+

static void testNunavutCopyBits(void)
{
    const uint8_t src[] = { 1, 2, 3, 4, 5 };
    uint8_t dst[6];
    memset(dst, 0, sizeof(dst));
    nunavutCopyBits(sizeof(src) * 8, 0, 0, src, dst);
    for(size_t i = 0; i < sizeof(src); ++i)
    {
        TEST_ASSERT_EQUAL_UINT8(src[i], dst[i]);
    }
}

static void testNunavutCopyBitsWithAlignedOffset(void)
{
    const uint8_t src[] = { 1, 2, 3, 4, 5 };
    uint8_t dst[6];
    memset(dst, 0, sizeof(dst));
    nunavutCopyBits((sizeof(src) - 1) * 8, 8, 0, src, dst);
    for(size_t i = 0; i < sizeof(src) - 1; ++i)
    {
        TEST_ASSERT_EQUAL_UINT8(src[i + 1], dst[i]);
    }
    TEST_ASSERT_EQUAL_UINT8(0, dst[sizeof(dst) - 1]);

    memset(dst, 0, sizeof(dst));
    nunavutCopyBits(sizeof(src) * 8, 0, 8, src, dst);
    for(size_t i = 0; i < sizeof(src) - 1; ++i)
    {
        TEST_ASSERT_EQUAL_UINT8(src[i], dst[i+1]);
    }
    TEST_ASSERT_EQUAL_UINT8(0, dst[0]);
}

static void testNunavutCopyBitsWithUnalignedOffset(void)
{
    const uint8_t src[] = { 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA };
    uint8_t dst[6];
    memset(dst, 0, sizeof(dst));
    nunavutCopyBits((sizeof(src)-1) * 8, 1, 0, src, dst);
    for(size_t i = 0; i < sizeof(src) - 1; ++i)
    {
        TEST_ASSERT_EQUAL_HEX8(0x55, dst[i]);
    }
    TEST_ASSERT_EQUAL_HEX8(0x00, dst[sizeof(dst) - 1]);

    memset(dst, 0, sizeof(dst));
    nunavutCopyBits((sizeof(src)-1) * 8, 0, 1, src, dst);
    for(size_t i = 0; i < sizeof(src) - 1; ++i)
    {
        TEST_ASSERT_EQUAL_HEX8((i == 0) ? 0x54 : 0x55, dst[i]);
    }
    TEST_ASSERT_EQUAL_HEX8(0x54, dst[0]);
}

// +--------------------------------------------------------------------------+
// | nunavutInternalGetBitCopySize
// +--------------------------------------------------------------------------+

static void testNunavutInternalGetBitCopySize(void)
{
    // buf_size_bytes, offset_bit, requested_length_bit, value_length_bit
    TEST_ASSERT_EQUAL_UINT32(4 * 8, nunavutInternalGetBitCopySize(4, 0, 4 * 8, 24 * 8));
    TEST_ASSERT_EQUAL_UINT32((4 * 8) - 1, nunavutInternalGetBitCopySize(4, 1, 4 * 8, 24 * 8));
    TEST_ASSERT_EQUAL_UINT32(2 * 8, nunavutInternalGetBitCopySize(4, 0, 4 * 8, 2 * 8));
    TEST_ASSERT_EQUAL_UINT32((2 * 8) - 1, nunavutInternalGetBitCopySize(4, (2 * 8) + 1, 4 * 8, 3 * 8));
    TEST_ASSERT_EQUAL_UINT32(0, nunavutInternalGetBitCopySize(2, (3 * 8), 3 * 8, 4 * 8));
}

// +--------------------------------------------------------------------------+
// | nunavutSetIxx
// +--------------------------------------------------------------------------+

static void testNunavutSetIxx_neg1(void)
{
    uint8_t data[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    nunavutSetIxx(data, 0, -1, sizeof(data) * 8);
    for (size_t i = 0; i < sizeof(data); ++i)
    {
        TEST_ASSERT_EQUAL_HEX8(0xFF, data[i]);
    }
}

static void testNunavutSetIxx_neg255(void)
{
    uint8_t data[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    nunavutSetIxx(data, 0, -255, sizeof(data) * 8);
    TEST_ASSERT_EQUAL_HEX8(0xFF, data[1]);
    TEST_ASSERT_EQUAL_HEX8(0x01, data[0]);
}

static void testNunavutSetIxx_neg255_tooSmall(void)
{
    uint8_t data[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    nunavutSetIxx(data, 0, -255, sizeof(data) * 1);
    TEST_ASSERT_EQUAL_HEX8(0x00, data[1]);
    TEST_ASSERT_EQUAL_HEX8(0x01, data[0]);
}

// +--------------------------------------------------------------------------+
// | nunavutGetU8
// +--------------------------------------------------------------------------+

static void testnunavutGetU8(void)
{
    const uint8_t data[] = {0xFE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    TEST_ASSERT_EQUAL_HEX8(0xFE, nunavutGetU8(data, sizeof(data), 0, 8U));
}

static void testnunavutGetU8_tooSmall(void)
{
    const uint8_t data[] = {0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    TEST_ASSERT_EQUAL_HEX8(0x7F, nunavutGetU8(data, sizeof(data), 0, 7U));
}

// +--------------------------------------------------------------------------+
// | TEST CASE
// +--------------------------------------------------------------------------+

void setUp(void)
{

}

void tearDown(void)
{

}

int main(void)
{
    UNITY_BEGIN();
 
    RUN_TEST(testNunavutCopyBits);
    RUN_TEST(testNunavutCopyBitsWithAlignedOffset);
    RUN_TEST(testNunavutCopyBitsWithUnalignedOffset);
    RUN_TEST(testNunavutInternalGetBitCopySize);
    RUN_TEST(testNunavutSetIxx_neg1);
    RUN_TEST(testNunavutSetIxx_neg255);
    RUN_TEST(testNunavutSetIxx_neg255_tooSmall);
    RUN_TEST(testnunavutGetU8);
    RUN_TEST(testnunavutGetU8_tooSmall);

    return UNITY_END();
}
