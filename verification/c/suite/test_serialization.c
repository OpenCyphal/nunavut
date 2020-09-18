/// Copyright 2020 David Lenfesty
///
/// Tests different cases in serialization code.
///
#include "unity.h"
#include <assert.h>

#include "uavcan/primitive/scalar/Bit_1_0.h"
#include "uavcan/_register/Name_1_0.h"
#include "uavcan/_register/Value_1_0.h"

/// Void fields must explicitely be zeroed by serialization.
/// Ensures that uninitialized memory in buffer does not "leak".
static void testVoidZeroed(void)
{
    uavcan_primitive_scalar_Bit_1_0 subject;
    uint8_t buffer[1] = {0xFF};

    uavcan_primitive_scalar_Bit_1_0_init(&subject);
    (void) uavcan_primitive_scalar_Bit_1_0_serialize(&subject, 0, buffer);

    TEST_ASSERT_EQUAL_HEX8(0x00, (buffer[0] & 0x7F));
}

/// Ensures that variable length primitive arrays copy correctly.
static void testVariablePrimitiveArrayLength(void)
{
    uavcan_register_Name_1_0 subject;
    uint8_t buffer[uavcan_register_Name_1_0_MAX_SERIALIZED_REPRESENTATION_SIZE_BYTES];

    uavcan_register_Name_1_0_init(&subject);
    subject.name_length = strlen("foo");
    strcpy((char*)subject.name, "foo");
    uavcan_register_Name_1_0_serialize(&subject, 0, buffer);

    TEST_ASSERT_EQUAL_STRING_LEN("foo", (char*)&buffer[1], strlen("foo"));
}

static void testInvalidTag(void)
{
    uavcan_register_Value_1_0 subject;
    uint8_t buffer[uavcan_register_Value_1_0_MAX_SERIALIZED_REPRESENTATION_SIZE_BYTES];
    uavcan_register_Value_1_0_init(&subject);
    subject._tag_ = 20;
    int32_t rc = uavcan_register_Value_1_0_serialize(&subject, 0, buffer);
    TEST_ASSERT_EQUAL_INT32(-NUNAVUT_ERR_INVALID_TAG, rc);
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
    RUN_TEST(testInvalidTag);

    return UNITY_END();
}
