/// Copyright 2020 David Lenfesty
///
/// Tests different cases in serialization code.
///
#include "unity.h"

#include "uavcan/primitive/scalar/Bit_1_0.h"
#include "uavcan/_register/Access_1_0.h"

/// These unit tests assume that the headers under test were generated with
/// typename_unsigned_bit_length set to the value provided here.
typedef size_t typename_unsigned_bit_length;


/// Void fields must explicitely be zeroed by serialization.
/// Ensures that uninitialized memory in buffer does not "leak".
static void testVoidZeroed(void)
{
    uavcan_primitive_scalar_Bit_1_0 subject;
    uint8_t buffer[1] = {0xFF};
    typename_unsigned_bit_length bit_size;

    uavcan_primitive_scalar_Bit_1_0_init(&subject);
    int32_t rc = uavcan_primitive_scalar_Bit_1_0_serialize(&subject, 0, buffer, sizeof(buffer), &bit_size);

    TEST_ASSERT_EQUAL_HEX8(0x00, (buffer[0] & 0x7F));
    TEST_ASSERT_EQUAL_INT32(NUNAVUT_SUCCESS, rc);
}

/// Ensures that variable length primitive arrays copy correctly.
static void testVariablePrimitiveArrayLength(void)
{
    uavcan_register_Name_1_0 subject;
    uint8_t buffer[uavcan_register_Name_1_0_MAX_SERIALIZED_REPRESENTATION_SIZE_BYTES];
    typename_unsigned_bit_length bit_size;

    uavcan_register_Name_1_0_init(&subject);
    subject.name_length = strlen("foo");
    memcpy((void*)subject.name, (void*)"foo", subject.name_length);
    int32_t rc = uavcan_register_Name_1_0_serialize(&subject, 0, buffer, sizeof(buffer), &bit_size);

    TEST_ASSERT_EQUAL_STRING_LEN("foo", (char*)&buffer[1], strlen("foo"));
    TEST_ASSERT_EQUAL_INT32(NUNAVUT_SUCCESS, rc);
}

/// Serialization functions must catch over-sized arrays.
static void testArrayOverflow(void)
{
    uavcan_register_Name_1_0 subject;
    uint8_t buffer [uavcan_register_Name_1_0_MAX_SERIALIZED_REPRESENTATION_SIZE_BYTES];
    typename_unsigned_bit_length bit_size;

    uavcan_register_Name_1_0_init(&subject);
    subject.name_length = 51;
    int32_t rc = uavcan_register_Name_1_0_serialize(&subject, 0, buffer, sizeof(buffer), &bit_size);

    TEST_ASSERT_EQUAL_INT32(-NUNAVUT_ERR_INVALID_LEN, rc);
}

/// Test that an obviously invalid tag returns the correct error.
static void testInvalidTag(void)
{
    uavcan_register_Value_1_0 subject;
    uint8_t buffer[uavcan_register_Value_1_0_MAX_SERIALIZED_REPRESENTATION_SIZE_BYTES];
    typename_unsigned_bit_length bit_size;

    uavcan_register_Value_1_0_init(&subject);
    subject._tag_ = 200;
    int32_t rc = uavcan_register_Value_1_0_serialize(&subject, 0, buffer, sizeof(buffer), &bit_size);

    TEST_ASSERT_EQUAL_INT32(-NUNAVUT_ERR_INVALID_TAG, rc);
}

// Test that the length is correct when implementing nested composite types.
static void testCompositeLength(void)
{
    uavcan_register_Access_1_0_Request subject;
    uint8_t buffer[uavcan_register_Access_1_0_Request_MAX_SERIALIZED_REPRESENTATION_SIZE_BYTES];
    typename_unsigned_bit_length bit_size;

    uavcan_register_Access_1_0_Request_init(&subject);
    subject.name.name_length = strlen("foo");
    memcpy((void*)subject.name.name, (void*)"foo", subject.name.name_length);
    uavcan_register_Value_1_0_set_natural32(&subject.value);
    subject.value.natural32.value_length = 1;
    int32_t rc = uavcan_register_Access_1_0_Request_serialize(&subject, 0, buffer, sizeof(buffer), &bit_size);

    TEST_ASSERT_EQUAL_INT32(NUNAVUT_SUCCESS, rc);
    TEST_ASSERT_EQUAL_UINT32(80, bit_size);
}

void setUp(void)
{

}

void tearDown(void)
{

}

int main(void)
{
    UNITY_BEGIN();

    RUN_TEST(testVoidZeroed);
    RUN_TEST(testVariablePrimitiveArrayLength);
    RUN_TEST(testArrayOverflow);
    RUN_TEST(testInvalidTag);
    RUN_TEST(testCompositeLength);

    return UNITY_END();
}
