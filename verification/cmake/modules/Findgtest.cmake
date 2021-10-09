#
# Framework : Googletest
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

set(GOOGLETEST_SUBMODULE "${NUNAVUT_SUBMODULES_ROOT}/googletest")

if(EXISTS "${GOOGLETEST_SUBMODULE}/googletest")
    set(GTEST_FOUND ON)
else()
    message(FATAL_ERROR "Couldn't find Googletest. Did you forget to git submodule update --init?")
endif()

include_directories(
    ${GOOGLETEST_SUBMODULE}/googletest/include
    ${GOOGLETEST_SUBMODULE}/googlemock/include
)

add_library(gmock_main STATIC EXCLUDE_FROM_ALL
            ${GOOGLETEST_SUBMODULE}/googletest/src/gtest-all.cc
            ${GOOGLETEST_SUBMODULE}/googlemock/src/gmock-all.cc
            ${GOOGLETEST_SUBMODULE}/googlemock/src/gmock_main.cc
)

target_include_directories(gmock_main PRIVATE
                           ${GOOGLETEST_SUBMODULE}/googletest
                           ${GOOGLETEST_SUBMODULE}/googlemock
)

target_compile_options(gmock_main PUBLIC
                       "-Wno-switch-enum"
                       "-Wno-zero-as-null-pointer-constant"
                       "-Wno-missing-declarations"
                       "-Wno-sign-conversion"
                       "-DGTEST_HAS_PTHREAD=0"
                       "${NUNAVUT_VERIFICATION_EXTRA_COMPILE_CFLAGS}"
                       )

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(gtest
    REQUIRED_VARS GTEST_FOUND
)
