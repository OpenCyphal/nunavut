/*
 * Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * Authors: Scott Dixon <dixonsco@amazon.com>, Pavel Pletenev <cpp.create@gmail.com>
 * Sanity tests.
 */
#include "gmock/gmock.h"
#include "uavcan/time/TimeSystem_0_1.hpp"

/**
 * Temporary test as a placeholder while we wire up the build.
 */
TEST(GeneralTests, DoesSomethingCompile) {
    uavcan::time::TimeSystem_0_1 a;
    a.value = 1;
    ASSERT_EQ(1, a.value);
}
