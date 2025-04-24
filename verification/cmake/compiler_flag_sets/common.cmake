#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#

# C, CXX, LD, and AS flags for building native unit tests. These flags also include
# instrumentation for code coverage.
#

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(C_FLAG_SET)
set(EXE_LINKER_FLAG_SET)

if(${NUNAVUT_VERIFICATION_TARGET_PLATFORM} STREQUAL "armv7m")
    include(${CMAKE_CURRENT_LIST_DIR}/arm-none-eabi.cmake)
endif()

#
# Diagnostics for C and C++
#
list(APPEND C_FLAG_SET
    "-pedantic"
    "-Wall"
    "-Wextra"
    "-Werror"
    "-Wshadow"
    "-Wfloat-equal"
    "-Wconversion"
    "-Wunused-parameter"
    "-Wunused-variable"
    "-Wunused-value"
    "-Wcast-align"
    "-Wmissing-declarations"
    "-Wmissing-field-initializers"
    "-Wdouble-promotion"
    "-Wswitch-enum"
    "-Wtype-limits"
)

if(${NUNAVUT_VERIFICATION_TARGET_PLATFORM} STREQUAL "native32")
    list(APPEND C_FLAG_SET "-m32")
    list(APPEND EXE_LINKER_FLAG_SET "-m32")
endif()

set(CXX_FLAG_SET ${C_FLAG_SET})
set(ASM_FLAG_SET ${C_FLAG_SET})

#
# C++ only diagnostics
#
list(APPEND CXX_FLAG_SET
    "-Wsign-conversion"
    "-Wsign-promo"
    "-Wold-style-cast"
    "-Wzero-as-null-pointer-constant"
    "-Wnon-virtual-dtor"
    "-Woverloaded-virtual"
    "-Wno-c++17-attribute-extensions"
)

if(LOCAL_NUNAVUT_VERIFICATION_TARGET_LANG STREQUAL "c")
    #
    # If we are testing C headers with C++ tests we have to disable
    # certain checks to allow the inline code to compile without
    # warnings.
    #
    list(APPEND CXX_FLAG_SET "-Wno-old-style-cast")
endif()


if(CETLVAST_DISABLE_CPP_EXCEPTIONS)
    message(STATUS "CETLVAST_DISABLE_CPP_EXCEPTIONS is true. Adding -fno-exceptions to compiler flags.")
    list(APPEND CXX_FLAG_SET "-fno-exceptions")
endif()

list(APPEND CXX_FLAG_SET ${C_FLAG_SET})
list(APPEND ASM_FLAG_SET ${C_FLAG_SET})

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
    "-fno-omit-frame-pointer"
    "-fno-optimize-sibling-calls"
)

add_compile_options(
    "$<$<CONFIG:Release>:-O2>"
    "$<$<CONFIG:Debug,DebugAsan,DebugCov>:-Og>"
    "$<$<CONFIG:Debug,DebugAsan,DebugCov>:-ggdb>"
)
add_compile_options("$<$<COMPILE_LANGUAGE:C>:${C_FLAG_SET}>")
add_compile_options("$<$<COMPILE_LANGUAGE:CXX>:${CXX_FLAG_SET}>")
add_compile_options("$<$<COMPILE_LANGUAGE:ASM>:${ASM_FLAG_SET}>")
add_compile_options("$<$<C_COMPILER_ID:GNU>:-Wno-stringop-overflow>")
add_compile_options("$<$<CONFIG:DebugAsan>:${LOCAL_SANITIZER_OPTIONS}>")
add_compile_options(
    "$<$<AND:$<CONFIG:DebugCov>,$<C_COMPILER_ID:GNU>>:--coverage>"
    "$<$<AND:$<CONFIG:DebugCov>,$<COMPILE_LANG_AND_ID:CXX,AppleClang,Clang>>:-fno-elide-constructors>"
    "$<$<AND:$<CONFIG:DebugCov>,$<C_COMPILER_ID:AppleClang,Clang>>:-fprofile-instr-generate>"
    "$<$<AND:$<CONFIG:DebugCov>,$<C_COMPILER_ID:AppleClang,Clang>>:-ftest-coverage>"
    "$<$<AND:$<CONFIG:DebugCov>,$<C_COMPILER_ID:AppleClang,Clang>>:-fprofile-arcs>"
    "$<$<AND:$<CONFIG:DebugCov>,$<C_COMPILER_ID:AppleClang,Clang>>:-fcoverage-mapping>"
)
add_link_options(${EXE_LINKER_FLAG_SET})
add_link_options("$<$<CONFIG:DebugAsan>:${LOCAL_SANITIZER_OPTIONS}>")
add_link_options("$<$<CONFIG:DebugCov>:--coverage>")
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_EXTENSIONS OFF)
