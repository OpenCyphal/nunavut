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
// | nunavut[Get|Set]Bit
// +--------------------------------------------------------------------------+

static void testNunavutSetBit(void)
{
    uint8_t buffer[] = {0x00};
    nunavutSetBit(buffer, 0, true);
    TEST_ASSERT_EQUAL_HEX8(0x01, buffer[0]);
    nunavutSetBit(buffer, 0, false);
    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[0]);
    nunavutSetBit(buffer, 0, true);
    nunavutSetBit(buffer, 1, true);
    TEST_ASSERT_EQUAL_HEX8(0x03, buffer[0]);
}

static void testNunavutGetBit(void)
{
    uint8_t buffer[] = {0x01};
    TEST_ASSERT_EQUAL(true, nunavutGetBit(buffer, 1, 0));
    TEST_ASSERT_EQUAL(false, nunavutGetBit(buffer, 1, 1));
}

// +--------------------------------------------------------------------------+
// | nunavutGetU8
// +--------------------------------------------------------------------------+

static void testNunavutGetU8(void)
{
    const uint8_t data[] = {0xFE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    TEST_ASSERT_EQUAL_HEX8(0xFE, nunavutGetU8(data, sizeof(data), 0, 8U));
}

static void testNunavutGetU8_tooSmall(void)
{
    const uint8_t data[] = {0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    TEST_ASSERT_EQUAL_HEX8(0x7F, nunavutGetU8(data, sizeof(data), 0, 7U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetU16
// +--------------------------------------------------------------------------+

static void testNunavutGetU16(void)
{
    const uint8_t data[] = {0xAA, 0xAA};
    TEST_ASSERT_EQUAL_HEX16(0xAAAA, nunavutGetU16(data, sizeof(data), 0, 16U));
}

static void testNunavutGetU16_tooSmall(void)
{
    const uint8_t data[] = {0xAA, 0xAA};
    TEST_ASSERT_EQUAL_HEX16(0x0055, nunavutGetU16(data, sizeof(data), 9, 16U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetU32
// +--------------------------------------------------------------------------+

static void testNunavutGetU32(void)
{
    const uint8_t data[] = {0xAA, 0xAA, 0xAA, 0xAA};
    TEST_ASSERT_EQUAL_HEX32(0xAAAAAAAA, nunavutGetU32(data, sizeof(data), 0, 32U));
}

static void testNunavutGetU32_tooSmall(void)
{
    const uint8_t data[] = {0xAA, 0xAA, 0xAA, 0xAA};
    TEST_ASSERT_EQUAL_HEX32(0x00555555, nunavutGetU32(data, sizeof(data), 9, 32U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetU64
// +--------------------------------------------------------------------------+

static void testNunavutGetU64(void)
{
    const uint8_t data[] = {0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA};
    TEST_ASSERT_EQUAL_HEX64(0xAAAAAAAAAAAAAAAA, nunavutGetU64(data, sizeof(data), 0, 64U));
}

static void testNunavutGetU64_tooSmall(void)
{
    const uint8_t data[] = {0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA};
    TEST_ASSERT_EQUAL_HEX64(0x0055555555555555, nunavutGetU64(data, sizeof(data), 9, 64U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetI8
// +--------------------------------------------------------------------------+

static void testNunavutGetI8(void)
{
    const uint8_t data[] = {0xFF};
    TEST_ASSERT_EQUAL_INT8(-1, nunavutGetI8(data, sizeof(data), 0, 8U));
}

static void testNunavutGetI8_tooSmall(void)
{
    const uint8_t data[] = {0xFF};
    TEST_ASSERT_EQUAL_INT8(127, nunavutGetI8(data, sizeof(data), 1, 8U));
}

static void testNunavutGetI8_tooSmallAndNegative(void)
{
    const uint8_t data[] = {0xFF};
    TEST_ASSERT_EQUAL_INT8(-1, nunavutGetI8(data, sizeof(data), 0, 4U));
}

static void testNunavutGetI8_zeroDataLen(void)
{
    const uint8_t data[] = {0xFF};
    TEST_ASSERT_EQUAL_INT8(0, nunavutGetI8(data, sizeof(data), 0, 0U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetI16
// +--------------------------------------------------------------------------+

static void testNunavutGetI16(void)
{
    const uint8_t data[] = {0xFF, 0xFF};
    TEST_ASSERT_EQUAL_INT16(-1, nunavutGetI16(data, sizeof(data), 0, 16U));
}

static void testNunavutGetI16_tooSmall(void)
{
    const uint8_t data[] = {0xFF, 0xFF};
    TEST_ASSERT_EQUAL_INT16(32767, nunavutGetI16(data, sizeof(data), 1, 16U));
}

static void testNunavutGetI16_tooSmallAndNegative(void)
{
    const uint8_t data[] = {0xFF, 0xFF};
    TEST_ASSERT_EQUAL_INT16(-1, nunavutGetI16(data, sizeof(data), 0, 12U));
}

static void testNunavutGetI16_zeroDataLen(void)
{
    const uint8_t data[] = {0xFF, 0xFF};
    TEST_ASSERT_EQUAL_INT16(0, nunavutGetI16(data, sizeof(data), 0, 0U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetI32
// +--------------------------------------------------------------------------+

static void testNunavutGetI32(void)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF};
    TEST_ASSERT_EQUAL_INT32(-1, nunavutGetI32(data, sizeof(data), 0, 32U));
}

static void testNunavutGetI32_tooSmall(void)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF};
    TEST_ASSERT_EQUAL_INT32(2147483647, nunavutGetI32(data, sizeof(data), 1, 32U));
}

static void testNunavutGetI32_tooSmallAndNegative(void)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF};
    TEST_ASSERT_EQUAL_INT32(-1, nunavutGetI32(data, sizeof(data), 0, 20U));
}

static void testNunavutGetI32_zeroDataLen(void)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF};
    TEST_ASSERT_EQUAL_INT32(0, nunavutGetI32(data, sizeof(data), 0, 0U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetI64
// +--------------------------------------------------------------------------+

static void testNunavutGetI64(void)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    TEST_ASSERT_EQUAL_INT64(-1, nunavutGetI64(data, sizeof(data), 0, 64U));
}

static void testNunavutGetI64_tooSmall(void)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    TEST_ASSERT_EQUAL_INT64(9223372036854775807, nunavutGetI64(data, sizeof(data), 1, 64U));
}

static void testNunavutGetI64_tooSmallAndNegative(void)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    TEST_ASSERT_EQUAL_INT64(-1, nunavutGetI64(data, sizeof(data), 0, 60U));
}

static void testNunavutGetI64_zeroDataLen(void)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    TEST_ASSERT_EQUAL_INT64(0, nunavutGetI64(data, sizeof(data), 0, 0U));
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
    RUN_TEST(testNunavutSetBit);
    RUN_TEST(testNunavutGetBit);
    RUN_TEST(testNunavutGetU8);
    RUN_TEST(testNunavutGetU8_tooSmall);
    RUN_TEST(testNunavutGetU16);
    RUN_TEST(testNunavutGetU16_tooSmall);
    RUN_TEST(testNunavutGetU32);
    RUN_TEST(testNunavutGetU32_tooSmall);
    RUN_TEST(testNunavutGetU64);
    RUN_TEST(testNunavutGetU64_tooSmall);
    RUN_TEST(testNunavutGetI8);
    RUN_TEST(testNunavutGetI8_tooSmall);
    RUN_TEST(testNunavutGetI8_tooSmallAndNegative);
    RUN_TEST(testNunavutGetI8_zeroDataLen);
    RUN_TEST(testNunavutGetI16);
    RUN_TEST(testNunavutGetI16_tooSmall);
    RUN_TEST(testNunavutGetI16_tooSmallAndNegative);
    RUN_TEST(testNunavutGetI16_zeroDataLen);
    RUN_TEST(testNunavutGetI32);
    RUN_TEST(testNunavutGetI32_tooSmall);
    RUN_TEST(testNunavutGetI32_tooSmallAndNegative);
    RUN_TEST(testNunavutGetI32_zeroDataLen);
    RUN_TEST(testNunavutGetI64);
    RUN_TEST(testNunavutGetI64_tooSmall);
    RUN_TEST(testNunavutGetI64_tooSmallAndNegative);
    RUN_TEST(testNunavutGetI64_zeroDataLen);

    return UNITY_END();
}
