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
        return reinterpret_cast<T*>(o1heapAllocate(heap_alloc_, n));
    }

private:
    typename std::aligned_storage<sizeof(T), O1HEAP_ALIGNMENT>::type heap_[SizeCount];
    O1HeapInstance* heap_alloc_;
};

template <typename T>
class VariableLengthArrayTestSuite : public ::testing::Test
{
};

using VariableLengthArrayTestAllocators = ::testing::Types<std::allocator<int>,
                                                           std::allocator<long long>,
                                                           O1HeapAllocator<int, O1HEAP_ALIGNMENT * 8>>;
TYPED_TEST_SUITE(VariableLengthArrayTestSuite, VariableLengthArrayTestAllocators,);

TYPED_TEST(VariableLengthArrayTestSuite, TestReserve)
{
    nunavut::support::VariableLengthArray<typename TypeParam::value_type, TypeParam, 10> subject;
    ASSERT_EQ(nullptr, subject.data());
    ASSERT_EQ(0U, subject.capacity());
    ASSERT_EQ(0U, subject.size());
    ASSERT_EQ(10U, subject.max_size());
    ASSERT_EQ(nullptr, subject.push_back_no_alloc(1));

    subject.reserve(1);

    ASSERT_EQ(1U, subject.capacity());
    ASSERT_EQ(0U, subject.size());
    ASSERT_EQ(10U, subject.max_size());
    const typename TypeParam::value_type* const pushed = subject.push_back_no_alloc(1);
    ASSERT_EQ(*pushed, 1);
    ASSERT_EQ(1U, subject.size());
}
