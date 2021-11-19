/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests C++ generated code that uses unions or variants.
 */
#include "gmock/gmock.h"
#include "uavcan/_register/Value_1_0.hpp"
#include "regulated/basics/UnionWithSameTypes_0_1.hpp"

/**
 * Canary test to make sure C++ types that use unions compile.
 */
TEST(UnionantTests, value_compiles)
{
    using ValueType = uavcan::_register::Value_1_0;

    ValueType a{};

    a.union_value.emplace<ValueType::VariantType::IndexOf::empty>(uavcan::primitive::Empty_1_0());
    ASSERT_TRUE(
        uavcan::_register::Value_1_0::VariantType::holds_alternative<uavcan::primitive::Empty_1_0>(a.union_value));
}

/**
 * Verify that we can set variant values as rvalues
 */
TEST(UnionantTests, get_set_rvalue)
{
    uavcan::_register::Value_1_0 a{};
    ASSERT_FALSE(uavcan::_register::Value_1_0::VariantType::holds_alternative<uavcan::primitive::array::Integer32_1_0>(
        a.union_value));
    uavcan::primitive::array::Integer32_1_0& result = a.union_value.emplace<uavcan::primitive::array::Integer32_1_0>(
        uavcan::primitive::array::Integer32_1_0{{0, 1, 2}});
    ASSERT_TRUE(uavcan::_register::Value_1_0::VariantType::holds_alternative<uavcan::primitive::array::Integer32_1_0>(
        a.union_value));
    ASSERT_EQ(3UL, result.value.size());
    ASSERT_EQ(2, result.value[2]);
}

/**
 * Verify that we can set variant values as lvalues
 */
TEST(UnionantTests, get_set_lvalue)
{
    uavcan::_register::Value_1_0            a{};
    uavcan::primitive::array::Integer32_1_0 v{{0, 1, 2}};
    ASSERT_FALSE(uavcan::_register::Value_1_0::VariantType::holds_alternative<uavcan::primitive::array::Integer32_1_0>(
        a.union_value));
    uavcan::primitive::array::Integer32_1_0& result = a.union_value.emplace<uavcan::primitive::array::Integer32_1_0>(v);
    ASSERT_TRUE(uavcan::_register::Value_1_0::VariantType::holds_alternative<uavcan::primitive::array::Integer32_1_0>(
        a.union_value));
    ASSERT_EQ(3UL, result.value.size());
    ASSERT_EQ(2, result.value[2]);
    if (uavcan::primitive::array::Integer32_1_0* p =
            uavcan::_register::Value_1_0::VariantType::get_if<uavcan::primitive::array::Integer32_1_0>(&a.union_value))
    {
        ASSERT_NE(nullptr, p);
        ASSERT_EQ(3UL, p->value.size());
    }
}

TEST(UnionantTests, get_set_lvalue_const_value)
{
    uavcan::_register::Value_1_0                  a{};
    const uavcan::primitive::array::Integer32_1_0 v{{0, 1, 2}};
    ASSERT_FALSE(uavcan::_register::Value_1_0::VariantType::holds_alternative<uavcan::primitive::array::Integer32_1_0>(
        a.union_value));
    uavcan::primitive::array::Integer32_1_0& result = a.union_value.emplace<uavcan::primitive::array::Integer32_1_0>(v);
    ASSERT_TRUE(uavcan::_register::Value_1_0::VariantType::holds_alternative<uavcan::primitive::array::Integer32_1_0>(
        a.union_value));
    ASSERT_EQ(3UL, result.value.size());
    ASSERT_EQ(2, result.value[2]);
    if (uavcan::primitive::array::Integer32_1_0* p =
            uavcan::_register::Value_1_0::VariantType::get_if<uavcan::primitive::array::Integer32_1_0>(&a.union_value))
    {
        ASSERT_NE(nullptr, p);
        ASSERT_EQ(3UL, p->value.size());
    }
}

TEST(UnionantTests, get_if_const_variant)
{
    const uavcan::_register::Value_1_0             a{};
    const uavcan::primitive::array::Integer32_1_0* p =
        uavcan::_register::Value_1_0::VariantType::get_if<uavcan::primitive::array::Integer32_1_0>(&a.union_value);
    ASSERT_EQ(nullptr, p);
}

TEST(UnionantTests, union_with_same_types)
{
    regulated::basics::UnionWithSameTypes_0_1 a{};
}
