/*
 * Copyright 2024 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests C++ generated code that uses unions or variants.
 */
#include "gmock/gmock.h"
#include "uavcan/_register/Value_1_0.hpp"
#include "regulated/basics/UnionWithSameTypes_0_1.hpp"
#include "uavcan/metatransport/can/ArbitrationID_0_1.hpp"

#include <type_traits>

struct MockMemoryResource : public nunavut::support::memory_resource_type {
    MOCK_METHOD(void*, do_allocate, (std::size_t size_bytes, std::size_t alignment), (override));
    MOCK_METHOD(void, do_deallocate, (void* p, std::size_t size_bytes, std::size_t alignment), (override));
    MOCK_METHOD(bool, do_is_equal, (const nunavut::support::memory_resource_type& rhs), (const, noexcept, override));
};

struct UnionantTest : public testing::Test
{
    using ValueType = uavcan::_register::Value_1_0;

    MockMemoryResource mock_memory_resource;
    nunavut::support::allocator_type<void> allocator;

    ValueType value_0_1;

    UnionantTest()
        : allocator{&mock_memory_resource},
          value_0_1{allocator}
    {}
};

// Union composite tests

/**
 * Canary test to make sure C++ types that use unions compile.
 */
TEST_F(UnionantTest, value_compiles)
{
    // Make sure that index 0 is the default tag. By default the variant initializes as if it is the first type in
    // the variant list unless a non-default constructor is used.
    ASSERT_NE(nullptr, value_0_1.get_empty_if());
}

/**
 * Verify that we can set variant values as rvalues
 */
TEST_F(UnionantTest, get_set_rvalue)
{
    uavcan::primitive::array::Integer32_1_0::_traits_::TypeOf::value rhs_value{std::initializer_list<int32_t>{0, 1, 2}, allocator};
    uavcan::primitive::array::Integer32_1_0 rhs{rhs_value, allocator};
    uavcan::primitive::array::Integer32_1_0& result{value_0_1.set_integer32(std::move(rhs))};
    ASSERT_EQ(3UL, result.value.size());
    ASSERT_EQ(2, result.value[2]);
}

/**
 * Verify that we can set variant values as lvalues
 */
TEST_F(UnionantTest, get_set_lvalue)
{
    uavcan::primitive::array::Integer32_1_0::_traits_::TypeOf::value rhs_value{std::initializer_list<int32_t>{0, 1, 2}, allocator};
    uavcan::primitive::array::Integer32_1_0 rhs{rhs_value, allocator};

    // By default, alternative value is not held
    ASSERT_EQ(nullptr, value_0_1.get_integer32_if());

    uavcan::primitive::array::Integer32_1_0& result{value_0_1.set_integer32(rhs)};
    ASSERT_NE(nullptr, value_0_1.get_integer32_if());
    EXPECT_EQ(rhs_value.size(), result.value.size());
    EXPECT_EQ(rhs_value[2], result.value[2]);

    uavcan::primitive::array::Integer32_1_0& fetched{value_0_1.get_integer32()};
    ASSERT_EQ(rhs_value.size(), fetched.value.size());
    EXPECT_EQ(rhs_value[2], fetched.value[2]);
}

/**
 * Verify that the variant value can be fetched only as the type being held
 */
TEST_F(UnionantTest, get_if_const_variant)
{
    const uavcan::_register::Value_1_0 value_0_1_const{value_0_1};

    const uavcan::primitive::Empty_1_0* p_empty{value_0_1_const.get_empty_if()};
    const uavcan::primitive::array::Integer32_1_0* p_int32{value_0_1_const.get_integer32_if()};

    ASSERT_NE(nullptr, p_empty);
    ASSERT_EQ(nullptr, p_int32);
}

/**
 *  Verify that the variant value can be fetched only at the alternative index for the type being held
 */
TEST_F(UnionantTest, union_with_same_types)
{
    using RepeatTypeUnion = regulated::basics::UnionWithSameTypes_0_1;
    RepeatTypeUnion repeat{allocator};

    regulated::basics::Struct__0_1* p_struct1 {repeat.get_struct0_if()};
    regulated::basics::Struct__0_1* p_struct2 {repeat.get_struct1_if()};
    std::array<regulated::basics::DelimitedFixedSize_0_1, 2>* p_delimited_fix_le2 = repeat.get_delimited_fix_le2_if();

    EXPECT_NE(nullptr, p_struct1);
    EXPECT_EQ(nullptr, p_struct2);
    EXPECT_EQ(nullptr, p_delimited_fix_le2);
}
