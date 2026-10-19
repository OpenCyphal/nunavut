// Copyright (c) 2026 OpenCyphal Development Team.
// This software is distributed under the terms of the MIT License.
//
// libFuzzer target for generated C deserialization code.
//
// The first byte of each input selects the DSDL type under test; the remaining bytes are fed to that type's
// deserialization function as untrusted wire data. For every input:
//
//   1. Deserialization must not crash or trigger undefined behavior (AddressSanitizer + UBSan).
//   2. Deserializing the same bytes into objects pre-filled with different garbage must give the same result. This
//      catches fields that deserialization forgets to initialize.
//   3. The reported consumed size must never exceed the input size.
//   4. If deserialization succeeds, the object must serialize, the result must deserialize again, and serializing
//      that second object must reproduce the same bytes. Serialized bytes are compared rather than objects because
//      union storage and padding bytes in the structs are indeterminate.
//
// When built with NUNAVUT_FUZZ_SEED_GENERATOR defined, this file instead provides a main() that writes a seed corpus
// of valid serialized samples for each type to the directory given as the first argument.

// Serialization asserts are enabled for Debug builds; make them fatal so the fuzzer reports them as crashes.
#include <stdio.h>
#include <stdlib.h>
#undef NUNAVUT_ASSERT
#define NUNAVUT_ASSERT(x) ((x) ? (void) 0 : nunavutFuzzAssertFailed(#x, __FILE__, __LINE__))
static inline void nunavutFuzzAssertFailed(const char* const expr, const char* const file, const int line)
{
    (void) fprintf(stderr, "NUNAVUT_ASSERT(%s) failed at %s:%d\n", expr, file, line);
    abort();
}

#include <mymsgs/OuterMore_1_0.h>
#include <regulated/basics/DelimitedFixedSize_0_1.h>
#include <regulated/basics/DelimitedVariableSize_0_1.h>
#include <regulated/basics/Primitive_0_1.h>
#include <regulated/basics/PrimitiveArrayFixed_0_1.h>
#include <regulated/basics/PrimitiveArrayVariable_0_1.h>
#include <regulated/basics/Struct__0_1.h>
#include <regulated/basics/UnalignedUnion_0_1.h>
#include <regulated/basics/UnalignedUnionContainer_0_1.h>
#include <regulated/basics/UnionWithSameTypes_0_1.h>
#include <regulated/basics/Union_0_1.h>
#include <regulated/delimited/A_1_0.h>
#include <regulated/delimited/A_1_1.h>
#include <regulated/drone/sensor/BMSStatus_1_0.h>
#include <regulated/zubax/sensor/bms/BatteryPackParams_0_1.h>
#include <uavcan/_register/Access_1_0.h>
#include <uavcan/_register/Value_1_0.h>
#include <uavcan/diagnostic/Record_1_1.h>
#include <uavcan/file/Read_1_1.h>
#include <uavcan/metatransport/can/Frame_0_2.h>
#include <uavcan/node/ExecuteCommand_1_3.h>
#include <uavcan/node/GetInfo_1_0.h>
#include <uavcan/node/Heartbeat_1_0.h>
#include <uavcan/node/port/SubjectIDList_1_0.h>
#include <uavcan/pnp/cluster/AppendEntries_1_0.h>
#include <uavcan/primitive/array/Bit_1_0.h>
#include <uavcan/primitive/array/Real16_1_0.h>
#include <string.h>

/// X-macro list of every type under test. Keep the order stable so that corpus entries keep selecting the same type.
#define NUNAVUT_FUZZ_TYPES(X)                           \
    X(regulated_basics_Struct__0_1)                     \
    X(regulated_basics_Union_0_1)                       \
    X(regulated_basics_UnionWithSameTypes_0_1)          \
    X(regulated_basics_UnalignedUnion_0_1)              \
    X(regulated_basics_UnalignedUnionContainer_0_1)     \
    X(regulated_basics_DelimitedFixedSize_0_1)          \
    X(regulated_basics_DelimitedVariableSize_0_1)       \
    X(regulated_basics_Primitive_0_1)                   \
    X(regulated_basics_PrimitiveArrayFixed_0_1)         \
    X(regulated_basics_PrimitiveArrayVariable_0_1)      \
    X(regulated_delimited_A_1_0)                        \
    X(regulated_delimited_A_1_1)                        \
    X(regulated_drone_sensor_BMSStatus_1_0)             \
    X(regulated_zubax_sensor_bms_BatteryPackParams_0_1) \
    X(mymsgs_OuterMore_1_0)                             \
    X(uavcan_register_Value_1_0)                        \
    X(uavcan_register_Access_Request_1_0)               \
    X(uavcan_diagnostic_Record_1_1)                     \
    X(uavcan_file_Read_Response_1_1)                    \
    X(uavcan_metatransport_can_Frame_0_2)               \
    X(uavcan_node_ExecuteCommand_Request_1_3)           \
    X(uavcan_node_GetInfo_Response_1_0)                 \
    X(uavcan_node_Heartbeat_1_0)                        \
    X(uavcan_node_port_SubjectIDList_1_0)               \
    X(uavcan_pnp_cluster_AppendEntries_Request_1_0)     \
    X(uavcan_primitive_array_Bit_1_0)                   \
    X(uavcan_primitive_array_Real16_1_0)

typedef int8_t (*DeserializeFunction)(void* const obj, const uint8_t* const buffer, size_t* const inout_size);
typedef int8_t (*SerializeFunction)(const void* const obj, uint8_t* const buffer, size_t* const inout_size);

typedef struct
{
    const char*         name;
    size_t              object_size;
    size_t              buffer_size;
    DeserializeFunction deserialize;
    SerializeFunction   serialize;
} FuzzType;

#define NUNAVUT_FUZZ_ADAPTERS(T)                                                                    \
    static int8_t deserialize_##T(void* const obj, const uint8_t* const buffer, size_t* const size) \
    {                                                                                               \
        return T##_deserialize_((T*) obj, buffer, size);                                            \
    }                                                                                               \
    static int8_t serialize_##T(const void* const obj, uint8_t* const buffer, size_t* const size)   \
    {                                                                                               \
        return T##_serialize_((const T*) obj, buffer, size);                                        \
    }
NUNAVUT_FUZZ_TYPES(NUNAVUT_FUZZ_ADAPTERS)

#define NUNAVUT_FUZZ_ENTRY(T) {#T, sizeof(T), T##_SERIALIZATION_BUFFER_SIZE_BYTES_, &deserialize_##T, &serialize_##T},
static const FuzzType FuzzTypes[] = {NUNAVUT_FUZZ_TYPES(NUNAVUT_FUZZ_ENTRY)};
#define NUNAVUT_FUZZ_TYPE_COUNT (sizeof(FuzzTypes) / sizeof(FuzzTypes[0]))

#define FUZZ_CHECK(type, cond)                                                                                 \
    do                                                                                                         \
    {                                                                                                          \
        if (!(cond))                                                                                           \
        {                                                                                                      \
            (void) fprintf(stderr, "%s: check failed: %s (%s:%d)\n", (type)->name, #cond, __FILE__, __LINE__); \
            abort();                                                                                           \
        }                                                                                                      \
    } while (0)

/// Heap allocations sized exactly to the request let AddressSanitizer catch any overrun of objects or buffers.
static void* allocFilled(const size_t size, const int fill)
{
    void* const out = malloc((size > 0U) ? size : 1U);
    if (out == NULL)
    {
        abort();
    }
    (void) memset(out, fill, (size > 0U) ? size : 1U);
    return out;
}

/// Serializes obj, requiring success. Returns a heap buffer the caller must free; its used size is in out_size.
static uint8_t* serializeOrDie(const FuzzType* const type, const void* const obj, size_t* const out_size)
{
    uint8_t* const buffer = (uint8_t*) allocFilled(type->buffer_size, 0xA5);
    size_t         size   = type->buffer_size;
    const int8_t   rc     = type->serialize(obj, buffer, &size);
    FUZZ_CHECK(type, rc >= 0);
    FUZZ_CHECK(type, size <= type->buffer_size);
    *out_size = size;
    return buffer;
}

/// Applies all checks described at the top of this file to one input. Returns the deserialization result.
static int8_t checkOneInput(const FuzzType* const type, const uint8_t* const data, const size_t size)
{
    void* const zeroed  = allocFilled(type->object_size, 0x00);
    void* const garbage = allocFilled(type->object_size, 0xFF);

    size_t       consumed_zeroed  = size;
    size_t       consumed_garbage = size;
    const int8_t rc_zeroed        = type->deserialize(zeroed, data, &consumed_zeroed);
    const int8_t rc_garbage       = type->deserialize(garbage, data, &consumed_garbage);
    FUZZ_CHECK(type, rc_zeroed == rc_garbage);

    if (rc_zeroed >= 0)
    {
        FUZZ_CHECK(type, consumed_zeroed <= size);
        FUZZ_CHECK(type, consumed_zeroed == consumed_garbage);

        size_t         first_size   = 0U;
        size_t         garbage_size = 0U;
        uint8_t* const first        = serializeOrDie(type, zeroed, &first_size);
        uint8_t* const from_garbage = serializeOrDie(type, garbage, &garbage_size);
        FUZZ_CHECK(type, first_size == garbage_size);
        FUZZ_CHECK(type, 0 == memcmp(first, from_garbage, first_size));

        void* const  again          = allocFilled(type->object_size, 0x5A);
        size_t       consumed_again = first_size;
        const int8_t rc_again       = type->deserialize(again, first, &consumed_again);
        FUZZ_CHECK(type, rc_again >= 0);
        FUZZ_CHECK(type, consumed_again == first_size);

        size_t         second_size = 0U;
        uint8_t* const second      = serializeOrDie(type, again, &second_size);
        FUZZ_CHECK(type, second_size == first_size);
        FUZZ_CHECK(type, 0 == memcmp(first, second, first_size));

        free(second);
        free(again);
        free(from_garbage);
        free(first);
    }
    free(garbage);
    free(zeroed);
    return rc_zeroed;
}

int LLVMFuzzerTestOneInput(const uint8_t* const data, const size_t size);
int LLVMFuzzerTestOneInput(const uint8_t* const data, const size_t size)
{
    if (size > 0U)
    {
        const FuzzType* const type = &FuzzTypes[data[0] % NUNAVUT_FUZZ_TYPE_COUNT];
        (void) checkOneInput(type, &data[1], size - 1U);
    }
    return 0;
}

#ifdef NUNAVUT_FUZZ_SEED_GENERATOR

/// Number of distinct valid samples to try to emit per type in addition to the default-initialized one.
#    define NUNAVUT_FUZZ_SEEDS_PER_TYPE 8U
/// Number of random buffers to try per type when looking for valid samples.
#    define NUNAVUT_FUZZ_SEED_ATTEMPTS 512U

static uint32_t seedRandom(uint32_t* const state)
{
    // xorshift32; deterministic so that the generated corpus is reproducible.
    uint32_t x = *state;
    x ^= x << 13U;
    x ^= x >> 17U;
    x ^= x << 5U;
    *state = x;
    return x;
}

static void writeSeed(const char* const    dir,
                      const size_t         type_index,
                      const unsigned       sample_index,
                      const uint8_t* const payload,
                      const size_t         payload_size)
{
    char path[4096];
    (void) snprintf(path,
                    sizeof(path),
                    "%s/%02u_%s_%u.bin",
                    dir,
                    (unsigned) type_index,
                    FuzzTypes[type_index].name,
                    sample_index);
    FILE* const file = fopen(path, "wb");
    if (file == NULL)
    {
        (void) fprintf(stderr, "Cannot open %s for writing\n", path);
        exit(1);
    }
    const uint8_t selector = (uint8_t) type_index;
    if ((fwrite(&selector, 1U, 1U, file) != 1U) ||
        ((payload_size > 0U) && (fwrite(payload, 1U, payload_size, file) != payload_size)))
    {
        (void) fprintf(stderr, "Cannot write %s\n", path);
        exit(1);
    }
    (void) fclose(file);
}

/// Serializes a valid object and writes it as a seed, after running it through the fuzz checks.
static void emitSample(const char* const dir,
                       const size_t      type_index,
                       const unsigned    sample_index,
                       const void* const obj)
{
    const FuzzType* const type        = &FuzzTypes[type_index];
    size_t                sample_size = 0U;
    uint8_t* const        sample      = serializeOrDie(type, obj, &sample_size);
    FUZZ_CHECK(type, checkOneInput(type, sample, sample_size) >= 0);
    writeSeed(dir, type_index, sample_index, sample, sample_size);
    free(sample);
}

int main(const int argc, const char* const argv[])
{
    if (argc != 2)
    {
        (void) fprintf(stderr, "Usage: %s <output-directory>\n", argv[0]);
        return 1;
    }
    // Biasing random bytes towards small values makes array lengths and union tags valid more often.
    static const uint8_t masks[] = {0x01U, 0x03U, 0x0FU, 0x3FU, 0xFFU};
    uint32_t             state   = 0x12345678UL;
    for (size_t i = 0U; i < NUNAVUT_FUZZ_TYPE_COUNT; ++i)
    {
        const FuzzType* const type = &FuzzTypes[i];
        void* const           obj  = allocFilled(type->object_size, 0x00);

        // A default-initialized object (deserialized from an empty buffer per the implicit zero extension rule).
        size_t empty = 0U;
        FUZZ_CHECK(type, type->deserialize(obj, NULL, &empty) >= 0);
        unsigned emitted = 0U;
        emitSample(argv[1], i, emitted++, obj);

        // Valid objects obtained by deserializing random buffers.
        uint8_t* const random_buffer = (uint8_t*) allocFilled(type->buffer_size, 0x00);
        for (unsigned attempt = 0U; (attempt < NUNAVUT_FUZZ_SEED_ATTEMPTS) && (emitted <= NUNAVUT_FUZZ_SEEDS_PER_TYPE);
             ++attempt)
        {
            const uint8_t mask = masks[attempt % sizeof(masks)];
            for (size_t k = 0U; k < type->buffer_size; ++k)
            {
                random_buffer[k] = (uint8_t) (seedRandom(&state) & mask);
            }
            size_t size = type->buffer_size;
            if (type->deserialize(obj, random_buffer, &size) >= 0)
            {
                emitSample(argv[1], i, emitted++, obj);
            }
        }
        free(random_buffer);
        free(obj);
        (void) printf("%-48s %u seeds\n", type->name, emitted);
    }
    return 0;
}

#endif  // NUNAVUT_FUZZ_SEED_GENERATOR
