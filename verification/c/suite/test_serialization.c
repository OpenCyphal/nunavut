// Copyright (c) 2020 OpenCyphal Development Team.
// This software is distributed under the terms of the MIT License.

#ifndef NUNAVUT_ASSERT
  #include <assert.h>
  #define NUNAVUT_ASSERT assert
#endif
#ifdef __ADSPTS__
  #define INFINITY 0
  #define isfinite(x) 1
  #define static_assert(cond,msg)
  //#define static_assert(cond,msg) typedef int static_assert_foo_t[(cond) ? 1 : -1]
  /*
  #define ASSERT_CONCAT_(a,b) a##b
  #define ASSERT_CONCAT(a,b) ASSERT_CONCAT_(a,b)
  #ifdef __COUNTER__
    #define static_assert(e,m) enum { ASSERT_CONCAT(static_assert_,__COUNTER__) = 1/(!!(e)) }
  #else
    #define static_assert(e,m) enum { ASSERT_CONCAT(assert_line_,__LINE__) = 1/(!!(e)) }
  #endif
  */  
#endif


#include "regulated/basics/Struct__0_1.h"
#include <regulated/basics/Union_0_1.h>
#include <regulated/basics/Primitive_0_1.h>
#include <regulated/basics/PrimitiveArrayFixed_0_1.h>
#include <regulated/basics/PrimitiveArrayVariable_0_1.h>
#include <regulated/delimited/A_1_0.h>
#include <regulated/delimited/A_1_1.h>
#include <uavcan/pnp/NodeIDAllocationData_2_0.h>
#include "unity.h"  // Include 3rd-party headers afterward to ensure that our headers are self-sufficient.
#include <stdlib.h>
#include <time.h>

/// The reference array has been pedantically validated manually bit by bit (it did really took me about three hours).
/// The following Python script has been used to cross-check against Pycyphal, which has been cross-checked against
/// earlier v0 implementations beforehand:
///
///     import sys, pathlib, importlib, pycyphal
///     sys.path.append(str(pathlib.Path.cwd()))
///     target, lookup = sys.argv[1], sys.argv[2:]
///     for lk in lookup:
///         pycyphal.dsdl.generate_package(lk, lookup)
///     pycyphal.dsdl.generate_package(target, lookup)
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
///     sr = b''.join(pycyphal.dsdl.serialize(s))
///     print(len(sr), 'bytes')
///     print('\n'.join(f'0x{x:02X}U,' for x in sr))
static void testStructReference(void)
{
    regulated_basics_Struct__0_1 obj = {0};

    // Initialize a reference object, serialize, and compare against the reference serialized representation.
    obj.boolean = true;
    obj.i10_4[0] = +0x5555;                             // saturates to +511
    obj.i10_4[1] = -0x6666;                             // saturates to -512
    obj.i10_4[2] = +0x0055;                             // original value retained
    obj.i10_4[3] = -0x00AA;                             // original value retained
    obj.f16_le2.elements[0] = -1e9F;                    // saturated to -65504
    obj.f16_le2.elements[1] = +INFINITY;                // infinity retained
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

    const unsigned char reference[] = {
    #if CHAR_BIT == 8
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
        0x55U   // canary 16
    #elif CHAR_BIT == 16
        0x07FEU, // The above 8bit elements packed to 16bit words
        0x1560U,
        0x0B56U,
        0xEFFCU,
        0xF003U,
        0x0215U,
        0xDE6FU,
        0xEF89U,
        0x0377U,
        0x0136U,
        0x0000U,
        0x0000U,
        0x1234U,
        0x5678U,
        0x0811U,
        0x0003U,
        0x0000U,
        0x0000U,
        0x097CU,
        0x0000U,
        0x0200U,
        0x5CA5U,
        0xF1C3U,
        0x6329U,
        0xC83DU,
        0x0101U,
        // END OF SERIALIZED REPRESENTATION
        0x5555U,
        0x5555U,
        0x5555U,
        0x5555U,
        0x5555U,
        0x5555U,
        0x5555U,
        0x5555U
    #elif CHAR_BIT == 32
        0x156007FEU, // The above 8bit elements packed to 32bit words
        0xEFFC0B56U,
        0x0215F003U,
        0xEF89DE6FU,
        0x01360377U,
        0x00000000U,
        0x56781234U,
        0x00000003U,
        0x097C0000U,
        0x02000000U,
        0xF1C35CA5U,
        0xC83D6329U,
        0x55550101U,
        // END OF SERIALIZED REPRESENTATION
        0x55555555U,
        0x55555555U,
        0x55555555U
    #endif
    };
    const unsigned char Ox55 = (unsigned char)
    #if CHAR_BIT == 8
        0x55U;
    #elif CHAR_BIT == 16
        0x5555U;
    #elif CHAR_BIT == 32
        0x55555555U;
    #endif

    unsigned char buf[sizeof(reference)];
    (void) memset(&buf[0], Ox55, sizeof(buf));  // fill out canaries

    const size_t buf_size_chars = sizeof(buf);
    const size_t buf_size_bits  = buf_size_chars * CHAR_BIT;
    size_t ini_ofs = 0;
    TEST_ASSERT_EQUAL(0, regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], buf_size_bits, &ini_ofs));
    TEST_ASSERT_EQUAL((sizeof(reference) - 16U)*CHAR_BIT, ini_ofs);
    TEST_ASSERT_EQUAL_HEX8_ARRAY(reference, buf, sizeof(reference));

    // Check union manipulation functions.
    TEST_ASSERT_TRUE(regulated_basics_DelimitedVariableSize_0_1_is_f16_(&obj.delimited_var_2[0]));
    TEST_ASSERT_FALSE(regulated_basics_DelimitedVariableSize_0_1_is_f32_(&obj.delimited_var_2[0]));
    TEST_ASSERT_FALSE(regulated_basics_DelimitedVariableSize_0_1_is_f64_(&obj.delimited_var_2[0]));
    TEST_ASSERT_FALSE(regulated_basics_DelimitedVariableSize_0_1_is_f64_(NULL));
    regulated_basics_DelimitedVariableSize_0_1_select_f32_(NULL);        // No action; same state retained.
    TEST_ASSERT_TRUE(regulated_basics_DelimitedVariableSize_0_1_is_f16_(&obj.delimited_var_2[0]));
    TEST_ASSERT_FALSE(regulated_basics_DelimitedVariableSize_0_1_is_f32_(&obj.delimited_var_2[0]));
    TEST_ASSERT_FALSE(regulated_basics_DelimitedVariableSize_0_1_is_f64_(&obj.delimited_var_2[0]));
    TEST_ASSERT_FALSE(regulated_basics_DelimitedVariableSize_0_1_is_f64_(NULL));

    // Test default initialization.
    (void) memset(&obj, Ox55, sizeof(obj));             // Fill using a non-zero pattern.
    regulated_basics_Struct__0_1_initialize_(&obj);
    TEST_ASSERT_EQUAL(false, obj.boolean);
    TEST_ASSERT_EQUAL(0, obj.i10_4[0]);
    TEST_ASSERT_EQUAL(0, obj.i10_4[1]);
    TEST_ASSERT_EQUAL(0, obj.i10_4[2]);
    TEST_ASSERT_EQUAL(0, obj.i10_4[3]);
    TEST_ASSERT_EQUAL(0, obj.f16_le2.count);
    TEST_ASSERT_EQUAL(0, obj.unaligned_bitpacked_3_bitpacked_[0]);
    TEST_ASSERT_EQUAL(0, obj.bytes_lt3.count);
    TEST_ASSERT_EQUAL(0, obj.bytes_3[0]);
    TEST_ASSERT_EQUAL(0, obj.bytes_3[1]);
    TEST_ASSERT_EQUAL(0, obj.bytes_3[2]);
    TEST_ASSERT_EQUAL(0, obj.u2_le4.count);
    TEST_ASSERT_EQUAL(0, obj.delimited_fix_le2.count);
    TEST_ASSERT_EQUAL(0, obj.u16_2[0]);
    TEST_ASSERT_EQUAL(0, obj.u16_2[1]);
    TEST_ASSERT_EQUAL(0, obj.aligned_bitpacked_3_bitpacked_[0]);
    TEST_ASSERT_EQUAL(0, obj.unaligned_bitpacked_lt3.count);
    TEST_ASSERT_EQUAL(0, obj.delimited_var_2[0]._tag_);
    TEST_ASSERT_FLOAT_WITHIN(1e-9, 0, obj.delimited_var_2[0].f16);
    TEST_ASSERT_EQUAL(0, obj.delimited_var_2[1]._tag_);
    TEST_ASSERT_FLOAT_WITHIN(1e-9, 0, obj.delimited_var_2[1].f16);
    TEST_ASSERT_EQUAL(0, obj.aligned_bitpacked_le3.count);

    // Deserialize the above reference representation and compare the result against the original object.
    ini_ofs = 0;
    TEST_ASSERT_EQUAL(0, regulated_basics_Struct__0_1_deserialize_(&obj, &reference[0], buf_size_bits, &ini_ofs));
    TEST_ASSERT_EQUAL((sizeof(reference)*CHAR_BIT - 16U*8U), ini_ofs);     // 16 trailing bytes implicitly truncated away

    TEST_ASSERT_EQUAL(true, obj.boolean);
    TEST_ASSERT_EQUAL(+511, obj.i10_4[0]);                              // saturated
    TEST_ASSERT_EQUAL(-512, obj.i10_4[1]);                              // saturated
    TEST_ASSERT_EQUAL(+0x55, obj.i10_4[2]);
    TEST_ASSERT_EQUAL(-0xAA, obj.i10_4[3]);
    TEST_ASSERT_FLOAT_WITHIN(1e-3, -65504.0, obj.f16_le2.elements[0]);
    TEST_ASSERT_FLOAT_IS_INF(obj.f16_le2.elements[1]);
    TEST_ASSERT_EQUAL(2, obj.f16_le2.count);
    TEST_ASSERT_EQUAL(5, obj.unaligned_bitpacked_3_bitpacked_[0]);      // unused MSB are zero-padded
    TEST_ASSERT_EQUAL(111, obj.bytes_lt3.elements[0]);
    TEST_ASSERT_EQUAL(222, obj.bytes_lt3.elements[1]);
    TEST_ASSERT_EQUAL(2, obj.bytes_lt3.count);
    TEST_ASSERT_EQUAL(-0x77, obj.bytes_3[0]);
    TEST_ASSERT_EQUAL(-0x11, obj.bytes_3[1]);
    TEST_ASSERT_EQUAL(+0x77, obj.bytes_3[2]);
    TEST_ASSERT_EQUAL(2, obj.u2_le4.elements[0]);
    TEST_ASSERT_EQUAL(1, obj.u2_le4.elements[1]);
    TEST_ASSERT_EQUAL(3, obj.u2_le4.elements[2]);
    TEST_ASSERT_EQUAL(3, obj.u2_le4.count);
    TEST_ASSERT_EQUAL(1, obj.delimited_fix_le2.count);
    TEST_ASSERT_EQUAL(0x1234, obj.u16_2[0]);
    TEST_ASSERT_EQUAL(0x5678, obj.u16_2[1]);
    TEST_ASSERT_EQUAL(1, obj.aligned_bitpacked_3_bitpacked_[0]);        // unused MSB are zero-padded
    TEST_ASSERT_EQUAL(1, obj.unaligned_bitpacked_lt3.bitpacked[0]);     // unused MSB are zero-padded
    TEST_ASSERT_EQUAL(2, obj.unaligned_bitpacked_lt3.count);
    TEST_ASSERT_EQUAL(0, obj.delimited_var_2[0]._tag_);
    TEST_ASSERT_FLOAT_IS_INF(obj.delimited_var_2[0].f16);
    TEST_ASSERT_EQUAL(2, obj.delimited_var_2[1]._tag_);
    TEST_ASSERT_DOUBLE_WITHIN(0.5, -1e+40, obj.delimited_var_2[1].f64);
    TEST_ASSERT_EQUAL(1, obj.aligned_bitpacked_le3.bitpacked[0]);       // unused MSB are zero-padded
    TEST_ASSERT_EQUAL(1, obj.aligned_bitpacked_le3.count);

    // Repeat the above, but apply implicit zero extension somewhere in the middle.
    ini_ofs = 0;
    TEST_ASSERT_EQUAL(0, regulated_basics_Struct__0_1_deserialize_(&obj, &reference[0], 25U*8U, &ini_ofs));
    TEST_ASSERT_EQUAL(25U*8U, ini_ofs);   // the returned size shall not exceed the buffer size

    TEST_ASSERT_EQUAL(true, obj.boolean);
    TEST_ASSERT_EQUAL(+511, obj.i10_4[0]);                              // saturated
    TEST_ASSERT_EQUAL(-512, obj.i10_4[1]);                              // saturated
    TEST_ASSERT_EQUAL(+0x55, obj.i10_4[2]);
    TEST_ASSERT_EQUAL(-0xAA, obj.i10_4[3]);
    TEST_ASSERT_FLOAT_WITHIN(1e-3, -65504.0, obj.f16_le2.elements[0]);
    TEST_ASSERT_FLOAT_IS_INF(obj.f16_le2.elements[1]);
    TEST_ASSERT_EQUAL(2, obj.f16_le2.count);
    TEST_ASSERT_EQUAL(5, obj.unaligned_bitpacked_3_bitpacked_[0]);      // unused MSB are zero-padded
    TEST_ASSERT_EQUAL(111, obj.bytes_lt3.elements[0]);
    TEST_ASSERT_EQUAL(222, obj.bytes_lt3.elements[1]);
    TEST_ASSERT_EQUAL(2, obj.bytes_lt3.count);
    TEST_ASSERT_EQUAL(-0x77, obj.bytes_3[0]);
    TEST_ASSERT_EQUAL(-0x11, obj.bytes_3[1]);
    TEST_ASSERT_EQUAL(+0x77, obj.bytes_3[2]);
    TEST_ASSERT_EQUAL(2, obj.u2_le4.elements[0]);
    TEST_ASSERT_EQUAL(1, obj.u2_le4.elements[1]);
    TEST_ASSERT_EQUAL(3, obj.u2_le4.elements[2]);
    TEST_ASSERT_EQUAL(3, obj.u2_le4.count);
    TEST_ASSERT_EQUAL(1, obj.delimited_fix_le2.count);
    TEST_ASSERT_EQUAL(0x0034, obj.u16_2[0]);                            // <-- IMPLICIT ZERO EXTENSION STARTS HERE
    TEST_ASSERT_EQUAL(0x0000, obj.u16_2[1]);                            // IT'S
    TEST_ASSERT_EQUAL(0, obj.aligned_bitpacked_3_bitpacked_[0]);        //      ZEROS
    TEST_ASSERT_EQUAL(0, obj.unaligned_bitpacked_lt3.count);            //          ALL
    TEST_ASSERT_EQUAL(0, obj.delimited_var_2[0]._tag_);                 //              THE
    TEST_ASSERT_FLOAT_WITHIN(1e-9, 0, obj.delimited_var_2[0].f16);      //                  WAY
    TEST_ASSERT_EQUAL(0, obj.delimited_var_2[1]._tag_);                 //                      DOWN
    TEST_ASSERT_FLOAT_WITHIN(1e-9, 0, obj.delimited_var_2[1].f16);
    TEST_ASSERT_EQUAL(0, obj.aligned_bitpacked_le3.count);
}

/// The test is based on https://forum.opencyphal.org/t/delimited-serialization-example/975
static void testStructDelimited(void)
{
    regulated_delimited_A_1_0 obj;
    regulated_delimited_A_1_0_initialize_(&obj);
    regulated_delimited_A_1_0_select_del_(&obj);
    regulated_delimited_A_1_0_select_del_(NULL);  // No action.
    obj.del.var.count = 2;
    obj.del.var.elements[0].a.count = 2;
    obj.del.var.elements[0].a.elements[0] = 1;
    obj.del.var.elements[0].a.elements[1] = 2;
    obj.del.var.elements[0].b = 0;
    obj.del.var.elements[1].a.count = 1;
    obj.del.var.elements[1].a.elements[0] = 3;
    obj.del.var.elements[1].a.elements[1] = 123;  // ignored
    obj.del.var.elements[1].b = 4;
    obj.del.fix.count = 1;
    obj.del.fix.elements[0].a[0] = 5;
    obj.del.fix.elements[0].a[1] = 6;

    const unsigned char reference[] = {
        // 0    1      2      3      4      5      6      7      8      9     10     11     12     13     14     15
        0x01U, 0x17U, 0x00U, 0x00U, 0x00U, 0x02U, 0x04U, 0x00U, 0x00U, 0x00U, 0x02U, 0x01U, 0x02U, 0x00U, 0x03U, 0x00U,
        0x00U, 0x00U, 0x01U, 0x03U, 0x04U, 0x01U, 0x02U, 0x00U, 0x00U, 0x00U, 0x05U, 0x06U,
        // END OF SERIALIZED REPRESENTATION
        0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU,
        0xAAU,
    };
    static_assert(sizeof(reference) == regulated_delimited_A_1_0_SERIALIZATION_BUFFER_SIZE_BYTES_, "");

    unsigned char buf[1024] = {0};
    (void) memset(&buf[0], 0xAAU, sizeof(buf));  // Fill out the canaries
    size_t buf_size_chars = sizeof(buf);
    size_t buf_size_bits  = buf_size_chars * CHAR_BIT;
    size_t ini_ofs = 0;
    TEST_ASSERT_EQUAL(0, regulated_delimited_A_1_0_serialize_(&obj, &buf[0], buf_size_bits, &ini_ofs));
    TEST_ASSERT_EQUAL(28U*8U, ini_ofs);
    TEST_ASSERT_EQUAL_HEX8_ARRAY(reference, buf, sizeof(reference));

    // Deserialize back from the reference using the same type and compare the field values.
    regulated_delimited_A_1_0_initialize_(&obj);  // Erase prior state.
    buf_size_chars = sizeof(reference);
    buf_size_bits  = buf_size_chars * CHAR_BIT;
    ini_ofs = 0;
    TEST_ASSERT_EQUAL(0, regulated_delimited_A_1_0_deserialize_(&obj, &reference[0], buf_size_bits, &ini_ofs));
    TEST_ASSERT_EQUAL(28U*8U, ini_ofs);
    TEST_ASSERT_TRUE(regulated_delimited_A_1_0_is_del_(&obj));
    TEST_ASSERT_EQUAL(2, obj.del.var.count);
    TEST_ASSERT_EQUAL(2, obj.del.var.elements[0].a.count);
    TEST_ASSERT_EQUAL(1, obj.del.var.elements[0].a.elements[0]);
    TEST_ASSERT_EQUAL(2, obj.del.var.elements[0].a.elements[1]);
    TEST_ASSERT_EQUAL(0, obj.del.var.elements[0].b);
    TEST_ASSERT_EQUAL(1, obj.del.var.elements[1].a.count);
    TEST_ASSERT_EQUAL(3, obj.del.var.elements[1].a.elements[0]);
    TEST_ASSERT_EQUAL(4, obj.del.var.elements[1].b);
    TEST_ASSERT_EQUAL(1, obj.del.fix.count);
    TEST_ASSERT_EQUAL(5, obj.del.fix.elements[0].a[0]);
    TEST_ASSERT_EQUAL(6, obj.del.fix.elements[0].a[1]);

    // Deserialize using a different type to test extensibility enabled by delimited serialization.
    regulated_delimited_A_1_1 dif;
    ini_ofs = 0;
    TEST_ASSERT_EQUAL(0, regulated_delimited_A_1_1_deserialize_(&dif, &reference[0], buf_size_bits, &ini_ofs));
    TEST_ASSERT_EQUAL(28U*8U, ini_ofs);
    TEST_ASSERT_TRUE(regulated_delimited_A_1_1_is_del_(&dif));
    TEST_ASSERT_EQUAL(2, dif.del.var.count);
    TEST_ASSERT_EQUAL(2, dif.del.var.elements[0].a.count);
    TEST_ASSERT_EQUAL(1, dif.del.var.elements[0].a.elements[0]);
    TEST_ASSERT_EQUAL(2, dif.del.var.elements[0].a.elements[1]);
    // b implicitly truncated away
    TEST_ASSERT_EQUAL(1, dif.del.var.elements[1].a.count);
    TEST_ASSERT_EQUAL(3, dif.del.var.elements[1].a.elements[0]);
    // b implicitly truncated away
    TEST_ASSERT_EQUAL(1, dif.del.fix.count);
    TEST_ASSERT_EQUAL(5, dif.del.fix.elements[0].a[0]);
    TEST_ASSERT_EQUAL(6, dif.del.fix.elements[0].a[1]);
    TEST_ASSERT_EQUAL(0, dif.del.fix.elements[0].a[2]);     // 3rd element is implicitly zero-extended
    TEST_ASSERT_EQUAL(0, dif.del.fix.elements[0].b);        // b is implicitly zero-extended

    // Reverse version switch -- serialize v1.1 and then deserialize back using v1.0.
    dif.del.var.count = 1;
    dif.del.var.elements[0].a.count = 2;
    dif.del.var.elements[0].a.elements[0] = 11;
    dif.del.var.elements[0].a.elements[1] = 22;
    dif.del.fix.count = 2;
    dif.del.fix.elements[0].a[0] = 5;
    dif.del.fix.elements[0].a[1] = 6;
    dif.del.fix.elements[0].a[2] = 7;
    dif.del.fix.elements[0].b = 8;
    dif.del.fix.elements[1].a[0] = 100;
    dif.del.fix.elements[1].a[1] = 200;
    dif.del.fix.elements[1].a[2] = 123;
    dif.del.fix.elements[1].b = 99;
    ini_ofs = 0;
    TEST_ASSERT_EQUAL(0, regulated_delimited_A_1_1_serialize_(&dif, &buf[0], buf_size_bits, &ini_ofs));
    TEST_ASSERT_EQUAL(30U*8U, ini_ofs);                           // the reference size was computed by hand
    ini_ofs = 0;
    TEST_ASSERT_EQUAL(0, regulated_delimited_A_1_0_deserialize_(&obj, &buf[0], buf_size_bits, &ini_ofs));
    TEST_ASSERT_TRUE(regulated_delimited_A_1_0_is_del_(&obj));
    TEST_ASSERT_EQUAL(1, obj.del.var.count);
    TEST_ASSERT_EQUAL(2, obj.del.var.elements[0].a.count);
    TEST_ASSERT_EQUAL(11, obj.del.var.elements[0].a.elements[0]);
    TEST_ASSERT_EQUAL(22, obj.del.var.elements[0].a.elements[1]);
    TEST_ASSERT_EQUAL(0, obj.del.var.elements[0].b);        // b is implicitly zero-extended
    TEST_ASSERT_EQUAL(2, obj.del.fix.count);
    TEST_ASSERT_EQUAL(5, obj.del.fix.elements[0].a[0]);     // 3rd is implicitly truncated, b is implicitly truncated
    TEST_ASSERT_EQUAL(6, obj.del.fix.elements[0].a[1]);
    TEST_ASSERT_EQUAL(100, obj.del.fix.elements[1].a[0]);   // 3rd is implicitly truncated, b is implicitly truncated
    TEST_ASSERT_EQUAL(200, obj.del.fix.elements[1].a[1]);
}

static void testStructErrors(void)
{
    regulated_basics_Struct__0_1 obj = {0};
    // Construct a reference in Python for cross-validation: b''.join(pycyphal.dsdl.serialize(Struct__0_1()))
    // Default state -- all zeros except delimiter headers of the nested delimited objects:
    unsigned char sr[] = {
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

    unsigned char buf[regulated_basics_Struct__0_1_SERIALIZATION_BUFFER_SIZE_BYTES_];  // Min size buffer
    (void) memset(&buf[0], 0xAAU, sizeof(buf));  // Fill out the canaries

    // Happy path, validate the test rig
    size_t buf_size_chars = regulated_basics_Struct__0_1_SERIALIZATION_BUFFER_SIZE_BYTES_;
    size_t buf_size_bits  = buf_size_chars * CHAR_BIT;
    size_t ini_ofs = 0;
    TEST_ASSERT_EQUAL(0, regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], buf_size_bits, &ini_ofs));
    TEST_ASSERT_EQUAL((sizeof(sr) - 16U)*CHAR_BIT, ini_ofs);
    TEST_ASSERT_EQUAL_HEX8_ARRAY(sr, buf, sizeof(sr));

    // Buffer too small
    buf_size_chars = regulated_basics_Struct__0_1_SERIALIZATION_BUFFER_SIZE_BYTES_ - 1;
    buf_size_bits  = buf_size_chars * CHAR_BIT;
    ini_ofs = 0;
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_SERIALIZATION_BUFFER_TOO_SMALL,
                      regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], buf_size_bits, &ini_ofs));

    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_SERIALIZATION_BUFFER_TOO_SMALL,
                      regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], 0, &ini_ofs));

    // Null pointers at the input
    ini_ofs = 0;
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_INVALID_ARGUMENT,
                      regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], buf_size_bits, NULL));
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_INVALID_ARGUMENT,
                      regulated_basics_Struct__0_1_serialize_(&obj, NULL, buf_size_bits, &ini_ofs));
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_INVALID_ARGUMENT,
                      regulated_basics_Struct__0_1_serialize_(NULL, &buf[0], buf_size_bits, &ini_ofs));

    // Bad array length
    buf_size_chars = regulated_basics_Struct__0_1_SERIALIZATION_BUFFER_SIZE_BYTES_;
    buf_size_bits  = buf_size_chars * CHAR_BIT;
    ini_ofs = 0;
    obj.delimited_fix_le2.count = 123;
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_REPRESENTATION_BAD_ARRAY_LENGTH,
                      regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], buf_size_bits, &ini_ofs));
    obj.delimited_fix_le2.count = 0;

    // Bad union tag
    ini_ofs = 0;
    obj.delimited_var_2[0]._tag_ = 42;
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_REPRESENTATION_BAD_UNION_TAG,
                      regulated_basics_Struct__0_1_serialize_(&obj, &buf[0], buf_size_bits, &ini_ofs));
    obj.delimited_var_2[0]._tag_ = 0;

    // Bad delimiter header error cannot occur during serialization so this state is not explored.

    // The other way around -- deserialization. First, validate the happy path to make sure the test rig is okay.
    buf_size_chars = sizeof(sr);
    buf_size_bits  = buf_size_chars * CHAR_BIT;
    ini_ofs = 0;
    TEST_ASSERT_EQUAL(0, regulated_basics_Struct__0_1_deserialize_(&obj, &sr[0], buf_size_bits, &ini_ofs));
    TEST_ASSERT_EQUAL((sizeof(sr) - 16U)*CHAR_BIT, ini_ofs);

    // Null pointers at the input.
    ini_ofs = 0;
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_INVALID_ARGUMENT,
                      regulated_basics_Struct__0_1_deserialize_(&obj, &buf[0], buf_size_bits, NULL));
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_INVALID_ARGUMENT,
                      regulated_basics_Struct__0_1_deserialize_(&obj, NULL, buf_size_bits, &ini_ofs));
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_INVALID_ARGUMENT,
                      regulated_basics_Struct__0_1_deserialize_(NULL, &buf[0], buf_size_bits, &ini_ofs));

    // Bad array length
    ini_ofs = 0;
    sr[7] = 123;  // uint8[<3] bytes_lt3
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_REPRESENTATION_BAD_ARRAY_LENGTH,
                      regulated_basics_Struct__0_1_deserialize_(&obj, &sr[0], buf_size_bits, &ini_ofs));
    sr[7] = 0;

    // Bad union tag in a nested composite; make sure the error floats up to the caller.
    ini_ofs = 0;
    sr[23] = 4;  // first element of DelimitedVariableSize.0.1[2] delimited_var_2
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_REPRESENTATION_BAD_UNION_TAG,
                      regulated_basics_Struct__0_1_deserialize_(&obj, &sr[0], buf_size_bits, &ini_ofs));
    sr[23] = 0;

    // Bad delimiter header
    ini_ofs = 0;
    sr[20] = 200;  // 2nd byte of delimiter header of the first element of DelimitedVariableSize.0.1[2] delimited_var_2
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_REPRESENTATION_BAD_DELIMITER_HEADER,
                      regulated_basics_Struct__0_1_deserialize_(&obj, &sr[0], buf_size_bits, &ini_ofs));
    sr[20] = 0;
}

static int_fast8_t randI8(void)
{
    return (int_fast8_t) rand();
}

static int_fast16_t randI16(void)
{
    return (int_fast16_t) ((randI8() + 1) * randI8());
}

static int_fast32_t randI32(void)
{
    return (int_fast32_t) ((randI16() + 1L) * randI16());
}

static int_fast64_t randI64(void)
{
    return (int_fast64_t) ((randI32() + 1LL) * randI32());
}

static float randF16(void)
{
    return (float) randI8();
}

static float randF32(void)
{
    return (float) randI64();
}

static double randF64(void)
{
    return (double) randI64();
}

static void testPrimitive(void)
{
    size_t i;
    for (i = 0U; i < 100; i++)
    {
        regulated_basics_Primitive_0_1 ref;
        ref.a_u64  = (uint_fast64_t) randI64();
        ref.a_u32  = (uint_fast32_t) randI32();
        ref.a_u16  = (uint_fast16_t) randI16();
        ref.a_u8   = (uint_fast8_t)  randI8();
        ref.a_u7   = (uint_fast8_t)  randI8() & 127U;
        ref.n_u64  = (uint_fast64_t) randI64();
        ref.n_u32  = (uint_fast32_t) randI32();
        ref.n_u16  = (uint_fast16_t) randI16();
        ref.n_u8   = (uint_fast8_t)  randI8();
        ref.n_u7   = (uint_fast8_t)  randI8() & 127U;
        ref.a_i64  = randI64();
        ref.a_i32  = randI32();
        ref.a_i16  = randI16();
        ref.a_i8   = randI8();
        ref.a_i7   = randI8() % 64;
        ref.n_i64  = randI64();
        ref.n_i32  = randI32();
        ref.n_i16  = randI16();
        ref.n_i8   = randI8();
        ref.n_i7   = randI8() % 64;
        ref.a_f64  = randF64();
        ref.a_f32  = randF32();
        ref.a_f16  = randF16();
        ref.a_bool = randI8() % 2 == 0;
        ref.n_bool = randI8() % 2 == 0;
        ref.n_f64  = randF64();
        ref.n_f32  = randF32();
        ref.n_f16  = randF16();

        unsigned char buf[regulated_basics_Primitive_0_1_SERIALIZATION_BUFFER_SIZE_BYTES_];
        size_t buf_size_chars = sizeof(buf);
        size_t buf_size_bits  = buf_size_chars * CHAR_BIT;
        size_t ini_ofs = 0;
        TEST_ASSERT_EQUAL(0, regulated_basics_Primitive_0_1_serialize_(&ref, &buf[0], buf_size_bits, &ini_ofs));
        TEST_ASSERT_EQUAL(regulated_basics_Primitive_0_1_SERIALIZATION_BUFFER_SIZE_BYTES_*CHAR_BIT, ini_ofs);  // fixed

        regulated_basics_Primitive_0_1 obj;
        ini_ofs = 0;
        TEST_ASSERT_EQUAL(0, regulated_basics_Primitive_0_1_deserialize_(&obj, &buf[0], buf_size_bits, &ini_ofs));
        TEST_ASSERT_EQUAL(regulated_basics_Primitive_0_1_SERIALIZATION_BUFFER_SIZE_BYTES_*CHAR_BIT, ini_ofs);  // fixed
        TEST_ASSERT_EQUAL(ref.a_u64  , obj.a_u64 );
        TEST_ASSERT_EQUAL(ref.a_u32  , obj.a_u32 );
        TEST_ASSERT_EQUAL(ref.a_u16  , obj.a_u16 );
        TEST_ASSERT_EQUAL(ref.a_u8   , obj.a_u8  );
        TEST_ASSERT_EQUAL(ref.a_u7   , obj.a_u7  );
        TEST_ASSERT_EQUAL(ref.n_u64  , obj.n_u64 );
        TEST_ASSERT_EQUAL(ref.n_u32  , obj.n_u32 );
        TEST_ASSERT_EQUAL(ref.n_u16  , obj.n_u16 );
        TEST_ASSERT_EQUAL(ref.n_u8   , obj.n_u8  );
        TEST_ASSERT_EQUAL(ref.n_u7   , obj.n_u7  );
        TEST_ASSERT_EQUAL(ref.a_i64  , obj.a_i64 );
        TEST_ASSERT_EQUAL(ref.a_i32  , obj.a_i32 );
        TEST_ASSERT_EQUAL(ref.a_i16  , obj.a_i16 );
        TEST_ASSERT_EQUAL(ref.a_i8   , obj.a_i8  );
        TEST_ASSERT_EQUAL(ref.a_i7   , obj.a_i7  );
        TEST_ASSERT_EQUAL(ref.n_i64  , obj.n_i64 );
        TEST_ASSERT_EQUAL(ref.n_i32  , obj.n_i32 );
        TEST_ASSERT_EQUAL(ref.n_i16  , obj.n_i16 );
        TEST_ASSERT_EQUAL(ref.n_i8   , obj.n_i8  );
        TEST_ASSERT_EQUAL(ref.n_i7   , obj.n_i7  );
        TEST_ASSERT_EQUAL(ref.a_f64  , obj.a_f64 );
        TEST_ASSERT_EQUAL(ref.a_f32  , obj.a_f32 );
        TEST_ASSERT_EQUAL(ref.a_f16  , obj.a_f16 );
        TEST_ASSERT_EQUAL(ref.a_bool , obj.a_bool);
        TEST_ASSERT_EQUAL(ref.n_bool , obj.n_bool);
        TEST_ASSERT_EQUAL(ref.n_f64  , obj.n_f64 );
        TEST_ASSERT_EQUAL(ref.n_f32  , obj.n_f32 );
        TEST_ASSERT_EQUAL(ref.n_f16  , obj.n_f16 );
    }
}

static void testPrimitiveArrayFixed(void)
{
    size_t i;
    for (i = 0U; i < 100; i++)
    {
        regulated_basics_PrimitiveArrayFixed_0_1 ref;
        size_t k;
        for (k = 0; k < 2; k++)
        {
            ref.a_u64[k] = (uint_fast64_t) randI64();
            ref.a_u32[k] = (uint_fast32_t) randI32();
            ref.a_u16[k] = (uint_fast16_t) randI16();
            ref.a_u8 [k] = (uint_fast8_t)  randI8();
            ref.a_u7 [k] = (uint_fast8_t)  randI8() & 127U;
            ref.n_u64[k] = (uint_fast64_t) randI64();
            ref.n_u32[k] = (uint_fast32_t) randI32();
            ref.n_u16[k] = (uint_fast16_t) randI16();
            ref.n_u8 [k] = (uint_fast8_t)  randI8();
            ref.n_u7 [k] = (uint_fast8_t)  randI8() & 127U;
            ref.a_i64[k] = randI64();
            ref.a_i32[k] = randI32();
            ref.a_i16[k] = randI16();
            ref.a_i8 [k] = randI8();
            ref.a_i7 [k] = randI8() % 64;
            ref.n_i64[k] = randI64();
            ref.n_i32[k] = randI32();
            ref.n_i16[k] = randI16();
            ref.n_i8 [k] = randI8();
            ref.n_i7 [k] = randI8() % 64;
            ref.a_f64[k] = randF64();
            ref.a_f32[k] = randF32();
            ref.a_f16[k] = randF16();
            ref.n_f64[k] = randF64();
            ref.n_f32[k] = randF32();
            ref.n_f16[k] = randF16();
        }
        ref.a_bool_bitpacked_[0] = ((uint_fast8_t) randI8()) & 3;
        ref.n_bool_bitpacked_[0] = ((uint_fast8_t) randI8()) & 3;

        unsigned char buf[regulated_basics_PrimitiveArrayFixed_0_1_SERIALIZATION_BUFFER_SIZE_BYTES_];
        size_t buf_size_chars = sizeof(buf);
        size_t buf_size_bits  = buf_size_chars * CHAR_BIT;
        size_t ini_ofs = 0;
        TEST_ASSERT_EQUAL(0, regulated_basics_PrimitiveArrayFixed_0_1_serialize_(&ref, &buf[0], buf_size_bits, &ini_ofs));
        TEST_ASSERT_EQUAL(regulated_basics_PrimitiveArrayFixed_0_1_SERIALIZATION_BUFFER_SIZE_BYTES_*CHAR_BIT, ini_ofs);  // fixed

        regulated_basics_PrimitiveArrayFixed_0_1 obj;
        ini_ofs = 0;
        TEST_ASSERT_EQUAL(0, regulated_basics_PrimitiveArrayFixed_0_1_deserialize_(&obj, &buf[0], buf_size_bits, &ini_ofs));
        TEST_ASSERT_EQUAL(regulated_basics_PrimitiveArrayFixed_0_1_SERIALIZATION_BUFFER_SIZE_BYTES_*CHAR_BIT, ini_ofs);  // fixed
        for (k = 0; k < 2; k++)
        {
            TEST_ASSERT_EQUAL(ref.a_u64[k], obj.a_u64[k]);
            TEST_ASSERT_EQUAL(ref.a_u32[k], obj.a_u32[k]);
            TEST_ASSERT_EQUAL(ref.a_u16[k], obj.a_u16[k]);
            TEST_ASSERT_EQUAL(ref.a_u8 [k], obj.a_u8 [k]);
            TEST_ASSERT_EQUAL(ref.a_u7 [k], obj.a_u7 [k]);
            TEST_ASSERT_EQUAL(ref.n_u64[k], obj.n_u64[k]);
            TEST_ASSERT_EQUAL(ref.n_u32[k], obj.n_u32[k]);
            TEST_ASSERT_EQUAL(ref.n_u16[k], obj.n_u16[k]);
            TEST_ASSERT_EQUAL(ref.n_u8 [k], obj.n_u8 [k]);
            TEST_ASSERT_EQUAL(ref.n_u7 [k], obj.n_u7 [k]);
            TEST_ASSERT_EQUAL(ref.a_i64[k], obj.a_i64[k]);
            TEST_ASSERT_EQUAL(ref.a_i32[k], obj.a_i32[k]);
            TEST_ASSERT_EQUAL(ref.a_i16[k], obj.a_i16[k]);
            TEST_ASSERT_EQUAL(ref.a_i8 [k], obj.a_i8 [k]);
            TEST_ASSERT_EQUAL(ref.a_i7 [k], obj.a_i7 [k]);
            TEST_ASSERT_EQUAL(ref.n_i64[k], obj.n_i64[k]);
            TEST_ASSERT_EQUAL(ref.n_i32[k], obj.n_i32[k]);
            TEST_ASSERT_EQUAL(ref.n_i16[k], obj.n_i16[k]);
            TEST_ASSERT_EQUAL(ref.n_i8 [k], obj.n_i8 [k]);
            TEST_ASSERT_EQUAL(ref.n_i7 [k], obj.n_i7 [k]);
            TEST_ASSERT_EQUAL(ref.a_f64[k], obj.a_f64[k]);
            TEST_ASSERT_EQUAL(ref.a_f32[k], obj.a_f32[k]);
            TEST_ASSERT_EQUAL(ref.a_f16[k], obj.a_f16[k]);
            TEST_ASSERT_EQUAL(ref.n_f64[k], obj.n_f64[k]);
            TEST_ASSERT_EQUAL(ref.n_f32[k], obj.n_f32[k]);
            TEST_ASSERT_EQUAL(ref.n_f16[k], obj.n_f16[k]);
        }
        TEST_ASSERT_EQUAL(ref.a_bool_bitpacked_[0], obj.a_bool_bitpacked_[0]);
        TEST_ASSERT_EQUAL(ref.n_bool_bitpacked_[0], obj.n_bool_bitpacked_[0]);
    }
}

static void testPrimitiveArrayVariable(void)
{
    size_t i;
    for (i = 0U; i < 100; i++)
    {
        regulated_basics_PrimitiveArrayVariable_0_1 ref;
        size_t k;
        for (k = 0; k < regulated_basics_PrimitiveArrayVariable_0_1_CAPACITY; k++)
        {
            ref.a_u64.elements[k] = (uint_fast64_t) randI64();
            ref.a_u32.elements[k] = (uint_fast32_t) randI32();
            ref.a_u16.elements[k] = (uint_fast16_t) randI16();
            ref.a_u8 .elements[k] = (uint_fast8_t)  randI8();
            ref.a_u7 .elements[k] = (uint_fast8_t)  randI8() & 127U;
            ref.n_u64.elements[k] = (uint_fast64_t) randI64();
            ref.n_u32.elements[k] = (uint_fast32_t) randI32();
            ref.n_u16.elements[k] = (uint_fast16_t) randI16();
            ref.n_u8 .elements[k] = (uint_fast8_t)  randI8();
            ref.n_u7 .elements[k] = (uint_fast8_t)  randI8() & 127U;
            ref.a_i64.elements[k] = randI64();
            ref.a_i32.elements[k] = randI32();
            ref.a_i16.elements[k] = randI16();
            ref.a_i8 .elements[k] = randI8();
            ref.a_i7 .elements[k] = randI8() % 64;
            ref.n_i64.elements[k] = randI64();
            ref.n_i32.elements[k] = randI32();
            ref.n_i16.elements[k] = randI16();
            ref.n_i8 .elements[k] = randI8();
            ref.n_i7 .elements[k] = randI8() % 64;
            ref.a_f64.elements[k] = randF64();
            ref.a_f32.elements[k] = randF32();
            ref.a_f16.elements[k] = randF16();
            ref.n_f64.elements[k] = randF64();
            ref.n_f32.elements[k] = randF32();
            ref.n_f16.elements[k] = randF16();
        }
        ref.a_bool.bitpacked[0] = ((uint_fast8_t) randI8()) & 3;
        ref.n_bool.bitpacked[0] = ((uint_fast8_t) randI8()) & 3;
        ref.a_u64.count = ((uint_fast8_t)randI8()) & 3U;
        ref.a_u32.count = ((uint_fast8_t)randI8()) & 3U;
        ref.a_u16.count = ((uint_fast8_t)randI8()) & 3U;
        ref.a_u8 .count = ((uint_fast8_t)randI8()) & 3U;
        ref.a_u7 .count = ((uint_fast8_t)randI8()) & 3U;
        ref.n_u64.count = ((uint_fast8_t)randI8()) & 3U;
        ref.n_u32.count = ((uint_fast8_t)randI8()) & 3U;
        ref.n_u16.count = ((uint_fast8_t)randI8()) & 3U;
        ref.n_u8 .count = ((uint_fast8_t)randI8()) & 3U;
        ref.n_u7 .count = ((uint_fast8_t)randI8()) & 3U;
        ref.a_i64.count = ((uint_fast8_t)randI8()) & 3U;
        ref.a_i32.count = ((uint_fast8_t)randI8()) & 3U;
        ref.a_i16.count = ((uint_fast8_t)randI8()) & 3U;
        ref.a_i8 .count = ((uint_fast8_t)randI8()) & 3U;
        ref.a_i7 .count = ((uint_fast8_t)randI8()) & 3U;
        ref.n_i64.count = ((uint_fast8_t)randI8()) & 3U;
        ref.n_i32.count = ((uint_fast8_t)randI8()) & 3U;
        ref.n_i16.count = ((uint_fast8_t)randI8()) & 3U;
        ref.n_i8 .count = ((uint_fast8_t)randI8()) & 3U;
        ref.n_i7 .count = ((uint_fast8_t)randI8()) & 3U;
        ref.a_f64.count = ((uint_fast8_t)randI8()) & 3U;
        ref.a_f32.count = ((uint_fast8_t)randI8()) & 3U;
        ref.a_f16.count = ((uint_fast8_t)randI8()) & 3U;
        ref.a_bool.count =((uint_fast8_t)randI8()) & 3U;
        ref.n_bool.count =((uint_fast8_t)randI8()) & 3U;
        ref.n_f64.count = ((uint_fast8_t)randI8()) & 3U;
        ref.n_f32.count = ((uint_fast8_t)randI8()) & 3U;
        ref.n_f16.count = ((uint_fast8_t)randI8()) & 3U;

        unsigned char buf[regulated_basics_PrimitiveArrayVariable_0_1_SERIALIZATION_BUFFER_SIZE_BYTES_];
        size_t buf_size_chars = sizeof(buf);
        size_t buf_size_bits  = buf_size_chars * CHAR_BIT;
        size_t ini_ofs = 0;
        TEST_ASSERT_EQUAL(0, regulated_basics_PrimitiveArrayVariable_0_1_serialize_(&ref, &buf[0], buf_size_bits, &ini_ofs));

        regulated_basics_PrimitiveArrayVariable_0_1 obj;
        ini_ofs = 0;
        TEST_ASSERT_EQUAL(0, regulated_basics_PrimitiveArrayVariable_0_1_deserialize_(&obj, &buf[0], buf_size_bits, &ini_ofs));
        for (k = 0; k < regulated_basics_PrimitiveArrayVariable_0_1_CAPACITY; k++)
        {
            TEST_ASSERT_EQUAL(ref.a_u64.count, obj.a_u64.count);
            TEST_ASSERT_EQUAL(ref.a_u32.count, obj.a_u32.count);
            TEST_ASSERT_EQUAL(ref.a_u16.count, obj.a_u16.count);
            TEST_ASSERT_EQUAL(ref.a_u8 .count, obj.a_u8 .count);
            TEST_ASSERT_EQUAL(ref.a_u7 .count, obj.a_u7 .count);
            TEST_ASSERT_EQUAL(ref.n_u64.count, obj.n_u64.count);
            TEST_ASSERT_EQUAL(ref.n_u32.count, obj.n_u32.count);
            TEST_ASSERT_EQUAL(ref.n_u16.count, obj.n_u16.count);
            TEST_ASSERT_EQUAL(ref.n_u8 .count, obj.n_u8 .count);
            TEST_ASSERT_EQUAL(ref.n_u7 .count, obj.n_u7 .count);
            TEST_ASSERT_EQUAL(ref.a_i64.count, obj.a_i64.count);
            TEST_ASSERT_EQUAL(ref.a_i32.count, obj.a_i32.count);
            TEST_ASSERT_EQUAL(ref.a_i16.count, obj.a_i16.count);
            TEST_ASSERT_EQUAL(ref.a_i8 .count, obj.a_i8 .count);
            TEST_ASSERT_EQUAL(ref.a_i7 .count, obj.a_i7 .count);
            TEST_ASSERT_EQUAL(ref.n_i64.count, obj.n_i64.count);
            TEST_ASSERT_EQUAL(ref.n_i32.count, obj.n_i32.count);
            TEST_ASSERT_EQUAL(ref.n_i16.count, obj.n_i16.count);
            TEST_ASSERT_EQUAL(ref.n_i8 .count, obj.n_i8 .count);
            TEST_ASSERT_EQUAL(ref.n_i7 .count, obj.n_i7 .count);
            TEST_ASSERT_EQUAL(ref.a_f64.count, obj.a_f64.count);
            TEST_ASSERT_EQUAL(ref.a_f32.count, obj.a_f32.count);
            TEST_ASSERT_EQUAL(ref.a_f16.count, obj.a_f16.count);
            TEST_ASSERT_EQUAL(ref.a_bool.count,obj.a_bool.count);
            TEST_ASSERT_EQUAL(ref.n_bool.count,obj.n_bool.count);
            TEST_ASSERT_EQUAL(ref.n_f64.count, obj.n_f64.count);
            TEST_ASSERT_EQUAL(ref.n_f32.count, obj.n_f32.count);
            TEST_ASSERT_EQUAL(ref.n_f16.count, obj.n_f16.count);
            TEST_ASSERT_TRUE((ref.a_u64.count > k) ? (ref.a_u64.elements[k] == obj.a_u64.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.a_u32.count > k) ? (ref.a_u32.elements[k] == obj.a_u32.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.a_u16.count > k) ? (ref.a_u16.elements[k] == obj.a_u16.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.a_u8 .count > k) ? (ref.a_u8 .elements[k] == obj.a_u8 .elements[k]) : true);
            TEST_ASSERT_TRUE((ref.a_u7 .count > k) ? (ref.a_u7 .elements[k] == obj.a_u7 .elements[k]) : true);
            TEST_ASSERT_TRUE((ref.n_u64.count > k) ? (ref.n_u64.elements[k] == obj.n_u64.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.n_u32.count > k) ? (ref.n_u32.elements[k] == obj.n_u32.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.n_u16.count > k) ? (ref.n_u16.elements[k] == obj.n_u16.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.n_u8 .count > k) ? (ref.n_u8 .elements[k] == obj.n_u8 .elements[k]) : true);
            TEST_ASSERT_TRUE((ref.n_u7 .count > k) ? (ref.n_u7 .elements[k] == obj.n_u7 .elements[k]) : true);
            TEST_ASSERT_TRUE((ref.a_i64.count > k) ? (ref.a_i64.elements[k] == obj.a_i64.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.a_i32.count > k) ? (ref.a_i32.elements[k] == obj.a_i32.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.a_i16.count > k) ? (ref.a_i16.elements[k] == obj.a_i16.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.a_i8 .count > k) ? (ref.a_i8 .elements[k] == obj.a_i8 .elements[k]) : true);
            TEST_ASSERT_TRUE((ref.a_i7 .count > k) ? (ref.a_i7 .elements[k] == obj.a_i7 .elements[k]) : true);
            TEST_ASSERT_TRUE((ref.n_i64.count > k) ? (ref.n_i64.elements[k] == obj.n_i64.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.n_i32.count > k) ? (ref.n_i32.elements[k] == obj.n_i32.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.n_i16.count > k) ? (ref.n_i16.elements[k] == obj.n_i16.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.n_i8 .count > k) ? (ref.n_i8 .elements[k] == obj.n_i8 .elements[k]) : true);
            TEST_ASSERT_TRUE((ref.n_i7 .count > k) ? (ref.n_i7 .elements[k] == obj.n_i7 .elements[k]) : true);
            TEST_ASSERT_TRUE((ref.a_f64.count > k) ? (ref.a_f64.elements[k] == obj.a_f64.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.a_f32.count > k) ? (ref.a_f32.elements[k] == obj.a_f32.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.a_f16.count > k) ? (ref.a_f16.elements[k] == obj.a_f16.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.n_f64.count > k) ? (ref.n_f64.elements[k] == obj.n_f64.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.n_f32.count > k) ? (ref.n_f32.elements[k] == obj.n_f32.elements[k]) : true);
            TEST_ASSERT_TRUE((ref.n_f16.count > k) ? (ref.n_f16.elements[k] == obj.n_f16.elements[k]) : true);
        }
        TEST_ASSERT_EQUAL(ref.a_bool.bitpacked[0] & ((1U << ref.a_bool.count) - 1U),
                          obj.a_bool.bitpacked[0] & ((1U << ref.a_bool.count) - 1U));
        TEST_ASSERT_EQUAL(ref.n_bool.bitpacked[0] & ((1U << ref.n_bool.count) - 1U),
                          obj.n_bool.bitpacked[0] & ((1U << ref.n_bool.count) - 1U));
    }
}

/*
 * Test that deserialization methods do not signal an error if a zero size is specified for a null output buffer.
 */
static void testIssue221(void)
{
    unsigned char buf[regulated_basics_Primitive_0_1_SERIALIZATION_BUFFER_SIZE_BYTES_];
    const size_t buf_size_chars      = sizeof(buf);
    const size_t fixed_buf_size_bits = buf_size_chars * CHAR_BIT;
    size_t buf_size_bits = fixed_buf_size_bits;
    size_t ini_ofs = 0;

    regulated_basics_Primitive_0_1 obj;
    TEST_ASSERT_EQUAL(0, regulated_basics_Primitive_0_1_deserialize_(&obj, &buf[0], buf_size_bits, &ini_ofs));
    ini_ofs = 0;
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_INVALID_ARGUMENT,
                      regulated_basics_Primitive_0_1_deserialize_(NULL, &buf[0], buf_size_bits, &ini_ofs));
    ini_ofs = 0;
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_INVALID_ARGUMENT,
                      regulated_basics_Primitive_0_1_deserialize_(&obj, NULL, buf_size_bits, &ini_ofs));
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_INVALID_ARGUMENT,
                      regulated_basics_Primitive_0_1_deserialize_(&obj, &buf[0], buf_size_bits, NULL));
    ini_ofs = 0;
    TEST_ASSERT_EQUAL(0,
                      regulated_basics_Primitive_0_1_deserialize_(&obj, NULL, 0, &ini_ofs));
    TEST_ASSERT_EQUAL(0, ini_ofs);
}

/*
 * Ensure that, where there is no input data, the deserialization method applies the zero-extension rule as defined
 * in section 3.7.1.4 of the specification.
 */
static void testIssue221_zeroExtensionRule(void)
{
    size_t buf_size_bits = 0;
    size_t ini_ofs = 0;
    uavcan_pnp_NodeIDAllocationData_2_0 obj;
    obj.node_id.value = 0xAAAA;
    TEST_ASSERT_EQUAL(0, uavcan_pnp_NodeIDAllocationData_2_0_deserialize_(&obj, NULL, buf_size_bits, &ini_ofs));
    TEST_ASSERT_EQUAL(0, obj.node_id.value);
}


void setUp(void)
{
    const unsigned seed = (unsigned) time(NULL);
    printf("Random seed in %s: srand(%u)\n", __FILE__, seed);
    srand(seed);
}

void tearDown(void)
{

}

int main(void)
{
    UNITY_BEGIN();

    RUN_TEST(testStructReference);
    RUN_TEST(testStructDelimited);
    RUN_TEST(testStructErrors);
    RUN_TEST(testPrimitive);
    RUN_TEST(testPrimitiveArrayFixed);
    RUN_TEST(testPrimitiveArrayVariable);
    RUN_TEST(testIssue221);
    RUN_TEST(testIssue221_zeroExtensionRule);

    return UNITY_END();
}
