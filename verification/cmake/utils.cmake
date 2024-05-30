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
# param: TEST_NAME string             - The name to give the test target.
# param: TEST_SOURCE List[path]       - A list of source files to compile into
#                                  the test binary.
# param: OUTDIR path             - A path to output test binaries and coverage data under.
# param: DSDL_TARGETS List[str]  - Zero to many targets that generate types under test.
#
function(define_native_unit_test)

    # +--[ INPUTS ]-----------------------------------------------------------+
    set(options "")
    set(monoValues FRAMEWORK TEST_NAME OUTDIR)
    set(multiValues TEST_SOURCE DSDL_TARGETS)

    cmake_parse_arguments(
        ARG
        "${options}"
        "${monoValues}"
        "${multiValues}"
        ${ARGN}
    )

    # +--[ BODY ]------------------------------------------------------------+
    # TODO: we need to find a way to run this without googletest or unity. It they are orders of magnitude too complex
    # to run on gtest or unity binaries (may take hours to run).
    # target_compile_options(${ARG_TEST_NAME} PRIVATE "$<$<C_COMPILER_ID:GNU>:-fanalyzer>")
    # target_compile_options(${ARG_TEST_NAME} PRIVATE "$<$<C_COMPILER_ID:GNU>:-fanalyzer-checker=taint>")

    add_executable(${ARG_TEST_NAME} ${ARG_TEST_SOURCE})

    if (ARG_DSDL_TARGETS)
        add_dependencies(${ARG_TEST_NAME} ${ARG_DSDL_TARGETS})
        target_link_libraries(${ARG_TEST_NAME} PUBLIC ${ARG_DSDL_TARGETS})
    endif()

    if (${ARG_FRAMEWORK} STREQUAL "gtest")
        target_link_libraries(${ARG_TEST_NAME} PUBLIC gmock_main)
    elseif (${ARG_FRAMEWORK} STREQUAL "unity")
        target_link_libraries(${ARG_TEST_NAME} PUBLIC unity_core)
    else()
        message(FATAL_ERROR "${ARG_FRAMEWORK} isn't a supported unit test framework. Currently we support gtest and unity.")
    endif()

    set_target_properties(${ARG_TEST_NAME}
                          PROPERTIES
                          RUNTIME_OUTPUT_DIRECTORY "${ARG_OUTDIR}"
    )

    target_link_options(${ARG_TEST_NAME} PUBLIC
        "$<$<C_COMPILER_ID:GNU>:-Wl,-Map=${ARG_OUTDIR}/${ARG_TEST_NAME}.map,--cref>"
        "$<$<C_COMPILER_ID:Clang>:-Wl,-Map,${ARG_OUTDIR}/${ARG_TEST_NAME}.map>"
    )

    add_custom_command(OUTPUT ${ARG_OUTDIR}/${ARG_TEST_NAME}-disassembly.S
                       DEPENDS ${ARG_TEST_NAME}
                       COMMAND ${CMAKE_OBJDUMP} -d ${ARG_OUTDIR}/${ARG_TEST_NAME}
                            --demangle
                            --disassemble-zeroes
                            --disassembler-options=reg-names-std
                            --syms
                            --special-syms
                            --all-headers
                            --wide > ${ARG_OUTDIR}/${ARG_TEST_NAME}-disassembly.S
                       COMMENT "Creating disassembly from ${ARG_TEST_NAME}"
    )

    add_custom_target(${ARG_TEST_NAME}-disassembly DEPENDS ${ARG_OUTDIR}/${ARG_TEST_NAME}-disassembly.S)

endfunction()


#
# function: define_native_test_run - creates a makefile target that will build and
# run individual unit tests.
#
# param: ARG_TEST_NAME string - The name of the test to run. A target will be created
#                          with the name run_${ARG_TEST_NAME}
# param: ARG_OUTDIR path - The path where the test binaries live.
#
function(define_native_test_run)
    # +--[ INPUTS ]-----------------------------------------------------------+
    set(options "")
    set(monoValues TEST_NAME OUTDIR)
    set(multiValues "")

    cmake_parse_arguments(
        ARG
        "${options}"
        "${monoValues}"
        "${multiValues}"
        ${ARGN}
    )

    # +--[ BODY ]------------------------------------------------------------+
    add_custom_target(
        run_${ARG_TEST_NAME}
        COMMAND
            ${ARG_OUTDIR}/${ARG_TEST_NAME}
        DEPENDS
            ${ARG_TEST_NAME}
    )

endfunction()
