/*
 * Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests the common functionality provided by the Nunavut support headers.
 */
#include "unity.h"
#include <assert.h>
#include "nunavut/support/serialization.h"

static void test_foo(void)
{
    TEST_ASSERT_EQUAL(0L, 0L);
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
 
    RUN_TEST(test_foo);
 
    return UNITY_END();
}