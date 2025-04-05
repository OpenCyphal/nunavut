#
# Copyright Amazon.com Inc. or its affiliates.
#

set(CMAKE_SYSTEM_NAME Generic)
# This should be board-specific but we also should have this set by the toolchain. Need to fix then when we add new
# target processors.
set(CMAKE_SYSTEM_PROCESSOR "cortex-m7")

set(TOOLCHAIN_PREFIX arm-none-eabi)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

find_program(COMPILER_PATH ${TOOLCHAIN_PREFIX}-gcc)

# Take the directory the compiler is located on
cmake_path(GET COMPILER_PATH PARENT_PATH CMAKE_TOOLCHAIN_ROOT)

set(CMAKE_C_COMPILER        ${CMAKE_TOOLCHAIN_ROOT}/${TOOLCHAIN_PREFIX}-gcc      CACHE INTERNAL "C Compiler")
set(CMAKE_LINKER            ${CMAKE_TOOLCHAIN_ROOT}/${TOOLCHAIN_PREFIX}-ld       CACHE INTERNAL "Linker")
set(CMAKE_CXX_COMPILER      ${CMAKE_TOOLCHAIN_ROOT}/${TOOLCHAIN_PREFIX}-g++      CACHE INTERNAL "C++ Compiler")
set(CMAKE_ASM_COMPILER      ${CMAKE_C_COMPILER}                                  CACHE INTERNAL "Assembler")
set(CMAKE_OBJCOPY           ${CMAKE_TOOLCHAIN_ROOT}/${TOOLCHAIN_PREFIX}-objcopy  CACHE INTERNAL "Object Copy")
set(CMAKE_OBJDUMP           ${CMAKE_TOOLCHAIN_ROOT}/${TOOLCHAIN_PREFIX}-objdump  CACHE INTERNAL "Object 💩")
set(CMAKE_RANLIB            ${CMAKE_TOOLCHAIN_ROOT}/${TOOLCHAIN_PREFIX}-ranlib   CACHE INTERNAL "Library Indexer")
set(CMAKE_SIZE_UTIL         ${CMAKE_TOOLCHAIN_ROOT}/${TOOLCHAIN_PREFIX}-size     CACHE INTERNAL "Size Utility")
