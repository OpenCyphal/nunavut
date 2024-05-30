#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#

#
# Enable undefined behaviour sanitizer
#

include(${CMAKE_CURRENT_LIST_DIR}/common.cmake)


list(APPEND LOCAL_SANITIZER_OPTIONS
    "-fsanitize=address"
    "-fsanitize=pointer-compare"
    "-fsanitize=pointer-subtract"
    "-fsanitize=undefined"
        "-fsanitize=alignment"
        "-fsanitize=null"
        "-fsanitize=pointer-compare"
        "-fsanitize=pointer-subtract"
        "-fsanitize=pointer-overflow"
        "-fsanitize=bounds"
        "-fsanitize=signed-integer-overflow"
        "-fsanitize=shift"
        "-fsanitize=shift-exponent"
        "-fsanitize=shift-base"
        "-fsanitize=float-divide-by-zero"
        "-fsanitize=float-cast-overflow"
        "-fsanitize=pointer-overflow"
        "-fsanitize=builtin"
)

add_compile_options(
    ${LOCAL_SANITIZER_OPTIONS}
)

add_link_options(
   ${LOCAL_SANITIZER_OPTIONS}
)
