/*
 *
 * UAVCAN serialization support routines.                                                                     +-+ +-+
 *  Copyright (C) 2014 Pavel Kirienko <pavel.kirienko@gmail.com>                                              | | | |
 *  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                   \  -  /
 *  This software is distributed under the terms of the MIT License.                                            ---
 *                                                                                                               o
 * +------------------------------------------------------------------------------------------------------------------+
 */
// WARNING: THIS IS A WORK IN PROGRESS
#ifndef NUNAVUT_SUPPORT_HPP_INCLUDED
#define NUNAVUT_SUPPORT_HPP_INCLUDED

#include <cstdint>
#include <algorithm>
#include <vector>
#include <type_traits>
#include <limits>

// TODO: assert is temporary
#include <cassert>

namespace nunavut
{
namespace support
{
template <unsigned BitLen>
struct NativeFloatSelector
{
    struct ErrorNoSuchFloat;
    typedef typename std::conditional<
        sizeof(float) * 8 >= BitLen,
        float,
        typename std::conditional<
            sizeof(double) * 8 >= BitLen,
            double,
            typename std::conditional<sizeof(long double) * 8 >= BitLen, long double, ErrorNoSuchFloat>::type>::type>::
        type float_type;

    typedef typename std::conditional<
        BitLen <= 16,
        std::uint16_t,
        typename std::conditional<BitLen <= 32,
                                  std::uint32_t,
                                  typename std::conditional<BitLen <= 64, long double, ErrorNoSuchFloat>::type>::type>::
        type int_storage_type;
};

namespace IEEE754Conversion
{
namespace internal
{
template <unsigned BitLen>
void enforceIeee()
{
    /*
     * Some compilers may have is_iec559 to be defined false despite the fact that IEEE754 is supported.
     * An acceptable workaround would be to put an #ifdef here.
     */
    static_assert(std::numeric_limits<typename NativeFloatSelector<BitLen>::Type>::is_iec559,
                  "We were not able to find a compatible floating-point type for this compiler.");
}

union Fp32
{
    std::uint32_t u;
    float         f;
};

}  // namespace internal

template <typename NativeType>
NativeType nativeIeeeToHalf(float value)
{
    static_assert(sizeof(NativeType) >= 2, "NativeType must be at least 16 bits.");
    static_assert(std::numeric_limits<NativeType>::is_integer, "NativeType must be integral.");
    static_assert(!std::numeric_limits<NativeType>::is_signed, "NativeType must be unsigned.");

    /*
     * https://gist.github.com/rygorous/2156668
     * Public domain, by Fabian "ryg" Giesen
     */
    const internal::Fp32 f32infty   = {255U << 23};
    const internal::Fp32 f16infty   = {31U << 23};
    const internal::Fp32 magic      = {15U << 23};
    const std::uint32_t  sign_mask  = 0x80000000U;
    const std::uint32_t  round_mask = ~0xFFFU;

    internal::Fp32 in;
    NativeType     out;

    in.f = value;

    std::uint32_t sign = in.u & sign_mask;
    in.u ^= sign;

    if (in.u >= f32infty.u) /* Inf or NaN (all exponent bits set) */
    {
        /* NaN->sNaN and Inf->Inf */
        out = (in.u > f32infty.u) ? 0x7FFFU : 0x7C00U;
    }
    else /* (De)normalized number or zero */
    {
        in.u &= round_mask;
        in.f *= magic.f;
        in.u -= round_mask;
        if (in.u > f16infty.u)
        {
            in.u = f16infty.u; /* Clamp to signed infinity if overflowed */
        }

        out = 0xFFFF & static_cast<NativeType>(in.u >> 13); /* Take the bits! */
    }

    out = 0xFFFF & static_cast<NativeType>(out | (sign >> 16));

    return out;
}

template <typename NativeType>
float halfToNativeIeee(NativeType value)
{
    static_assert(sizeof(NativeType) >= 2, "NativeType must be at least 16 bits.");
    static_assert(std::numeric_limits<NativeType>::is_integer, "NativeType must be integral.");
    static_assert(!std::numeric_limits<NativeType>::is_signed, "NativeType must be unsigned.");

    /*
     * https://gist.github.com/rygorous/2144712
     * Public domain, by Fabian "ryg" Giesen
     */
    const internal::Fp32 magic      = {(254U - 15U) << 23};
    const internal::Fp32 was_infnan = {(127U + 16U) << 23};
    internal::Fp32       out;

    out.u = (value & 0x7FFFU) << 13; /* exponent/mantissa bits */
    out.f *= magic.f;                /* exponent adjust */
    if (out.f >= was_infnan.f)       /* make sure Inf/NaN survive */
    {
        out.u |= 255U << 23;
    }
    out.u |= (value & 0x8000U) << 16; /* sign bit */

    return out.f;
}

template <unsigned BitLen>
static typename NativeFloatSelector<BitLen>::int_storage_type toIeee(
    typename NativeFloatSelector<BitLen>::float_type value)
{
    internal::enforceIeee<BitLen>();
    union
    {
        typename NativeFloatSelector<BitLen>::int_storage_type i;
        typename NativeFloatSelector<BitLen>::float_type       f;
    } u;
    static_assert(sizeof(u.f) * 8 == BitLen, "Float type selected does not match BitLen");
    u.f = value;
    return u.i;
}

template <unsigned BitLen>
static typename NativeFloatSelector<BitLen>::float_type toNative(
    typename NativeFloatSelector<BitLen>::int_storage_type value)
{
    internal::enforceIeee<BitLen>();
    union
    {
        typename NativeFloatSelector<BitLen>::int_storage_type i;
        typename NativeFloatSelector<BitLen>::Type             f;
    } u;
    static_assert(sizeof(u.f) * 8 == BitLen, "Float type selected does not match BitLen");
    u.i = value;
    return u.f;
}

}  // namespace IEEE754Converter

template <typename ByteType, std::size_t static_capacity_bits>
class LittleEndianSerializer
{
public:
    static_assert(!std::is_signed<ByteType>::value, "ByteType must be unsigned");
    static_assert(std::is_integral<ByteType>::value, "ByteType must be an integer");

    LittleEndianSerializer(std::vector<ByteType>& inout_buffer, std::size_t bit_offset)
        : _bit_offset(bit_offset)
        , _buf(inout_buffer)
    {
        _buf.resize((static_capacity_bits + 7) / 8);
        // TODO: reserve the capacity needed for the contents of dynamic arrays.
    }

    // Rule of Five
    ~LittleEndianSerializer()                              = default;
    LittleEndianSerializer(const LittleEndianSerializer&)  = delete;
    LittleEndianSerializer(const LittleEndianSerializer&&) = delete;
    LittleEndianSerializer& operator=(const LittleEndianSerializer&) = delete;
    LittleEndianSerializer& operator=(const LittleEndianSerializer&&) = delete;

    std::size_t get_current_bit_length() const
    {
        return _bit_offset;
    }

    void skip_bits(std::size_t bit_length)
    {
        _bit_offset += bit_length;
    }

    std::size_t get_byte_offset() const
    {
        return (_bit_offset + 7) / 8;
    }

    /**
     * Simply adds a sequence of bytes; the current bit offset must be byte-aligned.
     */
    void add_aligned_bytes(const ByteType* x, std::size_t xlen)
    {
        assert(_bit_offset % 8 == 0);
        memcpy(&_buf.data()[get_byte_offset()], x, xlen);
        _bit_offset += xlen * 8;
    }

    void add_aligned_u8(std::uint8_t x)
    {
        assert(_bit_offset % 8 == 0);
        _buf.push_back(x);
        _bit_offset += 8;
    }

    void add_aligned_unsigned(std::uint8_t x, std::size_t xlen)
    {
        add_aligned_bytes(&x, xlen);
    }

    void add_aligned_u16(std::uint16_t x)
    {
        add_aligned_u8(x & 0xFF);
        add_aligned_u8((x >> 8) & 0xFF);
    }

    void add_aligned_u32(std::uint32_t x)
    {
        add_aligned_u16(x & 0xFFFF);
        add_aligned_u16((x >> 16) & 0xFFFF);
    }

    void add_aligned_u64(std::uint64_t x)
    {
        add_aligned_u32(x & 0xFFFFFFFF);
        add_aligned_u32((x >> 32) & 0xFFFFFFFF);
    }

    void add_aligned_i8(std::int8_t x)
    {
        add_aligned_u8(static_cast<std::uint8_t>(x));
    }

    void add_aligned_i16(std::int16_t x)
    {
        add_aligned_u16(static_cast<std::uint16_t>(x));
    }

    void add_aligned_i32(std::int32_t x)
    {
        add_aligned_u32(static_cast<std::uint32_t>(x));
    }

    void add_aligned_i64(std::int64_t x)
    {
        add_aligned_u64(static_cast<std::uint64_t>(x));
    }

    void add_aligned_f16(float x)
    {
        union
        {
            std::uint16_t as_int;
            std::uint8_t as_bytes[2];
        } native_value;
        
        native_value.as_int = IEEE754Conversion::halfToNativeIeee<std::uint16_t>(x);
        add_aligned_bytes(native_value.as_bytes, 2);
    }

    void add_aligned_f32(float x)
    {
        union
        {
            std::uint32_t as_int;
            std::uint8_t as_bytes[4];
        } native_value;
        
        native_value.as_int = IEEE754Conversion::toIeee<32>(x);
        add_aligned_bytes(native_value.as_bytes, 4);
    }

    void add_aligned_f64(double x)
    {
        union
        {
            std::uint64_t as_int;
            std::uint8_t as_bytes[8];
        } native_value;
        
        native_value.as_int = IEEE754Conversion::toIeee<64>(x);
        add_aligned_bytes(native_value.as_bytes, 8);
    }

private:
    std::size_t            _bit_offset;
    std::vector<ByteType>& _buf;
};

}  // namespace support
}  // namespace nunavut

#endif  // NUNAVUT_SUPPORT_HPP_INCLUDED
