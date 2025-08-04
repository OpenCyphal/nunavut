/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests C++ generated code that uses unions or variants.
 */
#include "gmock/gmock.h"
#include "cetl/pf17/cetlpf.hpp"
#include "uavcan/_register/Value_1_0.hpp"
#include "regulated/basics/Union_0_1.hpp"
#include "regulated/basics/UnionWithSameTypes_0_1.hpp"
#include "test_helpers.hpp"
#include "uavcan/metatransport/can/ArbitrationID_0_1.hpp"

#include <type_traits>

using AllocatorType = cetl::pmr::polymorphic_allocator<void>;

template<typename T, typename... Args>
using is_allocator_constructible = typename std::is_constructible<T, Args..., AllocatorType>::type;

template<typename T>
class Creator
{
public:
    template<typename... Args>
    static T Create(Args&&... args)
    {
        return Impl(std::forward<Args>(args)...);
    }

    template<typename V>
    static T Create(std::initializer_list<V> init_list)
    {
        return Impl(init_list);
    }

private:
    template<typename... Args, std::enable_if_t<is_allocator_constructible<T, Args...>::value>* = nullptr>
    static T Impl(Args&&... args)
    {
        // Object is constructed with allocator
        static AllocatorType allocator{cetl::pmr::get_default_resource()};
        return T{std::forward<Args>(args)..., allocator};
    }

    template<typename... Args, std::enable_if_t<!is_allocator_constructible<T, Args...>::value>* = nullptr>
    static T Impl(Args&&... args)
    {
        // Object is constructed without allocator
        return T{std::forward<Args>(args)...};
    }
};

/**
 * Canary test to make sure C++ types that use unions compile.
 */
TEST(UnionantTests, value_compiles)
{
    using UnionType = regulated::basics::Union_0_1;

    // Make sure that index 0 is the default tag. By default the variant initializes as if it is the first type in
    // the variant list unless a non-default constructor is used.
    auto union_msg = Creator<UnionType>::Create();
    ASSERT_TRUE(union_msg.is_struct_());
    ASSERT_FALSE(union_msg.is_delimited_fix_le2());
    ASSERT_FALSE(union_msg.is_delimited_var_le2());
}

/**
 * Verify that we can set variant values as rvalues and read them back
 */
TEST(UnionantTests, set_get_rvalue)
{
    using UnionType = regulated::basics::Union_0_1;
    using ValueType = UnionType::_traits_::TypeOf::delimited_var_le2;

    constexpr size_t kSetValueSize{UnionType::_traits_::ArrayCapacity::delimited_var_le2};

    auto union_msg = Creator<UnionType>::Create();
    auto set_value = Creator<ValueType>::Create();
    for (size_t i = 0; i < kSetValueSize; i++)
    {
        set_value.emplace_back(Creator<ValueType::value_type>::Create());
        set_value.back().set_f32(static_cast<ValueType::value_type::_traits_::TypeOf::f32>(i));
    }

    const auto& get_value = union_msg.set_delimited_var_le2(std::move(set_value));

    ASSERT_TRUE(union_msg.is_delimited_var_le2());
    ASSERT_EQ(kSetValueSize, get_value.size());
    for (size_t i = 0; i < get_value.size(); i++)
    {
        ASSERT_TRUE(get_value[i].is_f32());
        ASSERT_TRUE(
            CompareFloatsNear(static_cast<ValueType::value_type::_traits_::TypeOf::f32>(i),
                              get_value[i].get_f32(),
                              1e-9f)
        );
    }
}

/**
 * Verify that we can set variant values as lvalues and read them back
 */
TEST(UnionantTests, get_set_lvalue)
{
    using UnionType = regulated::basics::Union_0_1;
    using ValueType = UnionType::_traits_::TypeOf::delimited_var_le2;

    constexpr size_t kSetValueSize{UnionType::_traits_::ArrayCapacity::delimited_var_le2};

    auto union_msg = Creator<UnionType>::Create();
    auto set_value = Creator<ValueType>::Create();
    for (size_t i = 0; i < kSetValueSize; i++)
    {
        set_value.emplace_back(Creator<ValueType::value_type>::Create());
        set_value.back().set_f32(static_cast<ValueType::value_type::_traits_::TypeOf::f32>(i));
    }

    const auto& get_value = union_msg.set_delimited_var_le2(set_value);

    ASSERT_TRUE(union_msg.is_delimited_var_le2());
    ASSERT_EQ(set_value.size(), get_value.size());
    for (size_t i = 0; i < get_value.size(); i++)
    {
        ASSERT_TRUE(get_value[i].is_f32());
        ASSERT_TRUE(
            CompareFloatsNear(set_value[i].get_f32(),
                              get_value[i].get_f32(),
                              1e-9f)
        );
    }
}

/**
 * Verify that the variant value can be fetched only as the type being held
 */
TEST(UnionantTests, get_if_const_variant)
{
    using UnionType = regulated::basics::Union_0_1;

    const auto union_msg = Creator<UnionType>::Create();

    ASSERT_NE(nullptr, union_msg.get_struct__if());
    ASSERT_EQ(nullptr, union_msg.get_delimited_fix_le2_if());
    ASSERT_EQ(nullptr, union_msg.get_delimited_var_le2_if());
}

/**
 *  Verify that the variant value can be fetched only at the alternative index for the type being held
 */
TEST(UnionantTests, union_with_same_types)
{
    using UnionWithSameTypesType = regulated::basics::UnionWithSameTypes_0_1;

    auto union_msg = Creator<UnionWithSameTypesType>::Create();

    EXPECT_NE(nullptr, union_msg.get_struct0_if());
    EXPECT_EQ(nullptr, union_msg.get_struct1_if());

    union_msg.set_struct1();
    EXPECT_EQ(nullptr, union_msg.get_struct0_if());
    EXPECT_NE(nullptr, union_msg.get_struct1_if());
}

/**
 * Verify the copy constructor of a composite union type
 */
TEST(UnionantTests, copy_ctor)
{
    using UnionType = uavcan::metatransport::can::ArbitrationID_0_1;
    using ValueType = uavcan::metatransport::can::ExtendedArbitrationID_0_1;

    auto a = Creator<UnionType>::Create();

    const ValueType::_traits_::TypeOf::value value_init{24U};
    a.set_extended(Creator<ValueType>::Create(value_init));

    const auto* a_value = a.get_extended_if();

    ASSERT_NE(nullptr, a_value);
    ASSERT_EQ(value_init, a_value->value);

    const UnionType b{a};

    const auto* b_value = b.get_extended_if();

    ASSERT_NE(nullptr, b_value);
    ASSERT_EQ(value_init, b_value->value);
}

/**
 * Verify the copy assignment operator of a composite union type
 */
TEST(UnionantTests, copy_assignment)
{
    using UnionType = uavcan::metatransport::can::ArbitrationID_0_1;
    using ValueType = uavcan::metatransport::can::ExtendedArbitrationID_0_1;

    auto a = Creator<UnionType>::Create();

    const ValueType::_traits_::TypeOf::value value_init{24U};
    a.set_extended(Creator<ValueType>::Create(value_init));

    const auto* a_value = a.get_extended_if();

    ASSERT_NE(nullptr, a_value);
    ASSERT_EQ(value_init, a_value->value);

    auto b = Creator<UnionType>::Create();
    b = a;

    const auto* b_value = b.get_extended_if();
    ASSERT_NE(nullptr, b_value);
    ASSERT_EQ(value_init, b_value->value);
}

/**
 * Verify the move constructor of a composite union type
 */
TEST(UnionantTests, move_ctor)
{
    using UnionType = uavcan::_register::Value_1_0;
    using ValueType = uavcan::primitive::String_1_0;

    const char* hello_world{"Hello World"};
    auto a = Creator<UnionType>::Create();

    const auto value_init =
        Creator<ValueType::_traits_::TypeOf::value>::Create(
            reinterpret_cast<const unsigned char*>(hello_world),
            reinterpret_cast<const unsigned char*>(&hello_world[11]));
    const auto& a_result = a.set_string(Creator<ValueType>::Create(value_init));
    ASSERT_EQ(11UL, a_result.value.size());
    ASSERT_EQ('W', a_result.value[6]);

    UnionType b{std::move(a)};
    ASSERT_NE(nullptr, a.get_string_if());
    ASSERT_EQ(0UL, a_result.value.size());

    const auto* b_value = b.get_string_if();
    ASSERT_NE(nullptr, b_value);
    ASSERT_EQ(11UL, b_value->value.size());
    ASSERT_EQ('W', b_value->value[6]);
}

/**
 * Verify the move assignment operator of a composite union type
 */
TEST(UnionantTests, move_assignment)
{
    using UnionType = uavcan::_register::Value_1_0;
    using ValueType = uavcan::primitive::String_1_0;

    const char* hello_world{"Hello World"};
    auto a = Creator<UnionType>::Create();

    const auto value_init =
        Creator<ValueType::_traits_::TypeOf::value>::Create(
            reinterpret_cast<const unsigned char*>(hello_world),
            reinterpret_cast<const unsigned char*>(&hello_world[11]));
    const auto& a_result = a.set_string(Creator<ValueType>::Create(value_init));
    ASSERT_EQ(11UL, a_result.value.size());
    ASSERT_EQ('W', a_result.value[6]);

    auto b = Creator<UnionType>::Create();
    b = std::move(a);
    ASSERT_NE(nullptr, a.get_string_if());
    ASSERT_EQ(0UL, a_result.value.size());

    const auto* b_value = b.get_string_if();
    ASSERT_NE(nullptr, b_value);
    ASSERT_EQ(value_init, b_value->value);
}
