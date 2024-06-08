// Copyright (c) 2020 OpenCyphal Development Team.
// This software is distributed under the terms of the MIT License.

#include <regulated/basics/Struct__0_1.h>
#include <regulated/basics/Union_0_1.h>
#include <regulated/basics/Primitive_0_1.h>
#include <regulated/basics/PrimitiveArrayFixed_0_1.h>
#include <regulated/basics/PrimitiveArrayVariable_0_1.h>
#include <regulated/delimited/A_1_0.h>
#include <regulated/delimited/A_1_1.h>
#include <uavcan/pnp/NodeIDAllocationData_2_0.h>
#include <stdlib.h>
#include <time.h>
#include <assert.h>

#define TEST_ASSERT_EQUAL(A, B) do {\
    if ((A) != (B)) { \
        abort(); \
    } \
} while(0)

#define TEST_ASSERT_TRUE(A) TEST_ASSERT_EQUAL(A, true)

/// A test to run with no test framework linked in. This allows some sanity checking but mostly is useful to support
/// analysis or instrumentation of the code while debugging.
static void testStructDelimited(void)
{
    regulated_delimited_A_1_0 obj;
    regulated_delimited_A_1_0_initialize_(&obj);
    regulated_delimited_A_1_0_select_del_(&obj);
    regulated_delimited_A_1_0_select_del_(NULL);  // No action.
    obj.del.var.count = 2;
    obj.del.var.elements[0].a.count = 2;
    obj.del.var.elements[0].a.elements[0] = 1;
    obj.del.var.elements[0].a.elements[1] = 2;
    obj.del.var.elements[0].b = 0;
    obj.del.var.elements[1].a.count = 1;
    obj.del.var.elements[1].a.elements[0] = 3;
    obj.del.var.elements[1].a.elements[1] = 123;  // ignored
    obj.del.var.elements[1].b = 4;
    obj.del.fix.count = 1;
    obj.del.fix.elements[0].a[0] = 5;
    obj.del.fix.elements[0].a[1] = 6;

    const uint8_t reference[] = {
        // 0    1      2      3      4      5      6      7      8      9     10     11     12     13     14     15
        0x01U, 0x17U, 0x00U, 0x00U, 0x00U, 0x02U, 0x04U, 0x00U, 0x00U, 0x00U, 0x02U, 0x01U, 0x02U, 0x00U, 0x03U, 0x00U,
        0x00U, 0x00U, 0x01U, 0x03U, 0x04U, 0x01U, 0x02U, 0x00U, 0x00U, 0x00U, 0x05U, 0x06U,
        // END OF SERIALIZED REPRESENTATION
        0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU, 0xAAU,
        0xAAU,
    };
    static_assert(sizeof(reference) == regulated_delimited_A_1_0_SERIALIZATION_BUFFER_SIZE_BYTES_, "");

    uint8_t buf[1024] = {0};
    (void) memset(&buf[0], 0xAAU, sizeof(buf));  // Fill out the canaries
    size_t size = sizeof(buf);
    TEST_ASSERT_EQUAL(0, regulated_delimited_A_1_0_serialize_(&obj, &buf[0], &size));
    TEST_ASSERT_EQUAL(28U, size);

    // Deserialize back from the reference using the same type and compare the field values.
    regulated_delimited_A_1_0_initialize_(&obj);  // Erase prior state.
    size = sizeof(reference);
    TEST_ASSERT_EQUAL(0, regulated_delimited_A_1_0_deserialize_(&obj, &reference[0], &size));
    TEST_ASSERT_EQUAL(28U, size);
    TEST_ASSERT_TRUE(regulated_delimited_A_1_0_is_del_(&obj));
    TEST_ASSERT_EQUAL(2, obj.del.var.count);
    TEST_ASSERT_EQUAL(2, obj.del.var.elements[0].a.count);
    TEST_ASSERT_EQUAL(1, obj.del.var.elements[0].a.elements[0]);
    TEST_ASSERT_EQUAL(2, obj.del.var.elements[0].a.elements[1]);
    TEST_ASSERT_EQUAL(0, obj.del.var.elements[0].b);
    TEST_ASSERT_EQUAL(1, obj.del.var.elements[1].a.count);
    TEST_ASSERT_EQUAL(3, obj.del.var.elements[1].a.elements[0]);
    TEST_ASSERT_EQUAL(4, obj.del.var.elements[1].b);
    TEST_ASSERT_EQUAL(1, obj.del.fix.count);
    TEST_ASSERT_EQUAL(5, obj.del.fix.elements[0].a[0]);
    TEST_ASSERT_EQUAL(6, obj.del.fix.elements[0].a[1]);

    // Deserialize using a different type to test extensibility enabled by delimited serialization.
    regulated_delimited_A_1_1 dif;
    size = sizeof(reference);
    TEST_ASSERT_EQUAL(0, regulated_delimited_A_1_1_deserialize_(&dif, &reference[0], &size));
    TEST_ASSERT_EQUAL(28U, size);
    TEST_ASSERT_TRUE(regulated_delimited_A_1_1_is_del_(&dif));
    TEST_ASSERT_EQUAL(2, dif.del.var.count);
    TEST_ASSERT_EQUAL(2, dif.del.var.elements[0].a.count);
    TEST_ASSERT_EQUAL(1, dif.del.var.elements[0].a.elements[0]);
    TEST_ASSERT_EQUAL(2, dif.del.var.elements[0].a.elements[1]);
    // b implicitly truncated away
    TEST_ASSERT_EQUAL(1, dif.del.var.elements[1].a.count);
    TEST_ASSERT_EQUAL(3, dif.del.var.elements[1].a.elements[0]);
    // b implicitly truncated away
    TEST_ASSERT_EQUAL(1, dif.del.fix.count);
    TEST_ASSERT_EQUAL(5, dif.del.fix.elements[0].a[0]);
    TEST_ASSERT_EQUAL(6, dif.del.fix.elements[0].a[1]);
    TEST_ASSERT_EQUAL(0, dif.del.fix.elements[0].a[2]);     // 3rd element is implicitly zero-extended
    TEST_ASSERT_EQUAL(0, dif.del.fix.elements[0].b);        // b is implicitly zero-extended

    // Reverse version switch -- serialize v1.1 and then deserialize back using v1.0.
    dif.del.var.count = 1;
    dif.del.var.elements[0].a.count = 2;
    dif.del.var.elements[0].a.elements[0] = 11;
    dif.del.var.elements[0].a.elements[1] = 22;
    dif.del.fix.count = 2;
    dif.del.fix.elements[0].a[0] = 5;
    dif.del.fix.elements[0].a[1] = 6;
    dif.del.fix.elements[0].a[2] = 7;
    dif.del.fix.elements[0].b = 8;
    dif.del.fix.elements[1].a[0] = 100;
    dif.del.fix.elements[1].a[1] = 200;
    dif.del.fix.elements[1].a[2] = 123;
    dif.del.fix.elements[1].b = 99;
    size = sizeof(buf);
    TEST_ASSERT_EQUAL(0, regulated_delimited_A_1_1_serialize_(&dif, &buf[0], &size));
    TEST_ASSERT_EQUAL(30U, size);                           // the reference size was computed by hand
    TEST_ASSERT_EQUAL(0, regulated_delimited_A_1_0_deserialize_(&obj, &buf[0], &size));
    TEST_ASSERT_TRUE(regulated_delimited_A_1_0_is_del_(&obj));
    TEST_ASSERT_EQUAL(1, obj.del.var.count);
    TEST_ASSERT_EQUAL(2, obj.del.var.elements[0].a.count);
    TEST_ASSERT_EQUAL(11, obj.del.var.elements[0].a.elements[0]);
    TEST_ASSERT_EQUAL(22, obj.del.var.elements[0].a.elements[1]);
    TEST_ASSERT_EQUAL(0, obj.del.var.elements[0].b);        // b is implicitly zero-extended
    TEST_ASSERT_EQUAL(2, obj.del.fix.count);
    TEST_ASSERT_EQUAL(5, obj.del.fix.elements[0].a[0]);     // 3rd is implicitly truncated, b is implicitly truncated
    TEST_ASSERT_EQUAL(6, obj.del.fix.elements[0].a[1]);
    TEST_ASSERT_EQUAL(100, obj.del.fix.elements[1].a[0]);   // 3rd is implicitly truncated, b is implicitly truncated
    TEST_ASSERT_EQUAL(200, obj.del.fix.elements[1].a[1]);
}

int main(void)
{
    testStructDelimited();
    return 0;
}
