/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Ensures certain static contracts are adhered to for the VariableLengthArray
 * type.
 */

#include "gmock/gmock.h"
#include "nunavut/support/VariableLengthArray.hpp"


template <typename T, std::size_t SizeCount>
class JunkyNoThrowAllocator
{
public:
    using value_type = T;

    JunkyNoThrowAllocator() noexcept
        : data_()
    {}

    JunkyNoThrowAllocator(const JunkyNoThrowAllocator& rhs) noexcept
        : data_()
    {
        (void)rhs;
    }

    T* allocate(std::size_t n) noexcept
    {
        if (n <= SizeCount)
        {
            return reinterpret_cast<T*>(&data_[0]);
        }
        else
        {
            return nullptr;
        }
    }

    constexpr void deallocate(T* p, std::size_t n) noexcept
    {
        (void)p;
        (void)n;
    }

private:
    T data_[SizeCount];
};


template <typename T, std::size_t SizeCount>
class JunkyThrowingAllocator
{
public:
    using value_type = T;

    JunkyThrowingAllocator()
        : data_()
    {}

    JunkyThrowingAllocator(const JunkyThrowingAllocator& rhs)
        : data_()
    {
        (void)rhs;
    }

    T* allocate(std::size_t n)
    {
        if (n <= SizeCount)
        {
            return reinterpret_cast<T*>(&data_[0]);
        }
        else
        {
            return nullptr;
        }
    }

    constexpr void deallocate(T* p, std::size_t n)
    {
        (void)p;
        (void)n;
    }

private:
    T data_[SizeCount];
};


TEST(VLATestsStatic, TestNoThrowAllocator)
{
    nunavut::support::VariableLengthArray<int, JunkyNoThrowAllocator<int, 10>, 10> subject;

    static_assert(std::is_nothrow_default_constructible<decltype(subject)>::value,
        "VariableLengthArray must be no-throw default constructible if the allocator is.");

    static_assert(std::is_nothrow_constructible<decltype(subject)>::value,
        "VariableLengthArray must be no-throw default constructible if the allocator is.");

    static_assert(std::is_nothrow_copy_constructible<decltype(subject)>::value,
        "VariableLengthArray must be no-throw copy constructible if the allocator is.");

    static_assert(std::is_nothrow_destructible<decltype(subject)>::value,
        "VariableLengthArray must be no-throw destructible if the allocator is.");

    static_assert(noexcept(subject.reserve(0)),
        "VariableLengthArray.reserve must not throw exceptions if Allocator::allocate does not.");

    static_assert(noexcept(subject.shrink_to_fit()),
        "VariableLengthArray.shrink_to_fit must not throw exceptions if Allocator::deallocate "
        "and Allocate::allocate do not.");

    // Use the subject to ensure it isn't elided.
    ASSERT_EQ(0U, subject.size());
}

TEST(VLATestsStatic, TestThrowingAllocator)
{
    nunavut::support::VariableLengthArray<int, JunkyThrowingAllocator<int, 10>, 10> subject;

    static_assert(std::is_default_constructible<decltype(subject)>::value
                    &&
                 !std::is_nothrow_default_constructible<decltype(subject)>::value,
        "VariableLengthArray must allow exceptions from the constructor if the allocator does.");

    static_assert(std::is_constructible<decltype(subject)>::value
                    &&
                 !std::is_nothrow_constructible<decltype(subject)>::value,
        "VariableLengthArray must allow exceptions from the constructor if the allocator does.");

    static_assert(std::is_copy_constructible<decltype(subject)>::value
                    &&
                 !std::is_nothrow_copy_constructible<decltype(subject)>::value,
        "VariableLengthArray must allow exceptions from the copy constructor if the allocator does.");

    static_assert(!std::is_nothrow_destructible<decltype(subject)>::value,
        "VariableLengthArray must be allow exceptions from the destructor if the allocator does.");

    static_assert(!noexcept(subject.reserve(0)),
        "VariableLengthArray.reserve must allow exceptions if Allocator::allocate does.");

    static_assert(!noexcept(subject.shrink_to_fit()),
        "VariableLengthArray.shrink_to_fit must allow exceptions if either Allocator::deallocate "
        "or Allocate::allocate do.");

    // Use the subject to ensure it isn't elided.
    ASSERT_EQ(0U, subject.size());
}
