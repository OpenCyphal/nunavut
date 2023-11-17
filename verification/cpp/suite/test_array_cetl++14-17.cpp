/*
 * Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * Authors: Skeets Norquist <skeets@amazon.com>
 * Sanity tests.
 */

#include "gmock/gmock.h"
#include "cetl/pf17/byte.hpp"
#include "cetl/pf17/sys/memory_resource.hpp"
#include "mymsgs/Inner_1_0.hpp"
#include "mymsgs/InnerMore_1_0.hpp"
#include "mymsgs/Outer_1_0.hpp"
#include "mymsgs/OuterMore_1_0.hpp"


/**
 * Inner message using cetl::pf17::pmr::polymorphic_allocator
 */
TEST(CetlVlaPmrTests, TestInner) {
    std::array<cetl::pf17::byte, 100> buffer{};
    cetl::pf17::pmr::monotonic_buffer_resource mbr{buffer.data(), buffer.size(), cetl::pf17::pmr::null_memory_resource()};
    cetl::pf17::pmr::polymorphic_allocator<mymsgs::Inner_1_0> pa{&mbr};

    // Reserve and push five items onto the array
    mymsgs::Inner_1_0 inner{pa};
    inner.inner_items.reserve(5);
    for (std::uint32_t i = 0; i < 5; i++) {
        inner.inner_items.push_back(i);
    }

    // Verify that the backing buffer has the five items
    for (std::uint32_t i = 0; i < 5; i++) {
        ASSERT_EQ(i, *reinterpret_cast<std::uint32_t*>(buffer.data()+(sizeof(std::uint32_t)*i)));
    }
}

/**
 * Outer message using cetl::pf17::pmr::polymorphic_allocator
 */
TEST(CetlVlaPmrTests, TestOuter) {
    std::array<cetl::pf17::byte, 100> buffer{};
    cetl::pf17::pmr::monotonic_buffer_resource mbr{buffer.data(), buffer.size(), cetl::pf17::pmr::null_memory_resource()};
    cetl::pf17::pmr::polymorphic_allocator<mymsgs::Outer_1_0> pa{&mbr};

    // Fill the data: inner first, then outer
    mymsgs::Outer_1_0 outer{pa};
    outer.inner.inner_items.reserve(5);
    for (std::uint32_t i = 0; i < 5; i++) {
        outer.inner.inner_items.push_back(i);
    }
    outer.outer_items.reserve(8);
    for (float i = 0; i < 8; i++) {
        outer.outer_items.push_back(i + 5.0f);
    }

    // Verify that the inner is followed by the outer data in the buffer
    cetl::pf17::byte* data = buffer.data();
    for (std::uint32_t i = 0; i < 13; i++) {
        if (i < 5) {
            ASSERT_EQ(i, *reinterpret_cast<std::uint32_t*>(data));
            data += sizeof(std::uint32_t);
        } else {
            ASSERT_EQ(static_cast<float>(i), *reinterpret_cast<float*>(data));
            data += sizeof(float);
        }
    }
}

/**
 * Serialization roundtrip using cetl::pf17::pmr::polymorphic_allocator
 */
TEST(CetlVlaPmrTests, SerializationRoundtrip) {
    std::array<cetl::pf17::byte, 500> buffer{};
    cetl::pf17::pmr::monotonic_buffer_resource mbr{buffer.data(), buffer.size(), cetl::pf17::pmr::null_memory_resource()};
    cetl::pf17::pmr::polymorphic_allocator<mymsgs::OuterMore_1_0> pa{&mbr};

    // Fill the data
    const mymsgs::OuterMore_1_0 outer1(
        {{1, 2, 3, 4}, pa},             // float32[<=8] outer_items
        {                               // InnerMore.1.0[<=2] inners
            {
                {                           // InnerMore_1_0
                    {{55, 66, 77}, pa},         // uint32[<=5] inner_items
                    false,                      // bool inner_primitive
                    pa
                },
                {                           // InnerMore_1_0
                    {{88, 99}, pa},             // uint32[<=5] inner_items
                    true,                       // bool inner_primitive
                    pa
                }
            },
            pa
        },
        777777,                         // int64 outer_primitive
        pa
    );

    // Serialize it
    std::array<unsigned char, mymsgs::OuterMore_1_0::_traits_::SerializationBufferSizeBytes> roundtrip_buffer{};
    nunavut::support::bitspan ser_buffer(roundtrip_buffer);
    const auto ser_result = serialize(outer1, ser_buffer);
    ASSERT_TRUE(ser_result);

    // Deserialize it
    mymsgs::OuterMore_1_0 outer2{pa};
    nunavut::support::const_bitspan des_buffer(static_cast<const unsigned char*>(roundtrip_buffer.data()), roundtrip_buffer.size());
    const auto des_result = deserialize(outer2, des_buffer);
    ASSERT_TRUE(des_result);

    // Verify that the messages match
    ASSERT_EQ(outer2.outer_items.size(), 4);
    ASSERT_EQ(outer2.outer_items[0], 1);
    ASSERT_EQ(outer2.outer_items[1], 2);
    ASSERT_EQ(outer2.outer_items[2], 3);
    ASSERT_EQ(outer2.outer_items[3], 4);
    ASSERT_EQ(outer2.inners.size(), 2);
    ASSERT_EQ(outer2.inners[0].inner_items.size(), 3);
    ASSERT_EQ(outer2.inners[0].inner_items[0], 55);
    ASSERT_EQ(outer2.inners[0].inner_items[1], 66);
    ASSERT_EQ(outer2.inners[0].inner_items[2], 77);
    ASSERT_EQ(outer2.inners[0].inner_primitive, false);
    ASSERT_EQ(outer2.inners[1].inner_items.size(), 2);
    ASSERT_EQ(outer2.inners[1].inner_items[0], 88);
    ASSERT_EQ(outer2.inners[1].inner_items[1], 99);
    ASSERT_EQ(outer2.inners[1].inner_primitive, true);
    ASSERT_EQ(outer2.outer_primitive, 777777);
}

/**
 * Verify that cetl::pf17::pmr::polymorphic_allocator gets passed down to nested types
 */
TEST(CetlVlaPmrTests, TestAllocatorIsPassedDown) {

    ASSERT_TRUE((std::uses_allocator<mymsgs::OuterMore_1_0, cetl::pf17::pmr::polymorphic_allocator<void>>::value));

    std::array<cetl::pf17::byte, 500> buffer{};
    cetl::pf17::pmr::monotonic_buffer_resource mbr{buffer.data(), buffer.size(), cetl::pf17::pmr::null_memory_resource()};
    cetl::pf17::pmr::polymorphic_allocator<void> pa{&mbr};

    mymsgs::OuterMore_1_0 outer{pa};
    outer.outer_items.push_back(1.23456f);
    outer.inners.resize(1);
    outer.inners[0].inner_items.resize(1);

    // Verify that the allocator got passed down from the OuterMore_1_0 to the InnerMore_1_0
    ASSERT_EQ(outer.inners[0].inner_items.get_allocator().resource(), outer.outer_items.get_allocator().resource());
}
