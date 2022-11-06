// Copyright (c) 2020 OpenCyphal Development Team.
// This software is distributed under the terms of the MIT License.


#include <nunavut/support/serialization.h>

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
    memset(&ref, 0, sizeof(ref));
    uint8_t buf[regulated_basics_PrimitiveArrayVariable_0_1_SERIALIZATION_BUFFER_SIZE_BYTES_ - 1];

#if NUNAVUT_SUPPORT_LANGUAGE_OPTION_ENABLE_OVERRIDE_VARIABLE_ARRAY_CAPACITY == 1
    TEST_ASSERT_EQUAL(OVERRIDE_SIZE, regulated_basics_PrimitiveArrayVariable_0_1_a_u64_ARRAY_CAPACITY_);
    TEST_ASSERT_EQUAL(OVERRIDE_SIZE, sizeof(ref.a_u64.elements) / sizeof(ref.a_u64.elements[0]));
    TEST_ASSERT_EQUAL(OVERRIDE_SIZE, regulated_basics_PrimitiveArrayVariable_0_1_n_f32_ARRAY_CAPACITY_);
    TEST_ASSERT_EQUAL(OVERRIDE_SIZE, sizeof(ref.n_f32.elements) / sizeof(ref.n_f32.elements[0]));
#else
    TEST_ASSERT_EQUAL(sizeof(ref.a_u64.elements[0]) *
                      regulated_basics_PrimitiveArrayVariable_0_1_a_u64_ARRAY_CAPACITY_,
                      sizeof(ref.a_u64.elements));
    TEST_ASSERT_EQUAL(sizeof(ref.n_f64.elements[0]) *
                      regulated_basics_PrimitiveArrayVariable_0_1_n_f32_ARRAY_CAPACITY_,
                      sizeof(ref.n_f64.elements));
#endif

    size_t size = sizeof(buf);

#if NUNAVUT_SUPPORT_LANGUAGE_OPTION_ENABLE_OVERRIDE_VARIABLE_ARRAY_CAPACITY == 1
    TEST_ASSERT_EQUAL(NUNAVUT_SUCCESS,
                      regulated_basics_PrimitiveArrayVariable_0_1_serialize_(&ref, &buf[0], &size));
#else
    TEST_ASSERT_EQUAL(-NUNAVUT_ERROR_SERIALIZATION_BUFFER_TOO_SMALL,
                      regulated_basics_PrimitiveArrayVariable_0_1_serialize_(&ref, &buf[0], &size));
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
