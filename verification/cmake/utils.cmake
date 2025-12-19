#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#

# +===========================================================================+
# | UNIT TESTING
# +===========================================================================+
#
# function: define_native_unit_test - creates an executable target and links it
# to the "all" target to build a gtest binary for the given test source.
#
# param: FRAMEWORK [gtest|unity] - The name of the test framework to use.
# param: NAME string             - The name to give the test target.
# param: SOURCE List[path]       - A list of source files to compile into
#                                  the test binary.
# param: OUTDIR path             - A path to output test binaries and coverage data under.
# param: DSDL_TARGETS List[str]  - Zero to many targets that generate types under test.
#
function(define_native_unit_test)

    # +--[ INPUTS ]-----------------------------------------------------------+
    set(options "")
    set(monoValues FRAMEWORK NAME OUTDIR)
    set(multiValues SOURCE DSDL_TARGETS)

    cmake_parse_arguments(
        ARG
        "${options}"
        "${monoValues}"
        "${multiValues}"
        ${ARGN}
    )

    # +--[ BODY ]------------------------------------------------------------+
    add_executable(${ARG_NAME} ${ARG_SOURCE})

    if (ARG_DSDL_TARGETS)
        add_dependencies(${ARG_NAME} ${ARG_DSDL_TARGETS})
        target_link_libraries(${ARG_NAME} PUBLIC ${ARG_DSDL_TARGETS})
    endif()

    if (${ARG_FRAMEWORK} STREQUAL "gtest")
        target_link_libraries(${ARG_NAME} PUBLIC gmock_main)
    elseif (${ARG_FRAMEWORK} STREQUAL "unity")
        target_link_libraries(${ARG_NAME} PUBLIC unity_core)
    elseif (${ARG_FRAMEWORK} STREQUAL "none")
        message(STATUS "${ARG_NAME}: No test framework")
        target_compile_options(${ARG_NAME} PRIVATE "$<$<C_COMPILER_ID:GNU>:-fanalyzer>")
        target_compile_options(${ARG_NAME} PRIVATE "$<$<C_COMPILER_ID:GNU>:-fanalyzer-checker=taint>")
    else()
        message(FATAL_ERROR "${ARG_FRAMEWORK} isn't a supported unit test framework. Currently we support gtest and unity.")
    endif()

    set_target_properties(${ARG_NAME}
                          PROPERTIES
                          RUNTIME_OUTPUT_DIRECTORY "${ARG_OUTDIR}"
    )

    add_custom_command(OUTPUT ${ARG_OUTDIR}/${ARG_NAME}-disassembly.S
                       DEPENDS ${ARG_NAME}
                       COMMAND ${CMAKE_OBJDUMP} -d ${ARG_OUTDIR}/${ARG_NAME}
                            --demangle
                            --disassemble-zeroes
                            --disassembler-options=reg-names-std
                            --syms
                            --special-syms
                            --all-headers
                            --wide > ${ARG_OUTDIR}/${ARG_NAME}-disassembly.S
                       COMMENT "Creating disassembly from ${ARG_NAME}"
    )

    add_custom_target(${ARG_NAME}-disassembly DEPENDS ${ARG_OUTDIR}/${ARG_NAME}-disassembly.S)

endfunction()

#
# function: handle_nunavut_verification_language_and_standard - Parse NUNAVUT_VERIFICATION_LANG,
# NUNAVUT_VERIFICATION_LANG_STANDARD, and NUNAVUT_VERIFICATION_TARGET_PLATFORM applying defaults,
# error checking, and other transformations to produce a consistent result for these values.
#
# option: PRINT_STATUS                              - If set then STATUS messages will be emitted
#                           to make the results of this function visible in configuration logs.
# option: REQUIRED                                  - If set then each language standard will have
#                           their coresponding CMAKE_[langaug]_STANDARD_REQUIRED variable set.
# param: OUT_LOCAL_VERIFICATION_TARGET_LANGUAGE     - The name of a variable to set in the parent
#                           scope with the resolved verification target language. This shall be a valid,
#                           built-in --target-language value for Nunavut.
# param: OUT_VERIFICATION_LANGUAGE_STANDARD_CPP     - The name of a variable to set in the parent
#                           scope with the resolved c++ standard to use when generating c++ headers.
#                           This shall be a valid built-in --language-standard value for Nunavut.
# param: OUT_VERIFICATION_LANGUAGE_STANDARD_C       - The name of a variable to set in the parent
#                           scope with the resolved c standard to use when generating c headers.
#                           This shall be a valid built-in --language-standard value for Nunavut.
function(handle_nunavut_verification_language_and_standard)
    # +--[ INPUTS ]-----------------------------------------------------------+
    set(options PRINT_STATUS REQUIRED)
    set(monoValues
        OUT_LOCAL_VERIFICATION_TARGET_LANGUAGE
        OUT_VERIFICATION_LANGUAGE_STANDARD_CPP
        OUT_VERIFICATION_LANGUAGE_STANDARD_C
    )
    set(multiValues "")

    cmake_parse_arguments(
        ARG
        "${options}"
        "${monoValues}"
        "${multiValues}"
        ${ARGN}
    )

    # +--[ BODY ]------------------------------------------------------------+

    if(DEFINED ENV{NUNAVUT_VERIFICATION_LANG})
        if (ARG_PRINT_STATUS)
            message(STATUS "Getting NUNAVUT_VERIFICATION_LANG from the environment ($ENV{NUNAVUT_VERIFICATION_LANG})")
        endif()
        set(NUNAVUT_VERIFICATION_LANG "$ENV{NUNAVUT_VERIFICATION_LANG}" CACHE STRING "The Nunavut output language to verify.")
    else()
        set(NUNAVUT_VERIFICATION_LANG "c" CACHE STRING "The Nunavut output language to verify.")
    endif()

    string(TOLOWER ${NUNAVUT_VERIFICATION_LANG} LOCAL_VERIFICATION_LANG)

    if(NOT (LOCAL_VERIFICATION_LANG STREQUAL "cpp" OR LOCAL_VERIFICATION_LANG STREQUAL "c"))
        message(FATAL_ERROR "Unknown or no verification language (${NUNAVUT_VERIFICATION_LANG}). Try cmake -DNUNAVUT_VERIFICATION_LANG:string=[cpp|c]")
    endif()

    if(DEFINED ENV{NUNAVUT_VERIFICATION_LANG_STANDARD})
        if (ARG_PRINT_STATUS)
            message(STATUS "Getting NUNAVUT_VERIFICATION_LANG_STANDARD from the environment ($ENV{NUNAVUT_VERIFICATION_LANG_STANDARD})")
        endif()
        set(NUNAVUT_VERIFICATION_LANG_STANDARD "$ENV{NUNAVUT_VERIFICATION_LANG_STANDARD}" CACHE STRING "The language standard to use when generating source for verification.")
    else()
        set(NUNAVUT_VERIFICATION_LANG_STANDARD "c11" CACHE STRING "The language standard to use when generating source for verification.")
    endif()

    if(NOT DEFINED ENV{NUNAVUT_VERIFICATION_TARGET_PLATFORM})
        set(NUNAVUT_VERIFICATION_TARGET_PLATFORM "native" CACHE STRING "The platform to compile for when generating source for verification.")
    endif()

    # C++
    if(LOCAL_VERIFICATION_LANG STREQUAL "cpp")
        string(TOLOWER ${NUNAVUT_VERIFICATION_LANG_STANDARD} LOCAL_VERIFICATION_LANG_CPP_STANDARD)
    else()
        set(LOCAL_VERIFICATION_LANG_CPP_STANDARD "c++20")
    endif()

    string(REGEX MATCH "c?e?t?l?[px\+]+-?([0-9]*).*" LOCAL_VERIFICATION_LANG_CPP_MATCH ${LOCAL_VERIFICATION_LANG_CPP_STANDARD})

    if(NOT LOCAL_VERIFICATION_LANG_CPP_MATCH)
        message(FATAL_ERROR "NUNAVUT_VERIFICATION_LANG_STANDARD (${LOCAL_VERIFICATION_LANG_CPP_STANDARD}) is in an unexpected format.")
    endif()

    set(LOCAL_VERIFICATION_LANG_CPP_MATCH ${CMAKE_MATCH_1})

    set(CMAKE_CXX_STANDARD ${LOCAL_VERIFICATION_LANG_CPP_MATCH} PARENT_SCOPE)
    if (ARG_REQUIRED)
        set(CMAKE_CXX_STANDARD_REQUIRED ON PARENT_SCOPE)
    endif()

    # C
    if(NUNAVUT_VERIFICATION_LANG STREQUAL "c")
        string(TOLOWER ${NUNAVUT_VERIFICATION_LANG_STANDARD} LOCAL_VERIFICATION_LANG_C_STANDARD)
    else()
        set(LOCAL_VERIFICATION_LANG_C_STANDARD "c11")
    endif()

    string(REGEX REPLACE "c-?([0-9]*).*" "\\1" LOCAL_VERIFICATION_LANG_C_MATCH ${LOCAL_VERIFICATION_LANG_C_STANDARD})

    if(NOT LOCAL_VERIFICATION_LANG_C_MATCH)
        message(FATAL_ERROR "NUNAVUT_VERIFICATION_LANG_STANDARD (${LOCAL_VERIFICATION_LANG_C_STANDARD}) is in an unexpected format.")
    endif()

    set(CMAKE_C_STANDARD ${LOCAL_VERIFICATION_LANG_C_MATCH} PARENT_SCOPE)
    if (ARG_REQUIRED)
        set(CMAKE_C_STANDARD_REQUIRED ON PARENT_SCOPE)
    endif()

    # PLATFORM
    if(NOT (${NUNAVUT_VERIFICATION_TARGET_PLATFORM} STREQUAL "native32" OR ${NUNAVUT_VERIFICATION_TARGET_PLATFORM} STREQUAL "native" OR ${NUNAVUT_VERIFICATION_TARGET_PLATFORM} STREQUAL "armv7m"))
        message(FATAL_ERROR "\"NUNAVUT_VERIFICATION_TARGET_PLATFORM=${NUNAVUT_VERIFICATION_TARGET_PLATFORM}\" is not a supported value.")
    endif()

    # STATUS
    if (ARG_PRINT_STATUS)
        message(STATUS "${ARG_OUT_LOCAL_VERIFICATION_TARGET_LANGUAGE} is ${LOCAL_VERIFICATION_LANG}")
        message(STATUS "NUNAVUT_VERIFICATION_TARGET_PLATFORM is ${NUNAVUT_VERIFICATION_TARGET_PLATFORM}")
        message(STATUS "${ARG_OUT_VERIFICATION_LANGUAGE_STANDARD_C} is ${NUNAVUT_VERIFICATION_LANG_STANDARD}")
        message(STATUS "${ARG_OUT_VERIFICATION_LANGUAGE_STANDARD_CPP} is ${LOCAL_VERIFICATION_LANG_CPP_STANDARD}")
        if (ARG_REQUIRED)
            set(LOCAL_REQUIRED_STATUS " (required)")
        else()
            set(LOCAL_REQUIRED_STATUS "")
        endif()
        message(STATUS "CMAKE_C_STANDARD is ${LOCAL_VERIFICATION_LANG_C_MATCH}${LOCAL_REQUIRED_STATUS}")
        message(STATUS "CMAKE_CXX_STANDARD is ${LOCAL_VERIFICATION_LANG_CPP_MATCH}${LOCAL_REQUIRED_STATUS}")
        message(STATUS "Is cross-compiling? ${CMAKE_CROSSCOMPILING}")
    endif()

    # +--[ OUT ]-------------------------------------------------------------+
    set(${ARG_OUT_LOCAL_VERIFICATION_TARGET_LANGUAGE} ${LOCAL_VERIFICATION_LANG} PARENT_SCOPE)
    set(${ARG_OUT_VERIFICATION_LANGUAGE_STANDARD_CPP} ${LOCAL_VERIFICATION_LANG_CPP_STANDARD} PARENT_SCOPE)
    set(${ARG_OUT_VERIFICATION_LANGUAGE_STANDARD_C} ${LOCAL_VERIFICATION_LANG_C_STANDARD} PARENT_SCOPE)
endfunction()
