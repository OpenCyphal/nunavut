/*
 * Copyright (c) 2022 UAVCAN Development Team.
 * Authors: Pavel Pletenev <cpp.create@gmail.com>
 * This software is distributed under the terms of the MIT License.
 *
 * Tests of serialization
 */

#include "test_helpers.hpp"
#include "nunavut/support/serialization.hpp"


TEST(BitSpan, Constructor) {
    uint8_t srcVar = 0x8F;
    std::array<uint8_t,5> srcArray{ 1, 2, 3, 4, 5 };
    {
        nunavut::support::bitspan sp{{&srcVar, 1}};
        ASSERT_EQ(sp.size(), 1U*8U);
    }
    {
        nunavut::support::bitspan sp{srcArray};
        ASSERT_EQ(sp.size(), 5U*8U);
    }
    const uint8_t csrcVar = 0x8F;
    const std::array<const uint8_t,5> csrcArray{ 1, 2, 3, 4, 5 };
    {
        nunavut::support::const_bitspan sp{{&csrcVar, 1}};
        ASSERT_EQ(sp.size(), 1U*8U);
    }
    {
        nunavut::support::const_bitspan sp{csrcArray};
        ASSERT_EQ(sp.size(), 5U*8U);
    }
}

TEST(BitSpan, SetZeros)
{
    std::array<uint8_t,2> srcArray{ 0xAA, 0xFF };
    nunavut::support::bitspan sp(srcArray, 10U);
    auto res = sp.padAndMoveToAlignment(8U);
    ASSERT_TRUE(res) << "Error was " << res.error();
    ASSERT_EQ(srcArray[1], 0x03);
}

TEST(BitSpan, Subspan)
{
    std::array<uint8_t,2> srcArray{ 0xAA, 0xFF };
    nunavut::support::bitspan sp(srcArray);
    auto res = sp.subspan(0U, 8U);
    ASSERT_TRUE(res) << "Error was " << res.error();
    ASSERT_EQ(0U, res.value().offset());
    ASSERT_EQ(8U, res.value().size());
    ASSERT_EQ(0xAAU, res.value().aligned_ref());

    res = sp.subspan(8U, 8U);
    ASSERT_TRUE(res) << "Error was " << res.error();
    ASSERT_EQ(0U, res.value().offset());
    ASSERT_EQ(8U, res.value().size());
    ASSERT_EQ(0xFFU, res.value().aligned_ref());

    res = sp.subspan(12U, 4U);
    ASSERT_TRUE(res) << "Error was " << res.error();
    ASSERT_EQ(4U, res.value().offset());
    ASSERT_EQ(4U, res.value().size());
    ASSERT_EQ(0xFFU, res.value().aligned_ref());

    res = sp.subspan(0U, 32U);
    ASSERT_FALSE(res);
    ASSERT_EQ(nunavut::support::Error::SERIALIZATION_BUFFER_TOO_SMALL, res.error());
}

TEST(BitSpan, AlignedPtr) {
    std::array<uint8_t,5> srcArray{ 1, 2, 3, 4, 5 };
    {
        auto actualPtr = nunavut::support::bitspan(srcArray).aligned_ptr();
        ASSERT_EQ(actualPtr, srcArray.data());
    }
    {
        auto actualPtr = nunavut::support::bitspan(srcArray, 1).aligned_ptr();
        ASSERT_EQ(actualPtr, srcArray.data());
    }
    {
        auto actualPtr = nunavut::support::bitspan(srcArray, 5).aligned_ptr();
        ASSERT_EQ(actualPtr, srcArray.data());
    }
    {
        auto actualPtr = nunavut::support::bitspan(srcArray, 7).aligned_ptr();
        ASSERT_EQ(actualPtr, srcArray.data());
    }
    {
        auto actualPtr = nunavut::support::bitspan(srcArray).aligned_ptr(8);
        ASSERT_EQ(actualPtr, &srcArray[1]);
    }
}

TEST(BitSpan, TestSize) {
    std::array<uint8_t,5> src{ 1, 2, 3, 4, 5 };
    {
        nunavut::support::bitspan sp{src};
        ASSERT_EQ(sp.size(), 5U*8U);
    }
    {
        nunavut::support::bitspan sp{src, 1};
        ASSERT_EQ(sp.size(), 5U*8U - 1U);
    }
    std::array<const uint8_t,5> csrc{ 1, 2, 3, 4, 5 };
    {
        nunavut::support::const_bitspan sp{csrc};
        ASSERT_EQ(sp.size(), 5U*8U);
    }
    {
        nunavut::support::const_bitspan sp{csrc, 1};
        ASSERT_EQ(sp.size(), 5U*8U - 1U);
    }
}

TEST(BitSpan, CopyBits) {
    std::array<const uint8_t,5> src{ 1, 2, 3, 4, 5 };
    std::array<uint8_t,6> dst{};
    memset(dst.data(), 0, dst.size());

    nunavut::support::const_bitspan{src}.copyTo(nunavut::support::bitspan{dst});
    for(size_t i = 0; i < src.size(); ++i)
    {
        ASSERT_EQ(src[i], dst[i]);
    }
}

TEST(BitSpan, CopyBitsWithAlignedOffset) {
    std::array<const uint8_t,5> src{ 0x11, 0x22, 0x33, 0x44, 0x55 };
    std::array<uint8_t,6> dst{};
    memset(dst.data(), 0, dst.size());

    nunavut::support::const_bitspan{src, 8}.copyTo(nunavut::support::bitspan{dst});

    for(size_t i = 0; i < src.size() - 1; ++i)
    {
        ASSERT_EQ(src[i + 1], dst[i]);
    }
    ASSERT_EQ(0, dst[dst.size() - 1]);

    memset(dst.data(), 0, dst.size());

    nunavut::support::const_bitspan{src, 0}.copyTo(nunavut::support::bitspan{dst, 8});

    for(size_t i = 0; i < src.size() - 1; ++i)
    {
        ASSERT_EQ(src[i], dst[i+1]);
    }
    ASSERT_EQ(0, dst[0]);

    memset(dst.data(), 0xA, dst.size());

    nunavut::support::const_bitspan{src, 0}.copyTo(nunavut::support::bitspan{dst, 8}, 3U*8U+4U);

    for(size_t i = 0; i < src.size() - 2; ++i)
    {
        ASSERT_EQ(src[i], dst[i+1]);
    }
    EXPECT_EQ(src[3] & 0x0F, dst[4]);
    ASSERT_EQ(0xA, dst[0]);
}

TEST(BitSpan, CopyBitsWithAlignedOffsetNonByteLen) {
    std::array<const uint8_t,7> src{ 0x0, 0x0, 0x11, 0x22, 0x33, 0x44, 0x55 };
    std::array<uint8_t,1> dst{};
    memset(dst.data(), 0, dst.size());

    nunavut::support::const_bitspan({src}, 2U * 8U).copyTo(nunavut::support::bitspan{dst}, 4);
    ASSERT_EQ(0x1U, dst[0]);

    nunavut::support::const_bitspan({src}, 3U * 8U).copyTo(nunavut::support::bitspan{dst}, 4);
    ASSERT_EQ(0x2U, dst[0]);
}

TEST(BitSpan, CopyBitsWithUnalignedOffset){
    std::array<const uint8_t,6> src{ 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA };
    std::array<uint8_t,6> dst{};
    memset(dst.data(), 0, dst.size());

    nunavut::support::const_bitspan{src, 1}.copyTo(
        nunavut::support::bitspan{dst, 0}, (src.size()-1)*8U);
    for(size_t i = 0; i < src.size() - 1; ++i)
    {
        ASSERT_EQ(0x55, dst[i]);
    }
    ASSERT_EQ(0x00, dst[dst.size() - 1]);

    memset(dst.data(), 0, dst.size());

    nunavut::support::const_bitspan{src}.copyTo(
        nunavut::support::bitspan{dst, 1}, 8U * (src.size() - 1));

    for(size_t i = 0; i < src.size() - 1; ++i)
    {
        ASSERT_EQ((i == 0) ? 0x54 : 0x55, dst[i]);
    }
    ASSERT_EQ(0x54, dst[0]);
}


TEST(BitSpan, SaturateBufferFragmentBitLength)
{
    using namespace nunavut::support;
    std::array<const uint8_t, 4> data{};
    ASSERT_EQ(32U, const_bitspan(data,  0U).saturateBufferFragmentBitLength(32));
    ASSERT_EQ(31U, const_bitspan(data,  1U).saturateBufferFragmentBitLength(32));
    ASSERT_EQ(16U, const_bitspan(data,  0U).saturateBufferFragmentBitLength(16));
    ASSERT_EQ(15U, const_bitspan(data, 17U).saturateBufferFragmentBitLength(24));
    ASSERT_EQ(0U,  const_bitspan({data.data(), 2}, 24U).saturateBufferFragmentBitLength(24));
}


TEST(BitSpan, GetBits)
{
    std::array<const uint8_t, 16> src{ 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF };
    std::array<uint8_t, 6> dst{};
    memset(dst.data(), 0xAA, dst.size());
    nunavut::support::const_bitspan{{src.data(), 6U}, 0}.getBits(dst, 0);
    ASSERT_EQ(0xAA, dst[0]);   // no bytes copied
    ASSERT_EQ(0xAA, dst[1]);
    ASSERT_EQ(0xAA, dst[2]);
    ASSERT_EQ(0xAA, dst[3]);
    ASSERT_EQ(0xAA, dst[4]);
    ASSERT_EQ(0xAA, dst[5]);

    nunavut::support::const_bitspan{{src.data(), 0U}, 0}.getBits(dst, 4U*8U);
    ASSERT_EQ(0x00, dst[0]);   // all bytes zero-extended
    ASSERT_EQ(0x00, dst[1]);
    ASSERT_EQ(0x00, dst[2]);
    ASSERT_EQ(0x00, dst[3]);
    ASSERT_EQ(0xAA, dst[4]);
    ASSERT_EQ(0xAA, dst[5]);

    memset(dst.data(), 0xAA, dst.size());
    nunavut::support::const_bitspan{{src.data(), 6}, 6U*8U}.getBits(dst, 4U*8U);
    ASSERT_EQ(0x00, dst[0]);   // all bytes zero-extended
    ASSERT_EQ(0x00, dst[1]);
    ASSERT_EQ(0x00, dst[2]);
    ASSERT_EQ(0x00, dst[3]);
    ASSERT_EQ(0xAA, dst[4]);
    ASSERT_EQ(0xAA, dst[5]);

    memset(dst.data(), 0xAA, dst.size());
    nunavut::support::const_bitspan{{src.data(), 6U}, 5U*8U}.getBits(dst, 4U*8U);
    ASSERT_EQ(0x66, dst[0]);   // one byte copied
    ASSERT_EQ(0x00, dst[1]);   // the rest are zero-extended
    ASSERT_EQ(0x00, dst[2]);
    ASSERT_EQ(0x00, dst[3]);
    ASSERT_EQ(0xAA, dst[4]);
    ASSERT_EQ(0xAA, dst[5]);

    memset(dst.data(), 0xAA, dst.size());
    nunavut::support::const_bitspan{{src.data(), 6}, 4U * 8U + 4U}.getBits(dst, 4U*8U);
    ASSERT_EQ(0x65, dst[0]);   // one-and-half bytes are copied
    ASSERT_EQ(0x06, dst[1]);   // the rest are zero-extended
    ASSERT_EQ(0x00, dst[2]);
    ASSERT_EQ(0x00, dst[3]);
    ASSERT_EQ(0xAA, dst[4]);
    ASSERT_EQ(0xAA, dst[5]);

    memset(dst.data(), 0xAA, dst.size());
    nunavut::support::const_bitspan{{src.data(), 7}, 4U}.getBits(dst, 4U*8U);
    ASSERT_EQ(0x21, dst[0]);   // all bytes are copied offset by half
    ASSERT_EQ(0x32, dst[1]);
    ASSERT_EQ(0x43, dst[2]);
    ASSERT_EQ(0x54, dst[3]);
    ASSERT_EQ(0xAA, dst[4]);
    ASSERT_EQ(0xAA, dst[5]);

    memset(dst.data(), 0xAA, dst.size());
    nunavut::support::const_bitspan{{src.data(), 7}, 4U}.getBits(dst, 3U*8U + 4U);
    ASSERT_EQ(0x21, dst[0]);   // 28 bits are copied
    ASSERT_EQ(0x32, dst[1]);
    ASSERT_EQ(0x43, dst[2]);
    ASSERT_EQ(0x04, dst[3]);   // the last bits of the last byte are zero-padded out
    ASSERT_EQ(0xAA, dst[4]);
    ASSERT_EQ(0xAA, dst[5]);
}

TEST(BitSpan, SetIxx_neg1)
{
    uint8_t data[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    auto res = nunavut::support::bitspan{data}.setIxx(-1, sizeof(data) * 8);
    ASSERT_TRUE(res);
    for (size_t i = 0; i < sizeof(data); ++i)
    {
        ASSERT_EQ(0xFF, data[i]);
    }
}

TEST(BitSpan, SetIxx_neg255)
{
    uint8_t data[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    nunavut::support::bitspan{data}.setIxx(-255, sizeof(data) * 8);
    ASSERT_EQ(0xFF, data[1]);
    ASSERT_EQ(0x01, data[0]);
}

TEST(BitSpan, SetIxx_neg255_tooSmall)
{
    uint8_t data[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    nunavut::support::bitspan{data}.setIxx(-255, sizeof(data) * 1);
    ASSERT_EQ(0x00, data[1]);
    ASSERT_EQ(0x01, data[0]);
}

TEST(BitSpan, SetIxx_bufferOverflow)
{
    uint8_t buffer[] = {0x00, 0x00, 0x00};

    auto rc = nunavut::support::bitspan{{buffer, 3U}, 2U*8U}.setIxx(0xAA, 8);
    ASSERT_TRUE(rc);
    ASSERT_EQ(0xAA, buffer[2]);
    rc = nunavut::support::bitspan{{buffer, 2U}, 2U*8U}.setIxx(0xAA, 8);
    ASSERT_FALSE(rc);
    ASSERT_EQ(nunavut::support::Error::SERIALIZATION_BUFFER_TOO_SMALL, rc.error());
    ASSERT_EQ(0xAA, buffer[2]);
}

// +--------------------------------------------------------------------------+
// | nunavut[Get|Set]Bit
// +--------------------------------------------------------------------------+

TEST(BitSpan, SetBit)
{
    uint8_t buffer[] = {0x00};
    nunavut::support::bitspan sp{{buffer, sizeof(buffer)}};

    auto res = sp.setBit(true);
    ASSERT_TRUE(res);
    ASSERT_EQ(0x01, buffer[0]);
    res = sp.setBit(false);
    ASSERT_TRUE(res);
    ASSERT_EQ(0x00, buffer[0]);
    res = sp.setBit(true);
    ASSERT_TRUE(res);
    res = sp.at_offset(1).setBit(true);
    ASSERT_TRUE(res);
    ASSERT_EQ(0x03, buffer[0]);
}

TEST(BitSpan, SetBit_bufferOverflow)
{
    uint8_t buffer[] = {0x00, 0x00};

    auto res = nunavut::support::bitspan{{buffer, 1U}, 8}.setBit(true);

    ASSERT_FALSE(res.has_value());
    ASSERT_EQ(nunavut::support::Error::SERIALIZATION_BUFFER_TOO_SMALL, res.error());
    ASSERT_EQ(0x00, buffer[1]);
}

TEST(BitSpan, GetBit)
{
    const uint8_t buffer[] = {0x01};
    nunavut::support::const_bitspan sp{{buffer, 1U}, 0};
    ASSERT_EQ(true, sp.getBit());
    ASSERT_EQ(false, sp.at_offset(1).getBit());
}

// +--------------------------------------------------------------------------+
// | nunavutGetU8
// +--------------------------------------------------------------------------+

TEST(BitSpan, GetU8)
{
    const uint8_t data[] = {0xFE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    ASSERT_EQ(0xFE, nunavut::support::const_bitspan(data, 0).getU8(8U));
}

TEST(BitSpan, GetU8_tooSmall)
{
    const uint8_t data[] = {0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    ASSERT_EQ(0x7F, nunavut::support::const_bitspan(data, 0).getU8(7U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetU16
// +--------------------------------------------------------------------------+

TEST(BitSpan, GetU16)
{
    const uint8_t data[] = {0xAA, 0xAA};
    ASSERT_EQ(0xAAAAU, nunavut::support::const_bitspan(data, 0).getU16(16U));
}

TEST(BitSpan, GetU16_tooSmall)
{
    const uint8_t data[] = {0xAA, 0xAA};
    ASSERT_EQ(0x0055U, nunavut::support::const_bitspan(data, 9).getU16(16U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetU32
// +--------------------------------------------------------------------------+

TEST(BitSpan, GetU32)
{
    {
        const uint8_t data[] = {0xAA, 0xAA, 0xAA, 0xAA};
        ASSERT_EQ(0xAAAAAAAAU, nunavut::support::const_bitspan(data, 0).getU32(32U));
    }
    {
        const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF};
        ASSERT_EQ(0xFFFFFFFFU, nunavut::support::const_bitspan(data, 0).getU32(32U));
    }
}

TEST(BitSpan, GetU32_tooSmall)
{
    const uint8_t data[] = {0xAA, 0xAA, 0xAA, 0xAA};
    ASSERT_EQ(0x00555555U, nunavut::support::const_bitspan(data, 9).getU32(32U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetU64
// +--------------------------------------------------------------------------+

TEST(BitSpan, GetU64)
{
    {
        const uint8_t data[] = {0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA};
        ASSERT_EQ(0xAAAAAAAAAAAAAAAAU, nunavut::support::const_bitspan(data, 0).getU64(64U));
    }
    {
        const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
        ASSERT_EQ(0xFFFFFFFFFFFFFFFFU, nunavut::support::const_bitspan(data, 0).getU64(64U));
    }
}

TEST(BitSpan, GetU64_tooSmall)
{
    const uint8_t data[] = {0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA};
    ASSERT_EQ(0x0055555555555555U, nunavut::support::const_bitspan(data, 9).getU64(64U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetI8
// +--------------------------------------------------------------------------+

TEST(BitSpan, GetI8)
{
    const uint8_t data[] = {0xFF};
    ASSERT_EQ(-1, nunavut::support::const_bitspan(data, 0).getI8(8U));
}

TEST(BitSpan, GetI8_tooSmall)
{
    const uint8_t data[] = {0xFF};
    ASSERT_EQ(127, nunavut::support::const_bitspan(data, 1).getI8(8U));
}

TEST(BitSpan, GetI8_tooSmallAndNegative)
{
    const uint8_t data[] = {0xFF};
    ASSERT_EQ(-1, nunavut::support::const_bitspan(data, 0).getI8(4U));
}

TEST(BitSpan, GetI8_zeroDataLen)
{
    const uint8_t data[] = {0xFF};
    ASSERT_EQ(0, nunavut::support::const_bitspan(data, 0).getI8(0U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetI16
// +--------------------------------------------------------------------------+

TEST(BitSpan, GetI16)
{
    const uint8_t data[] = {0xFF, 0xFF};
    ASSERT_EQ(-1, nunavut::support::const_bitspan(data, 0).getI16(16U));
}

TEST(BitSpan, GetI16_tooSmall)
{
    const uint8_t data[] = {0xFF, 0xFF};
    ASSERT_EQ(32767, nunavut::support::const_bitspan(data, 1).getI16(16U));
}

TEST(BitSpan, GetI16_tooSmallAndNegative)
{
    const uint8_t data[] = {0xFF, 0xFF};
    ASSERT_EQ(-1, nunavut::support::const_bitspan(data, 0).getI16(12U));
}

TEST(BitSpan, GetI16_zeroDataLen)
{
    const uint8_t data[] = {0xFF, 0xFF};
    ASSERT_EQ(0, nunavut::support::const_bitspan(data, 0).getI16(0U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetI32
// +--------------------------------------------------------------------------+

TEST(BitSpan, GetI32)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF};
    ASSERT_EQ(-1, nunavut::support::const_bitspan(data, 0).getI32(32U));
}

TEST(BitSpan, GetI32_tooSmall)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF};
    ASSERT_EQ(2147483647, nunavut::support::const_bitspan(data, 1).getI32(32U));
}

TEST(BitSpan, GetI32_tooSmallAndNegative)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF};
    ASSERT_EQ(-1, nunavut::support::const_bitspan(data, 0).getI32(20U));
}

TEST(BitSpan, GetI32_zeroDataLen)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF};
    ASSERT_EQ(0, nunavut::support::const_bitspan(data, 0).getI32(0U));
}

// +--------------------------------------------------------------------------+
// | nunavutGetI64
// +--------------------------------------------------------------------------+

TEST(BitSpan, GetI64)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    ASSERT_EQ(-1, nunavut::support::const_bitspan(data, 0).getI64(64U));
}

TEST(BitSpan, GetI64_tooSmall)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    ASSERT_EQ(9223372036854775807, nunavut::support::const_bitspan(data, 1).getI64(64U));
}

TEST(BitSpan, GetI64_tooSmallAndNegative)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    ASSERT_EQ(-1, nunavut::support::const_bitspan(data, 0).getI64(60U));
}

TEST(BitSpan, GetI64_zeroDataLen)
{
    const uint8_t data[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    ASSERT_EQ(0, nunavut::support::const_bitspan(data, 0).getI64(0U));
}

// +--------------------------------------------------------------------------+
// | GetU/I*(8/16/32/64) out of range
// +--------------------------------------------------------------------------+

TEST(BitSpan, GetU8_outofrange)
{
    const uint8_t data[] = {0xFF};
    ASSERT_EQ(0x0U, nunavut::support::const_bitspan(data, 1U * 8U+1).getU8(8U));
}

TEST(BitSpan, GetU16_outofrange)
{
    const uint8_t data[] = {0xFF};
    ASSERT_EQ(0x0U, nunavut::support::const_bitspan(data, 2U * 8U+1).getU16(16U));
}

TEST(BitSpan, GetU32_outofrange)
{
    const uint8_t data[] = {0xFF};
    ASSERT_EQ(0x0U, nunavut::support::const_bitspan(data, 4U * 8U+1).getU32(32U));
}

TEST(BitSpan, GetU64_outofrange)
{
    const uint8_t data[] = {0xFF};
    ASSERT_EQ(0x0U, nunavut::support::const_bitspan(data, 4U * 8U+1).getU64(64U));
}

TEST(BitSpan, GetI8_outofrange)
{
    const uint8_t data[] = {0xFF};
    ASSERT_EQ(0x0, nunavut::support::const_bitspan(data, 1U * 8U+1).getI8(8U));
}

TEST(BitSpan, GetI16_outofrange)
{
    const uint8_t data[] = {0xFF};
    ASSERT_EQ(0x0, nunavut::support::const_bitspan(data, 2U * 8U+1).getI16(16U));
}

TEST(BitSpan, GetI32_outofrange)
{
    const uint8_t data[] = {0xFF};
    ASSERT_EQ(0x0, nunavut::support::const_bitspan(data, 4U * 8U+1).getI32(32U));
}

TEST(BitSpan, GetI64_outofrange)
{
    const uint8_t data[] = {0xFF};
    ASSERT_EQ(0x0, nunavut::support::const_bitspan(data, 4U * 8U+1).getI64(64U));
}

// +--------------------------------------------------------------------------+
// | SetGet(U/I)(8/16/32/64)
// +--------------------------------------------------------------------------+

constexpr static size_t getset_n_tries = 10;

using namespace nunavut::testing;

TEST(BitSpan, SetGetU8)
{
    uint8_t data[getset_n_tries * 64]{0};
    for (size_t i = 0U; i < getset_n_tries; i++)
    {
        auto ref = randU8();
        const auto offset = i * sizeof(ref) * 8U;
        auto rslt = nunavut::support::bitspan({data}, offset).setUxx(ref, 8U);
        ASSERT_TRUE(rslt.has_value()) << "Error was " << rslt.error();
        auto act = nunavut::support::const_bitspan(data, offset).getU8(8U);
        ASSERT_EQ(hex(ref), hex(act)) << i;
    }
}

TEST(BitSpan, SetGetU16)
{
    uint8_t data[getset_n_tries * 64]{0};
    for (size_t i = 0U; i < getset_n_tries; i++)
    {
        auto ref = randU16();
        const auto offset = i * sizeof(ref) * 8U;
        auto rslt = nunavut::support::bitspan({data}, offset).setUxx(ref, 16U);
        ASSERT_TRUE(rslt.has_value()) << "Error was " << rslt.error();
        auto act = nunavut::support::const_bitspan(data, offset).getU16(16U);
        ASSERT_EQ(hex(ref), hex(act)) << i;
    }
}

TEST(BitSpan, SetGetU32)
{
    uint8_t data[getset_n_tries * 64]{0};
    for (size_t i = 0U; i < getset_n_tries; i++)
    {
        auto ref = randU32();
        const auto offset = i * sizeof(ref) * 8U;
        auto rslt = nunavut::support::bitspan({data}, offset).setUxx(ref, 32U);
        ASSERT_TRUE(rslt.has_value()) << "Error was " << rslt.error();
        auto act = nunavut::support::const_bitspan(data, offset).getU32(32U);
        ASSERT_EQ(hex(ref), hex(act)) << i;
    }
}

TEST(BitSpan, SetGetU64)
{
    uint8_t data[getset_n_tries * 64]{0};
    for (size_t i = 0U; i < getset_n_tries; i++)
    {
        auto ref = randU64();
        const auto offset = i * sizeof(ref) * 8U;
        auto rslt = nunavut::support::bitspan({data}, offset).setUxx(ref, 64U);
        ASSERT_TRUE(rslt.has_value()) << "Error was " << rslt.error();
        auto act = nunavut::support::const_bitspan(data, offset).getU64(64U);
        ASSERT_EQ(hex(ref), hex(act)) << i;
    }
}

TEST(BitSpan, SetGetI8)
{
    uint8_t data[getset_n_tries * 64]{0};
    for (size_t i = 0U; i < getset_n_tries; i++)
    {
        auto ref = randI8();
        const auto offset = i * sizeof(ref) * 8U;
        auto rslt = nunavut::support::bitspan({data}, offset).setIxx(ref, 8U);
        ASSERT_TRUE(rslt.has_value()) << "Error was " << rslt.error();
        auto act = nunavut::support::const_bitspan(data, offset).getI8(8U);
        ASSERT_EQ(hex(ref), hex(act)) << i;
    }
}

TEST(BitSpan, SetGetI16)
{
    uint8_t data[getset_n_tries * 64]{0};
    for (size_t i = 0U; i < getset_n_tries; i++)
    {
        auto ref = randI16();
        const auto offset = i * sizeof(ref) * 8U;
        auto rslt = nunavut::support::bitspan({data}, offset).setIxx(ref, 16U);
        ASSERT_TRUE(rslt.has_value()) << "Error was " << rslt.error();
        auto act = nunavut::support::const_bitspan(data, offset).getI16(16U);
        ASSERT_EQ(hex(ref), hex(act)) << i;
    }
}

TEST(BitSpan, SetGetI32)
{
    uint8_t data[getset_n_tries * 64]{0};
    for (size_t i = 0U; i < getset_n_tries; i++)
    {
        auto ref = randI32();
        const auto offset = i * sizeof(ref) * 8U;
        auto rslt = nunavut::support::bitspan({data}, offset).setIxx(ref, 32U);
        ASSERT_TRUE(rslt.has_value()) << "Error was " << rslt.error();
        auto act = nunavut::support::const_bitspan(data, offset).getI32(32U);
        ASSERT_EQ(hex(ref), hex(act)) << i;
    }
}

TEST(BitSpan, SetGetI64)
{
    uint8_t data[getset_n_tries * 64]{0};
    for (size_t i = 0U; i < getset_n_tries; i++)
    {
        auto ref = randI64();
        const auto offset = i * sizeof(ref) * 8U;
        auto rslt = nunavut::support::bitspan({data}, offset).setIxx(ref, 64U);
        ASSERT_TRUE(rslt.has_value()) << "Error was " << rslt.error();
        auto act = nunavut::support::const_bitspan(data, offset).getI64(64U);
        ASSERT_EQ(hex(ref), hex(act)) << i;
    }
}

// +--------------------------------------------------------------------------+
// | nunavut::support::float16Pack
// +--------------------------------------------------------------------------+

TEST(BitSpan, Float16Pack)
{
    // Comparing to NumPy calculated values

    uint16_t packed_float = nunavut::support::float16Pack(3.14f);
    // hex(int.from_bytes(np.array([np.float16('3.14')]).tobytes(), 'little'))
    ASSERT_EQ(0x4248, packed_float) << "Failed to serialize 3.14f";

    packed_float = nunavut::support::float16Pack(-3.14f);
    // hex(int.from_bytes(np.array([-np.float16('3.14')]).tobytes(), 'little'))
    ASSERT_EQ(0xC248, packed_float) << "Failed to serialize -3.14f";

    packed_float = nunavut::support::float16Pack(65536.141592653589793238462643383279f);
    // hex(int.from_bytes(np.array([np.float16('65536.141592653589793238462643383279')]).tobytes(), 'little'))
    ASSERT_EQ(0x7C00, packed_float) << "Failed to serialize 65536.141592653589793238462643383279f";

    packed_float = nunavut::support::float16Pack(-65536.141592653589793238462643383279f);
    // hex(int.from_bytes(np.array([np.float16('65536.141592653589793238462643383279')]).tobytes(), 'little'))
    ASSERT_EQ(0xFC00, packed_float) << "Failed to serialize -65536.141592653589793238462643383279f";
}

TEST(BitSpan, Float16Pack_NAN_cmath)
{
    uint16_t packed_float = nunavut::support::float16Pack(NAN);
    ASSERT_EQ(0x7C00U, (0x7C00UL & packed_float)) << "Exponent bits were not all set for NAN.";
    ASSERT_EQ(0x0000U, (0x8000UL & packed_float)) << "NAN sign bit was negative.";

    packed_float = nunavut::support::float16Pack(-NAN);
    ASSERT_EQ(0x7C00U, (0x7C00UL & packed_float)) << "Exponent bits were not all set for -NAN.";
    ASSERT_EQ(0x8000U, (0x8000UL & packed_float)) << "-NAN sign bit was positive.";
}

TEST(BitSpan, Float16Pack_infinity)
{
    uint16_t packed_float = nunavut::support::float16Pack(INFINITY);
    ASSERT_EQ(0x0000, (0x03FF & packed_float)) << "Mantessa bits were not 0 for INFINITY.";
    ASSERT_EQ(0x7C00, (0x7C00 & packed_float)) << "INFINITY did not set bits G5 - G4+w";
    ASSERT_EQ(0x0000, (0x8000 & packed_float)) << "INFINITY sign bit was negative.";

    packed_float = nunavut::support::float16Pack(-INFINITY);
    ASSERT_EQ(0x0000, (0x03FF & packed_float)) << "Mantessa bits were not 0 for -INFINITY.";
    ASSERT_EQ(0x7C00, (0x7C00 & packed_float)) << "-INFINITY did not set bits G5 - G4+w";
    ASSERT_EQ(0x8000, (0x8000 & packed_float)) << "-INFINITY sign bit was positive.";
}

TEST(BitSpan, Float16Pack_zero)
{
    uint16_t packed_float = nunavut::support::float16Pack(0.0f);
    ASSERT_EQ(0x0, (0x03FF & packed_float)) << "0.0f had bits in significand.";
    ASSERT_EQ(0x0, (0x7C00 & packed_float)) << "0.0f had bits in exponent.";
    ASSERT_EQ(0x0, (0x8000 & packed_float)) << "0.0f sign bit was negative.";

    packed_float = nunavut::support::float16Pack(-0.0f);
    ASSERT_EQ(0x0000, (0x03FF & packed_float)) << "-0.0f had bits in significand.";
    ASSERT_EQ(0x0000, (0x7C00 & packed_float)) << "-0.0f had bits in exponent.";
    ASSERT_EQ(0x8000, (0x8000 & packed_float)) << "-0.0f sign bit was not negative.";
}

// +--------------------------------------------------------------------------+
// | nunavut::support::float16Unpack
// +--------------------------------------------------------------------------+

TEST(BitSpan, Float16Unpack)
{
    // >>> hex(int.from_bytes(np.array([-np.float16('3.14')]).tobytes(), 'little'))
    // '0xc248'
    ASSERT_TRUE(CompareFloatsNear(-3.14f, nunavut::support::float16Unpack(0xC248), 0.001f));
    // >>> hex(int.from_bytes(np.array([np.float16('3.14')]).tobytes(), 'little'))
    // '0x4248'
    ASSERT_TRUE(CompareFloatsNear(3.14f, nunavut::support::float16Unpack(0x4248), 0.001f));
    // >>> hex(int.from_bytes(np.array([np.float16('nan')]).tobytes(), 'little'))
    // '0x7e00'
    ASSERT_TRUE(std::isnan(nunavut::support::float16Unpack(0x7e00)));
    // >>> hex(int.from_bytes(np.array([-np.float16('nan')]).tobytes(), 'little'))
    // '0xfe00'
    ASSERT_TRUE(std::isnan(nunavut::support::float16Unpack(0xfe00)));
    // >>> hex(int.from_bytes(np.array([np.float16('infinity')]).tobytes(), 'little'))
    // '0x7c00'
    ASSERT_FLOAT_EQ(std::numeric_limits<float>::infinity(), nunavut::support::float16Unpack(0x7c00));
    // >>> hex(int.from_bytes(np.array([-np.float16('infinity')]).tobytes(), 'little'))
    // '0xfc00'
    ASSERT_FLOAT_EQ(-std::numeric_limits<float>::infinity(), nunavut::support::float16Unpack(0xfc00));
}

TEST(BitSpan, Float16Unpack_INFINITY)
{
    ASSERT_FLOAT_EQ(std::numeric_limits<float>::infinity(), nunavut::support::float16Unpack(0x7C00));
    ASSERT_FLOAT_EQ(-std::numeric_limits<float>::infinity(), nunavut::support::float16Unpack(0xFC00));
}

// +--------------------------------------------------------------------------+
// | nunavut::support::float16Pack/Unpack
// +--------------------------------------------------------------------------+

static bool helperPackUnpack(const float source_value, uint16_t compare_mask, size_t iterations)
{
    const uint16_t packed = nunavut::support::float16Pack(source_value);
    uint16_t repacked = packed;
    //char message_buffer[128];

    for(size_t i = 0; i < iterations; ++i)
    {
        repacked = nunavut::support::float16Pack(nunavut::support::float16Unpack(repacked));
        EXPECT_EQ(packed & compare_mask, repacked & compare_mask)
            << "source_value=" << source_value << "compare_mask=" << std::hex << compare_mask << "i=" << i;
        if(::testing::Test::HasFailure()) return false;
    }
    return true;
}

/**
 * Test pack/unpack stability.
 */
TEST(BitSpan, Float16PackUnpack)
{
    const uint32_t signalling_nan_bits = 0x7F800000U | 0x200000U;
    const uint32_t signalling_negative_nan_bits = 0xFF800000U | 0x200000U;

    ASSERT_TRUE(helperPackUnpack(3.14f, 0xFFFF, 10));
    ASSERT_TRUE(helperPackUnpack(-3.14f, 0xFFFF, 10));
    ASSERT_TRUE(helperPackUnpack(65536.141592653589793238462643383279f, 0xFFFF, 100));
    ASSERT_TRUE(helperPackUnpack(-65536.141592653589793238462643383279f, 0xFFFF, 100));

    ASSERT_TRUE(helperPackUnpack(NAN, 0xFE00, 10));
    ASSERT_TRUE(helperPackUnpack(-NAN, 0xFE00, 10));
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wstrict-aliasing"
    ASSERT_TRUE(helperPackUnpack(*(reinterpret_cast<const float*>(&signalling_nan_bits)), 0xFF00, 10));
    ASSERT_TRUE(helperPackUnpack(*(reinterpret_cast<const float*>(&signalling_negative_nan_bits)), 0xFF00, 10));
#pragma GCC diagnostic pop
    ASSERT_TRUE(helperPackUnpack(std::numeric_limits<float>::infinity(), 0xFF00, 10));
    ASSERT_TRUE(helperPackUnpack(-std::numeric_limits<float>::infinity(), 0xFF00, 10));
}

TEST(BitSpan, Float16PackUnpack_NAN)
{
    ASSERT_TRUE(std::isnan(nunavut::support::float16Unpack(nunavut::support::float16Pack(NAN))));
}

// +--------------------------------------------------------------------------+
// | testNunavutSetF16
// +--------------------------------------------------------------------------+

TEST(BitSpan, Set16)
{
    uint8_t buf[3];
    buf[2] = 0x00;

    nunavut::support::bitspan{ {buf, sizeof(buf)} }.setF16(3.14f);
    ASSERT_EQ(0x48, buf[0]);
    ASSERT_EQ(0x42, buf[1]);
    ASSERT_EQ(0x00, buf[2]);
}



// +--------------------------------------------------------------------------+
// | testNunavutGetF16
// +--------------------------------------------------------------------------+

TEST(BitSpan, Get16)
{
    // >>> hex(int.from_bytes(np.array([np.float16('3.14')]).tobytes(), 'little'))
    // '0x4248'
    const uint8_t buf[3] = {0x48, 0x42, 0x00};
    const float result = nunavut::support::const_bitspan{ { buf, sizeof(buf) } }.getF16( );
    ASSERT_TRUE(CompareFloatsNear(3.14f, result, 0.001f));
}


// +--------------------------------------------------------------------------+
// | testNunavutSetF32
// +--------------------------------------------------------------------------+
/**
 * Compare the results of Nunavut serialization to the IEEE definition. These must match.
 */
static void helperAssertSerFloat32SameAsIEEE(const float original_value, const uint8_t* serialized_result)
{
    union
    {
        float f;
        struct
        {
            uint32_t mantissa : 23;
            uint32_t exponent : 8;
            uint32_t negative : 1;
        } ieee;
    } as_int = {original_value};

    ASSERT_EQ(as_int.ieee.mantissa & 0xFF, serialized_result[0]) << "First 8 bits of mantissa did not match.";
    ASSERT_EQ((as_int.ieee.mantissa >> 8U) & 0xFF, serialized_result[1]) << "Second 8 bits of mantissa did not match.";
    ASSERT_EQ((as_int.ieee.mantissa >> 16U) & 0x3F, serialized_result[2] & 0x3F) << "Last 6 bits of mantissa did not match.";
    ASSERT_EQ((as_int.ieee.mantissa >> 16U) & 0x40, serialized_result[2] & 0x40) << "7th bit of mantissa did not match.";
    ASSERT_EQ(as_int.ieee.exponent & 0x1, (serialized_result[2] >> 7U) & 0x01) << "First bit of exponent did not match.";
    ASSERT_EQ((as_int.ieee.exponent >> 1U) & 0x7F, serialized_result[3] & 0x7F) << "Last 7 bits of exponent did not match.";
    ASSERT_EQ(as_int.ieee.negative & 0x1, (serialized_result[3] >> 7U) & 0x01) << "Negative bit did not match.";
}

TEST(BitSpan, SetF32)
{
    uint8_t buffer[] = {0x00, 0x00, 0x00, 0x00};
    nunavut::support::bitspan{ { buffer, sizeof(buffer) } }.setF32( 3.14f);
    helperAssertSerFloat32SameAsIEEE(3.14f, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavut::support::bitspan{ { buffer, sizeof(buffer) } }.setF32( -3.14f);
    helperAssertSerFloat32SameAsIEEE(-3.14f, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavut::support::bitspan{ { buffer, sizeof(buffer) } }.setF32( -NAN);
    helperAssertSerFloat32SameAsIEEE(-NAN, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavut::support::bitspan{ { buffer, sizeof(buffer) } }.setF32( NAN);
    helperAssertSerFloat32SameAsIEEE(NAN, buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavut::support::bitspan{ { buffer, sizeof(buffer) } }.setF32( INFINITY);
    helperAssertSerFloat32SameAsIEEE(std::numeric_limits<float>::infinity(), buffer);

    memset(buffer, 0, sizeof(buffer));
    nunavut::support::bitspan{ { buffer, sizeof(buffer) } }.setF32( -INFINITY);
    helperAssertSerFloat32SameAsIEEE(-std::numeric_limits<float>::infinity(), buffer);
}

// +--------------------------------------------------------------------------+
// | testNunavutGetF32
// +--------------------------------------------------------------------------+

TEST(BitSpan, GetF32)
{
    // >>> hex(int.from_bytes(np.array([-np.float32('infinity')]).tobytes(), 'little'))
    // '0xff800000'
    const uint8_t buffer_neg_inf[] = {0x00, 0x00, 0x80, 0xFF};
    float result = nunavut::support::const_bitspan{ { buffer_neg_inf, sizeof(buffer_neg_inf) } }.getF32( );
    ASSERT_FLOAT_EQ(-std::numeric_limits<float>::infinity(), result);

    // >>> hex(int.from_bytes(np.array([np.float32('infinity')]).tobytes(), 'little'))
    // '0x7f800000'
    const uint8_t buffer_inf[] = {0x00, 0x00, 0x80, 0x7F};
    result = nunavut::support::const_bitspan{ { buffer_inf, sizeof(buffer_inf) } }.getF32( );
    ASSERT_FLOAT_EQ(std::numeric_limits<float>::infinity(), result);

    // >>> hex(int.from_bytes(np.array([np.float32('nan')]).tobytes(), 'little'))
    // '0x7fc00000'
    const uint8_t buffer_nan[] = {0x00, 0x00, 0xC0, 0x7F};
    result = nunavut::support::const_bitspan{ { buffer_nan, sizeof(buffer_nan) } }.getF32( );
    ASSERT_TRUE(std::isnan(result));

    // >>> hex(int.from_bytes(np.array([np.float32('3.14')]).tobytes(), 'little'))
    // '0x4048f5c3'
    const uint8_t buffer_pi[] = {0xC3, 0xF5, 0x48, 0x40};
    result = nunavut::support::const_bitspan{ { buffer_pi, sizeof(buffer_pi) } }.getF32( );
    ASSERT_FLOAT_EQ(3.14f, result);
}


// +--------------------------------------------------------------------------+
// | testNunavutGetF64
// +--------------------------------------------------------------------------+

TEST(BitSpan, GetF64)
{
    // >>> hex(int.from_bytes(np.array([np.float64('3.141592653589793')]).tobytes(), 'little'))
    // '0x400921fb54442d18'
    const uint8_t buffer_pi[] = {0x18, 0x2D, 0x44, 0x54, 0xFB, 0x21, 0x09, 0x40};
    double result = nunavut::support::const_bitspan{ { buffer_pi, sizeof(buffer_pi) } }.getF64( );
    ASSERT_DOUBLE_EQ(3.141592653589793, result);

    // >>> hex(int.from_bytes(np.array([np.float64('infinity')]).tobytes(), 'little'))
    // '0x7ff0000000000000'
    const uint8_t buffer_inf[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF0, 0x7F};
    result = nunavut::support::const_bitspan{ { buffer_inf, sizeof(buffer_inf) } }.getF64( );
    ASSERT_DOUBLE_EQ(std::numeric_limits<double>::infinity(), result);

    // >>> hex(int.from_bytes(np.array([-np.float64('infinity')]).tobytes(), 'little'))
    // '0xfff0000000000000'
    const uint8_t buffer_neg_inf[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF0, 0xFF};
    result = nunavut::support::const_bitspan{ { buffer_neg_inf, sizeof(buffer_neg_inf) } }.getF64( );
    ASSERT_DOUBLE_EQ(-std::numeric_limits<double>::infinity(), result);

    // >>> hex(int.from_bytes(np.array([np.float64('nan')]).tobytes(), 'little'))
    // '0x7ff8000000000000'
    const uint8_t buffer_nan[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF8, 0x7F};
    result = nunavut::support::const_bitspan{ { buffer_nan, sizeof(buffer_nan) } }.getF64( );
    ASSERT_TRUE(std::isnan(result));
}

// +--------------------------------------------------------------------------+
// | testNunavutSetF64
// +--------------------------------------------------------------------------+
/**
 * Compare the results of Nunavut serialization to the IEEE definition. These must match.
 */
static bool helperAssertSerFloat64SameAsIEEE(const double original_value, const uint8_t* serialized_result)
{
    union
    {
        double f;
        struct
        {
            uint64_t mantissa : 52;
            uint64_t exponent : 11;
            uint64_t negative : 1;
        } ieee;
    } as_int = {original_value};

    union
    {
        uint64_t as_int;
        uint8_t as_bytes[8];
    } result_bytes;
    memcpy(result_bytes.as_bytes, serialized_result, 8);

    EXPECT_EQ(as_int.ieee.mantissa & 0xFFFFFFFFFFFFF, result_bytes.as_int & 0xFFFFFFFFFFFFF) << "Mantessa did not match.";
    EXPECT_EQ(as_int.ieee.exponent & 0xF, (serialized_result[6] >> 4U) & 0xF) << "First four bits of exponent did not match.";
    EXPECT_EQ((as_int.ieee.exponent >> 4U) & 0x7F, serialized_result[7] & 0x7F) << "Last 7 bits of exponent did not match.";
    EXPECT_EQ(as_int.ieee.negative & 0x1, (serialized_result[7] >> 7U) & 0x01) << "Negative bit did not match.";
    return not ::testing::Test::HasFailure();
}

TEST(BitSpan, SetF64)
{
    uint8_t buffer[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    nunavut::support::bitspan{ { buffer, sizeof(buffer) } }.setF64( 3.141592653589793);
    ASSERT_TRUE(helperAssertSerFloat64SameAsIEEE(3.141592653589793, buffer));

    memset(buffer, 0, sizeof(buffer));
    nunavut::support::bitspan{ { buffer, sizeof(buffer) } }.setF64( -3.141592653589793);
    ASSERT_TRUE(helperAssertSerFloat64SameAsIEEE(-3.141592653589793, buffer));

    memset(buffer, 0, sizeof(buffer));
    nunavut::support::bitspan{ { buffer, sizeof(buffer) } }.setF64( -std::numeric_limits<double>::quiet_NaN());
    ASSERT_TRUE(helperAssertSerFloat64SameAsIEEE(-std::numeric_limits<double>::quiet_NaN(), buffer));

    memset(buffer, 0, sizeof(buffer));
    nunavut::support::bitspan{ { buffer, sizeof(buffer) } }.setF64( std::numeric_limits<double>::quiet_NaN());
    ASSERT_TRUE(helperAssertSerFloat64SameAsIEEE(std::numeric_limits<double>::quiet_NaN(), buffer));

    memset(buffer, 0, sizeof(buffer));
    nunavut::support::bitspan{ { buffer, sizeof(buffer) } }.setF64( std::numeric_limits<double>::infinity());
    ASSERT_TRUE(helperAssertSerFloat64SameAsIEEE(std::numeric_limits<double>::infinity(), buffer));

    memset(buffer, 0, sizeof(buffer));
    nunavut::support::bitspan{ { buffer, sizeof(buffer) } }.setF64( -std::numeric_limits<double>::infinity());
    ASSERT_TRUE(helperAssertSerFloat64SameAsIEEE(-std::numeric_limits<double>::infinity(), buffer));
}
