/*
 * Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Sanity tests.
 */
#include "gmock/gmock.h"
#include "uavcan/time/TimeSystem_0_1.h"
#include "uavcan/primitive/Empty_1_0.h"
#include "uavcan/_register/Value_1_0.h"
#include "uavcan/primitive/String_1_0.h"
#include "uavcan/_register/Access_1_0.h"

/**
 * Verify that a simple struct type compiles.
 */
TEST(GeneralTests, StructCompiles)
{
    uavcan_time_TimeSystem_0_1 subject;
    subject.value = 1;
    ASSERT_EQ(1, subject.value);
}

/**
 * Verify that the empty type in primitives compiles
 */
TEST(GeneralTests, EmptyCompiles) {
    uavcan_primitive_Empty_1_0 subject;
    ASSERT_TRUE(0 != static_cast<void*>(&subject));
}

/**
 * Verify that union types compile
 */
TEST(GeneralTests, UnionCompiles) {
    uavcan_register_Value_1_0 subject;
    subject._tag_ = 0;
    ASSERT_TRUE(is_uavcan_register_Value_1_0_empty(&subject));
}

/**
 * Verify that a variable-length array type compiles.
 */
TEST(GeneralTests, VarArrayCompiles) {
    uavcan_primitive_String_1_0 subject;
    subject.value_length = 0;
    ASSERT_EQ(0U, subject.value_length);
}

/**
 * Make sure we strop C++ reserved words in C-structures.
 */
TEST(GeneralTests, TestCppReservedWord) {
    uavcan_register_Access_1_0_Response subject;
    // mutable is only reserved in C++. It should be stropped to _mutable
    // for c types to be compatible with C++.
    subject._mutable = false;
    ASSERT_FALSE(subject._mutable);
}
