/*
 * Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * Copyright (C) 2014 Pavel Kirienko <pavel.kirienko@gmail.com>
 * Copyright (C) 2021  UAVCAN Development Team  <uavcan.org>
 * This software is distributed under the terms of the MIT License.
 */

#ifndef NUNAVUT_SUPPORT_VARIABLE_LENGTH_ARRAY_HPP_INCLUDED
#define NUNAVUT_SUPPORT_VARIABLE_LENGTH_ARRAY_HPP_INCLUDED

#include <cstddef>
#include <cstring>
#include <type_traits>
#include <memory>
#include <utility>

namespace nunavut
{
namespace support
{
template <typename T, typename Allocator, std::size_t MaxSize>
class VariableLengthArray
{
public:
    VariableLengthArray()
        : data_(nullptr)
        , capacity_(0)
        , size_(0)
        , alloc_()
    {}

    ~VariableLengthArray()
    {
        fast_deallocate(data_, size_, capacity_, alloc_);
    }

    using allocator_type = Allocator;

    // +----------------------------------------------------------------------+
    // | ELEMENT ACCESS
    // +----------------------------------------------------------------------+
    constexpr T* data() noexcept
    {
        return data_;
    }

    constexpr const T& operator[](std::size_t i) const noexcept
    {
        return data_[i];
    }

    constexpr T& operator[](std::size_t i) noexcept
    {
        return data_[i];
    }

    constexpr T* at_or_null(std::size_t pos) noexcept
    {
        if (pos < size_)
        {
            return &data_[pos];
        }
        else
        {
            return nullptr;
        }
    }

    constexpr const T* at_or_null(std::size_t pos) const noexcept
    {
        if (pos < size_)
        {
            return &data_[pos];
        }
        else
        {
            return nullptr;
        }
    }

    // +----------------------------------------------------------------------+
    // | CAPACITY
    // +----------------------------------------------------------------------+
    constexpr std::size_t max_size() const noexcept
    {
        return MaxSize;
    }

    constexpr std::size_t capacity() const noexcept
    {
        return capacity_;
    }

    constexpr std::size_t size() const noexcept
    {
        return size_;
    }

    std::size_t reserve(const std::size_t desired_capacity) noexcept
    {
        const std::size_t clamped_capacity   = (desired_capacity > MaxSize) ? MaxSize : desired_capacity;
        const std::size_t no_shrink_capacity = (clamped_capacity > size_) ? clamped_capacity : size_;

        T* new_data = nullptr;
        try
        {
            new_data = alloc_.allocate(no_shrink_capacity);
        } catch (const std::bad_array_new_length& e)
        {
            // we ignore the exception since all allocation failures are modeled using
            // null by this class.
            (void) e;
        }

        if (new_data != nullptr)
        {
            if (new_data != data_)
            {
                move_and_free(new_data, data_, size_, capacity_, alloc_);
            }  // else the allocator was able to simply extend the reserved area for the same memory pointer.
            data_     = new_data;
            capacity_ = no_shrink_capacity;
        }

        return capacity_;
    }

    bool shrink_to_fit()
    {
        if (size_ == capacity_)
        {
            // already shrunk
            return true;
        }
        // Allocate only enough to store what we have.
        T* minimized_data = nullptr;

        try
        {
            minimized_data = alloc_.allocate(size_ * sizeof(T));
        } catch (const std::bad_array_new_length& e)
        {
            // we ignore the exception since all allocation failures are modeled using
            // null by this class.
            (void) e;
        }
        if (minimized_data == nullptr)
        {
            return false;
        }
        else
        {
            if (minimized_data != data_)
            {
                move_and_free(minimized_data, data_, size_, capacity_, alloc_);
            }  // else the allocator was able to simply shrink the reserved area for the same memory pointer.
            data_     = minimized_data;
            capacity_ = size_;
            return true;
        }
    }

    // +----------------------------------------------------------------------+
    // | MODIFIERS
    // +----------------------------------------------------------------------+
    constexpr T* push_back_no_alloc(T&& value)
    {
        if (size_ < capacity_)
        {
            return new (&data_[size_++]) T(value);
        }
        else
        {
            return nullptr;
        }
    }

    constexpr T* push_back_no_alloc(const T& value)
    {
        if (size_ < capacity_)
        {
            return new (&data_[size_++]) T(value);
        }
        else
        {
            return nullptr;
        }
    }

    constexpr void pop_back() noexcept
    {
        static_assert(std::is_nothrow_destructible<T>::value,
                      "This container cannot contain objects with destructors that may throw exceptions.");
        if (size_ > 0)
        {
            data_[size_--].~T();
        }
    }

private:
    /**
     * If trivially destructible then we don't have to call the destructors.
     */
    template <typename U>
    static constexpr void fast_deallocate(
        U* const    src,
        std::size_t src_size_count,
        std::size_t src_capacity_count,
        Allocator&  alloc,
        typename std::enable_if<std::is_trivially_destructible<U>::value>::type* = 0) noexcept
    {
        (void) src_size_count;
        alloc.deallocate(src, src_capacity_count);
    }

    /**
     * If not trivially destructible then we invoke each destructor.
     */
    template <typename U>
    static constexpr void fast_deallocate(
        U* const    src,
        std::size_t src_size_count,
        std::size_t src_capacity_count,
        Allocator&  alloc,
        typename std::enable_if<!std::is_trivially_destructible<U>::value>::type* = 0) noexcept
    {
        static_assert(std::is_nothrow_destructible<U>::value,
                      "This container cannot contain objects with destructors that may throw exceptions.");
        for (std::size_t i = 0; i < src_size_count; ++i)
        {
            src[i].~U();
        }
        alloc.deallocate(src, src_capacity_count);
    }

    /**
     * Move stuff in src to dst and then free all the memory allocated for src.
     */
    template <typename U>
    static constexpr void move_and_free(U* const    dst,
                                        U* const    src,
                                        std::size_t src_len_count,
                                        std::size_t src_capacity_count,
                                        Allocator&  alloc,
                                        typename std::enable_if<std::is_fundamental<U>::value>::type*     = 0,
                                        typename std::enable_if<std::is_move_assignable<U>::value>::type* = 0) noexcept
    {
        if (src_len_count > 0)
        {
            // The allocator returned new memory. Copy any initialized objects in the old region to the new one.
            std::memcpy(dst, src, src_len_count * sizeof(U));
        }
        fast_deallocate(src, src_len_count, src_capacity_count, alloc);
    }

    /**
     * Same as above but for non-fundamental types. We can't just memcpy for these.
     */
    template <typename U>
    static constexpr void move_and_free(
        U* const    dst,
        U* const    src,
        std::size_t src_len_count,
        std::size_t src_capacity_count,
        Allocator&  alloc,
        typename std::enable_if<!std::is_fundamental<U>::value>::type*               = 0,
        typename std::enable_if<std::is_nothrow_move_constructible<U>::value>::type* = 0) noexcept
    {
        if (src_len_count > 0)
        {
            // The allocator returned new memory. Copy any initialized objects in the old region to the new one.
            for (size_t i = 0; i < src_len_count; ++i)
            {
                new (&dst[i]) U(std::move(src[i]));
            }
        }
        fast_deallocate(src, src_len_count, src_capacity_count, alloc);
    }

    /**
     * Same as non-fundamental move but for objects that don't support move constructors.
     */
    template <typename U>
    static constexpr void move_and_free(
        U* const    dst,
        U* const    src,
        std::size_t src_len_count,
        std::size_t src_capacity_count,
        Allocator&  alloc,
        typename std::enable_if<!std::is_fundamental<U>::value>::type*                = 0,
        typename std::enable_if<!std::is_nothrow_move_constructible<U>::value>::type* = 0) noexcept
    {
        static_assert(std::is_nothrow_copy_constructible<U>::value,
                      "This container cannot be used with non-fundamental objects that do not have a copy or move "
                      "constructor that does not throw exceptions.");
        if (src_len_count > 0)
        {
            // The allocator returned new memory. Copy any initialized objects in the old region to the new one.
            for (size_t i = 0; i < src_len_count; ++i)
            {
                new (&dst[i]) U(src[i]);
            }
        }
        fast_deallocate(src, src_len_count, src_capacity_count, alloc);
    }

    T*          data_;
    std::size_t capacity_;
    std::size_t size_;
    Allocator   alloc_;
};

}  // namespace support
}  // namespace nunavut

#endif  // NUNAVUT_SUPPORT_VARIABLE_LENGTH_ARRAY_HPP_INCLUDED
