/*
 * Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests the common functionality provided by the Nunavut support headers.
 */
#include "unity.h"
#include <assert.h>
#include "nunavut/support/serialization.h"

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
    nunavutCopyBits(sizeof(src) * 8, 8, 0, src, dst);
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
    nunavutCopyBits(sizeof(src) * 8, 1, 0, src, dst);
    for(size_t i = 0; i < sizeof(src) - 1; ++i)
    {
        TEST_ASSERT_EQUAL_HEX8(0x55, dst[i]);
    }
    TEST_ASSERT_EQUAL_HEX8(0x55, dst[sizeof(dst) - 1]);

    memset(dst, 0, sizeof(dst));
    nunavutCopyBits(sizeof(src) * 8, 0, 1, src, dst);
    for(size_t i = 0; i < sizeof(src) - 1; ++i)
    {
        TEST_ASSERT_EQUAL_HEX8((i == 0) ? 0x54 : 0x55, dst[i]);
    }
    TEST_ASSERT_EQUAL_HEX8(0x54, dst[0]);
}
 
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
 
    return UNITY_END();
}
