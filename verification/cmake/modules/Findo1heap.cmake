#
# Framework : O(1) Heap
# Homepage: https://github.com/pavel-kirienko/o1heap.git
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

set(O1HEAP_SUBMODULE "${NUNAVUT_SUBMODULES_ROOT}/o1heap")

if(EXISTS "${O1HEAP_SUBMODULE}/README.md")
    set(O1HEAP_FOUND ON)
else()
    message(FATAL_ERROR "Couldn't find ${O1HEAP_SUBMODULE}/README.md. Did you forget to git submodule --init?")
endif()

include_directories(
    ${O1HEAP_SUBMODULE}
)

add_library(o1heap STATIC EXCLUDE_FROM_ALL
            ${O1HEAP_SUBMODULE}/o1heap/o1heap.c
)

target_compile_options(o1heap PUBLIC
                        "${NUNAVUT_VERIFICATION_EXTRA_COMPILE_FLAGS}"
                       )

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(o1heap
    REQUIRED_VARS O1HEAP_FOUND
)
