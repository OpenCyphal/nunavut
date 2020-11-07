// Copyright (c) 2020 UAVCAN Development Team.
// This software is distributed under the terms of the MIT License.

#include <regulated/basics/Struct__0_1.h>
#include <regulated/basics/Union_0_1.h>
#include "unity.h"  // Include 3rd-party headers afterward to ensure that our header is self-sufficient.

static void testStructConstants(void)
{
    // Application constants.
    TEST_ASSERT_FLOAT_WITHIN(1e-9, -3.0, regulated_basics_Struct__0_1_CONSTANT_MINUS_THREE);
    TEST_ASSERT_EQUAL((uint32_t) 'Z', regulated_basics_Struct__0_1_CONSTANT_ZEE);
    TEST_ASSERT_LESS_OR_EQUAL(regulated_basics_Struct__0_1_SERIALIZATION_BUFFER_SIZE_BYTES_ * 8U,
                              -regulated_basics_Struct__0_1_CONSTANT_MINUS_MAX_OFFSET);
    TEST_ASSERT_TRUE(regulated_basics_Struct__0_1_CONSTANT_TRUTH);

    // Metadata. Expected values encoded in the field names.
    TEST_ASSERT_EQUAL(4, regulated_basics_Struct__0_1_i10_4_ARRAY_CAPACITY_);
    TEST_ASSERT_FALSE(regulated_basics_Struct__0_1_i10_4_ARRAY_IS_VARIABLE_LENGTH_);

    TEST_ASSERT_EQUAL(2, regulated_basics_Struct__0_1_f16_le2_ARRAY_CAPACITY_);
    TEST_ASSERT_TRUE(regulated_basics_Struct__0_1_f16_le2_ARRAY_IS_VARIABLE_LENGTH_);

    TEST_ASSERT_EQUAL(3, regulated_basics_Struct__0_1_unaligned_bitpacked_3_ARRAY_CAPACITY_);
    TEST_ASSERT_FALSE(regulated_basics_Struct__0_1_unaligned_bitpacked_3_ARRAY_IS_VARIABLE_LENGTH_);

    TEST_ASSERT_EQUAL(2, regulated_basics_Struct__0_1_bytes_lt3_ARRAY_CAPACITY_);
    TEST_ASSERT_TRUE(regulated_basics_Struct__0_1_bytes_lt3_ARRAY_IS_VARIABLE_LENGTH_);

    TEST_ASSERT_EQUAL(3, regulated_basics_Struct__0_1_bytes_4_ARRAY_CAPACITY_);
    TEST_ASSERT_FALSE(regulated_basics_Struct__0_1_bytes_4_ARRAY_IS_VARIABLE_LENGTH_);

    TEST_ASSERT_EQUAL(4, regulated_basics_Struct__0_1_u2_le4_ARRAY_CAPACITY_);
    TEST_ASSERT_TRUE(regulated_basics_Struct__0_1_u2_le4_ARRAY_IS_VARIABLE_LENGTH_);

    TEST_ASSERT_EQUAL(2, regulated_basics_Struct__0_1_delimited_fix_le2_ARRAY_CAPACITY_);
    TEST_ASSERT_TRUE(regulated_basics_Struct__0_1_delimited_fix_le2_ARRAY_IS_VARIABLE_LENGTH_);

    TEST_ASSERT_EQUAL(2, regulated_basics_Struct__0_1_u16_2_ARRAY_CAPACITY_);
    TEST_ASSERT_FALSE(regulated_basics_Struct__0_1_u16_2_ARRAY_IS_VARIABLE_LENGTH_);

    TEST_ASSERT_EQUAL(3, regulated_basics_Struct__0_1_aligned_bitpacked_3_ARRAY_CAPACITY_);
    TEST_ASSERT_FALSE(regulated_basics_Struct__0_1_aligned_bitpacked_3_ARRAY_IS_VARIABLE_LENGTH_);

    TEST_ASSERT_EQUAL(2, regulated_basics_Struct__0_1_unaligned_bitpacked_lt3_ARRAY_CAPACITY_);
    TEST_ASSERT_TRUE(regulated_basics_Struct__0_1_unaligned_bitpacked_lt3_ARRAY_IS_VARIABLE_LENGTH_);

    TEST_ASSERT_EQUAL(2, regulated_basics_Struct__0_1_delimited_var_2_ARRAY_CAPACITY_);
    TEST_ASSERT_FALSE(regulated_basics_Struct__0_1_delimited_var_2_ARRAY_IS_VARIABLE_LENGTH_);

    TEST_ASSERT_EQUAL(2, regulated_basics_Struct__0_1_aligned_bitpacked_le3_ARRAY_CAPACITY_);
    TEST_ASSERT_TRUE(regulated_basics_Struct__0_1_aligned_bitpacked_le3_ARRAY_IS_VARIABLE_LENGTH_);
}

static void testUnionConstants(void)
{
    // Type parameters.
    TEST_ASSERT_EQUAL(1U + regulated_basics_Struct__0_1_EXTENT_BYTES_,  // Largest option + union tag field
                      regulated_basics_Union_0_1_EXTENT_BYTES_);
    TEST_ASSERT_EQUAL(3, regulated_basics_Union_0_1_UNION_OPTION_COUNT_);

    // Field metadata. Expected values encoded in the field names.
    TEST_ASSERT_EQUAL(2, regulated_basics_Union_0_1_delimited_fix_le2_ARRAY_CAPACITY_);
    TEST_ASSERT_FALSE(regulated_basics_Union_0_1_delimited_fix_le2_ARRAY_IS_VARIABLE_LENGTH_);

    TEST_ASSERT_EQUAL(2, regulated_basics_Union_0_1_delimited_var_le2_ARRAY_CAPACITY_);
    TEST_ASSERT_TRUE(regulated_basics_Union_0_1_delimited_var_le2_ARRAY_IS_VARIABLE_LENGTH_);
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

    RUN_TEST(testStructConstants);
    RUN_TEST(testUnionConstants);

    return UNITY_END();
}
