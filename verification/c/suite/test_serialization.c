// Copyright (c) 2020 UAVCAN Development Team.
// This software is distributed under the terms of the MIT License.

#include <regulated/basics/Struct__0_1.h>
#include <regulated/basics/Union_0_1.h>
#include "unity.h"  // Include 3rd-party headers afterward to ensure that our headers are self-sufficient.

/// The reference array has been pedantically validated manually bit by bit (it did really took me about three hours).
/// The following Python script has been used to cross-check against PyUAVCAN, which has been cross-checked against
/// earlier v0 implementations beforehand:
///
///     import sys, pathlib, importlib, pyuavcan
///     sys.path.append(str(pathlib.Path.cwd()))
///     target, lookup = sys.argv[1], sys.argv[2:]
///     for lk in lookup:
///         pyuavcan.dsdl.generate_package(lk, lookup)
///     pyuavcan.dsdl.generate_package(target, lookup)
///     from regulated.basics import Struct__0_1, DelimitedFixedSize_0_1, DelimitedVariableSize_0_1, Union_0_1
///     s = Struct__0_1()
///     s.boolean = True
///     s.i10_4[0] = +0x5555                              # saturates to +511
///     s.i10_4[1] = -0x6666                              # saturates to -512
///     s.i10_4[2] = +0x0055                              # original value retained
///     s.i10_4[3] = -0x00AA                              # original value retained
///     s.f16_le2 = [
///         -65504.0,
///         +float('inf'),                                # negative infinity retained
///     ]
///     s.unaligned_bitpacked_3 = [1, 0, 1]
///     s.bytes_lt3 = [111, 222]
///     s.bytes_3[0] = -0x77
///     s.bytes_3[1] = -0x11
///     s.bytes_3[2] = +0x77
///     s.u2_le4 = [
///         0x02,                                         # retained
///         0x11,                                         # truncated => 1
///         0xFF,                                         # truncated => 3
///     ]
///     s.delimited_fix_le2 = [DelimitedFixedSize_0_1()]
///     s.u16_2[0] = 0x1234
///     s.u16_2[1] = 0x5678
///     s.aligned_bitpacked_3 = [1, 0, 0]
///     s.unaligned_bitpacked_lt3 = [1, 0]                # 0b01
///     s.delimited_var_2[0].f16 = +float('inf')
///     s.delimited_var_2[1].f64 = -1e40                  # retained
///     s.aligned_bitpacked_le3 = [1]
///     sr = b''.join(pyuavcan.dsdl.serialize(s))
///     print(len(sr), 'bytes')
///     print('\n'.join(f'0x{x:02X}U,' for x in sr))
static void testStructReference(void)
{
    regulated_basics_Struct__0_1 obj = {0};
    obj.boolean = true;
    obj.i10_4[0] = +0x5555;                             // saturates to +511
    obj.i10_4[1] = -0x6666;                             // saturates to -512
    obj.i10_4[2] = +0x0055;                             // original value retained
    obj.i10_4[3] = -0x00AA;                             // original value retained
    obj.f16_le2.elements[0] = -1e9F;                    // saturated to -65504
    obj.f16_le2.elements[1] = +INFINITY;                // negative infinity retained
    obj.f16_le2.count = 2;
    obj.unaligned_bitpacked_3_bitpacked_[0] = 0xF5;     // 0b101, rest truncated away and ignored
    obj.sealed._dummy_ = 123;                           // ignored
    obj.bytes_lt3.elements[0] = 111;
    obj.bytes_lt3.elements[1] = 222;
    obj.bytes_lt3.count = 2;
    obj.bytes_3[0] = -0x77;
    obj.bytes_3[1] = -0x11;
    obj.bytes_3[2] = +0x77;
    obj.u2_le4.elements[0] = 0x02;                      // retained
    obj.u2_le4.elements[1] = 0x11;                      // truncated => 1
    obj.u2_le4.elements[2] = 0xFF;                      // truncated => 3
    obj.u2_le4.elements[3] = 0xFF;                      // ignored because the length is 3
    obj.u2_le4.count = 3;
    obj.delimited_fix_le2.elements[0]._dummy_ = 111;    // ignored
    obj.delimited_fix_le2.count = 1;
    obj.u16_2[0] = 0x1234;
    obj.u16_2[1] = 0x5678;
    obj.aligned_bitpacked_3_bitpacked_[0] = 0xF1U;
    obj.unaligned_bitpacked_lt3.bitpacked[0] = 0xF1U;
    obj.unaligned_bitpacked_lt3.count = 2;              // 0b01, rest truncated
    regulated_basics_DelimitedVariableSize_0_1_select_f16_(&obj.delimited_var_2[0]);
    obj.delimited_var_2[0].f16 = +1e9F;                 // truncated to infinity
    regulated_basics_DelimitedVariableSize_0_1_select_f64_(&obj.delimited_var_2[1]);
    obj.delimited_var_2[1].f64 = -1e40;                 // retained
    obj.aligned_bitpacked_le3.bitpacked[0] = 0xFF;
    obj.aligned_bitpacked_le3.count = 1;                // only lsb is set, other truncated

    const uint8_t reference[] = {
        0xFEU,  // void1, true, 6 lsb of int10 = 511
        0x07U,  // 4 msb of int10 = 511, 4 lsb of -512 = 0b_10_0000_0000
        0x60U,  // 6 msb of -512 (0x60 = 0b_0110_0000), 2 lsb of 0x0055 = 0b0001010101
        0x15U,  // 8 msb of 0b_00_0101_0101,                       0x15 = 0b00010101
        0x56U,  // ALIGNED; -0x00AA in two's complement is 0x356 = 0b_11_01010110
        0x0BU,  // 2 msb of the above (0b11) followed by 8 bit of length prefix (2) of float16[<=2] f16_le2
        0xFCU,  // 2 msb of the length prefix followed by 6 lsb of (float16.min = 0xfbff = 0b_11111011_11111111)
        0xEFU,  // 0b_xx_111011_11xxxxxx (continuation of the float16)
        0x03U,  // 2 msb of the above (0b11) and the next float16 = +inf, represented 0x7C00 = 0b_01111100_00000000
        0xF0U,  // 0b_xx111100_00xxxxxx (continuation of the infinity)
        0x15U,  // 2 msb of the above (0b01) followed by bool[3] unaligned_bitpacked_3 = [1, 0, 1], then PADDING
        0x02U,  // ALIGNED; empty struct not manifested, here we have length = 2 of uint8[<3] bytes_lt3
        0x6FU,  // bytes_lt3[0] = 111
        0xDEU,  // bytes_lt3[1] = 222
        0x89U,  // bytes_3[0] = -0x77 (two's complement)
        0xEFU,  // bytes_3[1] = -0x11 (two's complement)
        0x77U,  // bytes_3[2] = +0x77
        0x03U,  // length = 3 of truncated uint2[<=4] u2_le4
        0x36U,  // 0b_00_11_01_10: u2_le4[0] = 0b10, u2_le4[1] = 0b01, u2_le4[2] = 0b11, then dynamic padding
        0x01U,  // ALIGNED; length = 1 of DelimitedFixedSize.0.1[<=2] delimited_fix_le2
        0x00U,  // Constant DH of DelimitedFixedSize.0.1
        0x00U,  // ditto
        0x00U,  // ditto
        0x00U,  // ditto
        0x34U,  // uint16[2] u16_2; first element = 0x1234
        0x12U,  // continuation
        0x78U,  // second element = 0x5678
        0x56U,  // continuation
        0x11U,  // bool[3] aligned_bitpacked_3 = [1, 0, 0]; then 5 lsb of length = 2 of bool[<3] unaligned_bitpacked_lt3
        0x08U,  // 3 msb of length = 2 (i.e., zeros), then values [1, 0], then 1 bit of padding before composite
        0x03U,  // DH = 3 of the first element of DelimitedVariableSize.0.1[2] delimited_var_2
        0x00U,  // ditto
        0x00U,  // ditto
        0x00U,  // ditto
        0x00U,  // union tag = 0, f16 selected
        0x00U,  // f16 truncated to positive infinity; see representation above
        0x7CU,  // ditto
        0x09U,  // DH = (8 + 1) of the second element of DelimitedVariableSize.0.1[2] delimited_var_2
        0x00U,  // ditto
        0x00U,  // ditto
        0x00U,  // ditto
        0x02U,  // union tag = 2, f64 selected (notice that union tags are always aligned by design)
        0xA5U,  // float64 = -1e40 is 0xc83d6329f1c35ca5, this is the LSB
        0x5CU,  // ditto
        0xC3U,  // ditto
        0xF1U,  // ditto
        0x29U,  // ditto
        0x63U,  // ditto
        0x3DU,  // ditto
        0xC8U,  // ditto
        0x01U,  // length = 1 of bool[<=3] aligned_bitpacked_le3
        0x01U,  // the one single bit of the above, then 7 bits of dynamic padding to byte
        // END OF SERIALIZED REPRESENTATION
        0x55U,  // canary  1
        0x55U,  // canary  2
        0x55U,  // canary  3
        0x55U,  // canary  4
        0x55U,  // canary  5
        0x55U,  // canary  6
        0x55U,  // canary  7
        0x55U,  // canary  8
        0x55U,  // canary  9
        0x55U,  // canary 10
        0x55U,  // canary 11
        0x55U,  // canary 12
        0x55U,  // canary 13
        0x55U,  // canary 14
        0x55U,  // canary 15
        0x55U,  // canary 16
    };

    uint8_t buf[sizeof(reference)];
    (void) memset(&buf[0], 0x55U, sizeof(buf));  // fill out canaries

    size_t size = sizeof(buf);
    TEST_ASSERT_EQUAL(0, regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], &size));
    TEST_ASSERT_EQUAL(sizeof(reference) - 16U, size);

    TEST_ASSERT_EQUAL_HEX8_ARRAY(reference, buf, sizeof(reference));
}

static void testStructErrors(void)
{
    regulated_basics_Struct__0_1 obj = {0};
    // Default state -- all zeros except delimiter headers of the nested delimited objects:
    const uint8_t reference[] = {
        0x00U,  // void1, boolean, i10_4[0]
        0x00U,  // i10_4[]
        0x00U,  // i10_4[]
        0x00U,  // i10_4[]
        0x00U,  // i10_4[]
        0x00U,  // i10_4[] f16_le2[]
        0x00U,  // f16_le2[] unaligned_bitpacked_3[]
        0x00U,  // bytes_lt3[]
        0x00U,  // bytes_3[0]
        0x00U,  // bytes_3[1]
        0x00U,  // bytes_3[2]
        0x00U,  // u2_le4[]
        0x00U,  // delimited_fix_le2[]
        0x00U,  // u16_2[0]
        0x00U,  // u16_2[0]
        0x00U,  // u16_2[1]
        0x00U,  // u16_2[1]
        0x00U,  // aligned_bitpacked_3[] unaligned_bitpacked_lt3[]
        0x00U,  // unaligned_bitpacked_lt3[], padding
        0x03U,  // delimited_var_2[0] delimiter header                  <--- nonzero
        0x00U,  // delimited_var_2[0] delimiter header
        0x00U,  // delimited_var_2[0] delimiter header
        0x00U,  // delimited_var_2[0] delimiter header
        0x00U,  // delimited_var_2[0] union tag
        0x00U,  // delimited_var_2[0] f16
        0x00U,  // delimited_var_2[0] f16
        0x03U,  // delimited_var_2[1] delimiter header                  <--- nonzero
        0x00U,  // delimited_var_2[1] delimiter header
        0x00U,  // delimited_var_2[1] delimiter header
        0x00U,  // delimited_var_2[1] delimiter header
        0x00U,  // delimited_var_2[1] union tag
        0x00U,  // delimited_var_2[1] f16
        0x00U,  // delimited_var_2[1] f16
        0x00U,  // aligned_bitpacked_le3[], padding
        // END OF SERIALIZED REPRESENTATION
        0xAAU,  // canary  1
        0xAAU,  // canary  2
        0xAAU,  // canary  3
        0xAAU,  // canary  4
        0xAAU,  // canary  5
        0xAAU,  // canary  6
        0xAAU,  // canary  7
        0xAAU,  // canary  8
        0xAAU,  // canary  9
        0xAAU,  // canary 10
        0xAAU,  // canary 11
        0xAAU,  // canary 12
        0xAAU,  // canary 13
        0xAAU,  // canary 14
        0xAAU,  // canary 15
        0xAAU,  // canary 16
    };

    uint8_t buf[regulated_basics_Struct__0_1_SERIALIZATION_BUFFER_SIZE_BYTES_];  // Min size buffer
    (void) memset(&buf[0], 0xAAU, sizeof(buf));  // Fill out the canaries

    // Happy path, validate the test rig
    size_t size = regulated_basics_Struct__0_1_SERIALIZATION_BUFFER_SIZE_BYTES_;
    TEST_ASSERT_EQUAL(0, regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], &size));
    TEST_ASSERT_EQUAL(sizeof(reference) - 16U, size);
    TEST_ASSERT_EQUAL_HEX8_ARRAY(reference, buf, sizeof(reference));

    // Buffer too small
    size = regulated_basics_Struct__0_1_SERIALIZATION_BUFFER_SIZE_BYTES_ - 1;
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_SERIALIZATION_BUFFER_TOO_SMALL,
                      regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], &size));
    size = 0;
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_SERIALIZATION_BUFFER_TOO_SMALL,
                      regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], &size));

    // Null pointers at the input
    size = regulated_basics_Struct__0_1_SERIALIZATION_BUFFER_SIZE_BYTES_;
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_INVALID_ARGUMENT,
                      regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], NULL));
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_INVALID_ARGUMENT,
                      regulated_basics_Struct__0_1_serialize_(&obj, NULL, &size));
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_INVALID_ARGUMENT,
                      regulated_basics_Struct__0_1_serialize_(NULL, &buf[0], &size));

    // Bad array length
    size = regulated_basics_Struct__0_1_SERIALIZATION_BUFFER_SIZE_BYTES_;
    obj.delimited_fix_le2.count = 123;
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_REPRESENTATION_BAD_ARRAY_LENGTH,
                      regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], &size));
    obj.delimited_fix_le2.count = 0;

    // Bad union tag
    obj.delimited_var_2[0]._tag_ = 42;
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_REPRESENTATION_BAD_UNION_TAG,
                      regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], &size));
    obj.delimited_var_2[0]._tag_ = 0;

    // Bad delimiter header error cannot occur during serialization so this state is not explored.
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

    RUN_TEST(testStructReference);
    RUN_TEST(testStructErrors);

    return UNITY_END();
}
