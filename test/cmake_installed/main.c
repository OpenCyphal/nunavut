//
// Copyright (C) OpenCyphal Development Team  <opencyphal.org>
// Copyright Amazon.com Inc. or its affiliates.
// SPDX-License-Identifier: MIT
//

#include "smoke/Ping_1_0.h"

int main(void)
{
    smoke_Ping_1_0 ping;
    smoke_Ping_1_0_initialize_(&ping);
    ping.count = 42U;
    uint8_t buffer[smoke_Ping_1_0_SERIALIZATION_BUFFER_SIZE_BYTES_];
    size_t  size = sizeof(buffer);
    return ((smoke_Ping_1_0_serialize_(&ping, buffer, &size) == 0) && (size == sizeof(buffer))) ? 0 : 1;
}
