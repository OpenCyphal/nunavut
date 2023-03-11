// Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
//
// Tests the common functionality provided by the Nunavut support headers.

#include "helpers.h"

#include "nunavut/support/serialization.h"
#include "unity.h"  // Include 3rd-party headers afterward to ensure that our header is self-sufficient.

// +--------------------------------------------------------------------------+
// | nunavutCopyBits
// +--------------------------------------------------------------------------+

#if CHAR_BIT == 32

  #define x00 0x00000000
  #define x11 0x11111111
  #define x22 0x22222222
  #define x33 0x33333333
  #define x44 0x44444444
  #define x55 0x55555555
  #define x66 0x66666666
  #define x77 0x77777777
  #define x88 0x88888888
  #define x99 0x99999999
  #define xAA 0xAAAAAAAA
  #define xBB 0xBBBBBBBB
  #define xCC 0xCCCCCCCC
  #define xDD 0xDDDDDDDD
  #define xEE 0xEEEEEEEE
  #define xFF 0xFFFFFFFF

#elif CHAR_BIT == 16

  #define x00 0x0000
  #define x11 0x1111
  #define x22 0x2222
  #define x33 0x3333
  #define x44 0x4444
  #define x55 0x5555
  #define x66 0x6666
  #define x77 0x7777
  #define x88 0x8888
  #define x99 0x9999
  #define xAA 0xAAAA
  #define xBB 0xBBBB
  #define xCC 0xCCCC
  #define xDD 0xDDDD
  #define xEE 0xEEEE
  #define xFF 0xFFFF

#elif CHAR_BIT == 8

  #define x00 0x00
  #define x11 0x11
  #define x22 0x22
  #define x33 0x33
  #define x44 0x44
  #define x55 0x55
  #define x66 0x66
  #define x77 0x77
  #define x88 0x88
  #define x99 0x99
  #define xAA 0xAA
  #define xBB 0xBB
  #define xCC 0xCC
  #define xDD 0xDD
  #define xEE 0xEE
  #define xFF 0xFF

#else

  #error Strange CHAR_BIT value!

#endif

// +--------------------------------------------------------------------------+
// | nunavutCopyBits
// +--------------------------------------------------------------------------+

static void testNunavutCopyBits(void)
{
    size_t i;
    const unsigned char src[] = { x11, x22, x33, x44, x55 };
    unsigned char dst[6];
    memset(dst, 0, sizeof(dst));
    nunavutCopyBits(dst, 0, sizeof(src) * CHAR_BIT, src, 0);
    for( i = 0; i < sizeof(src); ++i)
    {
        TEST_ASSERT_EQUAL_UINT8(src[i], dst[i]);
    }
}

static void testNunavutCopyBitsWithAlignedOffset(void)
{
    size_t i;
    const unsigned char src[] = { x11, x22, x33, x44, x55 };
    unsigned char dst[6];
    memset(dst, 0, sizeof(dst));
    nunavutCopyBits(dst, 0, (sizeof(src) - 1) * CHAR_BIT, src, CHAR_BIT);
    for(i = 0; i < sizeof(src) - 1; ++i)
    {
        TEST_ASSERT_EQUAL_UINT8(src[i + 1], dst[i]);
    }
    TEST_ASSERT_EQUAL_UINT8(0, dst[sizeof(dst) - 1]);

    memset(dst, 0, sizeof(dst));
    nunavutCopyBits(dst, CHAR_BIT, sizeof(src) * CHAR_BIT, src, 0);
    for(i = 0; i < sizeof(src) - 1; ++i)
    {
        TEST_ASSERT_EQUAL_UINT8(src[i], dst[i+1]);
    }
    TEST_ASSERT_EQUAL_UINT8(0, dst[0]);
}

static void testNunavutCopyBitsWithUnalignedOffset(void)
{
    size_t i;
    const unsigned char src[] = { xAA, xAA, xAA, xAA, xAA, xAA };
    unsigned char dst[6];
    memset(dst, 0, sizeof(dst));
    nunavutCopyBits(dst, 0, (sizeof(src)-1) * CHAR_BIT, src, 1);
    for(i = 0; i < sizeof(src) - 1; ++i)
    {
        TEST_ASSERT_EQUAL_HEX8(x55, dst[i]);
    }
    TEST_ASSERT_EQUAL_HEX8(x00, dst[sizeof(dst) - 1]);

    memset(dst, 0, sizeof(dst));
    nunavutCopyBits(dst, 1, (sizeof(src)-1) * CHAR_BIT, src, 0);
    for(i = 0; i < sizeof(src) - 1; ++i)
    {
        TEST_ASSERT_EQUAL_HEX8((i == 0) ? (x55^1) : x55, dst[i]);
    }
    TEST_ASSERT_EQUAL_HEX8((x55^1), dst[0]);
}

// +--------------------------------------------------------------------------+
// | nunavutSaturateBufferFragmentBitLength
// +--------------------------------------------------------------------------+

static void testNunavutSaturateBufferFragmentBitLength(void)
{
    TEST_ASSERT_EQUAL_UINT32(CHAR_BIT*4-0, nunavutSaturateBufferFragmentBitLength(4*CHAR_BIT, 0           , CHAR_BIT*4));
    TEST_ASSERT_EQUAL_UINT32(CHAR_BIT*4-1, nunavutSaturateBufferFragmentBitLength(4*CHAR_BIT, 1           , CHAR_BIT*4));
    TEST_ASSERT_EQUAL_UINT32(CHAR_BIT*2-0, nunavutSaturateBufferFragmentBitLength(4*CHAR_BIT, 0           , CHAR_BIT*2));
    TEST_ASSERT_EQUAL_UINT32(CHAR_BIT*2-1, nunavutSaturateBufferFragmentBitLength(4*CHAR_BIT, CHAR_BIT*2+1, CHAR_BIT*3));
    TEST_ASSERT_EQUAL_UINT32(CHAR_BIT*0-0, nunavutSaturateBufferFragmentBitLength(2*CHAR_BIT, CHAR_BIT*3  , CHAR_BIT*3));
}

// +--------------------------------------------------------------------------+
// | nunavutGetBits
// +--------------------------------------------------------------------------+

static inline unsigned char helperHalfcharsCombine(const unsigned char* src)
{
    #define HALFCHAR_BIT (CHAR_BIT >> 1u)
    #define LOWER_HALFCHAR_MASK ((1 << HALFCHAR_BIT) - 1u)
    #define UPPER_HALFCHAR_MASK (LOWER_HALFCHAR_MASK << HALFCHAR_BIT)
    return ((src[1] & LOWER_HALFCHAR_MASK) << HALFCHAR_BIT) | (((src[0] & UPPER_HALFCHAR_MASK) >> HALFCHAR_BIT) & LOWER_HALFCHAR_MASK);
}
static void testNunavutGetBits(void)
{
    const unsigned char src[] = { x11, x22, x33, x44, x55, x66, x77, x88, x99, xAA, xBB, xCC, xDD, xEE, xFF };
    unsigned char dst[6];
    memset(dst, xAA, sizeof(dst));
    nunavutGetBits(dst, src, 6*CHAR_BIT, 0, 0);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[0]);   // no bytes copied
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[1]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[2]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[3]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[4]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[5]);

    nunavutGetBits(dst, src, 0*CHAR_BIT, 0, 4*CHAR_BIT);
    TEST_ASSERT_EQUAL_HEX8(x00, dst[0]);   // all bytes zero-extended
    TEST_ASSERT_EQUAL_HEX8(x00, dst[1]);
    TEST_ASSERT_EQUAL_HEX8(x00, dst[2]);
    TEST_ASSERT_EQUAL_HEX8(x00, dst[3]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[4]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[5]);

    nunavutGetBits(dst, src, 6*CHAR_BIT, 6*CHAR_BIT, 4*CHAR_BIT);
    TEST_ASSERT_EQUAL_HEX8(x00, dst[0]);   // all bytes zero-extended
    TEST_ASSERT_EQUAL_HEX8(x00, dst[1]);
    TEST_ASSERT_EQUAL_HEX8(x00, dst[2]);
    TEST_ASSERT_EQUAL_HEX8(x00, dst[3]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[4]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[5]);

    memset(dst, xAA, sizeof(dst));
    nunavutGetBits(dst, src, 6*CHAR_BIT, 5*CHAR_BIT, 4*CHAR_BIT);
    TEST_ASSERT_EQUAL_HEX8(x66, dst[0]);   // one byte copied
    TEST_ASSERT_EQUAL_HEX8(x00, dst[1]);   // the rest are zero-extended
    TEST_ASSERT_EQUAL_HEX8(x00, dst[2]);
    TEST_ASSERT_EQUAL_HEX8(x00, dst[3]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[4]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[5]);

    memset(dst, xAA, sizeof(dst));
    nunavutGetBits(dst, src, 6*CHAR_BIT, 5*CHAR_BIT - (CHAR_BIT >> 1), 4*CHAR_BIT);
    #define x65  helperHalfcharsCombine(src+4)
    #define x06 (helperHalfcharsCombine(src+5) & LOWER_HALFCHAR_MASK)
    TEST_ASSERT_EQUAL_HEX8(x65, dst[0]);   // one-and-half bytes are copied
    TEST_ASSERT_EQUAL_HEX8(x06, dst[1]);   // the rest are zero-extended
    TEST_ASSERT_EQUAL_HEX8(x00, dst[2]);
    TEST_ASSERT_EQUAL_HEX8(x00, dst[3]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[4]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[5]);

    memset(dst, xAA, sizeof(dst));
    #define x21  helperHalfcharsCombine(src+0)
    #define x32  helperHalfcharsCombine(src+1)
    #define x43  helperHalfcharsCombine(src+2)
    #define x54  helperHalfcharsCombine(src+3)
    nunavutGetBits(dst, src, 7*CHAR_BIT, (CHAR_BIT >> 1), 4*CHAR_BIT);
    TEST_ASSERT_EQUAL_HEX8(x21, dst[0]);   // all bytes are copied offset by half
    TEST_ASSERT_EQUAL_HEX8(x32, dst[1]);
    TEST_ASSERT_EQUAL_HEX8(x43, dst[2]);
    TEST_ASSERT_EQUAL_HEX8(x54, dst[3]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[4]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[5]);

    memset(dst, xAA, sizeof(dst));
    #define x04 (helperHalfcharsCombine(src+3) & LOWER_HALFCHAR_MASK)
    nunavutGetBits(dst, src, 7*CHAR_BIT, (CHAR_BIT >> 1), 4*CHAR_BIT - (CHAR_BIT >> 1));
    TEST_ASSERT_EQUAL_HEX8(x21, dst[0]);   // three-and-half bytes are copied
    TEST_ASSERT_EQUAL_HEX8(x32, dst[1]);
    TEST_ASSERT_EQUAL_HEX8(x43, dst[2]);
    TEST_ASSERT_EQUAL_HEX8(x04, dst[3]);   // the last bits of the last byte are zero-padded out
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[4]);
    TEST_ASSERT_EQUAL_HEX8(xAA, dst[5]);
}

// +--------------------------------------------------------------------------+
// | nunavutSetIxx
// +--------------------------------------------------------------------------+

static void testNunavutSetIxx_neg1(void)
{
    int64_t i64 = 0;
    nunavutSetIxx(&i64, sizeof(i64)*CHAR_BIT, 0, -1, 64);
    TEST_ASSERT_EQUAL_HEX64(((int64_t)(-1)), i64);
}

static void testNunavutSetIxx_neg255(void)
{
    int64_t i64 = 0;
    const signed char min_val = xFF;
    nunavutSetIxx(&i64, sizeof(i64)*CHAR_BIT, 0, min_val, 64);
    TEST_ASSERT_EQUAL_HEX64(((int64_t)min_val), i64);
}

static void testNunavutSetIxx_neg255_tooSmall(void)
{
    int64_t i64 = 0;
    nunavutSetIxx(&i64, sizeof(i64)*CHAR_BIT, 0, -255, 8);
    TEST_ASSERT_EQUAL_HEX64(0x01, i64);
}

static void testNunavutSetIxx_bufferOverflow(void)
{
    unsigned char buffer[] = {x00, x00, x00};
    int rc = nunavutSetIxx(buffer, 3*CHAR_BIT, 2*CHAR_BIT, xAA, CHAR_BIT);
    TEST_ASSERT_EQUAL_INT8(NUNAVUT_SUCCESS, rc);
    TEST_ASSERT_EQUAL_HEX8(xAA, buffer[2]);
    rc = nunavutSetIxx(buffer, 2*CHAR_BIT, 2*CHAR_BIT, x00, CHAR_BIT);
    TEST_ASSERT_EQUAL_INT8(-NUNAVUT_ERROR_SERIALIZATION_BUFFER_TOO_SMALL, rc);
    TEST_ASSERT_EQUAL_HEX8(xAA, buffer[2]);
}

// +--------------------------------------------------------------------------+
// | nunavut[Get|Set]Bit
// +--------------------------------------------------------------------------+

static void testNunavutSetBit(void)
{
    unsigned char buffer[] = {0x00};
    nunavutSetBit(buffer, sizeof(buffer)*CHAR_BIT, 0, true);
    TEST_ASSERT_EQUAL_HEX8(0x01, buffer[0]);
    nunavutSetBit(buffer, sizeof(buffer)*CHAR_BIT, 0, false);
    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[0]);
    nunavutSetBit(buffer, sizeof(buffer)*CHAR_BIT, 0, true);
    nunavutSetBit(buffer, sizeof(buffer)*CHAR_BIT, 1, true);
    TEST_ASSERT_EQUAL_HEX8(0x03, buffer[0]);
}

static void testNunavutSetBit_bufferOverflow(void)
{
    unsigned char buffer[] = {0x00, 0x00};
    int rc = nunavutSetBit(buffer, 1*CHAR_BIT, 1*CHAR_BIT, true);
    TEST_ASSERT_EQUAL_INT8(-NUNAVUT_ERROR_SERIALIZATION_BUFFER_TOO_SMALL, rc);
    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[1]);
}

static void testNunavutGetBit(void)
{
    unsigned char buffer[] = {0x01};
    TEST_ASSERT_EQUAL(true , nunavutGetBit(buffer, 1*CHAR_BIT, 0));
    TEST_ASSERT_EQUAL(false, nunavutGetBit(buffer, 1*CHAR_BIT, 1));
}

// +--------------------------------------------------------------------------+
// | nunavutGetU8
// +--------------------------------------------------------------------------+

static void testNunavutGetU8(void)
{
    const unsigned char data[] = {0xAAFE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    TEST_ASSERT_EQUAL_HEX8(0xFE, nunavutGetU8(data, sizeof(data)*CHAR_BIT, 0, 8U));
}

static void testNunavutGetU8_tooSmall(void)
{
    const unsigned char data[] = {0xAAFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    TEST_ASSERT_EQUAL_HEX8(0x7F, nunavutGetU8(data, sizeof(data), 0, 7U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetU16
// +--------------------------------------------------------------------------+

static void testNunavutGetU16(void)
{
    const unsigned char data[] = {xAA, xAA};
    TEST_ASSERT_EQUAL_HEX16(0xAAAA, nunavutGetU16(data, sizeof(data)*CHAR_BIT, 0, 16U));
}

static void testNunavutGetU16_tooSmall(void)
{
    const unsigned char data[] = {0xAAAA};
    TEST_ASSERT_EQUAL_HEX16(0x0055, nunavutGetU16(data, sizeof(data)*CHAR_BIT, 9, 16U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetU32
// +--------------------------------------------------------------------------+

static void testNunavutGetU32(void)
{
    const uint_fast32_t data[] = {0xAAAAAAAA};
    TEST_ASSERT_EQUAL_HEX32(0xAAAAAAAA, nunavutGetU32(data, sizeof(data)*CHAR_BIT, 0, 32U));
}

static void testNunavutGetU32_tooSmall(void)
{
    const uint_fast32_t data[] = {0xAAAAAAAA};
    TEST_ASSERT_EQUAL_HEX32(0x00555555, nunavutGetU32(data, sizeof(data)*CHAR_BIT, 9, 32U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetU64
// +--------------------------------------------------------------------------+

static void testNunavutGetU64(void)
{
    const unsigned char data[] = {xAA, xAA, xAA, xAA, xAA, xAA, xAA, xAA};
    TEST_ASSERT_EQUAL_HEX64(0xAAAAAAAAAAAAAAAA, nunavutGetU64(data, sizeof(data)*CHAR_BIT, 0, 64U));
}

static void testNunavutGetU64_tooSmall(void)
{
    const uint64_t data[] = {0xAAAAAAAAAAAAAAAA};
    TEST_ASSERT_EQUAL_HEX64(0x0055555555555555, nunavutGetU64(data, sizeof(data)*CHAR_BIT, 9, 64U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetI8
// +--------------------------------------------------------------------------+

static void testNunavutGetI8(void)
{
    const unsigned char data[] = {0xFF};
    TEST_ASSERT_EQUAL_INT8(-1, nunavutGetI8(data, sizeof(data)*CHAR_BIT, 0, 8U));
}

static void testNunavutGetI8_tooSmall(void)
{
    const unsigned char data[] = {0xFF};
    TEST_ASSERT_EQUAL_INT8(127, nunavutGetI8(data, sizeof(data)*CHAR_BIT, 1, 8U));
}

static void testNunavutGetI8_tooSmallAndNegative(void)
{
    const unsigned char data[] = {0xFF};
    TEST_ASSERT_EQUAL_INT8(-1, nunavutGetI8(data, sizeof(data)*CHAR_BIT, 0, 4U));
}

static void testNunavutGetI8_zeroDataLen(void)
{
    const unsigned char data[] = {0xFF};
    TEST_ASSERT_EQUAL_INT8(0, nunavutGetI8(data, sizeof(data)*CHAR_BIT, 0, 0U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetI16
// +--------------------------------------------------------------------------+

static void testNunavutGetI16(void)
{
    const uint_fast16_t data[] = {0xFFFF};
    TEST_ASSERT_EQUAL_INT16(-1, nunavutGetI16(data, sizeof(data)*CHAR_BIT, 0, 16U));
}

static void testNunavutGetI16_tooSmall(void)
{
    const uint_fast16_t data[] = {0xFFFF};
    TEST_ASSERT_EQUAL_INT16(32767, nunavutGetI16(data, sizeof(data)*CHAR_BIT, 1, 16U));
}

static void testNunavutGetI16_tooSmallAndNegative(void)
{
    const uint_fast16_t data[] = {0xFFFF};
    TEST_ASSERT_EQUAL_INT16(-1, nunavutGetI16(data, sizeof(data)*CHAR_BIT, 0, 12U));
}

static void testNunavutGetI16_zeroDataLen(void)
{
    const uint_fast16_t data[] = {0xFFFF};
    TEST_ASSERT_EQUAL_INT16(0, nunavutGetI16(data, sizeof(data)*CHAR_BIT, 0, 0U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetI32
// +--------------------------------------------------------------------------+

static void testNunavutGetI32(void)
{
    const uint_fast32_t data[] = {0xFFFFFFFF};
    TEST_ASSERT_EQUAL_INT32(-1, nunavutGetI32(data, sizeof(data)*CHAR_BIT, 0, 32U));
}

static void testNunavutGetI32_tooSmall(void)
{
    const uint_fast32_t data[] = {0xFFFFFFFF};
    TEST_ASSERT_EQUAL_INT32(2147483647, nunavutGetI32(data, sizeof(data)*CHAR_BIT, 1, 32U));
}

static void testNunavutGetI32_tooSmallAndNegative(void)
{
    const uint_fast32_t data[] = {0xFFFFFFFF};
    TEST_ASSERT_EQUAL_INT32(-1, nunavutGetI32(data, sizeof(data)*CHAR_BIT, 0, 20U));
}

static void testNunavutGetI32_zeroDataLen(void)
{
    const uint_fast32_t data[] = {0xFFFFFFFF};
    TEST_ASSERT_EQUAL_INT32(0, nunavutGetI32(data, sizeof(data)*CHAR_BIT, 0, 0U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetI64
// +--------------------------------------------------------------------------+

static void testNunavutGetI64(void)
{
    const uint64_t data[] = {0xFFFFFFFFFFFFFFFF};
    TEST_ASSERT_EQUAL_INT64(-1, nunavutGetI64(data, sizeof(data)*CHAR_BIT, 0, 64U));
}

static void testNunavutGetI64_tooSmall(void)
{
    const uint64_t data[] = {0xFFFFFFFFFFFFFFFF};
    TEST_ASSERT_EQUAL_INT64(9223372036854775807, nunavutGetI64(data, sizeof(data)*CHAR_BIT, 1, 64U));
}

static void testNunavutGetI64_tooSmallAndNegative(void)
{
    const uint64_t data[] = {0xFFFFFFFFFFFFFFFF};
    TEST_ASSERT_EQUAL_INT64(-1, nunavutGetI64(data, sizeof(data)*CHAR_BIT, 0, 60U));
}

static void testNunavutGetI64_zeroDataLen(void)
{
    const uint64_t data[] = {0xFFFFFFFFFFFFFFFF};
    TEST_ASSERT_EQUAL_INT64(0, nunavutGetI64(data, sizeof(data)*CHAR_BIT, 0, 0U));
}

// +--------------------------------------------------------------------------+
// | nunavutFloat16Pack
// +--------------------------------------------------------------------------+

static void testNunavutFloat16Pack(void)
{
    // Comparing to NumPy calculated values

    uint_fast16_t packed_float = nunavutFloat16Pack(3.14f);
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
    uint_fast16_t packed_float = nunavutFloat16Pack(NAN32);
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x7C00, (0x7C00UL & packed_float), "Exponent bits were not all set for NAN32.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0000, (0x8000UL & packed_float), "NAN32 sign bit was negative.");

    packed_float = nunavutFloat16Pack(-NAN32);
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x7C00, (0x7C00UL & packed_float), "Exponent bits were not all set for -NAN32.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x8000, (0x8000UL & packed_float), "-NAN32 sign bit was positive.");
}

static void testNunavutFloat16Pack_infinity(void)
{
    uint_fast16_t packed_float = nunavutFloat16Pack(INF32);
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0000, (0x03FF & packed_float), "Mantessa bits were not 0 for INF32.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x7C00, (0x7C00 & packed_float), "INF32 did not set bits G5 - G4+w");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0000, (0x8000 & packed_float), "INF32 sign bit was negative.");

    packed_float = nunavutFloat16Pack(-INF32);
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0000, (0x03FF & packed_float), "Mantessa bits were not 0 for -INF32.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x7C00, (0x7C00 & packed_float), "-INF32 did not set bits G5 - G4+w");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x8000, (0x8000 & packed_float), "-INF32 sign bit was positive.");
}

static void testNunavutFloat16Pack_zero(void)
{
    uint_fast16_t packed_float = nunavutFloat16Pack(0.0f);
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x03FF & packed_float), "0.0f had bits in significand.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x7C00 & packed_float), "0.0f had bits in exponent.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0, (0x8000 & packed_float), "0.0f sign bit was negative.");

    #ifndef __TMS320C28XX__ // Texas Instruments C2000 Code Generation Tools 5.1.2 ignores minus sign in zero float
      packed_float = nunavutFloat16Pack(-0.0f);
      TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0000, (0x03FF & packed_float), "-0.0f had bits in significand.");
      TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x0000, (0x7C00 & packed_float), "-0.0f had bits in exponent.");
      TEST_ASSERT_EQUAL_HEX16_MESSAGE(0x8000, (0x8000 & packed_float), "-0.0f sign bit was not negative.");
    #endif
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

static void testNunavutFloat16Unpack_INFINITY(void)
{
    TEST_ASSERT_FLOAT_IS_INF    (nunavutFloat16Unpack(0x7C00));
    TEST_ASSERT_FLOAT_IS_NEG_INF(nunavutFloat16Unpack(0xFC00));
}

// +--------------------------------------------------------------------------+
// | nunavutFloat16Pack/Unpack
// +--------------------------------------------------------------------------+

static void helperPackUnpack(float source_value, uint_fast16_t compare_mask, size_t iterations)
{
    const uint_fast16_t packed = nunavutFloat16Pack(source_value);
    uint_fast16_t repacked = packed;
    char message_buffer[128];
    size_t i;
    message_buffer[0] = '\0';;
    for(i = 0; i < iterations; ++i)
    {
        repacked = nunavutFloat16Pack(nunavutFloat16Unpack(repacked));
        #ifndef __TMS320C28XX__ // Texas Instruments C2000 Code Generation Tools 5.1.2 hangs in the snprintf
          snprintf(message_buffer, 128, "source_value=%f, compare_mask=%X, i=%zu", source_value, compare_mask, i);
        #endif
        TEST_ASSERT_EQUAL_HEX16_MESSAGE(packed & compare_mask, repacked & compare_mask, message_buffer);
    }
}

//
// Test pack/unpack stability.
//
static void testNunavutFloat16PackUnpack(void)
{
    const uint_fast32_t signalling_nan_bits          = 0x7F800000U | 0x200000U;
    const uint_fast32_t signalling_negative_nan_bits = 0xFF800000U | 0x200000U;

    helperPackUnpack( 3.14f, 0xFFFF, 10);
    helperPackUnpack(-3.14f, 0xFFFF, 10);
    helperPackUnpack( 65536.141592653589793238462643383279f, 0xFFFF, 100);
    helperPackUnpack(-65536.141592653589793238462643383279f, 0xFFFF, 100);

    helperPackUnpack( NAN32, 0xFE00, 10);
    helperPackUnpack(-NAN32, 0xFE00, 10);
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wstrict-aliasing"
    helperPackUnpack(*((float*)&signalling_nan_bits         ), 0xFF00, 10);
    helperPackUnpack(*((float*)&signalling_negative_nan_bits), 0xFF00, 10);
#pragma GCC diagnostic pop
    helperPackUnpack( INF32, 0xFF00, 10);
    helperPackUnpack(-INF32, 0xFF00, 10);
}

static void testNunavutFloat16PackUnpack_NAN(void)
{
    TEST_ASSERT_FLOAT_IS_NAN(nunavutFloat16Unpack(nunavutFloat16Pack(NAN32)));
}

// +--------------------------------------------------------------------------+
// | testNunavutSetF16
// +--------------------------------------------------------------------------+

static void testNunavutSetF16(void)
{
    uint_fast16_t x = 0;
    nunavutSetF16(&x, sizeof(x)*CHAR_BIT, 0, 3.14f);
    TEST_ASSERT_EQUAL_HEX8(0x48, (x >> 0 ) & 0xFF);
    TEST_ASSERT_EQUAL_HEX8(0x42, (x >> 8 ) & 0xFF);
    TEST_ASSERT_EQUAL_HEX8(0x00, (x >> 16) & 0xFF);
}

// +--------------------------------------------------------------------------+
// | testNunavutGetF16
// +--------------------------------------------------------------------------+

static void testNunavutGetF16(void)
{
    // >>> hex(int.from_bytes(np.array([np.float16('3.14')]).tobytes(), 'little'))
    // '0x4248'
    const uint_fast16_t x = 0x4248;
    const float result = nunavutGetF16(&x, sizeof(x)*CHAR_BIT, 0);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 3.14f, result);
}

// +--------------------------------------------------------------------------+
// | testNunavutSetF32
// +--------------------------------------------------------------------------+
//
// Compare the results of Nunavut serialization to the IEEE definition. These must match.
//
static void helperAssertSerFloat32SameAsIEEE(const float original_value, const unsigned char* serialized_result)
{
    typedef union
    {
        float f;
        struct
        {
            uint_fast32_t mantissa : 23;
            uint_fast32_t exponent : 8 ;
            uint_fast32_t negative : 1 ;
        } ieee;
    } AsInt;
    const AsInt* serialized = (const AsInt*)serialized_result;
    AsInt original; original.f = original_value;

    TEST_ASSERT_EQUAL_HEX32_MESSAGE( original.ieee.mantissa, serialized->ieee.mantissa, "Mantissa did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE ( original.ieee.exponent, serialized->ieee.exponent, "Exponent did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE ( original.ieee.negative, serialized->ieee.negative, "Negative did not match.");
}

static void testNunavutSetF32(void)
{
    unsigned char buffer[] = {0x00, 0x00, 0x00, 0x00};
    nunavutSetF32(buffer, sizeof(buffer)*CHAR_BIT, 0, 3.14f);
    helperAssertSerFloat32SameAsIEEE(3.14f, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF32(buffer, sizeof(buffer)*CHAR_BIT, 0, -3.14f);
    helperAssertSerFloat32SameAsIEEE(-3.14f, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF32(buffer, sizeof(buffer)*CHAR_BIT, 0, -NAN32);
    helperAssertSerFloat32SameAsIEEE(-NAN32, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF32(buffer, sizeof(buffer)*CHAR_BIT, 0, NAN32);
    helperAssertSerFloat32SameAsIEEE(NAN32, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF32(buffer, sizeof(buffer)*CHAR_BIT, 0, INF32);
    helperAssertSerFloat32SameAsIEEE(INF32, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF32(buffer, sizeof(buffer)*CHAR_BIT, 0, -INF32);
    helperAssertSerFloat32SameAsIEEE(-INF32, buffer);
}

// +--------------------------------------------------------------------------+
// | testNunavutGetF32
// +--------------------------------------------------------------------------+

static void testNunavutGetF32(void)
{
    const uint_fast32_t neg_inf = 0xff800000;
    const uint_fast32_t inf     = 0x7f800000;
    const uint_fast32_t nan     = 0x7fc00000;
    const uint_fast32_t pi      = 0x4048f5c3;
    float result;

    // >>> hex(int.from_bytes(np.array([-np.float32('infinity')]).tobytes(), 'little'))
    // '0xff800000'
    result = nunavutGetF32(&neg_inf, sizeof(neg_inf)*CHAR_BIT, 0);
    TEST_ASSERT_FLOAT_IS_NEG_INF(result);

    // >>> hex(int.from_bytes(np.array([np.float32('infinity')]).tobytes(), 'little'))
    // '0x7f800000'
    result = nunavutGetF32(&inf, sizeof(inf)*CHAR_BIT, 0);
    TEST_ASSERT_FLOAT_IS_INF(result);

    // >>> hex(int.from_bytes(np.array([np.float32('nan')]).tobytes(), 'little'))
    // '0x7fc00000'
    result = nunavutGetF32(&nan, sizeof(nan)*CHAR_BIT, 0);
    TEST_ASSERT_FLOAT_IS_NAN(result);

    // >>> hex(int.from_bytes(np.array([np.float32('3.14')]).tobytes(), 'little'))
    // '0x4048f5c3'
    result = nunavutGetF32(&pi, sizeof(pi)*CHAR_BIT, 0);
    TEST_ASSERT_EQUAL_FLOAT(3.14f, result);
}

// +--------------------------------------------------------------------------+
// | testNunavutGetF64
// +--------------------------------------------------------------------------+

static void testNunavutGetF64(void)
{
    const uint64_t pi      = 0x400921fb54442d18;
    const uint64_t inf     = 0x7ff0000000000000;
    const uint64_t neg_inf = 0xfff0000000000000;
    const uint64_t nan     = 0x7ff8000000000000;
    double result;

    // >>> hex(int.from_bytes(np.array([np.float64('3.141592653589793')]).tobytes(), 'little'))
    // '0x400921fb54442d18'
    result = nunavutGetF64(&pi, sizeof(pi)*CHAR_BIT, 0);
    TEST_ASSERT_EQUAL_DOUBLE(3.141592653589793, result);

    // >>> hex(int.from_bytes(np.array([np.float64('infinity')]).tobytes(), 'little'))
    // '0x7ff0000000000000'
    result = nunavutGetF64(&inf, sizeof(inf)*CHAR_BIT, 0);
    TEST_ASSERT_DOUBLE_IS_INF(result);

    // >>> hex(int.from_bytes(np.array([-np.float64('infinity')]).tobytes(), 'little'))
    // '0xfff0000000000000'
    result = nunavutGetF64(&neg_inf, sizeof(neg_inf)*CHAR_BIT, 0);
    TEST_ASSERT_DOUBLE_IS_NEG_INF(result);

    // >>> hex(int.from_bytes(np.array([np.float64('nan')]).tobytes(), 'little'))
    // '0x7ff8000000000000'
    result = nunavutGetF64(&nan, sizeof(nan)*CHAR_BIT, 0);
    TEST_ASSERT_DOUBLE_IS_NAN(result);
}

// +--------------------------------------------------------------------------+
// | testNunavutSetF64
// +--------------------------------------------------------------------------+
//
// Compare the results of Nunavut serialization to the IEEE definition. These must match.
//
static void helperAssertSerFloat64SameAsIEEE(const double original_value, const void* serialized_result)
{
    typedef union
    {
        double f;
        struct
        {
            uint64_t mantissa : 52;
            uint64_t exponent : 11;
            uint64_t negative : 1 ;
        } ieee;
    } AsInt;
    const AsInt* serialized = (const AsInt*)serialized_result;
    AsInt original; original.f = original_value;

    TEST_ASSERT_EQUAL_HEX64_MESSAGE( original.ieee.mantissa, serialized->ieee.mantissa, "Mantissa did not match.");
    TEST_ASSERT_EQUAL_HEX16_MESSAGE( original.ieee.exponent, serialized->ieee.exponent, "Exponent did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE ( original.ieee.negative, serialized->ieee.negative, "Negative did not match.");
}

static void testNunavutSetF64(void)
{
    double x = 0;
    nunavutSetF64(&x, sizeof(x)*CHAR_BIT, 0, 3.141592653589793);
    helperAssertSerFloat64SameAsIEEE(3.141592653589793, &x);

    memset(&x, 0, sizeof(x));
    nunavutSetF64(&x, sizeof(x)*CHAR_BIT, 0, -3.141592653589793);
    helperAssertSerFloat64SameAsIEEE(-3.141592653589793, &x);

    memset(&x, 0, sizeof(x));
    nunavutSetF64(&x, sizeof(x)*CHAR_BIT, 0, -NAN64);
    helperAssertSerFloat64SameAsIEEE(-NAN64, &x);

    memset(&x, 0, sizeof(x));
    nunavutSetF64(&x, sizeof(x)*CHAR_BIT, 0, NAN64);
    helperAssertSerFloat64SameAsIEEE(NAN64, &x);

    memset(&x, 0, sizeof(x));
    nunavutSetF64(&x, sizeof(x)*CHAR_BIT, 0, INF64);
    helperAssertSerFloat64SameAsIEEE(INF64, &x);

    memset(&x, 0, sizeof(x));
    nunavutSetF64(&x, sizeof(x)*CHAR_BIT, 0, -INF64);
    helperAssertSerFloat64SameAsIEEE(-INF64, &x);
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
    RUN_TEST(testNunavutSaturateBufferFragmentBitLength);
    RUN_TEST(testNunavutGetBits);
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
    RUN_TEST(testNunavutFloat16Pack_infinity);
    RUN_TEST(testNunavutFloat16Pack_zero);
    RUN_TEST(testNunavutFloat16Unpack);
    RUN_TEST(testNunavutFloat16PackUnpack);
    RUN_TEST(testNunavutFloat16PackUnpack_NAN);
    RUN_TEST(testNunavutFloat16Unpack_INFINITY);
    RUN_TEST(testNunavutSetF16);
    RUN_TEST(testNunavutGetF16);
    RUN_TEST(testNunavutSetF32);
    RUN_TEST(testNunavutGetF32);
    RUN_TEST(testNunavutGetF64);
    RUN_TEST(testNunavutSetF64);
    return UNITY_END();
}
