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
// | nunavutFloat16Pack/Unpack
// +--------------------------------------------------------------------------+

/**
 * Ensure the methods are symmetrical.
 */
static void testNunavutFloat16PackUnpack(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 3.14f, nunavutFloat16Unpack(nunavutFloat16Pack(3.14f)));
}

// +--------------------------------------------------------------------------+
// | nunavutFloat16Pack
// +--------------------------------------------------------------------------+

/**
 * This method adapted from work by James Tursa published on mathworks.com
 * (https://www.mathworks.com/matlabcentral/fileexchange/23173-ieee-754r-half-precision-floating-point-converter)
 * under a BSD license.
 *
 * Copyright:   (c) 2009, 2020 by James Tursa, All Rights Reserved
 *
 *  This code uses the BSD License:
 *
 *  Redistribution and use in source and binary forms, with or without 
 *  modification, are permitted provided that the following conditions are 
 *  met:
 *
 *     * Redistributions of source code must retain the above copyright 
 *       notice, this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above copyright 
 *       notice, this list of conditions and the following disclaimer in 
 *       the documentation and/or other materials provided with the distribution
 *      
 *  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
 *  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
 *  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
 *  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE 
 *  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
 *  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
 *  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
 *  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
 *  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
 *  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
 *  POSSIBILITY OF SUCH DAMAGE.
 * 
 * We use this as an independent implementation to verify our own float16 serialization logic.
 * Note that in adapting James' work we hard-coded the rounding mode to be TONEAREST.
 */
static void single2halfp(const float source, uint16_t* hp)
{
    // Convert to uint32 without conversion (type punning).
    uint32_t x = *((uint32_t*)&source);
    uint16_t hs, he, hm, hr;
    uint32_t xs, xe, xm, xt, zm, zt, z1;
    int hes, N;
    
    if( hp == NULL ) // Nothing to convert (e.g., imag part of pure real)
    {
        return;
    }
    
    if( (x & 0x7FFFFFFFu) == 0 ) // Signed zero
    {
        *hp = (uint16_t) (x >> 16);  // Return the signed zero
    }
    else // Not zero
    {
        xs = x & 0x80000000u;  // Pick off sign bit
        xe = x & 0x7F800000u;  // Pick off exponent bits
        xm = x & 0x007FFFFFu;  // Pick off mantissa bits
        xt = x & 0x00001FFFu;  // Pick off trailing 13 mantissa bits beyond the shift (used for rounding normalized determination)
        if( xe == 0 ) // Denormal will underflow, return a signed zero or smallest denormal depending on rounding_mode
        {
            *hp = (uint16_t) (xs >> 16);  // Signed zero
        }
        else if( xe == 0x7F800000u ) // Inf or NaN (all the exponent bits are set)
        {
            if( xm == 0 ) // If mantissa is zero ...
            {
                *hp = (uint16_t) ((xs >> 16) | 0x7C00u); // Signed Inf
            }
            else
            {
                hm = (uint16_t) (xm >> 13); // Shift mantissa over
                if( hm ) // If we still have some non-zero bits (payload) after the shift ...
                {
                    *hp = (uint16_t) ((xs >> 16) | 0x7C00u | 0x200u | hm); // Signed NaN, shifted mantissa bits set
                    printf("HERE0 %d %d\n", hm, *hp);
                }
                else
                {
                    *hp = (uint16_t) ((xs >> 16) | 0x7E00u); // Signed NaN, only 1st mantissa bit set (quiet)
                }
            }
        } 
        else // Normalized number
        {
            hs = (uint16_t) (xs >> 16); // Sign bit
            hes = ((int)(xe >> 23)) - 127 + 15; // Exponent unbias the single, then bias the halfp
            if( hes >= 0x1F ) // Overflow
            {
                *hp = (uint16_t) ((xs >> 16) | 0x7C00u); // Signed Inf
            }
            else if( hes <= 0 ) // Underflow exponent, so halfp will be denormal
            {
                xm |= 0x00800000u;  // Add the hidden leading bit
                N = (14 - hes);  // Number of bits to shift mantissa to get it into halfp word
                hm = (N < 32) ? (uint16_t) (xm >> N) : (uint16_t) 0u; // Halfp mantissa
                hr = (uint16_t) 0u; // Rounding bit, default to 0 for now (this will catch FE_TOWARDZERO and other cases)
                if( N <= 24 ) // Mantissa bits have not shifted away from the end
                { 
                    zm = (0x00FFFFFFu >> N) << N;  // Halfp denormal mantissa bit mask
                    zt = 0x00FFFFFFu & ~zm;  // Halfp denormal trailing mantissa bits mask
                    z1 = (zt >> (N-1)) << (N-1);  // First bit of trailing bit mask
                    xt = xm & zt;  // Trailing mantissa bits
                    if( xt > z1 || xt == ( z1 && (hm & 1u) ) ) // Trailing bits are more than tie, or tie and mantissa is currently odd
                    {
                        hr = (uint16_t) 1u; // Rounding bit set to 1
                    }
                } // else Mantissa bits have shifted at least one bit beyond the end (ties not possible)
                *hp = (uint16_t)((hs | hm) + hr); // Combine sign bit and mantissa bits and rounding bit, biased exponent is zero
            }
            else
            {
                he = (uint16_t) (hes << 10); // Exponent
                hm = (uint16_t) (xm >> 13); // Mantissa
                hr = (uint16_t) 0u; // Rounding bit, default to 0 for now
                if( xt > 0x00001000u || xt == ( 0x00001000u && (hm & 1u) ) ) // Trailing bits are more than tie, or tie and mantissa is currently odd
                {
                    hr = (uint16_t) 1u; // Rounding bit set to 1
                }
                *hp = (uint16_t)((hs | he | hm) + hr);  // Adding rounding bit might overflow into exp bits, but that is OK
            }
        }
    }
}


static void helperAssertSerFloat16SameAsIEEE(const float original_value, const uint16_t serialized_result)
{
    uint16_t expected_value;
    
    single2halfp(original_value, &expected_value);

    TEST_ASSERT_EQUAL_HEX8_MESSAGE(expected_value & 0x3FF, serialized_result & 0x3FF, "Mantessa did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE((expected_value >> 10U) & 0x1F, (serialized_result >> 10U) & 0x1F, "Exponents did not match.");
    TEST_ASSERT_EQUAL_HEX8_MESSAGE((expected_value >> 15U) & 0x1, (serialized_result >> 15U) & 0x1, "Sign-bit did not match.");
}


static void testNunavutFloat16Pack(void)
{
    uint16_t packed_float = nunavutFloat16Pack(3.14f);
    helperAssertSerFloat16SameAsIEEE(3.14f, packed_float);

    packed_float = nunavutFloat16Pack(-3.14f);
    helperAssertSerFloat16SameAsIEEE(-3.14f, packed_float);

    packed_float = nunavutFloat16Pack(3.141592653589793238462643383279f);
    helperAssertSerFloat16SameAsIEEE(3.141592653589793238462643383279f, packed_float);

    packed_float = nunavutFloat16Pack(-3.141592653589793238462643383279f);
    helperAssertSerFloat16SameAsIEEE(-3.141592653589793238462643383279f, packed_float);

    // packed_float = nunavutFloat16Pack(NAN);
    // helperAssertSerFloat16SameAsIEEE(NAN, packed_float);

    // packed_float = nunavutFloat16Pack(-NAN);
    // helperAssertSerFloat16SameAsIEEE(-NAN, packed_float);
}

// +--------------------------------------------------------------------------+
// | testNunavutSet32
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

static void testNunavutSet32(void)
{
    uint8_t buffer[] = {0x00, 0x00, 0x00, 0x00};
    nunavutSetF32(buffer, 0, 3.14f);
    helperAssertSerFloat32SameAsIEEE(3.14f, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF32(buffer, 0, -3.14f);
    helperAssertSerFloat32SameAsIEEE(-3.14f, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF32(buffer, 0, -NAN);
    helperAssertSerFloat32SameAsIEEE(-NAN, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavutSetF32(buffer, 0, NAN);
    helperAssertSerFloat32SameAsIEEE(NAN, buffer);
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
    RUN_TEST(testNunavutFloat16PackUnpack);
    RUN_TEST(testNunavutFloat16Pack);
    RUN_TEST(testNunavutSet32);

    return UNITY_END();
}
