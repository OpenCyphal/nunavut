#
# Find nnvg and setup python environment to generate C++ from DSDL.
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# cSpell: words DNUNAVUT GTEST POSIX nnvg

# +---------------------------------------------------------------------------+
# | BUILD FUNCTIONS
# +---------------------------------------------------------------------------+

#
# :function: create_dsdl_library
# Creates a target to generate source and build object files from dsdl definitions.
#
# :param str NAME:               The name to give the target.
# :param str LANGUAGE:           The language to generate for this target.
# :param str LANGUAGE_STANDARD:  The language standard to use.
# :param list DSDL_FILES:        A list of paths to dsdl files to generate code for.
# :option ASSERT_TYPE_UNITY:     If set then the generated code will use the UNITY assert macro.
# :option ASSERT_TYPE_GTEST:     If set then the generated code will use the GTEST assert macro.
# :option ASSERT_TYPE_POSIX:     If set then the generated code will use the POSIX assert macro.
function (create_dsdl_library)
    #+-[input]----------------------------------------------------------------+
    set(options ASSERT_TYPE_UNITY ASSERT_TYPE_GTEST ASSERT_TYPE_POSIX)
    set(singleValueArgs NAME LANGUAGE LANGUAGE_STANDARD)
    set(multiValueArgs DSDL_FILES)
    cmake_parse_arguments(PARSE_ARGV 0 ARG "${options}" "${singleValueArgs}" "${multiValueArgs}")

    if (
            (ARG_ASSERT_TYPE_GTEST AND ARG_ASSERT_TYPE_POSIX) OR
            (ARG_ASSERT_TYPE_GTEST AND ARG_ASSERT_TYPE_UNITY) OR
            (ARG_ASSERT_TYPE_POSIX AND ARG_ASSERT_TYPE_UNITY)
       )
        message(FATAL_ERROR "Only one of ASSERT_TYPE_UNITY, ASSERT_TYPE_GTEST, or ASSERT_TYPE_POSIX can be set.")
    endif()

    #+-[body]-----------------------------------------------------------------+

    set(LOCAL_TARGET_NAME lib${ARG_NAME})
    set(LOCAL_OUTPUT_FOLDER ${CMAKE_CURRENT_BINARY_DIR}/${LOCAL_TARGET_NAME})
    set(LOCAL_OUTPUT_FOLDER_GENERATED ${LOCAL_OUTPUT_FOLDER}/generated)

    list(APPEND LOCAL_NNVG_CMD_ARGS --target-language)
    list(APPEND LOCAL_NNVG_CMD_ARGS ${ARG_LANGUAGE})
    list(APPEND LOCAL_NNVG_CMD_ARGS --outdir)
    list(APPEND LOCAL_NNVG_CMD_ARGS ${LOCAL_OUTPUT_FOLDER_GENERATED})
    list(APPEND LOCAL_NNVG_CMD_ARGS ${ARG_DSDL_FILES})


    execute_process(COMMAND ${NNVG} --list-outputs ${LOCAL_NNVG_CMD_ARGS}
                    OUTPUT_VARIABLE LOCAL_OUTPUT_FILES
                    RESULT_VARIABLE LOCAL_LIST_OUTPUTS_RESULT)

    execute_process(COMMAND ${NNVG} --list-inputs ${LOCAL_NNVG_CMD_ARGS}
                    OUTPUT_VARIABLE LOCAL_INPUT_FILES
                    RESULT_VARIABLE LOCAL_LIST_INPUTS_RESULT)

    add_custom_command(
                    OUTPUT ${LOCAL_OUTPUT_FILES}
                    COMMAND ${NNVG} ${LOCAL_NNVG_CMD_ARGS}
                    DEPENDS ${LOCAL_INPUT_FILES}
                    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                    COMMENT "Running nnvg")

    add_custom_target(${LOCAL_TARGET_NAME}-nnvg
                    DEPENDS ${LOCAL_OUTPUT_FILES})

    add_library(${LOCAL_TARGET_NAME} INTERFACE)

    add_dependencies(${LOCAL_TARGET_NAME} INTERFACE ${LOCAL_OUTPUT_FILES})

    target_include_directories(${LOCAL_TARGET_NAME} INTERFACE ${LOCAL_OUTPUT_FOLDER_GENERATED})

    if(ARG_ASSERT_TYPE_UNITY)
        target_compile_options(${LOCAL_TARGET_NAME} INTERFACE "-DNUNAVUT_ASSERT=TEST_ASSERT")
    elseif(ARG_ASSERT_TYPE_GTEST)
        target_compile_options(${LOCAL_TARGET_NAME} INTERFACE "-DNUNAVUT_ASSERT=ASSERT_TRUE")
    elseif(ARG_ASSERT_TYPE_POSIX)
        target_compile_options(${LOCAL_TARGET_NAME} INTERFACE "-DNUNAVUT_ASSERT=assert")
    endif()

    set(${ARG_TARGET_NAME}-OUTPUT ${OUTPUT_FILES} PARENT_SCOPE)

    #+-[output]---------------------------------------------------------------+

endfunction()

#
# :function: create_dsdl_target
# Creates a target that will generate source code from dsdl definitions.
#
# Extra command line arguments can be passed to nnvg by setting the string variable NNVG_FLAGS.
#
# :param str ARG_TARGET_NAME:               The name to give the target.
# :param str ARG_OUTPUT_LANGUAGE            The language to generate for this target.
# :param str ARG_OUTPUT_LANGUAGE_STD        The language standard use.
# :param Path ARG_OUTPUT_FOLDER:            The directory to generate all source under.
# :param Path ARG_DSDL_ROOT_DIR:            A directory containing the root namespace dsdl.
# :param bool ARG_ENABLE_CLANG_FORMAT:      If ON then clang-format will be run on each generated file.
# :param bool ARG_ENABLE_SER_ASSERT:        Generates code with serialization asserts enabled
# :param bool ARG_DISABLE_SER_FP:           Generates code with floating point support removed from
#                                           serialization logic.
# :param bool ARG_ENABLE_OVR_VAR_ARRAY:     Generates code with variable array capacity override enabled
# :param bool ARG_ENABLE_EXPERIMENTAL:      If true then nnvg is invoked with support for experimental
#                                           languages.
# :param str ARG_SER_ENDIANNESS:            One of 'any', 'big', or 'little' to pass as the value of the
#                                           nnvg `--target-endianness` argument. Set to an empty string
#                                           to omit this argument.
# :param str ARG_GENERATE_SUPPORT:          value for the nnvg --generate-support argument. See
#                                           nnvg --help for documentation
# :param ...:                               A list of paths to use when looking up dependent DSDL types.
# :return: Sets a variable "ARG_TARGET_NAME"-OUTPUT in the parent scope to the list of files the target
#           will generate. For example, if ARG_TARGET_NAME == 'foo-bar' then after calling this function
#           ${foo-bar-OUTPUT} will be set to the list of output files.
#
function (create_dsdl_target ARG_TARGET_NAME
                             ARG_OUTPUT_LANGUAGE
                             ARG_OUTPUT_LANGUAGE_STD
                             ARG_OUTPUT_FOLDER
                             ARG_DSDL_ROOT_DIR
                             ARG_ENABLE_CLANG_FORMAT
                             ARG_ENABLE_SER_ASSERT
                             ARG_DISABLE_SER_FP
                             ARG_ENABLE_OVR_VAR_ARRAY
                             ARG_ENABLE_EXPERIMENTAL
                             ARG_SER_ENDIANNESS
                             ARG_GENERATE_SUPPORT)

    separate_arguments(NNVG_CMD_ARGS UNIX_COMMAND "${NNVG_FLAGS}")

    if (${ARGC} GREATER 12)
        MATH(EXPR ARG_N_LAST "${ARGC}-1")
        foreach(ARG_N RANGE 12 ${ARG_N_LAST})
            list(APPEND NNVG_CMD_ARGS "-I")
            list(APPEND NNVG_CMD_ARGS "${ARGV${ARG_N}}")
        endforeach(ARG_N)
    endif()

    list(APPEND NNVG_CMD_ARGS --omit-dependencies)
    list(APPEND NNVG_CMD_ARGS --target-language)
    list(APPEND NNVG_CMD_ARGS ${ARG_OUTPUT_LANGUAGE})
    list(APPEND NNVG_CMD_ARGS  -O)
    list(APPEND NNVG_CMD_ARGS ${ARG_OUTPUT_FOLDER})

    if (ARG_DSDL_ROOT_DIR STREQUAL "")
        set(LOCAL_DSDL_FILES "")
    else()
        list(APPEND NNVG_CMD_ARGS -I)
        list(APPEND NNVG_CMD_ARGS ${ARG_DSDL_ROOT_DIR})
        file(GLOB_RECURSE LOCAL_DSDL_FILES CONFIGURE_DEPENDS "${ARG_DSDL_ROOT_DIR}/*.dsdl")
        list(APPEND NNVG_CMD_ARGS ${LOCAL_DSDL_FILES})
    endif()


    if (NOT "${ARG_SER_ENDIANNESS}" STREQUAL "")
        list(APPEND NNVG_CMD_ARGS "--target-endianness")
        list(APPEND NNVG_CMD_ARGS ${ARG_SER_ENDIANNESS})
        message(STATUS "nnvg:Setting --target-endianness to ${ARG_SER_ENDIANNESS}")
    endif()

    if (NOT "${ARG_OUTPUT_LANGUAGE_STD}" STREQUAL "")
        list(APPEND NNVG_CMD_ARGS "-std")
        list(APPEND NNVG_CMD_ARGS ${ARG_OUTPUT_LANGUAGE_STD})
        message(STATUS "nnvg:Setting -std to ${ARG_OUTPUT_LANGUAGE_STD}")
    endif()

    if (ARG_ENABLE_SER_ASSERT)
        list(APPEND NNVG_CMD_ARGS "--enable-serialization-asserts")
        message(STATUS "nnvg:Enabling serialization asserts in generated code.")
    endif()

    if (ARG_DISABLE_SER_FP)
        list(APPEND NNVG_CMD_ARGS "--omit-float-serialization-support")
        message(STATUS "nnvg:Disabling floating point serialization routines in generated support code.")
    endif()

    if (ARG_ENABLE_OVR_VAR_ARRAY)
        list(APPEND NNVG_CMD_ARGS "--enable-override-variable-array-capacity")
        message(STATUS "nnvg:Enabling variable array capacity override option in generated code.")
    endif()

    if (ARG_ENABLE_EXPERIMENTAL)
        list(APPEND NNVG_CMD_ARGS "--experimental-languages")
        message(STATUS "nnvg:Enabling support for experimental languages.")
    endif()

    execute_process(COMMAND ${NNVG} --generate-support=${ARG_GENERATE_SUPPORT} --list-outputs ${NNVG_CMD_ARGS}
                    OUTPUT_VARIABLE OUTPUT_FILES
                    RESULT_VARIABLE LIST_OUTPUTS_RESULT)

    if(NOT LIST_OUTPUTS_RESULT EQUAL 0)
        message(FATAL_ERROR "nnvg:Failed to retrieve a list of headers nnvg would "
                            "generate for the ${ARG_TARGET_NAME} target (${LIST_OUTPUTS_RESULT})"
                            " (${NNVG})")
    endif()

    execute_process(COMMAND ${NNVG} --generate-support=${ARG_GENERATE_SUPPORT} --list-inputs ${NNVG_CMD_ARGS}
                    OUTPUT_VARIABLE INPUT_FILES
                    RESULT_VARIABLE LIST_INPUTS_RESULT)

    if(NOT LIST_INPUTS_RESULT EQUAL 0)
        message(FATAL_ERROR "nnvg:Failed to resolve inputs using nnvg for the ${ARG_TARGET_NAME} "
                            "target (${LIST_INPUTS_RESULT})"
                            " (${NNVG})")
    endif()

    if(ARG_ENABLE_CLANG_FORMAT AND CLANG_FORMAT)
        set(CLANG_FORMAT_ARGS -pp-rp=${CLANG_FORMAT} -pp-rpa=-i -pp-rpa=-style=file)
    else()
        set(CLANG_FORMAT_ARGS "")
    endif()

    add_custom_command(OUTPUT ${OUTPUT_FILES}
                       COMMAND ${NNVG} --generate-support=${ARG_GENERATE_SUPPORT} ${CLANG_FORMAT_ARGS} ${NNVG_CMD_ARGS}
                       DEPENDS ${INPUT_FILES}
                       WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                       COMMENT "Running nnvg")

    add_custom_target(${ARG_TARGET_NAME}-gen
                      DEPENDS ${OUTPUT_FILES})

    add_library(${ARG_TARGET_NAME} INTERFACE)

    add_dependencies(${ARG_TARGET_NAME} ${ARG_TARGET_NAME}-gen)

    target_include_directories(${ARG_TARGET_NAME} INTERFACE ${ARG_OUTPUT_FOLDER})

    if (ARG_ENABLE_SER_ASSERT)
        if(${ARG_TARGET_NAME} STREQUAL "unity")
            target_compile_options(${ARG_TARGET_NAME} INTERFACE
                "-DNUNAVUT_ASSERT=TEST_ASSERT"
            )
        elseif(${ARG_TARGET_NAME} STREQUAL "gtest")
            target_compile_options(${ARG_TARGET_NAME} INTERFACE
                "-DNUNAVUT_ASSERT=ASSERT_TRUE"
            )
        else()
            target_compile_options(${ARG_TARGET_NAME} INTERFACE
                "-DNUNAVUT_ASSERT=assert"
            )
        endif()
    endif()

    set(${ARG_TARGET_NAME}-OUTPUT ${OUTPUT_FILES} PARENT_SCOPE)

endfunction(create_dsdl_target)

# +---------------------------------------------------------------------------+
# | CONFIGURE: PYTHON ENVIRONMENT
# +---------------------------------------------------------------------------+

if(NOT TOX)

    message(STATUS "nnvg:tox was not found. You must have nunavut and its"
                   " dependencies available in the global python environment.")

    find_program(NNVG nnvg)

else()

    find_program(NNVG nnvg HINTS ${TOX_LOCAL_PYTHON_BIN})

    if (NOT NNVG)
        message(WARNING "nnvg:nnvg program was not found. The build will probably fail. (${NNVG})")
    endif()
endif()

# +---------------------------------------------------------------------------+
# | CONFIGURE: VALIDATE NNVG
# +---------------------------------------------------------------------------+
if (NNVG)
    execute_process(COMMAND ${NNVG} --version
                    OUTPUT_VARIABLE NNVG_VERSION
                    RESULT_VARIABLE NNVG_VERSION_RESULT)

    if(NNVG_VERSION_RESULT EQUAL 0)
        string(STRIP ${NNVG_VERSION} NNVG_VERSION)
        message(STATUS "nnvg:${NNVG} --version: ${NNVG_VERSION}")
    endif()
endif()

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(nnvg
    REQUIRED_VARS NNVG_VERSION
)
