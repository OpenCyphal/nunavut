/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests C++ generated code that uses unions or variants.
 */
#include "gmock/gmock.h"
#include "uavcan/_register/Value_1_0.hpp"
#include "regulated/basics/UnionWithSameTypes_0_1.hpp"
#include "uavcan/metatransport/can/ArbitrationID_0_1.hpp"

/**
 * Canary test to make sure C++ types that use unions compile.
 */
TEST(UnionantTests, value_compiles)
{
    using ValueType = uavcan::_register::Value_1_0;
    static_assert(0 == ValueType::VariantType::IndexOf::empty,
                  "These tests are only valid if ValueType::VariantType::IndexOf::empty is the 0th index.");

    ValueType a{};

    // Make sure that index 0 is the default tag. By default the variant initializes as if it is the first type in
    // the variant list unless a non-default constructor is used.
    ASSERT_NE(nullptr,
              uavcan::_register::Value_1_0::VariantType::get_if<ValueType::VariantType::IndexOf::empty>(
                  &a.union_value));
}

/**
 * Verify that we can set variant values as rvalues
 */
TEST(UnionantTests, get_set_rvalue)
{
    uavcan::_register::Value_1_0 a{};
    using ValueType                                 = uavcan::_register::Value_1_0;
    uavcan::primitive::array::Integer32_1_0& result = a.union_value.emplace<ValueType::VariantType::IndexOf::integer32>(
        uavcan::primitive::array::Integer32_1_0{{0, 1, 2}});
    ASSERT_EQ(3UL, result.value.size());
    ASSERT_EQ(2, result.value[2]);
}

/**
 * Verify that we can set variant values as lvalues
 */
TEST(UnionantTests, get_set_lvalue)
{
    using ValueType = uavcan::_register::Value_1_0;
    uavcan::_register::Value_1_0            a{};
    uavcan::primitive::array::Integer32_1_0 v{{0, 1, 2}};
    ASSERT_EQ(nullptr,
              uavcan::_register::Value_1_0::VariantType::get_if<ValueType::VariantType::IndexOf::integer32>(
                  &a.union_value));
    uavcan::primitive::array::Integer32_1_0& result =
        a.union_value.emplace<ValueType::VariantType::IndexOf::integer32>(std::move(v));
    ASSERT_NE(nullptr,
              uavcan::_register::Value_1_0::VariantType::get_if<ValueType::VariantType::IndexOf::integer32>(
                  &a.union_value));
    ASSERT_EQ(3UL, result.value.size());
    ASSERT_EQ(2, result.value[2]);
    if (uavcan::primitive::array::Integer32_1_0* p =
            uavcan::_register::Value_1_0::VariantType::get_if<ValueType::VariantType::IndexOf::integer32>(
                &a.union_value))
    {
        ASSERT_NE(nullptr, p);
        ASSERT_EQ(3UL, p->value.size());
    }
}

TEST(UnionantTests, get_if_const_variant)
{
    using ValueType = uavcan::_register::Value_1_0;
    const uavcan::_register::Value_1_0             a{};
    const uavcan::primitive::array::Integer32_1_0* p =
        uavcan::_register::Value_1_0::VariantType::get_if<ValueType::VariantType::IndexOf::integer32>(&a.union_value);
    ASSERT_EQ(nullptr, p);
}

TEST(UnionantTests, union_with_same_types)
{
    using ValueType = regulated::basics::UnionWithSameTypes_0_1;
    ValueType                                                 a{};
    std::array<regulated::basics::DelimitedFixedSize_0_1, 2>* p =
        ValueType::VariantType::get_if<ValueType::VariantType::IndexOf::delimited_fix_le2>(&a.union_value);
    ASSERT_EQ(nullptr, p);
}

/**
 * Verify the copy constructor of the VariantType
 */
TEST(UnionantTests, union_value_copy_ctor)
{
    using ValueType = uavcan::metatransport::can::ArbitrationID_0_1;
    ValueType a{};

    a.union_value.emplace<ValueType::VariantType::IndexOf::extended>(
        uavcan::metatransport::can::ExtendedArbitrationID_0_1{24});

    uavcan::metatransport::can::ExtendedArbitrationID_0_1* a_value =
        ValueType::VariantType::get_if<ValueType::VariantType::IndexOf::extended>(&a.union_value);

    ASSERT_NE(nullptr, a_value);
    ASSERT_EQ(24U, a_value->value);

    ValueType b(a);

    uavcan::metatransport::can::ExtendedArbitrationID_0_1* b_value =
        ValueType::VariantType::get_if<ValueType::VariantType::IndexOf::extended>(&b.union_value);

    ASSERT_NE(nullptr, b_value);
    ASSERT_EQ(24U, b_value->value);
}

/**
 * Verify the move constructor of the VariantType
 */
TEST(UnionantTests, union_value_move_ctor)
{
    using ValueType = uavcan::_register::Value_1_0;
    const std::string hello_world{"Hello World"};
    ValueType         a{};
    // verify that empty is the default such that our emplace of string (next line) is actually changing the
    // variant's value type.
    ASSERT_NE(nullptr, ValueType::VariantType::get_if<ValueType::VariantType::IndexOf::empty>(&a.union_value));
    uavcan::primitive::String_1_0& a_result = a.union_value.emplace<ValueType::VariantType::IndexOf::string>(
        uavcan::primitive::String_1_0{std::vector<std::uint8_t>(hello_world.begin(), hello_world.end())});
    ASSERT_EQ(11UL, a_result.value.size());
    ASSERT_EQ('W', a_result.value[6]);

    ValueType::VariantType b(std::move(a.union_value));
    ASSERT_NE(nullptr, ValueType::VariantType::get_if<ValueType::VariantType::IndexOf::string>(&a.union_value));
    ASSERT_EQ(0UL, a_result.value.size());
    uavcan::primitive::String_1_0* b_value =
        ValueType::VariantType::get_if<ValueType::VariantType::IndexOf::string>(&b);
    ASSERT_NE(nullptr, b_value);
    ASSERT_EQ(11UL, b_value->value.size());
    ASSERT_EQ('W', b_value->value[6]);
}

/**
 * Verify the move assignment operator of the VariantType
 */
TEST(UnionantTests, union_value_move_assignment)
{
    using ValueType = uavcan::_register::Value_1_0;
    const std::string              hello_world{"Hello World"};
    const std::vector<std::uint8_t> hello_world_vector{hello_world.begin(), hello_world.end()};
    ValueType                      a{};
    uavcan::primitive::String_1_0& a_result = a.union_value.emplace<ValueType::VariantType::IndexOf::string>(
        uavcan::primitive::String_1_0{hello_world_vector});
    ASSERT_EQ(11UL, a_result.value.size());
    ASSERT_EQ('W', a_result.value[6]);

    ValueType::VariantType b;
    b = std::move(a.union_value);
    const uavcan::primitive::String_1_0* b_string_value =
        ValueType::VariantType::get_if<ValueType::VariantType::IndexOf::string>(&b);
    ASSERT_NE(nullptr, b_string_value);
    ASSERT_EQ(hello_world_vector, b_string_value->value);
}
