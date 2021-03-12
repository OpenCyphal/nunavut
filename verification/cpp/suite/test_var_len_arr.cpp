/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Sanity tests.
 */

#include "gmock/gmock.h"
#include "nunavut/support/VariableLengthArray.hpp"
#include <memory>
#include <type_traits>
#include <limits>
#include "o1heap/o1heap.h"
#include <string>
#include <array>

/**
 * Used to test that destructors were called.
 */
class Doomed
{
public:
    Doomed(int* out_signal_dtor)
        : out_signal_dtor_(out_signal_dtor)
        , moved_(false)
    {}
    Doomed(Doomed&& from) noexcept
        : out_signal_dtor_(from.out_signal_dtor_)
        , moved_(false)
    {
        from.moved_ = true;
    }
    Doomed(const Doomed&) = delete;
    Doomed& operator=(const Doomed&) = delete;
    Doomed& operator=(Doomed&&) = delete;

    ~Doomed()
    {
        if (!moved_)
        {
            (*out_signal_dtor_) += 1;
        }
    }

private:
    int* out_signal_dtor_;
    bool moved_;
};

/**
 * Pavel's O(1) Heap Allocator wrapped in an std::allocator concept.
 */
template <typename T, std::size_t SizeCount>
class O1HeapAllocator
{
public:
    using value_type = T;

    O1HeapAllocator()
        : heap_()
        , heap_alloc_(o1heapInit(&heap_[0], SizeCount * sizeof(T), nullptr, nullptr))
    {}

    T* allocate(std::size_t n)
    {
        return reinterpret_cast<T*>(o1heapAllocate(heap_alloc_, n * sizeof(T)));
    }

    constexpr void deallocate(T* p, std::size_t n)
    {
        (void) n;
        o1heapFree(heap_alloc_, p);
    }

private:
    typename std::aligned_storage<sizeof(T), O1HEAP_ALIGNMENT>::type heap_[SizeCount];
    O1HeapInstance*                                                  heap_alloc_;
};

/**
 * A Junky static allocator.
 */
template <typename T, std::size_t SizeCount>
class JunkyStaticAllocator
{
public:
    using value_type = T;
    using array_constref_type = const T(&)[SizeCount];

    JunkyStaticAllocator()
        : data_()
        , alloc_count_(0)
        , last_alloc_size_(0)
        , last_dealloc_size_(0)
    {}

    JunkyStaticAllocator(const JunkyStaticAllocator& rhs)
        : data_()
        , alloc_count_(rhs.alloc_count_)
        , last_alloc_size_(rhs.last_alloc_size_)
        , last_dealloc_size_(rhs.last_dealloc_size_)
    {
    }

    T* allocate(std::size_t n)
    {
        if (n <= SizeCount)
        {
            ++alloc_count_;
            last_alloc_size_ = n;
            return reinterpret_cast<T*>(&data_[0]);
        }
        else
        {
            return nullptr;
        }
    }

    constexpr void deallocate(T* p, std::size_t n)
    {
        // This allocator is junk.
        if (p == reinterpret_cast<T*>(&data_[0]))
        {
            last_dealloc_size_ = n;
        }
    }

    std::size_t get_last_alloc_size() const
    {
        return last_alloc_size_;
    }

    std::size_t get_alloc_count() const
    {
        return alloc_count_;
    }

    std::size_t get_last_dealloc_size() const
    {
        return last_dealloc_size_;
    }

    operator array_constref_type() const
    {
        return data_;
    }
private:
    T data_[SizeCount];
    std::size_t alloc_count_;
    std::size_t last_alloc_size_;
    std::size_t last_dealloc_size_;
};

// +----------------------------------------------------------------------+
/**
 * Test suite for running multiple allocators against the variable length array type.
 */
template <typename T>
class VLATestsGeneric : public ::testing::Test
{};

using VLATestsGenericAllocators = ::testing::Types<std::allocator<int>,
                                                   std::allocator<long long>,
                                                   O1HeapAllocator<int, O1HEAP_ALIGNMENT * 8>,
                                                   JunkyStaticAllocator<int, 30>>;
TYPED_TEST_SUITE(VLATestsGeneric, VLATestsGenericAllocators, );

TYPED_TEST(VLATestsGeneric, TestReserve)
{
    nunavut::support::VariableLengthArray<typename TypeParam::value_type, TypeParam, 10> subject;
    ASSERT_EQ(0U, subject.capacity());
    ASSERT_EQ(0U, subject.size());
    ASSERT_EQ(10U, subject.max_size);

    ASSERT_EQ(1U, subject.reserve(1));

    ASSERT_EQ(1U, subject.capacity());
    ASSERT_EQ(0U, subject.size());
    ASSERT_EQ(10U, subject.max_size);
}

TYPED_TEST(VLATestsGeneric, TestPush)
{
    nunavut::support::VariableLengthArray<typename TypeParam::value_type, TypeParam, 20> subject;
    ASSERT_EQ(nullptr, subject.data());
    ASSERT_EQ(nullptr, subject.push_back_no_alloc(1));

    ASSERT_EQ(10U, subject.reserve(10));

    ASSERT_EQ(10U, subject.capacity());
    ASSERT_EQ(0U, subject.size());
    ASSERT_EQ(20U, subject.max_size);
    const typename TypeParam::value_type* const pushed = subject.push_back_no_alloc(1);
    ASSERT_NE(nullptr, pushed);
    ASSERT_EQ(*pushed, 1);
    ASSERT_EQ(1U, subject.size());
}

TYPED_TEST(VLATestsGeneric, TestPop)
{
    nunavut::support::VariableLengthArray<typename TypeParam::value_type, TypeParam, 20> subject;
    ASSERT_EQ(10U, subject.reserve(10));
    const typename TypeParam::value_type* const pushed = subject.push_back_no_alloc(1);
    ASSERT_NE(nullptr, pushed);
    ASSERT_EQ(*pushed, 1);
    ASSERT_EQ(1U, subject.size());
    subject.pop_back();
    ASSERT_EQ(0U, subject.size());
    ASSERT_EQ(10U, subject.capacity());
}

TYPED_TEST(VLATestsGeneric, TestShrink)
{
    nunavut::support::VariableLengthArray<typename TypeParam::value_type, TypeParam, 20> subject;
    ASSERT_EQ(10U, subject.reserve(10));
    const typename TypeParam::value_type* const pushed = subject.push_back_no_alloc(1);
    ASSERT_NE(nullptr, pushed);
    ASSERT_EQ(*pushed, 1);
    ASSERT_EQ(1U, subject.size());
    ASSERT_EQ(10U, subject.capacity());
    subject.shrink_to_fit();
    ASSERT_EQ(1U, subject.capacity());
}

// +----------------------------------------------------------------------+
/**
 * Test suite for running static allocators against the variable length array type.
 */
template <typename T>
class VLATestsStatic : public ::testing::Test
{};

using VLATestsStaticAllocators =
    ::testing::Types<O1HeapAllocator<int, O1HEAP_ALIGNMENT * 8>, JunkyStaticAllocator<int, 10>>;
TYPED_TEST_SUITE(VLATestsStatic, VLATestsStaticAllocators, );

TYPED_TEST(VLATestsStatic, TestOutOfMemory)
{
    nunavut::support::
        VariableLengthArray<typename TypeParam::value_type, TypeParam, std::numeric_limits<std::size_t>::max()>
            subject;
    ASSERT_EQ(0U, subject.capacity());

    bool        did_run_out_of_memory = false;
    std::size_t ran_out_of_memory_at  = 0;
    for (std::size_t i = 1; i <= 1024; ++i)
    {
        ASSERT_EQ(i - 1, subject.size());
        if (subject.reserve(i) < i)
        {
            did_run_out_of_memory = true;
            ran_out_of_memory_at  = i;
            break;
        }
        ASSERT_EQ(i, subject.capacity());
        typename TypeParam::value_type* pushed =
            subject.push_back_no_alloc(static_cast<typename TypeParam::value_type>(i));
        ASSERT_NE(nullptr, pushed);
        ASSERT_EQ(static_cast<typename TypeParam::value_type>(i), *pushed);
    }
    ASSERT_TRUE(did_run_out_of_memory);
    ASSERT_EQ(nullptr, subject.push_back_no_alloc(0));
    for (std::size_t i = 1; i < ran_out_of_memory_at; ++i)
    {
        ASSERT_EQ(static_cast<typename TypeParam::value_type>(i), subject[i - 1]);
    }
}

TYPED_TEST(VLATestsStatic, TestOverMaxSize)
{
    static constexpr std::size_t MaxSize = 5;
    static_assert(MaxSize > 0, "Test assumes MaxSize > 0");
    nunavut::support::VariableLengthArray<typename TypeParam::value_type, TypeParam, MaxSize> subject;
    ASSERT_EQ(0U, subject.capacity());

    for (std::size_t i = 1; i <= MaxSize; ++i)
    {
        ASSERT_EQ(i, subject.reserve(i));
        typename TypeParam::value_type* pushed =
            subject.push_back_no_alloc(static_cast<typename TypeParam::value_type>(i));
        ASSERT_NE(nullptr, pushed);
        ASSERT_EQ(static_cast<typename TypeParam::value_type>(i), *pushed);
    }
    ASSERT_EQ(MaxSize, subject.reserve(MaxSize + 1));
    ASSERT_EQ(nullptr, subject.push_back_no_alloc(0));
    for (std::size_t i = 0; i < MaxSize; ++i)
    {
        ASSERT_EQ(static_cast<typename TypeParam::value_type>(i + 1), subject[i]);
    }
}

// +----------------------------------------------------------------------+
/**
 * Test suite to ensure non-trivial objects are properly handled.
 */

TEST(VLATestsNonTrivial, TestDeallocSize)
{
    nunavut::support::VariableLengthArray<int, JunkyStaticAllocator<int, 10>, 10> subject;
    ASSERT_EQ(0U, subject.get_allocator().get_alloc_count());
    subject.reserve(10);
    ASSERT_EQ(1U, subject.get_allocator().get_alloc_count());
    ASSERT_EQ(10U, subject.get_allocator().get_last_alloc_size());
    ASSERT_EQ(0U, subject.get_allocator().get_last_dealloc_size());
    subject.pop_back();
    subject.shrink_to_fit();
    ASSERT_EQ(10U, subject.get_allocator().get_last_dealloc_size());
}

TEST(VLATestsNonTrivial, TestDestroy)
{
    int dtor_called = 0;

    auto subject = std::make_shared<nunavut::support::VariableLengthArray<Doomed, std::allocator<Doomed>, 10>>();

    ASSERT_EQ(10U, subject->reserve(10));
    ASSERT_NE(nullptr, subject->push_back_no_alloc(Doomed(&dtor_called)));
    ASSERT_NE(nullptr, subject->push_back_no_alloc(Doomed(&dtor_called)));
    ASSERT_EQ(0, dtor_called);
    subject.reset();
    ASSERT_EQ(2, dtor_called);
}

TEST(VLATestsNonTrivial, TestNonFunamental)
{
    int dtor_called = 0;

    nunavut::support::VariableLengthArray<Doomed, std::allocator<Doomed>, 10> subject;
    ASSERT_EQ(10U, subject.reserve(10));
    ASSERT_NE(nullptr, subject.push_back_no_alloc(Doomed(&dtor_called)));
    subject.pop_back();
    ASSERT_EQ(1, dtor_called);
}

TEST(VLATestsNonTrivial, TestNotMovable)
{
    class NotMovable
    {
    public:
        NotMovable() {}
        NotMovable(NotMovable&&) = delete;
        NotMovable(const NotMovable& rhs) noexcept
        {
            (void) rhs;
        }
    };
    nunavut::support::VariableLengthArray<NotMovable, std::allocator<NotMovable>, 10> subject;
    ASSERT_EQ(10U, subject.reserve(10));
    NotMovable source;
    ASSERT_NE(nullptr, subject.push_back_no_alloc(source));
}

TEST(VLATestsNonTrivial, TestMovable)
{
    class Movable
    {
    public:
        Movable(int data)
            : data_(data)
        {}
        Movable(const Movable&) = delete;
        Movable(Movable&& move_from) noexcept
            : data_(move_from.data_)
        {
            move_from.data_ = 0;
        }
        int get_data() const
        {
            return data_;
        }

    private:
        int data_;
    };
    nunavut::support::VariableLengthArray<Movable, std::allocator<Movable>, 10> subject;
    ASSERT_EQ(10U, subject.reserve(10));
    Movable* pushed = subject.push_back_no_alloc(Movable(1));
    ASSERT_NE(nullptr, pushed);
    ASSERT_EQ(1, pushed->get_data());
}

/**
 * Just remember that this is a possible pattern (unfortunately).
 */
TEST(VLATestsNonTrivial, TestMoveToVector)
{
    nunavut::support::VariableLengthArray<std::size_t, std::allocator<std::size_t>, 10> subject;
    ASSERT_EQ(decltype(subject)::max_size, subject.reserve(decltype(subject)::max_size));
    for (std::size_t i = 0; i < decltype(subject)::max_size; ++i)
    {
        ASSERT_NE(nullptr, subject.push_back_no_alloc(i));
    }
    std::vector<std::size_t> a(subject.data(), subject.data() + subject.size());
    for (std::size_t i = 0; i < decltype(subject)::max_size; ++i)
    {
        ASSERT_EQ(i, a[i]);
    }
}
