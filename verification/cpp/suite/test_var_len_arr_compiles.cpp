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
    template <typename U> struct rebind final { using other = JunkyNoThrowAllocator<U, SizeCount>; };

    JunkyNoThrowAllocator() noexcept
        : data_()
    {
    }

    JunkyNoThrowAllocator(const JunkyNoThrowAllocator& rhs) noexcept
        : data_()
    {
        (void) rhs;
    }

    JunkyNoThrowAllocator(JunkyNoThrowAllocator&& rhs) noexcept
        : data_()
    {
        (void) rhs;
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
        (void) p;
        (void) n;
    }

private:
    T data_[SizeCount];
};

template <typename T, std::size_t SizeCount>
class JunkyThrowingAllocator
{
public:
    using value_type = T;
    template <typename U> struct rebind final { using other = JunkyThrowingAllocator<U, SizeCount>; };

    JunkyThrowingAllocator()
        : data_()
    {
    }

    JunkyThrowingAllocator(const JunkyThrowingAllocator& rhs)
        : data_()
    {
        (void) rhs;
    }

    JunkyThrowingAllocator(JunkyThrowingAllocator&& rhs)
        : data_()
    {
        (void) rhs;
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
        (void) p;
        (void) n;
    }

private:
    T data_[SizeCount];
};

struct ThrowyThing
{
    ThrowyThing() {}
    ThrowyThing(const ThrowyThing&) {}
    ThrowyThing(ThrowyThing&&) {}
};

struct NotThrowyThing
{
    NotThrowyThing() noexcept {}
    NotThrowyThing(const NotThrowyThing&) noexcept {}
    NotThrowyThing(NotThrowyThing&&) noexcept {}
};

// ---------------------------------------------------------------------------------------------------------------------

template <class T>
class TestDefaultAllocator : public testing::Test { };
using DefaultAllocatorTypes = ::testing::Types<
    nunavut::support::VariableLengthArray<int, 10>,
    nunavut::support::VariableLengthArray<bool, 10>
>;
TYPED_TEST_SUITE(TestDefaultAllocator, DefaultAllocatorTypes);
TYPED_TEST(TestDefaultAllocator, X)
{
    TypeParam subject;

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

// ---------------------------------------------------------------------------------------------------------------------

template <class T>
class TestNoThrowAllocator : public testing::Test { };
using NoThrowAllocatorTypes = ::testing::Types<
    nunavut::support::VariableLengthArray<int, 10, JunkyNoThrowAllocator<int, 10>>,
    nunavut::support::VariableLengthArray<bool, 10, JunkyNoThrowAllocator<bool, 10>>
>;
TYPED_TEST_SUITE(TestNoThrowAllocator, NoThrowAllocatorTypes);
TYPED_TEST(TestNoThrowAllocator, X)
{
    TypeParam subject;

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

// ---------------------------------------------------------------------------------------------------------------------

template <class T>
class TestThrowingAllocator : public testing::Test { };
using ThrowingAllocatorTypes = ::testing::Types<
    nunavut::support::VariableLengthArray<int, 10, JunkyThrowingAllocator<int, 10>>,
    nunavut::support::VariableLengthArray<bool, 10, JunkyThrowingAllocator<int, 10>>
>;
TYPED_TEST_SUITE(TestThrowingAllocator, ThrowingAllocatorTypes);
TYPED_TEST(TestThrowingAllocator, X)
{
    TypeParam subject;

    static_assert(std::is_default_constructible<decltype(subject)>::value &&
                      !std::is_nothrow_default_constructible<decltype(subject)>::value,
                  "VariableLengthArray must allow exceptions from the constructor if the allocator does.");

    static_assert(std::is_constructible<decltype(subject)>::value &&
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

// ---------------------------------------------------------------------------------------------------------------------

TEST(ValueThrowing, TestNotThrowingCopyCtor)
{
    using nothrowy_type =
        nunavut::support::VariableLengthArray<NotThrowyThing, 10, JunkyNoThrowAllocator<NotThrowyThing, 10>>;
    static_assert(noexcept(nothrowy_type(std::declval<std::add_lvalue_reference<nothrowy_type>::type>())),
                  "VariableLengthArray copy constructor should not throw if the value type doesn't.");
    using nothrowy_type_throwy_allocator =
        nunavut::support::VariableLengthArray<NotThrowyThing, 10, JunkyThrowingAllocator<NotThrowyThing, 10>>;
    static_assert(!noexcept(nothrowy_type_throwy_allocator(
                      std::declval<std::add_lvalue_reference<nothrowy_type_throwy_allocator>::type>())),
                  "VariableLengthArray copy constructor should throw if the allocator copy constructor throws even if "
                  "the value type doesn't.");
}

TEST(ValueThrowing, TestThrowingCopyCtor)
{
    using throwy_type = nunavut::support::VariableLengthArray<ThrowyThing, 10, JunkyThrowingAllocator<ThrowyThing, 10>>;
    static_assert(!noexcept(throwy_type(std::declval<std::add_lvalue_reference<throwy_type>::type>())),
                  "VariableLengthArray copy constructor should throw if the value type does.");
    using throwy_type_nothrowy_allocator =
        nunavut::support::VariableLengthArray<ThrowyThing, 10, JunkyNoThrowAllocator<ThrowyThing, 10>>;
    static_assert(!noexcept(throwy_type_nothrowy_allocator(
                      std::declval<std::add_lvalue_reference<throwy_type_nothrowy_allocator>::type>())),
                  "VariableLengthArray copy constructor should throw if the value type copy constructor throws even if "
                  "the allocator type doesn't.");
}
