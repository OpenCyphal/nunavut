// Copyright (c) 2020 UAVCAN Development Team.
// This software is distributed under the terms of the MIT License.


#if NUNAVUT_SUPPORT_LANGUAGE_OPTION_ENABLE_OVERRIDE_VARIABLE_ARRAY_CAPACITY == 1
#  define OVERRIDE_SIZE 2
#  define regulated_basics_PrimitiveArrayVariable_0_1_a_u64_ARRAY_CAPACITY_ OVERRIDE_SIZE
#  define regulated_basics_PrimitiveArrayVariable_0_1_n_f32_ARRAY_CAPACITY_ OVERRIDE_SIZE
#endif

#include <regulated/basics/PrimitiveArrayVariable_0_1.h>
#include "unity.h"  // Include 3rd-party headers afterward to ensure that our headers are self-sufficient.
#include <stdlib.h>
#include <time.h>


static void testPrimitiveArrayVariableOverride(void)
{
    regulated_basics_PrimitiveArrayVariable_0_1 ref;

#if NUNAVUT_SUPPORT_LANGUAGE_OPTION_ENABLE_OVERRIDE_VARIABLE_ARRAY_CAPACITY == 1
    TEST_ASSERT_EQUAL(sizeof(ref.a_u64.elements[0]) * OVERRIDE_SIZE, sizeof(ref.a_u64.elements));
    TEST_ASSERT_EQUAL(sizeof(ref.n_f64.elements[0]) * OVERRIDE_SIZE, sizeof(ref.n_f64.elements));
#else
    TEST_ASSERT_EQUAL(sizeof(ref.a_u64.elements[0]) *
                      regulated_basics_PrimitiveArrayVariable_0_1_a_u64_ARRAY_CAPACITY_,
                      sizeof(ref.a_u64.elements));
    TEST_ASSERT_EQUAL(sizeof(ref.n_f64.elements[0]) *
                      regulated_basics_PrimitiveArrayVariable_0_1_n_f32_ARRAY_CAPACITY_,
                      sizeof(ref.n_f64.elements));
#endif
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

    RUN_TEST(testPrimitiveArrayVariableOverride);

    return UNITY_END();
}
