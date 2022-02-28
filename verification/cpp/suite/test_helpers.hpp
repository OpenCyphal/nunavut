/*
 * Copyright (c) 2022 UAVCAN Development Team.
 * Authors: Pavel Pletenev <cpp.create@gmail.com>
 * This software is distributed under the terms of the MIT License.
 *
 * Tests of serialization
 */

#include "gmock/gmock.h"
#include "nunavut/support/serialization.hpp"

#if __cplusplus > 201703L
#include "magic_enum.hpp"
testing::Message& operator<<(testing::Message& s, const nunavut::support::Error& e){
    s << magic_enum::enum_name(e);
    return s;
}
#else
testing::Message& operator<<(testing::Message& s, const nunavut::support::Error& e){
    s << static_cast<std::underlying_type_t<nunavut::support::Error>>(e);
    return s;
}
#endif

namespace nunavut{
namespace testing{


template<typename I>
class Hex {
    using ft = std::conditional_t<(sizeof(I)<=2), std::conditional_t<(std::is_signed<I>::value), int16_t, uint16_t>, I>;
public:
    explicit Hex(I n) : number_(n) {}
    operator I() { return number_; }

    friend std::ostream& operator<<(std::ostream& s, const Hex& h){
        s << std::hex << static_cast<ft>(h.number_);
        return s;
    }
    bool operator==(const Hex& other)const{
        return number_ == other.number_;
    }
private:
    I number_;
};

template<typename I>
Hex<I> hex(I&& i){
    return Hex<I>(std::forward<I>(i));
}

} // namespace testing
} // namespace nunavut

inline int8_t randI8(void)
{
    return static_cast<int8_t>(rand());
}

inline int16_t randI16(void)
{
    return static_cast<int16_t>((randI8() + 1) * randI8());
}

inline int32_t randI32(void)
{
    return static_cast<int32_t>((randI16() + 1L) * randI16());
}

inline int64_t randI64(void)
{
    return static_cast<int64_t>((randI32() + 1LL) * randI32());
}

inline uint8_t randU8(void)
{
    return static_cast<uint8_t>(rand());
}

inline uint16_t randU16(void)
{
    return static_cast<uint16_t>((randU8() + 1) * randU8());
}

inline uint32_t randU32(void)
{
    return static_cast<uint32_t>((randU16() + 1L) * randU16());
}

inline uint64_t randU64(void)
{
    return static_cast<uint64_t>((randU32() + 1LL) * randU32());
}

inline float randF16(void)
{
    return static_cast<float>(randI8());
}

inline float randF32(void)
{
    return static_cast<float>(randI64());
}

inline double randF64(void)
{
    return static_cast<double>(randI64());
}
