/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Ensures certain static contracts are adhered to for the VariableLengthArray
 * type.
 */

#include "gmock/gmock.h"
#include "nunavut/support/variable_length_array.hpp"


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

TEST(VLATestsStatic, TestDefaultAllocator)
{
    nunavut::support::VariableLengthArray<int, 10> subject;

    static_assert(std::is_nothrow_default_constructible<decltype(subject)>::value,
        "VariableLengthArray's default allocator must be no-throw default constructible");

    static_assert(std::is_nothrow_constructible<decltype(subject)>::value,
        "VariableLengthArray's default allocator must be no-throw constructible.");

    static_assert(std::is_nothrow_destructible<decltype(subject)>::value,
        "VariableLengthArray's default allocator must be no-throw destructible.'.");

    static_assert(noexcept(subject.reserve(0)),
        "VariableLengthArray.reserve must not throw when using the default allocator.");

    static_assert(noexcept(subject.shrink_to_fit()),
        "VariableLengthArray.shrink_to_fit must not throw exceptions if using the default allocator");

    // Use the subject to ensure it isn't elided.
    ASSERT_EQ(0U, subject.size());
}

TEST(VLATestsStatic, TestNoThrowAllocator)
{
    nunavut::support::VariableLengthArray<int, 10, JunkyNoThrowAllocator<int, 10>> subject;

    static_assert(std::is_nothrow_default_constructible<decltype(subject)>::value,
        "VariableLengthArray must be no-throw default constructible if the allocator is.");

    static_assert(std::is_nothrow_constructible<decltype(subject)>::value,
        "VariableLengthArray must be no-throw constructible if the allocator is.");

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
    nunavut::support::VariableLengthArray<int, 10, JunkyThrowingAllocator<int, 10>> subject;

    static_assert(std::is_default_constructible<decltype(subject)>::value
                    &&
                 !std::is_nothrow_default_constructible<decltype(subject)>::value,
        "VariableLengthArray must allow exceptions from the constructor if the allocator does.");

    static_assert(std::is_constructible<decltype(subject)>::value
                    &&
                 !std::is_nothrow_constructible<decltype(subject)>::value,
        "VariableLengthArray must allow exceptions from the constructor if the allocator does.");

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

/**
 * Used to verify noexcept status for VariableLengthArray comparison with other container types.
 */
template<typename T>
struct ThrowyContainer
{
    constexpr std::size_t size() const
    {
        return 0;
    }

    constexpr const T* cbegin() const
    {
        return nullptr;
    }

    constexpr const T* cend() const
    {
        return nullptr;
    }

};

TEST(VLATestsStatic, TestThrowingComparitor)
{
    nunavut::support::VariableLengthArray<int, 10> subject;
    ThrowyContainer<int> throwy;
    std::vector<int> no_throwy;
    static_assert(!noexcept(subject == throwy),
        "VariableLengthArray comparison should throw when used with the ThrowyContainer type.");

    static_assert(!noexcept(subject != throwy),
        "VariableLengthArray comparison should throw when used with the ThrowyContainer type.");

    static_assert(noexcept(subject == no_throwy),
        "VariableLengthArray comparison should not throw when used the std::vector type.");

    static_assert(noexcept(subject != no_throwy),
        "VariableLengthArray comparison should not throw when used the std::vector type.");
}
