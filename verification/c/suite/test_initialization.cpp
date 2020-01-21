/*
 * Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Sanity tests.
 */
#include "gmock/gmock.h"
#include "uavcan/primitive/Empty_1_0.h"
#include "uavcan/si/unit/force/Vector3_1_0.h"
#include "uavcan/_register/Name_1_0.h"

/**
 * Verify an empty, complex type compiles and initializes.
 */
TEST(InitializationTests, InitEmpty)
{
    UAVCAN_PRIMITIVE_Empty_1_0 subject;
    ASSERT_EQ(nullptr, init_uavcan_primitive_empty_1_0(nullptr));
    UAVCAN_PRIMITIVE_Empty_1_0* ptr_to_subject = init_uavcan_primitive_empty_1_0(&subject);
    ASSERT_EQ(ptr_to_subject, &subject);
    ASSERT_EQ(0U, subject);
}

/**
 * Verify initialization of a primitive with a static array.
 */
TEST(InitializationTests, InitWithPrimitiveArray)
{
    UAVCAN_SI_UNIT_FORCE_Vector3_1_0 subject;
    ASSERT_EQ(nullptr, init_uavcan_si_unit_force_vector3_1_0(nullptr));
    UAVCAN_SI_UNIT_FORCE_Vector3_1_0* ptr_to_subject = init_uavcan_si_unit_force_vector3_1_0(&subject);
    ASSERT_EQ(ptr_to_subject, &subject);
    ASSERT_FALSE(UAVCAN_SI_UNIT_FORCE_Vector3_1_0_NEWTON_ARRAY_IS_VARIABLE_LENGTH);
    for (std::size_t i = 0; i < UAVCAN_SI_UNIT_FORCE_Vector3_1_0_NEWTON_ARRAY_LENGTH(&subject); ++i)
    {
        ASSERT_FLOAT_EQ(0.0f, subject.newton[i]);
    }
}

/**
 * Verify initialization of a primitive with a variable-length array.
 */
TEST(InitializationTests, InitWithVariableLengthArray)
{
    UAVCAN__REGISTER_Name_1_0 subject;
    ASSERT_EQ(nullptr, init_uavcan__register_name_1_0(nullptr));
    UAVCAN__REGISTER_Name_1_0* ptr_to_subject = init_uavcan__register_name_1_0(&subject);
    ASSERT_EQ(ptr_to_subject, &subject);
    ASSERT_TRUE(UAVCAN__REGISTER_Name_1_0_NAME_ARRAY_IS_VARIABLE_LENGTH);
    ASSERT_EQ(0U, UAVCAN__REGISTER_Name_1_0_NAME_ARRAY_LENGTH(&subject));
}
