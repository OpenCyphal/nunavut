#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#

find_program(LCOV lcov)

if(LCOV)

    # +---------------------------------------------------------------------------+
    #   What follows are some gymnastics to allow coverage reports to be generated
    #   using either gcc or clang but resulting in the same .info format. The
    #   consistent output is needed to ensure we can merge and compare coverage data
    #   regardless of the compiler used to create the tests.

    set(VERIFICATION_COVERAGE_GOV_TOOL_ARG )

    if (VERIFICATION_COVERAGE_USE_LLVM_COV)
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
                DESTINATION ${CMAKE_CURRENT_BINARY_DIR}
                NO_SOURCE_PERMISSIONS
                FILE_PERMISSIONS OWNER_READ
                                OWNER_WRITE
                                OWNER_EXECUTE
                                GROUP_READ
                                GROUP_EXECUTE
                                WORLD_READ
                                WORLD_EXECUTE)
            set(VERIFICATION_COVERAGE_GOV_TOOL_ARG "--gcov-tool" "${CMAKE_CURRENT_BINARY_DIR}/gcov_tool.sh")
        else()
            message(WARNING "llvm-cov was not found but we are compiling using clang. The coverage report build step may fail.")
        endif()
    endif()
    # +---------------------------------------------------------------------------+

    #
    # function: define_coverage_native_test_run - creates a makefile target that will build and
    # run individual unit tests. This also properly sets up the coverage counters.
    #
    # param: NAME string        - The name of the test to run.
    # param: JOB_POOL optional[string] - The name of a Ninja job pool to add the custom command to.
    # param: BASE_DIR optional[path] (default: CMAKE_CURRENT_BINARY_DIR)
    #                           - The root path under which object files for the test can be found. As these are
    #                             normally found under ${CMAKE_CURRENT_BINARY_DIR}/CMakeFiles its best to use
    #                             CMAKE_CURRENT_BINARY_DIR as this value which is the default. This can, however
    #                             cause problems when using Ninja Multi-Config.
    # param: OUTDIR path        - The path where the test binaries live and under which the info files will be
    #                             generated.
    # param: SOURCE_FILTER_DIR pattern - pattern for paths to include (exclusively) in the coverage
    #                                    data. For example, test/foo/*
    # param: OUT_CUSTOM_TARGET  - If set, this is the name of a local variable set in the calling (parent) scope
    #                             that contains the name of the custom target (i.e. add_custom_target) defined by
    #                             this method that will run the test and lcov to generate an info file.
    # param: OUT_INFO_FILE      - If set, this is the name of a local variable set in the calling (parent) scope
    #                             that will contain the info file generated with coverage data from the test run.
    #
    function(define_coverage_native_test_run)

        # +-[input]----------------------------------------------------------------+
        set(options)
        set(singleValueArgs
            NAME
            JOB_POOL
            OUTDIR
            SOURCE_FILTER_DIR
            BASE_DIR
            OUT_CUSTOM_TARGET
            OUT_INFO_FILE
        )
        set(multiValueArgs)
        cmake_parse_arguments(PARSE_ARGV 0 ARG "${options}" "${singleValueArgs}" "${multiValueArgs}")

        if (NOT ARG_BASE_DIR)
            set(ARG_BASE_DIR ${CMAKE_CURRENT_BINARY_DIR})
        endif()

        # +-[body]-----------------------------------------------------------------+
        message(STATUS "Adding test ${ARG_NAME} for source ${ARG_SOURCE_FILTER_DIR} (${ARG_OUTDIR}/${ARG_NAME})")

        set(LOCAL_INFO_FILE "${ARG_OUTDIR}/coverage.${ARG_NAME}.filtered.info")
        set(LOCAL_RUN_TARGET "run_${ARG_NAME}_with_lcov")
        if (ARG_JOB_POOL)
            list(APPEND LOCAL_JOB_POOL_ARG "JOB_POOL" ${ARG_JOB_POOL})
        else()
            set(LOCAL_JOB_POOL_ARG)
        endif()

        add_custom_command(
            WORKING_DIRECTORY ${ARG_BASE_DIR}
            ${LOCAL_JOB_POOL_ARG}
            COMMAND # Reset coverage data
                ${LCOV}
                        ${VERIFICATION_COVERAGE_GOV_TOOL_ARG}
                        --zerocounters
                        --directory ${ARG_BASE_DIR}
            COMMAND # Generate initial "zero coverage" data.
                ${LCOV}
                        ${VERIFICATION_COVERAGE_GOV_TOOL_ARG}
                        --rc lcov_branch_coverage=1
                        --capture
                        --initial
                        --directory ${ARG_BASE_DIR}
                        --output-file ${ARG_OUTDIR}/coverage.baseline.info
            COMMAND
                ${ARG_OUTDIR}/${ARG_NAME}
            COMMAND # Generate coverage from tests.
                ${LCOV}
                        ${VERIFICATION_COVERAGE_GOV_TOOL_ARG}
                        --rc lcov_branch_coverage=1
                        --capture
                        --directory ${ARG_BASE_DIR}
                        --test-name ${ARG_NAME}
                        --output-file ${ARG_OUTDIR}/coverage.${ARG_NAME}.test.info
            COMMAND # Combine all the test runs with the baseline
                ${LCOV}
                        ${VERIFICATION_COVERAGE_GOV_TOOL_ARG}
                        --rc lcov_branch_coverage=1
                        --add-tracefile ${ARG_OUTDIR}/coverage.baseline.info
                        --add-tracefile ${ARG_OUTDIR}/coverage.${ARG_NAME}.test.info
                        --output-file ${ARG_OUTDIR}/coverage.${ARG_NAME}.info
            COMMAND # Filter only the interesting data
                ${LCOV}
                        ${VERIFICATION_COVERAGE_GOV_TOOL_ARG}
                        --rc lcov_branch_coverage=1
                        --extract ${ARG_OUTDIR}/coverage.${ARG_NAME}.info
                        ${ARG_SOURCE_FILTER_DIR}
                        --output-file ${LOCAL_INFO_FILE}
            OUTPUT ${LOCAL_INFO_FILE}
            DEPENDS ${ARG_NAME}
        )

        add_custom_target(${LOCAL_RUN_TARGET} DEPENDS ${LOCAL_INFO_FILE})

        # +-[OUT]---------------------------------------------------------------------+

        if (ARG_OUT_CUSTOM_TARGET)
            set(${ARG_OUT_CUSTOM_TARGET} "${LOCAL_RUN_TARGET}" PARENT_SCOPE)
        endif()

        if (ARG_OUT_INFO_FILE)
            set(${ARG_OUT_INFO_FILE} ${LOCAL_INFO_FILE} PARENT_SCOPE)
        endif()

    endfunction()

    #
    # function: define_coverage_summary - Runs lcov over info files generated by test runs defined by calls to
    # define_coverage_native_test_run and creates a single, summarized coverage info file.
    #
    # Example Usage::
    #
    #    define_coverage_native_test_run(
    #       NAME my_test
    #       OUTDIR ${CMAKE_CURRENT_BINARY_DIR}/$<CONFIG>
    #       SOURCE_FILTER_DIR ${CMAKE_CURRENT_SOURCE_DIR}/\\*
    #       OUT_INFO_FILE LOCAL_INFO_FILE
    #    )
    #
    #    list(APPEND ALL_INFO_FILES ${LOCAL_INFO_FILE})
    #
    #    # add other tests and append to LOCAL_INFO_FILE list.
    #
    #    define_coverage_summary(
    #        INFO_FILES ${LOCAL_INFO_FILE}
    #        OUTDIR ${CMAKE_CURRENT_BINARY_DIR}/$<CONFIG>
    #        OUT_INFO_FILE LOCAL_SUMMARY_INFO_FILE
    #    )
    #    # ${LOCAL_SUMMARY_INFO_FILE} can be used as input to genhtml or uploaded to a coverage index service like
    #    # coveralls.io
    #
    # param: INFO_FILES list[path]  - A list of info files to include in the summary.
    # param: OUTDIR path            - The path where the info files live.
    # param: OUT_CUSTOM_TARGET      - If set, this is the name of a local variable set in the calling (parent) scope
    #                                 that contains the name of a custom target (i.e. add_custom_target) defined by
    #                                 this method that run the info summary rule.
    # param: OUT_INFO_FILE          - If set, this is the name of a local variable set in the calling (parent) scope
    #                                 that will contain the info file generated with coverage data from the test run.
    #
    function(define_coverage_summary)

        # +-[inputs]---------------------------------------------------------------+
        set(options)
        set(singleValueArgs
            OUTDIR
            OUT_INFO_FILE
            OUT_CUSTOM_TARGET
        )
        set(multiValueArgs
            INFO_FILES
        )
        cmake_parse_arguments(PARSE_ARGV 0 ARG "${options}" "${singleValueArgs}" "${multiValueArgs}")

        # +-[body]-----------------------------------------------------------------+

        set(LOCAL_ALL_INFO_FILE "${ARG_OUTDIR}/coverage.all.info")
        set(LOCAL_FILTERED_INFO_FILE "${ARG_OUTDIR}/coverage.info")
        list(REMOVE_DUPLICATES ARG_INFO_FILES)
        set(LOCAL_ADD_TRACEFILE_ARGS)
        foreach(LOCAL_INFO_FILE ${ARG_INFO_FILES})
            list(APPEND LOCAL_ADD_TRACEFILE_ARGS --add-tracefile ${LOCAL_INFO_FILE})
        endforeach()

        add_custom_command(
            OUTPUT ${LOCAL_ALL_INFO_FILE}
            COMMAND
                ${LCOV}
                    ${VERIFICATION_COVERAGE_GOV_TOOL_ARG}
                    --rc lcov_branch_coverage=1
                    ${LOCAL_ADD_TRACEFILE_ARGS}
                    --output-file ${LOCAL_ALL_INFO_FILE}
            DEPENDS ${ARG_INFO_FILES}
        )

        add_custom_command(
            OUTPUT ${LOCAL_FILTERED_INFO_FILE}
            COMMAND
                ${LCOV}
                    ${VERIFICATION_COVERAGE_GOV_TOOL_ARG}
                    --rc lcov_branch_coverage=1
                    --extract ${LOCAL_ALL_INFO_FILE}
                    ${LOCAL_PROJECT_ROOT}/\\*
                    --output-file ${LOCAL_FILTERED_INFO_FILE}
            DEPENDS ${LOCAL_ALL_INFO_FILE}
        )

        add_custom_target(
            cov_info
            DEPENDS ${LOCAL_FILTERED_INFO_FILE}
        )

        # +-[outputs]--------------------------------------------------------------+
        if (ARG_OUT_CUSTOM_TARGET)
            set(${ARG_OUT_CUSTOM_TARGET} "cov_info" PARENT_SCOPE)
        endif()

        if (ARG_OUT_INFO_FILE)
            set(${ARG_OUT_INFO_FILE} ${LOCAL_FILTERED_INFO_FILE} PARENT_SCOPE)
        endif()

    endfunction()



    #
    # function: define_coverage_zero_all - Defines a custom rule to zero out all counter under a given directory.
    #
    # param: OUTDIR path            - The path where the info files live.
    # param: OUT_CUSTOM_TARGET      - If set, this is the name of a local variable set in the calling (parent) scope
    #                                 that contains the name of a custom target (i.e. add_custom_target) defined by
    #                                 this method that run the info summary rule.
    #
    function(define_coverage_zero_all)
        # +-[inputs]---------------------------------------------------------------+
        set(options)
        set(singleValueArgs
            OUTDIR
            OUT_CUSTOM_TARGET
        )
        set(multiValueArgs)
        cmake_parse_arguments(PARSE_ARGV 0 ARG "${options}" "${singleValueArgs}" "${multiValueArgs}")

        # +-[body]-----------------------------------------------------------------+

        add_custom_target(
            cov_zero
            ${LCOV}
                ${VERIFICATION_COVERAGE_GOV_TOOL_ARG}
                --zerocounters
                --directory ${ARG_OUTDIR}
            COMMENT "Resetting coverage counters under ${ARG_OUTDIR}"
        )

        # +-[outputs]--------------------------------------------------------------+
        if (ARG_OUT_CUSTOM_TARGET)
            set(${ARG_OUT_CUSTOM_TARGET} "cov_zero" PARENT_SCOPE)
        endif()

    endfunction()

endif()

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(verification-coverage
    LCOV_FOUND
)
