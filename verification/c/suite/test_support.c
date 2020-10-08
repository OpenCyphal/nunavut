/*
 * Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests the common functionality provided by the Nunavut support headers.
 */
#include "unity.h"
#include "nunavut/support/serialization.h"
#include <math.h>

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
    nunavutSetIxx(data, sizeof(data), 0, -1, sizeof(data) * 8);
    for (size_t i = 0; i < sizeof(data); ++i)
    {
        TEST_ASSERT_EQUAL_HEX8(0xFF, data[i]);
    }
}

static void testNunavutSetIxx_neg255(void)
{
    uint8_t data[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    nunavutSetIxx(data, sizeof(data), 0, -255, sizeof(data) * 8);
    TEST_ASSERT_EQUAL_HEX8(0xFF, data[1]);
    TEST_ASSERT_EQUAL_HEX8(0x01, data[0]);
}

static void testNunavutSetIxx_neg255_tooSmall(void)
{
    uint8_t data[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    nunavutSetIxx(data, sizeof(data), 0, -255, sizeof(data) * 1);
    TEST_ASSERT_EQUAL_HEX8(0x00, data[1]);
    TEST_ASSERT_EQUAL_HEX8(0x01, data[0]);
}

static void testNunavutSetIxx_bufferOverflow(void)
{
    uint8_t buffer[] = {0x00, 0x00, 0x00};
    int8_t rc;
    rc = nunavutSetIxx(buffer, 3, 16, 0xAA, 8);
    TEST_ASSERT_EQUAL_INT8(NUNAVUT_SUCCESS, rc);
    TEST_ASSERT_EQUAL_HEX8(0xAA, buffer[2]);
    rc = nunavutSetIxx(buffer, 2, 16, 0x00, 8);
    TEST_ASSERT_EQUAL_INT8(-NUNAVUT_ERR_BUF_OVERFLOW, rc);
    TEST_ASSERT_EQUAL_HEX8(0xAA, buffer[2]);
}

// +--------------------------------------------------------------------------+
// | nunavut[Get|Set]Bit
// +--------------------------------------------------------------------------+

static void testNunavutSetBit(void)
{
    uint8_t buffer[] = {0x00};
    nunavutSetBit(buffer, sizeof(buffer), 0, true);
    TEST_ASSERT_EQUAL_HEX8(0x01, buffer[0]);
    nunavutSetBit(buffer, sizeof(buffer), 0, false);
    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[0]);
    nunavutSetBit(buffer, sizeof(buffer), 0, true);
    nunavutSetBit(buffer, sizeof(buffer), 1, true);
    TEST_ASSERT_EQUAL_HEX8(0x03, buffer[0]);
}

static void testNunavutSetBit_bufferOverflow(void)
{
    uint8_t buffer[] = {0x00, 0x00};
    int8_t rc = nunavutSetBit(buffer, 1, 8, true);
    TEST_ASSERT_EQUAL_INT8(-NUNAVUT_ERR_BUF_OVERFLOW, rc);
    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[1]);
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
// | nunavutFloat16Pack
// +--------------------------------------------------------------------------+

static void testNunavutFloat16Pack(void)
{
    // Comparing to Numpy calculated values

    uint16_t packed_float = nunavutFloat16Pack(3.14f);
    // hex(int.from_bytes(np.array([np.float16('3.14')]).tobytes(), 'little'))
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x4248, packed_float, "Failed to serialize 3.14f");

    packed_float = nunavutFloat16Pack(-3.14f);
    // hex(int.from_bytes(np.array([-np.float16('3.14')]).tobytes(), 'little'))
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0xC248, packed_float, "Failed to serialize -3.14f");

    packed_float = nunavutFloat16Pack(65536.141592653589793238462643383279f);
    // hex(int.from_bytes(np.array([np.float16('65536.141592653589793238462643383279')]).tobytes(), 'little'))
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x7C00, packed_float, "Failed to serialize 65536.141592653589793238462643383279f");

    packed_float = nunavutFloat16Pack(-65536.141592653589793238462643383279f);
    // hex(int.from_bytes(np.array([np.float16('65536.141592653589793238462643383279')]).tobytes(), 'little'))
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0xFC00, packed_float, "Failed to serialize -65536.141592653589793238462643383279f");
}


static void testNunavutFloat16Pack_NAN_cmath(void)
{
    uint16_t packed_float = nunavutFloat16Pack(NAN);
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x200, (0x200 & packed_float), "NAN was not silent.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x7C00, (0x7C00 & packed_float), "Exponent bits were not all set for NAN.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x80000 & packed_float), "NAN sign bit was negative.");

    packed_float = nunavutFloat16Pack(-NAN);
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x200, (0x200 & packed_float), "-NAN was not silent.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x7C00, (0x7C00 & packed_float), "Exponent bits were not all set for -NAN.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x80000, (0x80000 & packed_float), "-NAN sign bit was positive.");
}


static void testNunavutFloat16Pack_NAN_quiet(void)
{
    const uint32_t quiet_nan_bits = 0x7FC00000U | 0x200000U;
    uint16_t packed_float = nunavutFloat16Pack(*((float*)&quiet_nan_bits));
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x200, (0x200 & packed_float), "NAN was not silent.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x7C00, (0x7C00 & packed_float), "Exponent bits were not all set for NAN.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x80000 & packed_float), "NAN sign bit was negative.");

    const uint32_t quiet_nan_negative_bits = 0x7FC00000U | 0x200000U;
    packed_float = nunavutFloat16Pack(*((float*)&quiet_nan_negative_bits));
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x200, (0x200 & packed_float), "-NAN was not silent.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x7C00, (0x7C00 & packed_float), "Exponent bits were not all set for -NAN.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x80000, (0x80000 & packed_float), "-NAN sign bit was positive.");
}

static void testNunavutFloat16Pack_NAN_signalling(void)
{
    const uint32_t signalling_nan_bits = 0x7F800000U | 0x200000U;
    // The specification requires at least one non-zero bit is set in the trailing significant
    // to distinguish from INFINITY.
    uint16_t packed_float = nunavutFloat16Pack(*((float*)&signalling_nan_bits));
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x200 & packed_float), "NAN was silent.");
    TEST_ASSERT_MESSAGE(0 != (0x3FF & packed_float), "Mantessa bits were all zero. At least one bit must be non-zero.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x7C00, (0x7C00 & packed_float), "Exponent bits were not all set for signalling NAN.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x8000 & packed_float), "Signalling NAN sign bit was negative.");

    const uint32_t signalling_negative_nan_bits = 0xFF800000U | 0x200000U;
    packed_float = nunavutFloat16Pack(*((float*)&signalling_negative_nan_bits));
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x200 & packed_float), "-NAN was silent.");
    TEST_ASSERT_MESSAGE(0 != (0x3FF & packed_float), "Mantessa bits were all zero. At least one bit must be non-zero.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x7C00, (0x7C00 & packed_float), "Exponent bits were not all set for -NAN (signalling).");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x8000, (0x8000 & packed_float), "-NAN (signalling) sign bit was positive.");
}

static void testNunavutFloat16Pack_infinity(void)
{
    uint16_t packed_float = nunavutFloat16Pack(INFINITY);
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x3FF & packed_float), "Mantessa bits were not 0 for INFINITY.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x7C00, (0x7C00 & packed_float), "INFINITY did not set bits G5 - G4+w");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x80000 & packed_float), "INFINITY sign bit was negative.");

    packed_float = nunavutFloat16Pack(-INFINITY);
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x3FF & packed_float), "Mantessa bits were not 0 for -INFINITY.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x7C00, (0x7C00 & packed_float), "-INFINITY did not set bits G5 - G4+w");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x80000, (0x80000 & packed_float), "-INFINITY sign bit was positive.");
}

static void testNunavutFloat16Pack_zero(void)
{
    uint16_t packed_float = nunavutFloat16Pack(0.0f);
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x3FF & packed_float), "0.0f had bits in significand.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x7C00 & packed_float), "0.0f had bits in exponent.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x80000 & packed_float), "0.0f sign bit was negative.");

    packed_float = nunavutFloat16Pack(-0.0f);
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x3FF & packed_float), "-0.0f had bits in significand.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x7C00 & packed_float), "-0.0f had bits in exponent.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x80000, (0x80000 & packed_float), "-0.0f sign bit was not negative.");
}

// +--------------------------------------------------------------------------+
// | nunavutFloat16Unpack
// +--------------------------------------------------------------------------+

static void testNunavutFloat16Unpack(void)
{
    // >>> hex(int.from_bytes(np.array([-np.float16('3.14')]).tobytes(), 'little'))
    // '0xc248'
    TEST_ASSERT_FLOAT_WITHIN(0.001f, -3.14f, nunavutFloat16Unpack(0xC248));
    // >>> hex(int.from_bytes(np.array([np.float16('3.14')]).tobytes(), 'little'))
    // '0x4248'
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 3.14f, nunavutFloat16Unpack(0x4248));
    // >>> hex(int.from_bytes(np.array([np.float16('nan')]).tobytes(), 'little'))
    // '0x7e00'
    TEST_ASSERT_FLOAT_IS_NAN(nunavutFloat16Unpack(0x7e00));
    // >>> hex(int.from_bytes(np.array([-np.float16('nan')]).tobytes(), 'little'))
    // '0xfe00'
    TEST_ASSERT_FLOAT_IS_NAN(nunavutFloat16Unpack(0xfe00));
    // >>> hex(int.from_bytes(np.array([np.float16('infinity')]).tobytes(), 'little'))
    // '0x7c00'
    TEST_ASSERT_FLOAT_IS_INF(nunavutFloat16Unpack(0x7c00));
    // >>> hex(int.from_bytes(np.array([-np.float16('infinity')]).tobytes(), 'little'))
    // '0xfc00'
    TEST_ASSERT_FLOAT_IS_NEG_INF(nunavutFloat16Unpack(0xfc00));
}

static void testNunavutFloat16Unpack_signallingNan(void)
{
    const uint16_t signalling_nan_bits = 0x7D00;
    const float signalling_nan = nunavutFloat16Unpack(signalling_nan_bits);
    TEST_ASSERT_FLOAT_IS_NAN(signalling_nan);
    union
    {
        float fp;
        struct
        {
            union
            {
                uint32_t as_number : 23;
                struct
                {
                    uint32_t diagnostic : 22;
                    uint32_t nsignalling : 1;
                } as_nan;
            } mantessa;
            uint32_t exponent : 8;
            uint32_t sign : 1;
        } ieee;
    } as_bits = {signalling_nan};
    TEST_ASSERT_EQUAL_MESSAGE(0, as_bits.ieee.mantessa.as_nan.nsignalling, "Signalling NAN was quieted!");
}

static void testNunavutFloat16Unpack_quietNan(void)
{
    const uint16_t signalling_nan_bits = 0x7E00;
    const float signalling_nan = nunavutFloat16Unpack(signalling_nan_bits);
    TEST_ASSERT_FLOAT_IS_NAN(signalling_nan);
    union
    {
        float fp;
        struct
        {
            union
            {
                uint32_t as_number : 23;
                struct
                {
                    uint32_t diagnostic : 22;
                    uint32_t nsignalling : 1;
                } as_nan;
            } mantessa;
            uint32_t exponent : 8;
            uint32_t sign : 1;
        } ieee;
    } as_bits = {signalling_nan};
    TEST_ASSERT_EQUAL_MESSAGE(1, as_bits.ieee.mantessa.as_nan.nsignalling, "Quiet NAN was converted to signalling!");
}

void testNunavutFloat16Unpack_INFINITY(void)
{
    TEST_ASSERT_FLOAT_IS_INF(nunavutFloat16Unpack(0x7C00));
    TEST_ASSERT_FLOAT_IS_NEG_INF(nunavutFloat16Unpack(0xFC00));
}

// +--------------------------------------------------------------------------+
// | nunavutFloat16Pack/Unpack
// +--------------------------------------------------------------------------+

static void helperPackUnpack(float source_value, uint16_t compare_mask, size_t iterations)
{
    const uint16_t packed = nunavutFloat16Pack(source_value);
    uint16_t repacked = packed;
    char message_buffer[128];

    for(size_t i = 0; i < iterations; ++i)
    {
        repacked = nunavutFloat16Pack(nunavutFloat16Unpack(repacked));
        snprintf(message_buffer, 128, "source_value=%f, compare_mask=%X, i=%zu", source_value, compare_mask, i);
        TEST_ASSERT_EQUAL_HEX16_MESSAGE(packed & compare_mask, repacked & compare_mask, message_buffer);
    }
}

/**
 * Test pack/unpack stability.
 */
static void testNunavutFloat16PackUnpack(void)
{
    const uint32_t signalling_nan_bits = 0x7F800000U | 0x200000U;
    const uint32_t signalling_negative_nan_bits = 0xFF800000U | 0x200000U;

    helperPackUnpack(3.14f, 0xFFFF, 10);
    helperPackUnpack(-3.14f, 0xFFFF, 10);
    helperPackUnpack(65536.141592653589793238462643383279f, 0xFFFF, 100);
    helperPackUnpack(-65536.141592653589793238462643383279f, 0xFFFF, 100);

    helperPackUnpack(NAN, 0xFE00, 10);
    helperPackUnpack(-NAN, 0xFE00, 10);
    helperPackUnpack(*((float*)&signalling_nan_bits), 0xFF00, 10);
    helperPackUnpack(*((float*)&signalling_negative_nan_bits), 0xFF00, 10);
    helperPackUnpack(INFINITY, 0xFF00, 10);
    helperPackUnpack(-INFINITY, 0xFF00, 10);
}

static void testNunavutFloat16PackUnpack_NAN(void)
{
    TEST_ASSERT_FLOAT_IS_NAN(nunavutFloat16Unpack(nunavutFloat16Pack(NAN)));
}

// +--------------------------------------------------------------------------+
// | testNunavutSetF16
// +--------------------------------------------------------------------------+

static void testNunavutSet16(void)
{
    uint8_t buf[3];
    buf[2] = 0x00;
    nunavutSetF16(buf, sizeof(buf), 0, 3.14f);
    TEST_ASSERT_EQUAL_HEX8(0x48, buf[0]);
    TEST_ASSERT_EQUAL_HEX8(0x42, buf[1]);
    TEST_ASSERT_EQUAL_HEX8(0x00, buf[2]);
}



// +--------------------------------------------------------------------------+
// | testNunavutGetF16
// +--------------------------------------------------------------------------+

static void testNunavutGet16(void)
{
    // >>> hex(int.from_bytes(np.array([np.float16('3.14')]).tobytes(), 'little'))
    // '0x4248'
    const uint8_t buf[3] = {0x48, 0x42, 0x00};
    const float result = nunavutGetF16(buf, 3, 0);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 3.14f, result);
}

// +--------------------------------------------------------------------------+
// | testNunavutSetF32
// +--------------------------------------------------------------------------+
/**
 * Compare the results of Nunavut serialization to the IEEE definition. These must match.
 */
static void helperAssertSerFloat32SameAsIEEE(const float original_value, const uint8_t* serialized_result)
{
    union
    {
        float f;
        struct
        {
            uint32_t mantissa : 23;
            uint32_t exponent : 8;
            uint32_t negative : 1;
        } ieee;
    } as_int = {original_value};

    TEST_ASSERT_EQUAL_HEX8_MESSAGE(as_int.ieee.mantissa & 0xFF, serialized_result[0], "First 8 bits of mantissa did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE((as_int.ieee.mantissa >> 8U) & 0xFF, serialized_result[1], "Second 8 bits of mantissa did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE((as_int.ieee.mantissa >> 16U) & 0x3F, serialized_result[2] & 0x3F, "Last 6 bits of mantissa did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE((as_int.ieee.mantissa >> 16U) & 0x40, serialized_result[2] & 0x40, "7th bit of mantissa did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE(as_int.ieee.exponent & 0x1, (serialized_result[2] >> 7U) & 0x01, "First bit of exponent did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE((as_int.ieee.exponent >> 1U) & 0x7F, serialized_result[3] & 0x7F, "Last 7 bits of exponent did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE(as_int.ieee.negative & 0x1, (serialized_result[3] >> 7U) & 0x01, "Negative bit did not match.");
}

static void testNunavutSetF32(void)
{
    uint8_t buffer[] = {0x00, 0x00, 0x00, 0x00};
    nunavutSetF32(buffer, sizeof(buffer), 0, 3.14f);
    helperAssertSerFloat32SameAsIEEE(3.14f, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF32(buffer, sizeof(buffer), 0, -3.14f);
    helperAssertSerFloat32SameAsIEEE(-3.14f, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF32(buffer, sizeof(buffer), 0, -NAN);
    helperAssertSerFloat32SameAsIEEE(-NAN, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF32(buffer, sizeof(buffer), 0, NAN);
    helperAssertSerFloat32SameAsIEEE(NAN, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF32(buffer, sizeof(buffer), 0, INFINITY);
    helperAssertSerFloat32SameAsIEEE(INFINITY, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF32(buffer, sizeof(buffer), 0, -INFINITY);
    helperAssertSerFloat32SameAsIEEE(-INFINITY, buffer);
}

// +--------------------------------------------------------------------------+
// | testNunavutGetF32
// +--------------------------------------------------------------------------+

static void testNunavutGetF32(void)
{
    // >>> hex(int.from_bytes(np.array([-np.float32('infinity')]).tobytes(), 'little'))
    // '0xff800000'
    const uint8_t buffer_neg_inf[] = {0x00, 0x00, 0x80, 0xFF};
    float result = nunavutGetF32(buffer_neg_inf, 4, 0);
    TEST_ASSERT_FLOAT_IS_NEG_INF(result);

    // >>> hex(int.from_bytes(np.array([np.float32('infinity')]).tobytes(), 'little'))
    // '0x7f800000'
    const uint8_t buffer_inf[] = {0x00, 0x00, 0x80, 0x7F};
    result = nunavutGetF32(buffer_inf, 4, 0);
    TEST_ASSERT_FLOAT_IS_INF(result);

    // >>> hex(int.from_bytes(np.array([np.float32('nan')]).tobytes(), 'little'))
    // '0x7fc00000'
    const uint8_t buffer_nan[] = {0x00, 0x00, 0xC0, 0x7F};
    result = nunavutGetF32(buffer_nan, 4, 0);
    TEST_ASSERT_FLOAT_IS_NAN(result);

    // >>> hex(int.from_bytes(np.array([np.float32('3.14')]).tobytes(), 'little'))
    // '0x4048f5c3'
    const uint8_t buffer_pi[] = {0xC3, 0xF5, 0x48, 0x40};
    result = nunavutGetF32(buffer_pi, 4, 0);
    TEST_ASSERT_EQUAL_FLOAT(3.14f, result);
}


// +--------------------------------------------------------------------------+
// | testNunavutGetF64
// +--------------------------------------------------------------------------+

static void testNunavutGetF64(void)
{
    // >>> hex(int.from_bytes(np.array([np.float64('3.141592653589793')]).tobytes(), 'little'))
    // '0x400921fb54442d18'
    const uint8_t buffer_pi[] = {0x18, 0x2D, 0x44, 0x54, 0xFB, 0x21, 0x09, 0x40};
    double result = nunavutGetF64(buffer_pi, 8, 0);
    TEST_ASSERT_EQUAL_DOUBLE(3.141592653589793, result);

    // >>> hex(int.from_bytes(np.array([np.float64('infinity')]).tobytes(), 'little'))
    // '0x7ff0000000000000'
    const uint8_t buffer_inf[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF0, 0x7F};
    result = nunavutGetF64(buffer_inf, 8, 0);
    TEST_ASSERT_DOUBLE_IS_INF(result);

    // >>> hex(int.from_bytes(np.array([-np.float64('infinity')]).tobytes(), 'little'))
    // '0xfff0000000000000'
    const uint8_t buffer_neg_inf[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF0, 0xFF};
    result = nunavutGetF64(buffer_neg_inf, 8, 0);
    TEST_ASSERT_DOUBLE_IS_NEG_INF(result);

    // >>> hex(int.from_bytes(np.array([np.float64('nan')]).tobytes(), 'little'))
    // '0x7ff8000000000000'
    const uint8_t buffer_nan[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF8, 0x7F};
    result = nunavutGetF64(buffer_nan, 8, 0);
    TEST_ASSERT_DOUBLE_IS_NAN(result);

}

// +--------------------------------------------------------------------------+
// | testNunavutSetF64
// +--------------------------------------------------------------------------+
/**
 * Compare the results of Nunavut serialization to the IEEE definition. These must match.
 */
static void helperAssertSerFloat64SameAsIEEE(const double original_value, const uint8_t* serialized_result)
{
    union
    {
        double f;
        struct
        {
            uint64_t mantissa : 52;
            uint64_t exponent : 11;
            uint64_t negative : 1;
        } ieee;
    } as_int = {original_value};

    union
    {
        uint64_t as_int;
        uint8_t as_bytes[8];
    } result_bytes;
    memcpy(result_bytes.as_bytes, serialized_result, 8);

    TEST_ASSERT_EQUAL_HEX64_MESSAGE(as_int.ieee.mantissa & 0xFFFFFFFFFFFFF, result_bytes.as_int & 0xFFFFFFFFFFFFF, "Mantessa did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE(as_int.ieee.exponent & 0xF, (serialized_result[6] >> 4U) & 0xF, "First four bits of exponent did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE((as_int.ieee.exponent >> 4U) & 0x7F, serialized_result[7] & 0x7F, "Last 7 bits of exponent did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE(as_int.ieee.negative & 0x1, (serialized_result[7] >> 7U) & 0x01, "Negative bit did not match.");
}

static void testNunavutSetF64(void)
{
    uint8_t buffer[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    nunavutSetF64(buffer, sizeof(buffer), 0, 3.141592653589793);
    helperAssertSerFloat64SameAsIEEE(3.141592653589793, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF64(buffer, sizeof(buffer), 0, -3.141592653589793);
    helperAssertSerFloat64SameAsIEEE(-3.141592653589793, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF64(buffer, sizeof(buffer), 0, -NAN);
    helperAssertSerFloat64SameAsIEEE(-NAN, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF64(buffer, sizeof(buffer), 0, NAN);
    helperAssertSerFloat64SameAsIEEE(NAN, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF64(buffer, sizeof(buffer), 0, INFINITY);
    helperAssertSerFloat64SameAsIEEE(INFINITY, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF64(buffer, sizeof(buffer), 0, -INFINITY);
    helperAssertSerFloat64SameAsIEEE(-INFINITY, buffer);
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
    RUN_TEST(testNunavutSetIxx_bufferOverflow);
    RUN_TEST(testNunavutSetBit);
    RUN_TEST(testNunavutSetBit_bufferOverflow);
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
    RUN_TEST(testNunavutFloat16Pack);
    RUN_TEST(testNunavutFloat16Pack_NAN_cmath);
    RUN_TEST(testNunavutFloat16Pack_NAN_quiet);
    RUN_TEST(testNunavutFloat16Pack_NAN_signalling);
    RUN_TEST(testNunavutFloat16Pack_infinity);
    RUN_TEST(testNunavutFloat16Pack_zero);
    RUN_TEST(testNunavutFloat16Unpack);
    RUN_TEST(testNunavutFloat16Unpack_signallingNan);
    RUN_TEST(testNunavutFloat16Unpack_quietNan);
    RUN_TEST(testNunavutFloat16PackUnpack);
    RUN_TEST(testNunavutFloat16PackUnpack_NAN);
    RUN_TEST(testNunavutFloat16Unpack_INFINITY);
    RUN_TEST(testNunavutSet16);
    RUN_TEST(testNunavutGet16);
    RUN_TEST(testNunavutSetF32);
    RUN_TEST(testNunavutGetF32);
    RUN_TEST(testNunavutGetF64);
    RUN_TEST(testNunavutSetF64);

    return UNITY_END();
}
