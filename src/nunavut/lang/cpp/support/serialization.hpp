/*
 *
 * UAVCAN serialization support routines.                                                                     +-+ +-+
 *                                                                                                            | | | |
 *                                                                                                            \  -  /
 *                                                                                                              ---
 *                                                                                                               o
 * +------------------------------------------------------------------------------------------------------------------+
 */

#ifndef NUNAVUT_SUPPORT_HPP_INCLUDED
#define NUNAVUT_SUPPORT_HPP_INCLUDED

#include <cstdint>
#include <algorithm>
#include <vector>

namespace nunavut
{
namespace support
{
/**
 * Copy aligned bits from a byte buffer to another byte buffer using arbitrary alignment.
 *
 * @param  src              The byte buffer to copy from.
 * @param  dst              The byte buffer to copy data into.
 * @param  dst_offset_bits  The offset, in bits, from the start of the dst array to
 *                          start writing to.
 * @param  length_bits      The total length of bits to copy. The caller must ensure
 *                          that the size of src and dst are >= this value.
 *
 * @return The number of bits copied.
 */
template <typename SizeType, typename ByteType>
SizeType copyBitsAlignedToUnaligned(const ByteType* const  src,
                                    std::vector<ByteType>& dst,
                                    const SizeType         dst_offset_bits,
                                    const SizeType         length_bits)
{
    if (nullptr == src || length_bits == 0)
    {
        return 0;
    }
    constexpr SizeType bits_in_SizeType = sizeof(ByteType) * 8U;
    SizeType           bits_copied      = 0;
    SizeType           offset_bits      = dst_offset_bits;
    const SizeType     local_offset     = dst_offset_bits % bits_in_SizeType;
    do
    {
        SizeType       current_byte       = offset_bits / bits_in_SizeType;
        const SizeType bits_from_src_byte = bits_in_SizeType - local_offset;
        dst[current_byte] &= static_cast<ByteType>(0xFF >> bits_from_src_byte);
        dst[current_byte] |= static_cast<ByteType>(src[current_byte] << local_offset);
        offset_bits += bits_in_SizeType;
        bits_copied += std::min(length_bits, bits_from_src_byte);
        if (offset_bits < length_bits)
        {
            dst[current_byte] |= static_cast<ByteType>(src[offset_bits / bits_in_SizeType] >> bits_from_src_byte);
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

}  // namespace support
}  // namespace nunavut

#endif  // NUNAVUT_SUPPORT_HPP_INCLUDED
