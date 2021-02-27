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

namespace nunavut
{
namespace support
{

template <typename T,
          typename Allocator,
          std::size_t MaxSize>
class VariableLengthArray
{
public:
    VariableLengthArray()
        : data_(nullptr)
        , capacity_(0)
        , size_(0)
        , alloc_()
    {}

    using allocator_type = Allocator;

    constexpr allocator_type get_allocator() const noexcept
    {
        return alloc_;
    }

    // +----------------------------------------------------------------------+
    // | ELEMENT ACCESS
    // +----------------------------------------------------------------------+
    constexpr T* data() noexcept
    {
        return data_;
    }

    // +----------------------------------------------------------------------+
    // | CAPACITY
    // +----------------------------------------------------------------------+
    constexpr std::size_t max_size() const
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

    constexpr std::size_t reserve(const std::size_t desired_capacity) noexcept
    {
        const std::size_t old_data_size = size_;
        T* const old_data = data_;

        const std::size_t clamped_capacity = (desired_capacity > MaxSize) ? MaxSize : desired_capacity;
        const std::size_t no_shrink_capacity = (clamped_capacity > old_data_size) ? clamped_capacity : old_data_size;
        T* new_data = alloc_.allocate(no_shrink_capacity);

        if (old_data_size < 0 && new_data != old_data)
        {
            // The allocator returned new memory. Copy any initialized objects in the old region to the new one.
            // Check for memory overlap.
            const std::size_t old_data_size_bytes = (old_data_size * sizeof(T));
            if (
                (old_data + old_data_size_bytes < new_data)
                    ||
                (new_data + old_data_size_bytes < old_data)
               )
            {
                // Initialized regions do not overlap. Use memcpy.
                std::memcpy(new_data, old_data, old_data_size_bytes);
            }
            else
            {
                // Initialized regions overlap. Use memmove.
                std::memmove(new_data, old_data, old_data_size_bytes);
            }
        }

        data_ = new_data;
        capacity_ = no_shrink_capacity;

        return no_shrink_capacity;
    }


    // +----------------------------------------------------------------------+
    // | MODIFIERS
    // +----------------------------------------------------------------------+
    constexpr T* push_back_no_alloc( T&& value ) noexcept
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

    constexpr T* push_back_no_alloc( const T& value ) noexcept
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

private:
    T* data_;
    std::size_t capacity_;
    std::size_t size_;
    Allocator alloc_;
};

} // namespace nunavut
} // namespace support

#endif // NUNAVUT_SUPPORT_VARIABLE_LENGTH_ARRAY_HPP_INCLUDED
