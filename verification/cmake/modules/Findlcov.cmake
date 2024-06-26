#
# Find lcov and deal with clang weridness.
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

find_program(LCOV lcov)

if(LCOV)

    # +---------------------------------------------------------------------------+
    #   What follows are some gymnastics to allow coverage reports to be generated
    #   using either gcc or clang but resulting in the same .info format. The
    #   consistent output is needed to ensure we can merge and compare coverage data
    #   regardless of the compiler used to create the tests.

    set(NUNAVUT_GOV_TOOL_ARG )

    if (${NUNAVUT_USE_LLVM_COV})
        # Try to find llvm coverage. If we don't find it
        # we'll simply omit the tool arg and hope that lcov
        # can figure it out.
        # We also add some hints to help on osx. You may need to install llvm from
        # homebrew since it doesn't look like it comes with xcode.
        find_program(LLVM_COV
            NAMES
                llvm-cov
                llvm-cov-6.0
            HINTS
                /usr/local/opt/llvm/bin
        )

        if (LLVM_COV)
            message(STATUS "Generating an llvm-cov wrapper to enable lcov report generation from clang output.")
            # Thanks to http://logan.tw/posts/2015/04/28/check-code-coverage-with-clang-and-lcov/
            file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/${CMAKE_FILES_DIRECTORY}/gcov_tool.sh "#!/usr/bin/env bash\nexec ${LLVM_COV} gcov \"$@\"\n")
            file(COPY ${CMAKE_CURRENT_BINARY_DIR}/${CMAKE_FILES_DIRECTORY}/gcov_tool.sh
                DESTINATION ${NUNAVUT_VERIFICATIONS_BINARY_DIR}
                NO_SOURCE_PERMISSIONS
                FILE_PERMISSIONS OWNER_READ
                                OWNER_WRITE
                                OWNER_EXECUTE
                                GROUP_READ
                                GROUP_EXECUTE
                                WORLD_READ
                                WORLD_EXECUTE)
            set(NUNAVUT_GOV_TOOL_ARG "--gcov-tool" "${NUNAVUT_VERIFICATIONS_BINARY_DIR}/gcov_tool.sh")
        else()
            message(WARNING "llvm-cov was not found but we are compiling using clang. The coverage report build step may fail.")
        endif()
    endif()
    # +---------------------------------------------------------------------------+

    #
    # function: define_native_test_run_with_lcov - creates a makefile target that will build and
    # run individual unit tests. This also properly sets up the coverage counters.
    #
    # param: ARG_TEST_NAME string - The name of the test to run. A target will be created
    #                          with the name run_${ARG_TEST_NAME}_with_lcov
    # param: ARG_OUTDIR path - The path where the test binaries live.
    # param: ARG_SOURCE_FILTER_DIR pattern - pattern for paths to include (exclusively) in the coverage
    #                                        data.
    #
    function(define_native_test_run_with_lcov ARG_TEST_NAME ARG_OUTDIR ARG_SOURCE_FILTER_DIR)
        message(STATUS "Adding test ${ARG_TEST_NAME} for source ${ARG_SOURCE_FILTER_DIR}")
        add_custom_command(
            COMMAND # Reset coverage data
                ${LCOV}
                        ${NUNAVUT_GOV_TOOL_ARG}
                        --zerocounters
                        --directory ${CMAKE_CURRENT_BINARY_DIR}
            COMMAND # Generate initial "zero coverage" data.
                ${LCOV}
                        ${NUNAVUT_GOV_TOOL_ARG}
                        --rc lcov_branch_coverage=1
                        --capture
                        --initial
                        --directory ${CMAKE_CURRENT_BINARY_DIR}
                        --output-file ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.baseline.info
            COMMAND
                ${ARG_OUTDIR}/${ARG_TEST_NAME}
            COMMAND # Generate coverage from tests.
                ${LCOV}
                        ${NUNAVUT_GOV_TOOL_ARG}
                        --rc lcov_branch_coverage=1
                        --capture
                        --directory ${CMAKE_CURRENT_BINARY_DIR}
                        --test-name ${ARG_TEST_NAME}
                        --output-file ${ARG_OUTDIR}/coverage.${ARG_TEST_NAME}.test.info
            COMMAND # Combine all the test runs with the baseline
                ${LCOV}
                        ${NUNAVUT_GOV_TOOL_ARG}
                        --rc lcov_branch_coverage=1
                        --add-tracefile ${NUNAVUT_VERIFICATIONS_BINARY_DIR}/coverage.baseline.info
                        --add-tracefile ${ARG_OUTDIR}/coverage.${ARG_TEST_NAME}.test.info
                        --output-file ${ARG_OUTDIR}/coverage.${ARG_TEST_NAME}.info
            COMMAND # Filter only the interesting data
                ${LCOV}
                        ${NUNAVUT_GOV_TOOL_ARG}
                        --rc lcov_branch_coverage=1
                        --extract ${ARG_OUTDIR}/coverage.${ARG_TEST_NAME}.info
                        ${ARG_SOURCE_FILTER_DIR}
                        --output-file ${ARG_OUTDIR}/coverage.${ARG_TEST_NAME}.filtered.info
            OUTPUT ${ARG_OUTDIR}/coverage.${ARG_TEST_NAME}.filtered.info
            DEPENDS ${ARG_TEST_NAME}
        )

        add_custom_target(
            run_${ARG_TEST_NAME}_with_lcov
            DEPENDS ${ARG_OUTDIR}/coverage.${ARG_TEST_NAME}.filtered.info
        )

    endfunction()

endif()

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(lcov
    LCOV_FOUND
)
