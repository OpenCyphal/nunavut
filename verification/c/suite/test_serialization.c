// Copyright (c) 2020 UAVCAN Development Team.
// This software is distributed under the terms of the MIT License.

#include <regulated/basics/Struct__0_1.h>
#include <regulated/basics/Union_0_1.h>
#include "unity.h"  // Include 3rd-party headers afterward to ensure that our header is self-sufficient.

static void testStructAgainstReference(void)
{
    regulated_basics_Struct__0_1 obj = {0};
    obj.boolean = true;
    obj.i10_4[0] = +0x5555;                             // saturates to +511
    obj.i10_4[1] = -0x6666;                             // saturates to -511
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
    obj.u2_le4.elements[2] = 0x22;                      // truncated => 2
    obj.u2_le4.elements[3] = 0xFF;                      // truncated => 3
    obj.u2_le4.count = 4;
    obj.delimited_fix_le2.elements[0]._dummy_ = 111;    // ignored
    obj.delimited_fix_le2.count = 1;
    obj.u16_2[0] = 0x5555;
    obj.u16_2[1] = 0x6666;
    obj.aligned_bitpacked_3_bitpacked_[0] = 0xF1U;
    obj.unaligned_bitpacked_lt3.count = 2;              // 0b01, rest truncated
    regulated_basics_DelimitedVariableSize_0_1_select_f16_(&obj.delimited_var_2[0]);
    obj.delimited_var_2[0].f16 = +1e9F;                 // truncated to infinity
    regulated_basics_DelimitedVariableSize_0_1_select_f16_(&obj.delimited_var_2[1]);
    obj.delimited_var_2[0].f16 = -1e3F;                 // retained
    obj.aligned_bitpacked_le3.bitpacked[0] = 0xFF;
    obj.aligned_bitpacked_le3.count = 1;                // only lsb is set, other truncated

    uint8_t buf[80];
    (void) memset(&buf[0], 0x55U, sizeof(buf));

    const uint8_t reference[80] = {0};
    (void) reference;
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

    RUN_TEST(testStructAgainstReference);

    return UNITY_END();
}
