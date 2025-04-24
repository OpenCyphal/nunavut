#
# Copyright Amazon.com Inc. or its affiliates.
#

# This are compile options for all modules we compile. Architecture-specific stuff should be inherited from the
# board library's compile options since it's that module that defines what CPU we're running on.
add_compile_options(
    $<$<COMPILE_LANGUAGE:CXX>:-fno-rtti>
    $<$<COMPILE_LANGUAGE:CXX>:-fno-exceptions>
    $<$<COMPILE_LANGUAGE:CXX>:-fno-unwind-tables>
    -fdata-sections
    -ffunction-sections
    $<IF:$<CONFIG:Debug>,-Og,-Os>
    -ggdb3
    -fverbose-asm
    $<$<COMPILE_LANGUAGE:CXX>:-fno-use-cxa-atexit>
    $<$<COMPILE_LANGUAGE:ASM>:-x$<SEMICOLON>assembler-with-cpp>
    -mcpu=cortex-m7
    -mthumb
    -mlittle-endian
    $<$<C_COMPILER_ID:GNU>:-specs=nosys.specs>
    $<$<C_COMPILER_ID:GNU>:-specs=nano.specs>
    $<$<C_COMPILER_ID:gnu>:-save-temps>
)

add_link_options(
    LINKER:--print-memory-usage
    LINKER:--gc-sections
    --specs=nano.specs
    --specs=nosys.specs
    $<$<COMPILE_LANGUAGE:CXX>:-fno-rtti>
    $<$<COMPILE_LANGUAGE:CXX>:-fno-exceptions>
    $<$<COMPILE_LANGUAGE:CXX>:-fno-unwind-tables>
    $<$<COMPILE_LANGUAGE:CXX>:-fno-use-cxa-atexit>
)
