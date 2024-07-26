/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests C++ generated code that uses unions or variants.
 */
#include "gmock/gmock.h"
#include "uavcan/_register/Value_1_0.hpp"
#include "regulated/basics/UnionWithSameTypes_0_1.hpp"
#include "uavcan/metatransport/can/ArbitrationID_0_1.hpp"

#include <type_traits>

struct UnionantTest : public testing::Test
{
    using ValueType = uavcan::_register::Value_1_0;
    ValueType value_0_1;
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
    uavcan::primitive::array::Integer32_1_0::_traits_::TypeOf::value rhs_value{std::initializer_list<int32_t>{0, 1, 2}};
    uavcan::primitive::array::Integer32_1_0 rhs{rhs_value};

    uavcan::primitive::array::Integer32_1_0& result{value_0_1.set_integer32(std::move(rhs))};
    ASSERT_EQ(3UL, result.value.size());
    ASSERT_EQ(2, result.value[2]);
}

/**
 * Verify that we can set variant values as lvalues
 */
TEST_F(UnionantTest, get_set_lvalue)
{
    uavcan::primitive::array::Integer32_1_0::_traits_::TypeOf::value rhs_value{std::initializer_list<int32_t>{0, 1, 2}};
    uavcan::primitive::array::Integer32_1_0 rhs{rhs_value};

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
    RepeatTypeUnion repeat;

    regulated::basics::Struct__0_1* p_struct1 {repeat.get_struct0_if()};
    regulated::basics::Struct__0_1* p_struct2 {repeat.get_struct1_if()};
    std::array<regulated::basics::DelimitedFixedSize_0_1, 2>* p_delimited_fix_le2 = repeat.get_delimited_fix_le2_if();

    EXPECT_NE(nullptr, p_struct1);
    EXPECT_EQ(nullptr, p_struct2);
    EXPECT_EQ(nullptr, p_delimited_fix_le2);
}

// Variant Type tests

/**
 * Verify the initializing constructor of the VariantType
 */
TEST(VariantTypeTests, union_value_init_ctor)
{
    using ValueType = uavcan::_register::Value_1_0;

    uavcan::primitive::array::Integer32_1_0 v{{1, 2, 3}};
    const ValueType::VariantType a{
        nunavut::support::in_place_index_t<ValueType::VariantType::IndexOf::integer32>{},
        v
    };

    const uavcan::primitive::Empty_1_0* p_empty =
        uavcan::_register::Value_1_0::VariantType::get_if<ValueType::VariantType::IndexOf::empty>(&a);
    const uavcan::primitive::array::Integer32_1_0* p_int32 =
        uavcan::_register::Value_1_0::VariantType::get_if<ValueType::VariantType::IndexOf::integer32>(&a);

    ASSERT_EQ(nullptr, p_empty);

    ASSERT_NE(nullptr, p_int32);
    EXPECT_EQ(p_int32->value[0], 1);
    EXPECT_EQ(p_int32->value[1], 2);
    EXPECT_EQ(p_int32->value[2], 3);
}

/**
 * Verify the copy constructor of the VariantType
 */
TEST(VariantTypeTests, union_value_copy_ctor)
{
    using ValueType = uavcan::metatransport::can::ArbitrationID_0_1;
    ValueType a;

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
TEST(VariantTypeTests, union_value_move_ctor)
{
    using ValueType = uavcan::_register::Value_1_0;
    const char* hello_world{"Hello World"};
    ValueType         a;
    // verify that empty is the default such that our emplace of string (next line) is actually changing the
    // variant's value type.
    ASSERT_NE(nullptr, ValueType::VariantType::get_if<ValueType::VariantType::IndexOf::empty>(&a.union_value));
    uavcan::primitive::String_1_0& a_result = a.union_value.emplace<ValueType::VariantType::IndexOf::string>(
        uavcan::primitive::String_1_0
        {
            {
                reinterpret_cast<const unsigned char*>(hello_world),
                reinterpret_cast<const unsigned char*>(&hello_world[11])
            }
        }
                                                                                                            );
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
TEST(VariantTypeTests, union_value_move_assignment)
{
    using ValueType = uavcan::_register::Value_1_0;
    const char* hello_world{"Hello World"};
    const decltype(uavcan::primitive::String_1_0::value) hello_world_vla
            {
                reinterpret_cast<const unsigned char*>(hello_world),
                reinterpret_cast<const unsigned char*>(&hello_world[11])
            };
    ValueType                      a;
    uavcan::primitive::String_1_0& a_result = a.union_value.emplace<ValueType::VariantType::IndexOf::string>(
        uavcan::primitive::String_1_0{{hello_world_vla}});
    ASSERT_EQ(11UL, a_result.value.size());
    ASSERT_EQ('W', a_result.value[6]);

    ValueType::VariantType b;
    b = std::move(a.union_value);
    const uavcan::primitive::String_1_0* b_string_value =
        ValueType::VariantType::get_if<ValueType::VariantType::IndexOf::string>(&b);
    ASSERT_NE(nullptr, b_string_value);
    ASSERT_EQ(hello_world_vla, b_string_value->value);
}
