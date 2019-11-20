/*
 * Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 */
#ifndef NUNAVUT_SUPPORT_HPP_INCLUDED
#define NUNAVUT_SUPPORT_HPP_INCLUDED

#include <cstdint>
#include <algorithm>

namespace nunavut
{
/**
 * Copy aligned bits from a byte array to another byte array using arbitrary alignment.
 *
 * @param  src              The byte array to copy from.
 * @param  dst              The byte array to copy data into.
 * @param  dst_offset_bits  The offset, in bits, from the start of the dst array to
 *                          start writing to.
 * @param  length_bits      The total length of bits to copy. The caller must ensure
 *                          that the size of src and dst are >= this value.
 *
 * @return The number of bits copied.
 */
template <typename SIZE_TYPE, typename BYTE_TYPE>
SIZE_TYPE copyBitsAlignedToUnaligned(const BYTE_TYPE* const src,
                                     BYTE_TYPE* const       dst,
                                     const SIZE_TYPE        dst_offset_bits,
                                     const SIZE_TYPE        length_bits)
{
    if (nullptr == src || nullptr == dst || length_bits == 0)
    {
        return 0;
    }
    constexpr SIZE_TYPE bits_in_size_type = sizeof(BYTE_TYPE) * 8U;
    SIZE_TYPE           bits_copied       = 0;
    SIZE_TYPE           offset_bits       = dst_offset_bits;
    const SIZE_TYPE     local_offset      = dst_offset_bits % bits_in_size_type;
    do
    {
        SIZE_TYPE       current_byte       = offset_bits / bits_in_size_type;
        const SIZE_TYPE bits_from_src_byte = bits_in_size_type - local_offset;
        dst[current_byte] &= static_cast<BYTE_TYPE>(0xFF >> bits_from_src_byte);
        dst[current_byte] |= static_cast<BYTE_TYPE>(src[current_byte] << local_offset);
        offset_bits += bits_in_size_type;
        bits_copied += std::min(length_bits, bits_from_src_byte);
        if (offset_bits < length_bits)
        {
            dst[current_byte] |= static_cast<BYTE_TYPE>(src[offset_bits / bits_in_size_type] >> bits_from_src_byte);
            bits_copied += local_offset;
        }
        else
        {
            // we don't need to reevaluate the while condition.
            break;
        }
    } while (true);

    return bits_copied;
}

}  // namespace nunavut

#endif  // NUNAVUT_SUPPORT_HPP_INCLUDED
