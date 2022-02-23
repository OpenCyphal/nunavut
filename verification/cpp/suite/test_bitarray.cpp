#include "gmock/gmock.h"
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
    const std::array<uint8_t,5> csrcArray{ 1, 2, 3, 4, 5 };
    {
        nunavut::support::const_bitspan sp{{&csrcVar, 1}};
        ASSERT_EQ(sp.size(), 1U*8U);
    }
    {
        nunavut::support::const_bitspan sp{csrcArray};
        ASSERT_EQ(sp.size(), 5U*8U);
    }
}

TEST(BitSpan, AlignedPtr) {
    std::array<uint8_t,5> srcArray{ 1, 2, 3, 4, 5 };
    {
        auto actualPtr = nunavut::support::bitspan{srcArray}.aligned_ptr();
        ASSERT_EQ(actualPtr, srcArray.data());
    }
    {
        auto actualPtr = nunavut::support::bitspan{srcArray, 1}.aligned_ptr();
        ASSERT_EQ(actualPtr, srcArray.data());
    }
    {
        auto actualPtr = nunavut::support::bitspan{srcArray, 5}.aligned_ptr();
        ASSERT_EQ(actualPtr, srcArray.data());
    }
    {
        auto actualPtr = nunavut::support::bitspan{srcArray, 7}.aligned_ptr();
        ASSERT_EQ(actualPtr, srcArray.data());
    }
    {
        auto actualPtr = nunavut::support::bitspan{srcArray}.aligned_ptr(8);
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
}

TEST(BitSpan, CopyBits) {
    std::array<uint8_t,5> src{ 1, 2, 3, 4, 5 };
    std::array<uint8_t,6> dst{};
    memset(dst.data(), 0, dst.size());

    nunavut::support::const_bitspan sp{src};
    nunavut::support::bitspan dstSp{dst};
    sp.copyTo(dstSp);
    for(size_t i = 0; i < src.size(); ++i)
    {
        ASSERT_EQ(src[i], dst[i]);
    }
}

TEST(BitSpan, CopyBitsWithAlignedOffset) {
    std::array<uint8_t,5> src{ 1, 2, 3, 4, 5 };
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
}

TEST(BitSpan, CopyBitsWithUnalignedOffset){
    std::array<uint8_t,6> src{ 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA };
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
    std::array<uint8_t, 4> data{};
    ASSERT_EQ(32U, const_bitspan(data,  0U).saturateBufferFragmentBitLength(32));
    ASSERT_EQ(31U, const_bitspan(data,  1U).saturateBufferFragmentBitLength(32));
    ASSERT_EQ(16U, const_bitspan(data,  0U).saturateBufferFragmentBitLength(16));
    ASSERT_EQ(15U, const_bitspan(data, 17U).saturateBufferFragmentBitLength(24));
    ASSERT_EQ(0U,  const_bitspan({data.data(), 2}, 24U).saturateBufferFragmentBitLength(24));
}


TEST(BitSpan, GetBits)
{
    std::array<uint8_t, 16> src{ 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF };
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
    ASSERT_EQ(-nunavut::support::Error::SERIALIZATION_BUFFER_TOO_SMALL, rc);
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
    const uint8_t data[] = {0xAA, 0xAA, 0xAA, 0xAA};
    ASSERT_EQ(0xAAAAAAAAU, nunavut::support::const_bitspan(data, 0).getU32(32U));
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
    const uint8_t data[] = {0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA};
    ASSERT_EQ(0xAAAAAAAAAAAAAAAAU, nunavut::support::const_bitspan(data, 0).getU64(64U));
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
