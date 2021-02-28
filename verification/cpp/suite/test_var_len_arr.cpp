/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Sanity tests.
 */

#include "gmock/gmock.h"
#include "nunavut/support/VariableLengthArray.hpp"
#include <memory>
#include <type_traits>
#include "o1heap/o1heap.h"

/**
 * Pavel's O(1) Heap Allocator wrapped in an std::allocator concept.
 */
template<typename T, std::size_t SizeCount>
class O1HeapAllocator
{
public:
    using value_type = T;

    O1HeapAllocator()
        : heap_()
        , heap_alloc_(o1heapInit(&heap_[0], SizeCount * sizeof(T), nullptr, nullptr))
    {
    }

    T* allocate( std::size_t n )
    {
        return reinterpret_cast<T*>(o1heapAllocate(heap_alloc_, n * sizeof(T)));
    }

private:
    typename std::aligned_storage<sizeof(T), O1HEAP_ALIGNMENT>::type heap_[SizeCount];
    O1HeapInstance* heap_alloc_;
};

/**
 * A Junky static allocator.
 */
template<typename T, std::size_t SizeCount>
class JunkyStaticAllocator
{
public:
    using value_type = T;

    JunkyStaticAllocator()
        : data_()
    {
    }

    T* allocate( std::size_t n )
    {
        if (n < SizeCount)
        {
            return reinterpret_cast<T*>(&data_[0]);
        }
        else
        {
            return nullptr;
        }
    }

private:
    typename std::aligned_storage<sizeof(T), alignof(T)>::type data_[SizeCount];
};

// +----------------------------------------------------------------------+
/**
 * Test suite for running multiple allocators against the variable length array type.
 */
template <typename T>
class VLATestsGeneric : public ::testing::Test
{
};

using VLATestsGenericAllocators = ::testing::Types<std::allocator<int>,
                                                           std::allocator<long long>,
                                                           O1HeapAllocator<int, O1HEAP_ALIGNMENT * 8>,
                                                           JunkyStaticAllocator<int, 10>>;
TYPED_TEST_SUITE(VLATestsGeneric, VLATestsGenericAllocators,);



TYPED_TEST(VLATestsGeneric, TestReserve)
{
    nunavut::support::VariableLengthArray<typename TypeParam::value_type, TypeParam, 10> subject;
    ASSERT_EQ(nullptr, subject.data());
    ASSERT_EQ(0U, subject.capacity());
    ASSERT_EQ(0U, subject.size());
    ASSERT_EQ(10U, subject.max_size());
    ASSERT_EQ(nullptr, subject.push_back_no_alloc(1));

    ASSERT_EQ(1U, subject.reserve(1));

    ASSERT_EQ(1U, subject.capacity());
    ASSERT_EQ(0U, subject.size());
    ASSERT_EQ(10U, subject.max_size());
    const typename TypeParam::value_type* const pushed = subject.push_back_no_alloc(1);
    ASSERT_EQ(*pushed, 1);
    ASSERT_EQ(1U, subject.size());
}


// +----------------------------------------------------------------------+
/**
 * Test suite for running static allocators against the variable length array type.
 */
template <typename T>
class VLATestsStatic : public ::testing::Test
{
};

using VLATestsStaticAllocators = ::testing::Types<O1HeapAllocator<int, O1HEAP_ALIGNMENT * 8>,
                                                           JunkyStaticAllocator<int, 10>>;
TYPED_TEST_SUITE(VLATestsStatic, VLATestsStaticAllocators,);

TYPED_TEST(VLATestsStatic, TestOutOfMemory)
{
    nunavut::support::VariableLengthArray<typename TypeParam::value_type, TypeParam, 10> subject;
    ASSERT_EQ(0U, subject.capacity());

    std::size_t last_capacity = subject.capacity();
    bool did_run_out_of_memory = false;
    std::size_t ran_out_of_memory_at = 0;
    for(std::size_t i = 1; i <= 1024; ++i)
    {
        if (last_capacity == subject.reserve(i))
        {
            did_run_out_of_memory = true;
            ran_out_of_memory_at = i - 1;
            break;
        }
        last_capacity = subject.capacity();
        typename TypeParam::value_type* pushed = subject.push_back_no_alloc(static_cast<typename TypeParam::value_type>(i));
        ASSERT_NE(nullptr, pushed);
        ASSERT_EQ(static_cast<typename TypeParam::value_type>(i), *pushed);
    }
    ASSERT_TRUE(did_run_out_of_memory);
    ASSERT_EQ(nullptr,subject.push_back_no_alloc(0));
    for(std::size_t i = 0; i < ran_out_of_memory_at; ++i)
    {
        ASSERT_EQ(static_cast<typename TypeParam::value_type>(i+1), subject[i]);
    }
}
