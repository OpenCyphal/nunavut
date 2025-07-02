/*
 * Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests C++ generated code that mimics std::variant from C++17.
 */
#include <gtest/gtest.h>

#include "cetl/pf17/cetlpf.hpp"
#include "regulated/basics/Union_0_1.hpp"
#include "uavcan/metatransport/can/ArbitrationID_0_1.hpp"
#include "uavcan/_register/Value_1_0.hpp"

/**
 * Verify that the custom VariantType is default initialized to hold the first alternative value
 */
TEST(UnionantTests, union_value_default_ctor)
{
    using VariantType = uavcan::_register::Value_1_0::VariantType;

    const VariantType a;
    ASSERT_EQ(0U, a.index());
    ASSERT_NE(nullptr, VariantType::get_if<VariantType::IndexOf::empty>(&a));
}

/**
 * Verify the in-place initializing constructor of the custom VariantType
 */
constexpr std::size_t uavcan::_register::Value_1_0::VariantType::IndexOf::integer32; // Required for C++14 constexpr
TEST(UnionantTests, union_value_initializing_ctor)
{
    using VariantType = uavcan::_register::Value_1_0::VariantType;
    using ValueType = uavcan::_register::Value_1_0::_traits_::TypeOf::integer32;

    ValueType value_init{{1, 2, 3}};
    constexpr auto index = VariantType::IndexOf::integer32;
    VariantType a{cetl::in_place_index_t<index>{}, value_init};

    ASSERT_EQ(VariantType::IndexOf::integer32, a.index());
    ASSERT_EQ(nullptr, VariantType::get_if<VariantType::IndexOf::empty>(&a));
    ASSERT_NE(nullptr, VariantType::get_if<VariantType::IndexOf::integer32>(&a));
}

/**
 * Verify the copy constructor of the custom VariantType
 */
TEST(UnionantTests, union_value_copy_ctor)
{
    using VariantType = uavcan::metatransport::can::ArbitrationID_0_1::VariantType;
    using ValueType = uavcan::metatransport::can::ArbitrationID_0_1::_traits_::TypeOf::extended;
    VariantType a;

    a.emplace<VariantType::IndexOf::extended>(ValueType{24});

    const auto* a_value = VariantType::get_if<VariantType::IndexOf::extended>(&a);
    ASSERT_NE(nullptr, a_value);
    ASSERT_EQ(24U, a_value->value);

    VariantType b{a};

    const auto* b_value = VariantType::get_if<VariantType::IndexOf::extended>(&b);
    ASSERT_NE(nullptr, b_value);
    ASSERT_EQ(24U, b_value->value);
}

/**
 * Verify the copy assignment operator of the custom VariantType
 */
TEST(UnionantTests, union_value_copy_assignment)
{
    using VariantType = uavcan::metatransport::can::ArbitrationID_0_1::VariantType;
    using ValueType = uavcan::metatransport::can::ArbitrationID_0_1::_traits_::TypeOf::extended;
    VariantType a;

    a.emplace<VariantType::IndexOf::extended>(ValueType{24});

    const auto* a_value = VariantType::get_if<VariantType::IndexOf::extended>(&a);
    ASSERT_NE(nullptr, a_value);
    ASSERT_EQ(24U, a_value->value);

    VariantType b;
    b = a;

    const auto* b_value = VariantType::get_if<VariantType::IndexOf::extended>(&b);
    ASSERT_NE(nullptr, b_value);
    ASSERT_EQ(24U, b_value->value);
}

/**
 * Verify the move constructor of the custom VariantType
 */
TEST(UnionantTests, union_value_move_ctor)
{
    using VariantType = uavcan::_register::Value_1_0::VariantType;
    using ValueType = uavcan::_register::Value_1_0::_traits_::TypeOf::string;

    VariantType a;

    const char* hello_world{"Hello World"};
    auto& a_result = a.emplace<VariantType::IndexOf::string>(
        ValueType
        {
            {
                reinterpret_cast<const unsigned char*>(hello_world),
                reinterpret_cast<const unsigned char*>(&hello_world[11])
            }
        }
    );
    ASSERT_EQ(11UL, a_result.value.size());
    ASSERT_EQ('W', a_result.value[6]);

    VariantType b{std::move(a)};

    ASSERT_NE(nullptr, VariantType::get_if<VariantType::IndexOf::string>(&a));
    ASSERT_EQ(0UL, a_result.value.size());

    const auto* b_value = VariantType::get_if<VariantType::IndexOf::string>(&b);
    ASSERT_NE(nullptr, b_value);
    ASSERT_EQ(11UL, b_value->value.size());
    ASSERT_EQ('W', b_value->value[6]);
}

/**
 * Verify the move assignment operator of the custom VariantType
 */
TEST(UnionantTests, union_value_move_assignment)
{
    using VariantType = uavcan::_register::Value_1_0::VariantType;
    using ValueType = uavcan::_register::Value_1_0::_traits_::TypeOf::string;

    VariantType a;

    // verify that empty is the default such that our emplace of string (next line) is actually changing the
    // variant's value type.
    ASSERT_NE(nullptr, VariantType::get_if<VariantType::IndexOf::empty>(&a));

    const char* hello_world{"Hello World"};
    auto& a_result = a.emplace<VariantType::IndexOf::string>(
        ValueType
        {
            {
                reinterpret_cast<const unsigned char*>(hello_world),
                reinterpret_cast<const unsigned char*>(&hello_world[11])
            }
        }
    );
    ASSERT_EQ(11UL, a_result.value.size());
    ASSERT_EQ('W', a_result.value[6]);

    VariantType b;
    b = std::move(a);

    ASSERT_NE(nullptr, VariantType::get_if<VariantType::IndexOf::string>(&a));
    ASSERT_EQ(0UL, a_result.value.size());

    const auto* b_value = VariantType::get_if<VariantType::IndexOf::string>(&b);
    ASSERT_NE(nullptr, b_value);
    ASSERT_EQ(11UL, b_value->value.size());
    ASSERT_EQ('W', b_value->value[6]);
}
