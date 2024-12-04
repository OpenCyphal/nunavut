/*
 * Copyright (C) OpenCyphal Development Team  <opencyphal.org>
 * Copyright Amazon.com Inc. or its affiliates.
 * SPDX-License-Identifier: MIT
 */

#include <stdio.h>
#include "ecorp/customer/record_2_8.h"

int main() {
    ecorp_customer_record_2_8 record;
    ecorp_customer_record_2_8_initialize_(&record);
    printf("This is where we'd write the ECorp app using these types.\r\n");
    return 0;
}
