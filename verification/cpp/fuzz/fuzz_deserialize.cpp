// Copyright (c) 2026 OpenCyphal Development Team.
// This software is distributed under the terms of the MIT License.
//
// libFuzzer target for generated C++ deserialization code.
//
// The first byte of each input selects the DSDL type under test; the remaining bytes are fed to that type's
// deserialization function as untrusted wire data. For every input:
//
//   1. Deserialization must not crash or trigger undefined behavior (AddressSanitizer + UBSan).
//   2. Deserializing into a default-constructed object and into an object that already holds state from a different
//      input must give the same result. This catches state (array elements, union options) that deserialization
//      fails to reset.
//   3. The reported consumed size must never exceed the input size.
//   4. If deserialization succeeds, the object must serialize, the result must deserialize again, and serializing
//      that second object must reproduce the same bytes.
//
// When built with NUNAVUT_FUZZ_SEED_GENERATOR defined, this file instead provides a main() that writes a seed corpus
// of valid serialized samples for each type to the directory given as the first argument.

// Serialization asserts are enabled for Debug builds; make them fatal so the fuzzer reports them as crashes.
#include <cstdio>
#include <cstdlib>
#undef NUNAVUT_ASSERT
#define NUNAVUT_ASSERT(x) ((x) ? static_cast<void>(0) : nunavutFuzzAssertFailed(#x, __FILE__, __LINE__))
[[noreturn]] static inline void nunavutFuzzAssertFailed(const char* const expr, const char* const file, const int line)
{
    (void) std::fprintf(stderr, "NUNAVUT_ASSERT(%s) failed at %s:%d\n", expr, file, line);
    std::abort();
}

#include "mymsgs/OuterMore_1_0.hpp"
#include "regulated/basics/DelimitedFixedSize_0_1.hpp"
#include "regulated/basics/DelimitedVariableSize_0_1.hpp"
#include "regulated/basics/Primitive_0_1.hpp"
#include "regulated/basics/PrimitiveArrayFixed_0_1.hpp"
#include "regulated/basics/PrimitiveArrayVariable_0_1.hpp"
#include "regulated/basics/Struct__0_1.hpp"
#include "regulated/basics/UnalignedUnion_0_1.hpp"
#include "regulated/basics/UnalignedUnionContainer_0_1.hpp"
#include "regulated/basics/UnionWithSameTypes_0_1.hpp"
#include "regulated/basics/Union_0_1.hpp"
#include "regulated/delimited/A_1_0.hpp"
#include "regulated/delimited/A_1_1.hpp"
#include "regulated/drone/sensor/BMSStatus_1_0.hpp"
#include "regulated/zubax/sensor/bms/BatteryPackParams_0_1.hpp"
#include "uavcan/_register/Access_1_0.hpp"
#include "uavcan/_register/Value_1_0.hpp"
#include "uavcan/diagnostic/Record_1_1.hpp"
#include "uavcan/file/Read_1_1.hpp"
#include "uavcan/metatransport/can/Frame_0_2.hpp"
#include "uavcan/node/ExecuteCommand_1_3.hpp"
#include "uavcan/node/GetInfo_1_0.hpp"
#include "uavcan/node/Heartbeat_1_0.hpp"
#include "uavcan/node/port/SubjectIDList_1_0.hpp"
#include "uavcan/pnp/cluster/AppendEntries_1_0.hpp"
#include "uavcan/primitive/array/Bit_1_0.hpp"
#include "uavcan/primitive/array/Real16_1_0.hpp"
#include <cstdint>
#include <cstring>
#include <vector>

namespace
{

#define FUZZ_CHECK(cond)                                                                                    \
    do                                                                                                      \
    {                                                                                                       \
        if (!(cond))                                                                                        \
        {                                                                                                   \
            (void) std::fprintf(stderr, "%s: check failed: %s (%s:%d)\n", name, #cond, __FILE__, __LINE__); \
            std::abort();                                                                                   \
        }                                                                                                   \
    } while (false)

/// Heap buffers sized exactly to the serialization buffer size let AddressSanitizer catch any overrun.
template <typename T>
std::vector<std::uint8_t> serializeOrDie(const char* const name, const T& obj)
{
    constexpr std::size_t     BufferSize = T::_traits_::SerializationBufferSizeBytes;
    std::vector<std::uint8_t> buffer(BufferSize, 0xA5U);
    const auto                result = serialize(obj, nunavut::support::bitspan(buffer.data(), BufferSize));
    FUZZ_CHECK(result);
    FUZZ_CHECK(result.value() <= BufferSize);
    buffer.resize(result.value());
    return buffer;
}

/// Applies all checks described at the top of this file to one input. Returns true if deserialization succeeded.
template <typename T>
bool checkOneInput(const char* const name, const std::uint8_t* const data, const std::size_t size)
{
    T          fresh{};
    const auto result = deserialize(fresh, nunavut::support::const_bitspan(data, size));

    T dirty{};
    if (size > 0U)
    {
        // Load whatever state the input shifted by one byte produces, successful or not, then reuse the object.
        (void) deserialize(dirty, nunavut::support::const_bitspan(&data[1], size - 1U));
    }
    const auto dirty_result = deserialize(dirty, nunavut::support::const_bitspan(data, size));
    FUZZ_CHECK(result.has_value() == dirty_result.has_value());
    if (!result)
    {
        FUZZ_CHECK(result.error() == dirty_result.error());
        return false;
    }
    FUZZ_CHECK(result.value() <= size);
    FUZZ_CHECK(result.value() == dirty_result.value());

    const std::vector<std::uint8_t> first      = serializeOrDie(name, fresh);
    const std::vector<std::uint8_t> from_dirty = serializeOrDie(name, dirty);
    FUZZ_CHECK(first == from_dirty);

    T          again{};
    const auto again_result = deserialize(again, nunavut::support::const_bitspan(first.data(), first.size()));
    FUZZ_CHECK(again_result);
    FUZZ_CHECK(again_result.value() == first.size());
    FUZZ_CHECK(serializeOrDie(name, again) == first);
    return true;
}

#ifdef NUNAVUT_FUZZ_SEED_GENERATOR
template <typename T>
void writeSeeds(const char* const name, const char* const dir, const std::size_t type_index);
#endif

struct FuzzType
{
    const char* name;
    bool (*check)(const char* const name, const std::uint8_t* const data, const std::size_t size);
#ifdef NUNAVUT_FUZZ_SEED_GENERATOR
    void (*write_seeds)(const char* const name, const char* const dir, const std::size_t type_index);
#endif
};

#ifdef NUNAVUT_FUZZ_SEED_GENERATOR
#    define NUNAVUT_FUZZ_ENTRY(T) {#T, &checkOneInput<T>, &writeSeeds<T>}
#else
#    define NUNAVUT_FUZZ_ENTRY(T) {#T, &checkOneInput<T>}
#endif

/// Every type under test. Keep the order stable so that corpus entries keep selecting the same type.
const FuzzType FuzzTypes[] = {
    NUNAVUT_FUZZ_ENTRY(regulated::basics::Struct__0_1),
    NUNAVUT_FUZZ_ENTRY(regulated::basics::Union_0_1),
    NUNAVUT_FUZZ_ENTRY(regulated::basics::UnionWithSameTypes_0_1),
    NUNAVUT_FUZZ_ENTRY(regulated::basics::UnalignedUnion_0_1),
    NUNAVUT_FUZZ_ENTRY(regulated::basics::UnalignedUnionContainer_0_1),
    NUNAVUT_FUZZ_ENTRY(regulated::basics::DelimitedFixedSize_0_1),
    NUNAVUT_FUZZ_ENTRY(regulated::basics::DelimitedVariableSize_0_1),
    NUNAVUT_FUZZ_ENTRY(regulated::basics::Primitive_0_1),
    NUNAVUT_FUZZ_ENTRY(regulated::basics::PrimitiveArrayFixed_0_1),
    NUNAVUT_FUZZ_ENTRY(regulated::basics::PrimitiveArrayVariable_0_1),
    NUNAVUT_FUZZ_ENTRY(regulated::delimited::A_1_0),
    NUNAVUT_FUZZ_ENTRY(regulated::delimited::A_1_1),
    NUNAVUT_FUZZ_ENTRY(regulated::drone::sensor::BMSStatus_1_0),
    NUNAVUT_FUZZ_ENTRY(regulated::zubax::sensor::bms::BatteryPackParams_0_1),
    NUNAVUT_FUZZ_ENTRY(mymsgs::OuterMore_1_0),
    NUNAVUT_FUZZ_ENTRY(uavcan::_register::Value_1_0),
    NUNAVUT_FUZZ_ENTRY(uavcan::_register::Access::Request_1_0),
    NUNAVUT_FUZZ_ENTRY(uavcan::diagnostic::Record_1_1),
    NUNAVUT_FUZZ_ENTRY(uavcan::file::Read::Response_1_1),
    NUNAVUT_FUZZ_ENTRY(uavcan::metatransport::can::Frame_0_2),
    NUNAVUT_FUZZ_ENTRY(uavcan::node::ExecuteCommand::Request_1_3),
    NUNAVUT_FUZZ_ENTRY(uavcan::node::GetInfo::Response_1_0),
    NUNAVUT_FUZZ_ENTRY(uavcan::node::Heartbeat_1_0),
    NUNAVUT_FUZZ_ENTRY(uavcan::node::port::SubjectIDList_1_0),
    NUNAVUT_FUZZ_ENTRY(uavcan::pnp::cluster::AppendEntries::Request_1_0),
    NUNAVUT_FUZZ_ENTRY(uavcan::primitive::array::Bit_1_0),
    NUNAVUT_FUZZ_ENTRY(uavcan::primitive::array::Real16_1_0),
};
constexpr std::size_t FuzzTypeCount = sizeof(FuzzTypes) / sizeof(FuzzTypes[0]);

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* const data, const std::size_t size);
extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* const data, const std::size_t size)
{
    if (size > 0U)
    {
        const FuzzType& type = FuzzTypes[data[0] % FuzzTypeCount];
        (void) type.check(type.name, &data[1], size - 1U);
    }
    return 0;
}

#ifdef NUNAVUT_FUZZ_SEED_GENERATOR

namespace
{

/// Number of distinct valid samples to try to emit per type in addition to the default-constructed one.
constexpr unsigned SeedsPerType = 8U;
/// Number of random buffers to try per type when looking for valid samples.
constexpr unsigned SeedAttempts = 512U;

std::uint32_t seedRandom()
{
    // xorshift32; deterministic so that the generated corpus is reproducible.
    static std::uint32_t state = 0x12345678UL;
    state ^= state << 13U;
    state ^= state >> 17U;
    state ^= state << 5U;
    return state;
}

void writeSeed(const char* const                dir,
               const std::size_t                type_index,
               const unsigned                   sample_index,
               const std::vector<std::uint8_t>& payload)
{
    char path[4096];
    (void) std::snprintf(path,
                         sizeof(path),
                         "%s/%02u_%s_%u.bin",
                         dir,
                         static_cast<unsigned>(type_index),
                         FuzzTypes[type_index].name,
                         sample_index);
    for (char* c = path + std::strlen(dir); *c != '\0'; ++c)
    {
        if (*c == ':')
        {
            *c = '_';
        }
    }
    std::FILE* const file = std::fopen(path, "wb");
    if (file == nullptr)
    {
        (void) std::fprintf(stderr, "Cannot open %s for writing\n", path);
        std::exit(1);
    }
    const std::uint8_t selector = static_cast<std::uint8_t>(type_index);
    if ((std::fwrite(&selector, 1U, 1U, file) != 1U) ||
        ((!payload.empty()) && (std::fwrite(payload.data(), 1U, payload.size(), file) != payload.size())))
    {
        (void) std::fprintf(stderr, "Cannot write %s\n", path);
        std::exit(1);
    }
    (void) std::fclose(file);
}

template <typename T>
void emitSample(const char* const name,
                const char* const dir,
                const std::size_t type_index,
                const unsigned    index,
                const T&          obj)
{
    const std::vector<std::uint8_t> sample = serializeOrDie(name, obj);
    FUZZ_CHECK(checkOneInput<T>(name, sample.data(), sample.size()));
    writeSeed(dir, type_index, index, sample);
}

template <typename T>
void writeSeeds(const char* const name, const char* const dir, const std::size_t type_index)
{
    unsigned emitted = 0U;
    emitSample(name, dir, type_index, emitted++, T{});

    // Valid objects obtained by deserializing random buffers. Biasing random bytes towards small values makes array
    // lengths and union tags valid more often.
    static const std::uint8_t masks[]    = {0x01U, 0x03U, 0x0FU, 0x3FU, 0xFFU};
    constexpr std::size_t     BufferSize = T::_traits_::SerializationBufferSizeBytes;
    std::vector<std::uint8_t> random_buffer(BufferSize);
    for (unsigned attempt = 0U; (attempt < SeedAttempts) && (emitted <= SeedsPerType); ++attempt)
    {
        const std::uint8_t mask = masks[attempt % sizeof(masks)];
        for (auto& b : random_buffer)
        {
            b = static_cast<std::uint8_t>(seedRandom() & mask);
        }
        T obj{};
        if (deserialize(obj, nunavut::support::const_bitspan(random_buffer.data(), random_buffer.size())))
        {
            emitSample(name, dir, type_index, emitted++, obj);
        }
    }
    (void) std::printf("%-56s %u seeds\n", name, emitted);
}

}  // namespace

int main(const int argc, const char* const argv[])
{
    if (argc != 2)
    {
        (void) std::fprintf(stderr, "Usage: %s <output-directory>\n", argv[0]);
        return 1;
    }
    for (std::size_t i = 0U; i < FuzzTypeCount; ++i)
    {
        FuzzTypes[i].write_seeds(FuzzTypes[i].name, argv[1], i);
    }
    return 0;
}

#endif  // NUNAVUT_FUZZ_SEED_GENERATOR
