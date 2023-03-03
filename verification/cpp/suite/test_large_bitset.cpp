/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests C++ generated code that uses unions or variants.
 */
#include "gmock/gmock.h"
#include "uavcan/node/port/SubjectIDList_0_1.hpp"

/**
 * Use SubjectIDList to test serialization and deserialization of a bitspan.
 */
TEST(LargeBitsetTests, serialize)
{
    uavcan::node::port::SubjectIDList_0_1 sersubject;
    constexpr std::size_t buffer_size = sizeof(uavcan::node::port::SubjectIDList_0_1);
    std::uint8_t buffer[buffer_size]{0};
    nunavut::support::bitspan bufferspan{buffer, buffer_size};

    std::bitset<uavcan::node::port::SubjectIDList_0_1::CAPACITY>* sersubject_set = sersubject.get_mask_if();
    ASSERT_NE(nullptr, sersubject_set);
    ASSERT_EQ(0x0, sersubject_set->to_ulong());
    sersubject_set->set(1);
    ASSERT_EQ(0x2, sersubject_set->to_ulong());

    const nunavut::support::SerializeResult serresult = sersubject.serialize(bufferspan);
    ASSERT_TRUE(serresult) << "Error is " << static_cast<int>(serresult.error());

    uavcan::node::port::SubjectIDList_0_1 dessubject;
    const nunavut::support::SerializeResult desresult = dessubject.deserialize(nunavut::support::const_bitspan(buffer));
    ASSERT_TRUE(desresult) << "Error is " << static_cast<int>(desresult.error());
    std::bitset<uavcan::node::port::SubjectIDList_0_1::CAPACITY>* dessubject_set = dessubject.get_mask_if();
    ASSERT_NE(nullptr, dessubject_set);
    ASSERT_EQ(0x2, dessubject_set->to_ulong());

}
