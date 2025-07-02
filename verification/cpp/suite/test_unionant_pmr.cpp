/*
 * Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Tests C++ generated code with pmr flavoring that uses unions or variants.
 */
#include <gtest/gtest.h>

#include "cetl/pf17/cetlpf.hpp"
#include "regulated/basics/Union_0_1.hpp"
#include "uavcan/_register/Value_1_0.hpp"

template<size_t I>
::testing::AssertionResult address_is_in_buffer(const void* address, const std::array<cetl::byte, I>& buffer)
{
   const cetl::byte* buffer_end = buffer.data() + I + 1;
   if (address >= buffer.data() && address < buffer_end)
   {
      return ::testing::AssertionSuccess();
   }
   else
   {
      return ::testing::AssertionFailure()
         << "Address 0x" << std::hex << reinterpret_cast<uintptr_t>(address)
         << " not in range [0x" << reinterpret_cast<uintptr_t>(buffer.data())
         << ", 0x" << reinterpret_cast<uintptr_t>(buffer_end) << ")";
   }
}

/**
 * Verify that the allocator provided to the Union on construction is also passed down to the default value
 */
TEST(UnionantPmrTests, allocator_propagation_during_construction)
{
   using UnionType = regulated::basics::Union_0_1;

   std::array<cetl::byte, 100> buffer{};
   cetl::pmr::monotonic_buffer_resource mbr{buffer.data(), buffer.size(),
                                                   cetl::pmr::null_memory_resource()};
   cetl::pmr::polymorphic_allocator<void> allocator{&mbr};

   UnionType union_msg{allocator};
   auto& default_value = union_msg.get_struct_();

   default_value.f16_le2.reserve(1);
   ASSERT_TRUE(address_is_in_buffer(default_value.f16_le2.data(), buffer));

   default_value.bytes_lt3.reserve(1);
   ASSERT_TRUE(address_is_in_buffer(default_value.f16_le2.data(), buffer));

   default_value.u2_le4.reserve(1);
   ASSERT_TRUE(address_is_in_buffer(default_value.u2_le4.data(), buffer));

   default_value.delimited_fix_le2.reserve(1);
   ASSERT_TRUE(address_is_in_buffer(default_value.delimited_fix_le2.data(), buffer));
}

/**
 * Verify that the allocator provided to the union on construction is also used to emplace values
 */
TEST(UnionantPmrTests, allocator_propagation_during_value_emplacement)
{
   using UnionType = uavcan::_register::Value_1_0;
   using ValueType = uavcan::primitive::array::Integer8_1_0;

   std::array<cetl::byte, 100> target_buffer{};
   cetl::pmr::monotonic_buffer_resource target_mbr{target_buffer.data(), target_buffer.size(),
                                                   cetl::pmr::null_memory_resource()};
   cetl::pmr::polymorphic_allocator<void> target_allocator{&target_mbr};
   UnionType union_msg{target_allocator};

   cetl::pmr::polymorphic_allocator<void> other_allocator{cetl::pmr::get_default_resource()};
   const ValueType::_traits_::TypeOf::value value_init{{'a', 'b', 'c', 'd', 'e'}, other_allocator};
   const auto& get_value = union_msg.set_integer8(value_init);

   ASSERT_TRUE(address_is_in_buffer(reinterpret_cast<const void*>(get_value.value.data()), target_buffer));
   ASSERT_EQ(get_value.value.size(), value_init.size());
   for (size_t i = 0; i < value_init.size(); i++)
   {
      EXPECT_EQ(reinterpret_cast<const void*>(&get_value.value[i]),
                reinterpret_cast<const void*>(&target_buffer[i]));
      EXPECT_EQ(get_value.value[i], value_init[i]);
   }
}

/**
 * Verify the initializing constructor of the VariantType
 */
TEST(UnionantPmrTests, init_ctor_with_allocator)
{
    using UnionType = uavcan::_register::Value_1_0;
    using VariantType = UnionType::VariantType;
    using ValueType = uavcan::primitive::array::Integer64_1_0;

   std::array<cetl::byte, 100> target_buffer{};
   cetl::pmr::monotonic_buffer_resource target_mbr{target_buffer.data(), target_buffer.size(),
                                                   cetl::pmr::null_memory_resource()};
   cetl::pmr::polymorphic_allocator<void> target_allocator{&target_mbr};

   cetl::pmr::polymorphic_allocator<void> other_allocator{cetl::pmr::get_default_resource()};
   const ValueType::_traits_::TypeOf::value value_init{{1, 2, 3, 4, 5}, other_allocator};
   const UnionType a{cetl::in_place_index_t<VariantType::IndexOf::integer64>{}, ValueType{value_init, other_allocator}, target_allocator};

   ASSERT_FALSE(a.is_empty());
   ASSERT_TRUE(a.is_integer64());

   const auto& get_value = a.get_integer64();
   ASSERT_TRUE(address_is_in_buffer(reinterpret_cast<const void*>(get_value.value.data()), target_buffer));
   ASSERT_EQ(get_value.value.size(), value_init.size());
   for (size_t i = 0; i < value_init.size(); i++)
   {
      EXPECT_EQ(&get_value.value[i],
                reinterpret_cast<std::int64_t*>(target_buffer.data()+(sizeof(std::int64_t)*i)));
      EXPECT_EQ(get_value.value[i], value_init[i]);
   }
}

TEST(UnionantPmrTests, copy_ctor_with_allocator)
{
   using UnionType = uavcan::_register::Value_1_0;
   using ValueType = uavcan::primitive::array::Integer32_1_0;

   cetl::pmr::polymorphic_allocator<void> other_allocator{cetl::pmr::get_default_resource()};
   const ValueType::_traits_::TypeOf::value value_init{{100, 200, 300, 400, 500}, other_allocator};
   UnionType copy_src{other_allocator};
   copy_src.set_integer32(value_init);

   std::array<cetl::byte, 100> target_buffer{};
   cetl::pmr::monotonic_buffer_resource target_mbr{target_buffer.data(), target_buffer.size(),
                                                   cetl::pmr::null_memory_resource()};
   cetl::pmr::polymorphic_allocator<void> target_allocator{&target_mbr};
   UnionType copy_dest{copy_src, target_allocator};

   ASSERT_TRUE(copy_dest.is_integer32());

   const auto& copy_dest_value = copy_dest.get_integer32();
   ASSERT_TRUE(address_is_in_buffer(reinterpret_cast<const void*>(copy_dest_value.value.data()), target_buffer));
   ASSERT_EQ(copy_dest_value.value.size(), value_init.size());
   for (size_t i = 0; i < value_init.size(); i++)
   {
      EXPECT_EQ(&copy_dest_value.value[i],
                reinterpret_cast<std::int32_t*>(target_buffer.data()+(sizeof(std::int32_t)*i)));
      EXPECT_EQ(copy_dest_value.value[i], value_init[i]);
   }
}

TEST(UnionantPmrTests, move_ctor_with_allocator)
{
   using UnionType = uavcan::_register::Value_1_0;
   using ValueType = uavcan::primitive::array::Integer16_1_0;

   cetl::pmr::polymorphic_allocator<void> other_allocator{cetl::pmr::get_default_resource()};
   const ValueType::_traits_::TypeOf::value value_init{{10, 11, 12, 13, 14}, other_allocator};
   UnionType move_src{other_allocator};
   move_src.set_integer16(value_init);

   std::array<cetl::byte, 100> target_buffer{};
   cetl::pmr::monotonic_buffer_resource target_mbr{target_buffer.data(), target_buffer.size(),
                                                   cetl::pmr::null_memory_resource()};
   cetl::pmr::polymorphic_allocator<void> target_allocator{&target_mbr};
   UnionType move_dest{std::move(move_src), target_allocator};

   ASSERT_TRUE(move_dest.is_integer16());

   const auto& move_dest_value = move_dest.get_integer16();
   ASSERT_TRUE(address_is_in_buffer(reinterpret_cast<const void*>(move_dest_value.value.data()), target_buffer));
   ASSERT_EQ(move_dest_value.value.size(), value_init.size());
   for (size_t i = 0; i < value_init.size(); i++)
   {
      EXPECT_EQ(&move_dest_value.value[i],
                reinterpret_cast<std::int16_t*>(target_buffer.data()+(sizeof(std::int16_t)*i)));
      EXPECT_EQ(move_dest_value.value[i], value_init[i]);
   }
}
