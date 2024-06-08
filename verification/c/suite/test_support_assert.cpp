/// @file
/// Googletest death tests for serialization.h
///
/// @copyright
/// Copyright (C) OpenCyphal Development Team  <opencyphal.org>
/// Copyright Amazon.com Inc. or its affiliates.
/// SPDX-License-Identifier: MIT
///

#include "gtest/gtest.h"
#include "gmock/gmock.h"
#include "nunavut/support/serialization.h"

// +----------------------------------------------------------------------+
// | ☠️ DEATH TESTS ☠️
// +----------------------------------------------------------------------+
#ifndef NDEBUG

// covers https://github.com/OpenCyphal/nunavut/issues/338
TEST(NunavutSupportCopyBitsDeathTest, nunavutCopyBits)
{
    uintptr_t data[2];
    uintptr_t expected =  (1ul << ((sizeof(expected) * 8ul) - 1ul));
    const size_t word_size_bytes = sizeof(uintptr_t);
    const size_t word_size_bits = word_size_bytes * 8u;
    memset(&data[1], 0xFF, sizeof(uintptr_t));
    memset(&data[0], 0x00, sizeof(uintptr_t));

    for(size_t i = 0; i < word_size_bits; ++i) {
        nunavutCopyBits(&data[0], i, 1, &data[1], 1);
    }

    ASSERT_DEATH(
        nunavutCopyBits(&data[0], word_size_bits, 1, &data[1], 1),
        "(psrc > pdst)"
    );

    for(size_t i = 0; i < word_size_bits; ++i) {
        nunavutCopyBits(&data[1], 1, i, &data[0], 1);
    }

    ASSERT_DEATH(
        nunavutCopyBits(&data[1], 1, word_size_bits, &data[0], 1),
        "(psrc < pdst)"
    );
}

#endif
