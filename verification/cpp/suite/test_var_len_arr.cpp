/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Sanity tests.
 */

#include "gmock/gmock.h"
#include "nunavut/support/VariableLengthArray.hpp"
#include <memory>

TEST(VariableLengthArrayTestSuite, TestReserve) {
    nunavut::support::VariableLengthArray<int, std::allocator<int>, 10> subject;
    ASSERT_EQ(nullptr, subject.data());
    ASSERT_EQ(0U, subject.capacity());
    ASSERT_EQ(0U, subject.size());
    ASSERT_EQ(10U, subject.max_size());
    ASSERT_EQ(nullptr, subject.push_back_no_alloc(1));

    subject.reserve(1);

    ASSERT_EQ(1U, subject.capacity());
    ASSERT_EQ(0U, subject.size());
    ASSERT_EQ(10U, subject.max_size());
    const int*const pushed = subject.push_back_no_alloc(1);
    ASSERT_EQ(*pushed, 1);
    ASSERT_EQ(1U, subject.size());
}
