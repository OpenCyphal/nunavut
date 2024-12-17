#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#

cmake_minimum_required(VERSION 3.27.0 FATAL_ERROR)

set(NUNAVUT_VERSION "3.0")

# ###### Created using @PACKAGE_INIT@ by configure_package_config_file() #######
get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/" ABSOLUTE)

macro(set_and_check _var _file)
    set(${_var} "${_file}")

    if(NOT EXISTS "${_file}")
        message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
    endif()
endmacro()

macro(check_required_components _NAME)
    foreach(comp ${${_NAME}_FIND_COMPONENTS})
        if(NOT ${_NAME}_${comp}_FOUND)
            if(${_NAME}_FIND_REQUIRED_${comp})
                set(${_NAME}_FOUND FALSE)
            endif()
        endif()
    endforeach()
endmacro()

# ###################################################################################
find_package(Python3 3.9 REQUIRED)

set_and_check(NUNAVUT_SOURCE_DIR "${PACKAGE_PREFIX_DIR}/src")

check_required_components(Nunavut Python3)

execute_process(
    COMMAND ${Python3_EXECUTABLE} ${PACKAGE_PREFIX_DIR}/.github/verify.py --major-minor-version-only
    OUTPUT_VARIABLE NUNAVUT_VERSION_MAJOR_MINOR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    WORKING_DIRECTORY "${PACKAGE_PREFIX_DIR}"
)

execute_process(
    COMMAND ${Python3_EXECUTABLE} ${PACKAGE_PREFIX_DIR}/.github/verify.py --version-only
    OUTPUT_VARIABLE NUNAVUT_VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE
    WORKING_DIRECTORY "${PACKAGE_PREFIX_DIR}"
)

message(STATUS "Nunavut version: ${NUNAVUT_VERSION}")

# Taken from https://stackoverflow.com/questions/32585927/proper-way-to-use-platform-specific-separators-in-cmake as
# this issue (https://gitlab.kitware.com/cmake/cmake/-/issues/17946) is still open.
if("${CMAKE_HOST_SYSTEM}" MATCHES ".*Windows.*")
    set(NUNAVUT_PATH_LIST_SEP "\\;")
else() # e.g. Linux
    set(NUNAVUT_PATH_LIST_SEP ":")
endif()

# ###################################################################################
# HELPER MACROS FOR INTERNAL FUNCTIONS. YOU CAN IGNORE THESE.

# transform a JSON array into a CMAKE list
macro(nunavut_json_array_to_list _json_array _list)
    string(JSON _json_array_type ERROR_VARIABLE _json_error TYPE ${${_json_array}})

    if(_json_error)
        message(FATAL_ERROR "nunavut_json_array_to_list: Failed to parse JSON array: ${_json_error}")
    endif()

    if(NOT ${_json_array_type} STREQUAL "ARRAY")
        message(FATAL_ERROR "nunavut_json_array_to_list: Expected JSON array but got ${_json_array_type}.")
    endif()

    string(JSON _json_array_length ERROR_VARIABLE _json_error LENGTH ${${_json_array}})

    if(_json_error)
        message(FATAL_ERROR "nunavut_json_array_to_list: Failed to get length of JSON array: ${_json_error}")
    endif()

    set(_local_list "")

    math(EXPR _json_array_stop " ${_json_array_length} - 1")
    foreach(_index RANGE 0 ${_json_array_stop})
        string(JSON _item ERROR_VARIABLE _json_error GET ${${_json_array}} ${_index})

        if(_json_error)
            message(FATAL_ERROR "nunavut_json_array_to_list: Failed to get item from JSON array: ${_json_error}")
        endif()

        list(APPEND _local_list "${_item}")
    endforeach()

    set(${_list} ${_local_list})
endmacro()

# used internally to unify argument handling for standards nnvg arguments across all cmake functions
# Note: all options are repeated as "LOCAL_ARG_[option name]" to support forwarding.
macro(nunavut_config_args has_name options singleValueArgs multiValueArgs usageLines)
    list(APPEND ${options}
        ALLOW_EXPERIMENTAL_LANGUAGES
        CONSOLE_DEBUG
        SUPPORT_ONLY
        NO_SUPPORT
        OMIT_PUBLIC_REGULATED_NAMESPACE
    )
    list(APPEND ${singleValueArgs}
        NAME
        LANGUAGE
        OUTPUT_DIR
        LANGUAGE_STANDARD
        PYDSDL_PATH
        WORKING_DIRECTORY
        FILE_EXTENSION
    )
    list(APPEND ${multiValueArgs} CONFIGURATION DSDL_FILES DSDL_NAMESPACES)
    list(INSERT ${usageLines} 0
        "USAGE:"
        "  ${CMAKE_CURRENT_FUNCTION}")

    if(${has_name})
        list(INSERT ${usageLines} 2 "    NAME <name> LANGUAGE <language> DSDL_FILES <dsdl_files> [DSDL_NAMESPACES <dsdl_namespaces>]")
    else()
        list(INSERT ${usageLines} 2 "    LANGUAGE <language> DSDL_FILES <dsdl_files> [DSDL_NAMESPACES <dsdl_namespaces>]")
    endif()

    list(INSERT ${usageLines} 3
        "    [LANGUAGE_STANDARD <language_standard>] [OUTPUT_DIR <output_dir>] [CONFIGURATION <configuration>]"
        "    [WORKING_DIRECTORY <working_directory>] [PYDSDL_PATH <pydsdl_path>] [FILE_EXTENSION <file_extension>]"
        "    [ALLOW_EXPERIMENTAL_LANGUAGES] [CONSOLE_DEBUG] [SUPPORT_ONLY|NO_SUPPORT]"
    )

    cmake_parse_arguments(PARSE_ARGV 0 ARG "${${options}}" "${${singleValueArgs}}" "${${multiValueArgs}}")

    if(${has_name} AND NOT ARG_NAME)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: NAME is required.")
    endif()

    if(NOT ARG_LANGUAGE)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: LANGUAGE is required.")
    endif()

    if(${ARG_LANGUAGE} STREQUAL "cpp")
        if(NOT ARG_ALLOW_EXPERIMENTAL_LANGUAGES)
            message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: C++ support is experimental and must be enabled by setting the ALLOW_EXPERIMENTAL_LANGUAGES option.")
        endif()
    elseif(NOT ${ARG_LANGUAGE} STREQUAL "c")
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: LANGUAGE must be 'c' or 'cpp'.")
    endif()

    if(NOT ARG_DSDL_FILES)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: DSDL_FILES is required.")
    endif()

    if(NOT ARG_OUTPUT_DIR)
        set(ARG_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated")
    endif()

    if(NOT ARG_WORKING_DIRECTORY)
        set(ARG_WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}")
    endif()

    if(ARG_SUPPORT_ONLY AND ARG_NO_SUPPORT)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: SUPPORT_ONLY and NO_SUPPORT are mutually exclusive.")
    endif()

    if(ARG_UNPARSED_ARGUMENTS)
        list(INSERT ${usageLines} 0 "Unknown arguments found: ${ARG_UNPARSED_ARGUMENTS}")
        string(JOIN "\n" LOCAL_USAGE_MESSAGE ${${usageLines}})
        message(FATAL_ERROR "${LOCAL_USAGE_MESSAGE}\n")
    endif()
endmacro()

macro(nunavut_local_args)
    # handle forming arguments for the nunavut tool based on arguments passed into this function.
    set(LOCAL_DYNAMIC_ARGS "")

    if(ARG_DSDL_NAMESPACES)
        foreach(LOCAL_DSDL_NAMESPACE IN LISTS ARG_DSDL_NAMESPACES)
            list(APPEND LOCAL_DYNAMIC_ARGS "--lookup-dir" "${LOCAL_DSDL_NAMESPACE}")
        endforeach()
    endif()

    if(NOT ARG_OMIT_PUBLIC_REGULATED_NAMESPACE)
        list(APPEND LOCAL_DYNAMIC_ARGS "--lookup-dir" "${NUNAVUT_SUBMODULES_DIR}/public_regulated_data_types/uavcan")
    endif()

    if(ARG_LANGUAGE_STANDARD)
        list(APPEND LOCAL_DYNAMIC_ARGS "--language-standard" "${ARG_LANGUAGE_STANDARD}")
    endif()

    if(ARG_CONFIGURATION)
        foreach(LOCAL_CONFIGURATION IN LISTS ARG_CONFIGURATION)
            list(APPEND LOCAL_DYNAMIC_ARGS "--configuration" "${LOCAL_CONFIGURATION}")
        endforeach()
    endif()

    if(ARG_ALLOW_EXPERIMENTAL_LANGUAGES)
        set(LOCAL_ARG_ALLOW_EXPERIMENTAL_LANGUAGES "ALLOW_EXPERIMENTAL_LANGUAGES")
        list(APPEND LOCAL_DYNAMIC_ARGS "--include-experimental-languages")
    else()
        set(LOCAL_ARG_ALLOW_EXPERIMENTAL_LANGUAGES)
    endif()

    if(ARG_SUPPORT_ONLY)
        set(LOCAL_ARG_SUPPORT_ONLY "SUPPORT_ONLY")
        set(LOCAL_ARG_NO_SUPPORT "")
        list(APPEND LOCAL_DYNAMIC_ARGS "--generate-support" "only")
    elseif(ARG_NO_SUPPORT)
        set(LOCAL_ARG_SUPPORT_ONLY "")
        set(LOCAL_ARG_NO_SUPPORT "NO_SUPPORT")
        list(APPEND LOCAL_DYNAMIC_ARGS "--generate-support" "never")
    else()
        set(LOCAL_ARG_SUPPORT_ONLY "")
        set(LOCAL_ARG_NO_SUPPORT "")
    endif()

    if(ARG_FILE_EXTENSION)
        list(APPEND LOCAL_DYNAMIC_ARGS "--output-extension" "${ARG_FILE_EXTENSION}")
    endif()

    # Setup running nunavut and pydsdl from source
    set(LOCAL_PYTHON_PATH "${NUNAVUT_SOURCE_DIR}")

    if(ARG_PYDSDL_PATH)
        set(LOCAL_PYTHON_PATH "${LOCAL_PYTHON_PATH}${NUNAVUT_PATH_LIST_SEP}${ARG_PYDSDL_PATH}")
    else()
        set(LOCAL_PYTHON_PATH "${LOCAL_PYTHON_PATH}${NUNAVUT_PATH_LIST_SEP}${NUNAVUT_SUBMODULES_DIR}/pydsdl")
    endif()

    set(ENV{PYTHONPATH} ${LOCAL_PYTHON_PATH})

    # Setup additional debug options if requested.
    set(LOCAL_DEBUG_COMMAND_OPTIONS "")

    if(ARG_CONSOLE_DEBUG)
        set(LOCAL_ARG_CONSOLE_DEBUG "CONSOLE_DEBUG")
        list(APPEND LOCAL_DEBUG_COMMAND_OPTIONS "COMMAND_ECHO" "STDOUT" "ECHO_OUTPUT_VARIABLE")
    else()
        set(LOCAL_ARG_CONSOLE_DEBUG "")
    endif()

    if(ARG_EXPORT_MANIFEST)
        set(LOCAL_JSON_FORMAT "json-pretty")
        set(LOCAL_LIST_CONFIGURATION "--list-configuration")
    else()
        set(LOCAL_JSON_FORMAT "json")
        set(LOCAL_LIST_CONFIGURATION "")
    endif()
endmacro()

# ###################################################################################

#[==[.rst:
    .. cmake:variable:: NUNAVUT_SUBMODULES_DIR

        Path to the submodules folder in the nunavut repository.

#]==]
set(NUNAVUT_SUBMODULES_DIR ${CMAKE_CURRENT_LIST_DIR}/submodules)

#[==[.rst:

    .. cmake:command:: export_nunavut_manifest

        Generate a json file listing the inputs to a code gen rule and the outputs generated by the rule. This is
        useful for complex builds where discovering the inputs and outputs is time consuming. By generating this file
        and checking it into source control, the build can use the manifest to avoid dynamic discovery for each new
        configuration step.

        - **param** ``LANGUAGE`` **str**:

            The language to generate code for. Supported types are ``c`` and ``cpp``.

        - **param** ``DSDL_FILES`` **list[path]**:

            A list of DSDL files to generate code for.

        - **param** ``DSDL_NAMESPACES`` **optional list[path]**:

            A list of namespaces to search for dependencies in. Unless OMIT_PUBLIC_REGULATED_NAMESPACE is set, this
            will always include ${NUNAVUT_SUBMODULES_DIR}/public_regulated_data_types/uavcan

        - **param** ``LANGUAGE_STANDARD`` **optional str**:

            The language standard to use.

        - **param** ``OUTPUT_DIR`` **optional path**:

            The directory to write generated code to. If omitted then ``${CMAKE_CURRENT_BINARY_DIR}/generated`` is used.

        - **param** ``CONFIGURATION`` **optional list[path]**:

            A list of configuration files to pass into nnvg. See the nunavut documentation for more information about
            configuration files.

        - **param** ``WORKING_DIRECTORY`` **optional path**:

            The working directory to use when invoking the Nunavut tool. If omitted then ``${CMAKE_CURRENT_SOURCE_DIR}``
            is used.

        - **param** ``PYDSDL_PATH`` **optional path**:

            The path to the PyDSDL tool. If omitted then this is set to ${NUNAVUT_SUBMODULES_DIR}/pydsdl/pydsdl
            which is the root of the pydsdl submodule in the Nunavut repo.

        - **param** ``FILE_EXTENSION`` **optional str**:

            The file extension to use for generated files. If omitted then the default for the language is used.

        - **option** ``ALLOW_EXPERIMENTAL_LANGUAGES``:

            If set then unsupported languages will be allowed.

        - **option** ``CONSOLE_DEBUG``:

            If set then verbose output will be enabled.

        - **option** ``SUPPORT_ONLY``:

            If set then the library created will contain only support code needed to use the code generated for
            ``DSDL_FILES``. This allows different cyphal libraries to share a single set of support headers and avoids
            duplicate target rules. This option is mutually exclusive with ``NO_SUPPORT``.

        - **option** ``NO_SUPPORT``:

            If set then the library created will not contain support code needed to use the code generated for
            ``DSDL_FILES``. This is a mutually exclusive option with ``SUPPORT_ONLY``.

        - **option** ``OMIT_PUBLIC_REGULATED_NAMESPACE``:

            By default, ``${NUNAVUT_SUBMODULES_DIR}/pydsdl/pydsdl`` is added to the list of ``DSDL_NAMESPACES``
            even if this variable is not set. This option disables this behaviour so only explicitly listed
            ``DSDL_NAMESPACES`` values will be used.

        - **param** ``OUT_MANIFEST_PATH``:

            If set then this method write a variable named ``${OUT_MANIFEST_PATH}`` with the path to the manifest file
            in the calling scope.

#]==]
function(export_nunavut_manifest)
    # +-[input]----------------------------------------------------------------+
    set(options)
    set(singleValueArgs OUT_MANIFEST_PATH)
    set(multiValueArgs)
    set(usageLines "    [OUT_MANIFEST_PATH <out_manifest_path>]")
    nunavut_config_args(ON options singleValueArgs multiValueArgs usageLines)

    # +-[body]-----------------------------------------------------------------+
    nunavut_local_args()

    # List all inputs to use as the dependencies for the custom command.
    execute_process(
        COMMAND
        ${Python3_EXECUTABLE} -m nunavut
        --target-language ${ARG_LANGUAGE}
        --list-inputs
        --list-outputs
        --outdir ${ARG_OUTPUT_DIR}
        ${LOCAL_LIST_CONFIGURATION}
        --list-format ${LOCAL_JSON_FORMAT}
        --dry-run
        ${LOCAL_DYNAMIC_ARGS}
        ${ARG_DSDL_FILES}
        ${LOCAL_DEBUG_COMMAND_OPTIONS}
        WORKING_DIRECTORY ${ARG_WORKING_DIRECTORY}
        OUTPUT_VARIABLE LOCAL_LIB_INPUTS_AND_OUTPUTS
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ENCODING UTF8
    )

    set(LOCAL_MANIFEST_FILE "${ARG_OUTPUT_DIR}/${ARG_NAME}.json")
    file(WRITE ${LOCAL_MANIFEST_FILE} ${LOCAL_LIB_INPUTS_AND_OUTPUTS})

    # +-[output]---------------------------------------------------------------+
    if(ARG_OUT_MANIFEST_PATH)
        set(${ARG_OUT_MANIFEST_PATH} ${LOCAL_MANIFEST_FILE} PARENT_SCOPE)
    endif()
endfunction()

#[==[.rst:

    .. cmake:command:: discover_inputs_and_outputs

        Invoke nnvg to discover all dsdl inputs for a given set of namespaces and the outputs that these would generate
        from a codegen build step.

        .. note::

            The :cmake:command:`add_cyphal_library` function uses this method internally so it is not necessary to use
            this method if defining a library using that function.

        - **param** ``LANGUAGE`` **str**:

            The language to generate code for. Supported types are ``c`` and ``cpp``.

        - **param** ``DSDL_FILES`` **list[path]**:

            A list of DSDL files to generate code for.

        - **param** ``DSDL_NAMESPACES`` **optional list[path]**:

            A list of namespaces to search for dependencies in. While optional, it's rare that this would be omitted.

        - **param** ``LANGUAGE_STANDARD`` **optional str**:

            The language standard to use.

        - **param** ``OUTPUT_DIR`` **optional path**:

            The directory to write generated code to. If omitted then ``${CMAKE_CURRENT_BINARY_DIR}/generated`` is used.

        - **param** ``CONFIGURATION`` **optional list[path]**:

            A list of configuration files to pass into nnvg. See the nunavut documentation for more information about
            configuration files.

        - **param** ``WORKING_DIRECTORY`` **optional path**:

            The working directory to use when invoking the Nunavut tool. If omitted then ``${CMAKE_CURRENT_SOURCE_DIR}``
            is used.

        - **param** ``PYDSDL_PATH`` **optional path**:

            The path to the PyDSDL tool. If omitted then this is set to ${NUNAVUT_SUBMODULES_DIR}/pydsdl/pydsdl
            which is the root of the pydsdl submodule in the Nunavut repo.

        - **param** ``FILE_EXTENSION`` **optional str**:

            The file extension to use for generated files. If omitted then the default for the language is used.

        - **option** ``ALLOW_EXPERIMENTAL_LANGUAGES``:

            If set then unsupported languages will be allowed.

        - **option** ``CONSOLE_DEBUG``:

            If set then verbose output will be enabled.

        - **option** ``SUPPORT_ONLY``:

            If set then the library created will contain only support code needed to use the code generated for
            ``DSDL_FILES``. This allows different cyphal libraries to share a single set of support headers and avoids
            duplicate target rules. This option is mutually exclusive with ``NO_SUPPORT``.

        - **option** ``NO_SUPPORT``:

            If set then the library created will not contain support code needed to use the code generated for
            ``DSDL_FILES``. This is a mutually exclusive option with ``SUPPORT_ONLY``.

        - **option** ``OMIT_PUBLIC_REGULATED_NAMESPACE``:

            By default, ``${NUNAVUT_SUBMODULES_DIR}/pydsdl/pydsdl`` is added to the list of ``DSDL_NAMESPACES``
            even if this variable is not set. This option disables this behaviour so only explicitly listed
            ``DSDL_NAMESPACES`` values will be used.

        - **param** ``OUT_MANIFEST_DATA`` **optional variable:**

            If set, this method writes a variable named ``${OUT_MANIFEST_DATA}`` with the json string containing the
            entire manifest read in from the nnvg invocation.

        - **param** ``OUT_INPUTS_LIST`` **optional variable:**

            If set, this method writes a variable named ``${OUT_LIBRARY_TARGET}`` with the interface library target name
            defined for the library in the calling scope.

        - **param** ``OUT_OUTPUTS_LIST`` **optional variable:**

            If set, this method writes a variable named ``${OUT_CODEGEN_TARGET}`` with the custom target name defined
            for invoking the code generator.

#]==]
function(discover_inputs_and_outputs)
    # +-[input]----------------------------------------------------------------+
    set(options)
    set(singleValueArgs
        OUT_MANIFEST_DATA
        OUT_INPUTS_LIST
        OUT_OUTPUTS_LIST
    )
    set(multiValueArgs)
    list(APPEND usageLines
        "    [OUT_INPUTS_LIST <inputs_list_variable>] [OUT_OUTPUTS_LIST <outputs_list_variable>] [OUT_MANIFEST_DATA <manifest_variable>]"
    )
    nunavut_config_args(OFF options singleValueArgs multiValueArgs usageLines)

    # +-[body]-----------------------------------------------------------------+
    nunavut_local_args()

    # List all inputs to use as the dependencies for the custom command.
    execute_process(
        COMMAND
        ${Python3_EXECUTABLE} -m nunavut
        --target-language ${ARG_LANGUAGE}
        --list-inputs
        --list-outputs
        --outdir ${ARG_OUTPUT_DIR}
        ${LOCAL_LIST_CONFIGURATION}
        --list-format ${LOCAL_JSON_FORMAT}
        --dry-run
        ${LOCAL_DYNAMIC_ARGS}
        ${ARG_DSDL_FILES}
        ${LOCAL_DEBUG_COMMAND_OPTIONS}
        WORKING_DIRECTORY ${ARG_WORKING_DIRECTORY}
        OUTPUT_VARIABLE LOCAL_LIB_INPUTS_AND_OUTPUTS
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ENCODING UTF8
    )

    string(JSON LOCAL_LIB_INPUTS ERROR_VARIABLE LOCAL_LIB_READ_INPUTS_ERROR GET ${LOCAL_LIB_INPUTS_AND_OUTPUTS} "inputs")

    if(LOCAL_LIB_READ_INPUTS_ERROR)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: Failed to read inputs from nunavut: ${LOCAL_LIB_READ_INPUTS_ERROR}")
    endif()

    nunavut_json_array_to_list(LOCAL_LIB_INPUTS LOCAL_LIB_INPUTS_LIST)
    list(LENGTH LOCAL_LIB_INPUTS_LIST LOCAL_LIB_INPUTS_LENGTH)

    if(${LOCAL_LIB_INPUTS_LENGTH} EQUAL 0)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: No input files found for ${LOCAL_TARGET_NAME} (${LOCAL_LIB_INPUTS_LIST}).")
    endif()

    if(ARG_CONSOLE_DEBUG)
        message(STATUS "\n${CMAKE_CURRENT_FUNCTION}: Found input files: ${LOCAL_LIB_INPUTS_LIST}")
    endif()

    string(JSON LOCAL_LIB_OUTPUTS ERROR_VARIABLE LOCAL_LIB_READ_OUTPUTS_ERROR GET ${LOCAL_LIB_INPUTS_AND_OUTPUTS} "outputs")

    if(LOCAL_LIB_READ_OUTPUTS_ERROR)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: Failed to read outputs from nunavut: ${LOCAL_LIB_READ_OUTPUTS_ERROR}")
    endif()

    nunavut_json_array_to_list(LOCAL_LIB_OUTPUTS LOCAL_LIB_OUTPUTS_LIST)
    list(LENGTH LOCAL_LIB_OUTPUTS_LIST LOCAL_LIB_OUTPUTS_LENGTH)

    if(${LOCAL_LIB_OUTPUTS_LENGTH} EQUAL 0)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: No output files found for ${LOCAL_TARGET_NAME}.")
    endif()

    if(ARG_CONSOLE_DEBUG)
        message(STATUS "\n${CMAKE_CURRENT_FUNCTION}: Found output files: ${LOCAL_LIB_OUTPUTS_LIST}")
    endif()

    # +-[output]---------------------------------------------------------------+
    if(ARG_OUT_MANIFEST_DATA)
        set(${ARG_OUT_MANIFEST_DATA} ${LOCAL_LIB_INPUTS_AND_OUTPUTS} PARENT_SCOPE)
    endif()

    if(ARG_OUT_INPUTS_LIST)
        set(${ARG_OUT_INPUTS_LIST} ${LOCAL_LIB_INPUTS_LIST} PARENT_SCOPE)
    endif()

    if(ARG_OUT_OUTPUTS_LIST)
        set(${ARG_OUT_OUTPUTS_LIST} ${LOCAL_LIB_OUTPUTS_LIST} PARENT_SCOPE)
    endif()
endfunction()

#[==[.rst:
    .. cmake:command:: add_cyphal_library

        Create a library built from code generated by the Nunavut tool from dsdl files. This version
        of the function always defines an interface library since c and c++ types are generated as header-only.

        .. note::

            See the :ref:`fetch_content` for more guidance on using this function.

        - **param** ``NAME`` **str**:

            A name for the library. If ``EXACT_NAME`` is set then this is the exact name of the target. Otherwise, the
            target name will be derived from this name for uniqueness. Use ``OUT_LIBRARY_TARGET`` to capture the
            generated name of the library target.

        - **param** ``LANGUAGE`` **str**:

            The language to generate code for. Supported types are ``c`` and ``cpp``.

        - **param** ``DSDL_FILES`` **list[path]**:

            A list of DSDL files to generate code for.

        - **param** ``DSDL_NAMESPACES`` **optional list[path]**:

            A list of namespaces to search for dependencies in. While optional, it's rare that this would be omitted.

        - **param** ``LANGUAGE_STANDARD`` **optional str**:

            The language standard to use.

        - **param** ``OUTPUT_DIR`` **optional path**:

            The directory to write generated code to. If omitted then ``${CMAKE_CURRENT_BINARY_DIR}/generated`` is used.

        - **param** ``CONFIGURATION`` **optional list[path]**:

            A list of configuration files to pass into nnvg. See the nunavut documentation for more information about
            configuration files.

        - **param** ``WORKING_DIRECTORY`` **optional path**:

            The working directory to use when invoking the Nunavut tool. If omitted then ``${CMAKE_CURRENT_SOURCE_DIR}``
            is used.

        - **param** ``PYDSDL_PATH`` **optional path**:

            The path to the PyDSDL tool. If omitted then this is set to ${NUNAVUT_SUBMODULES_DIR}/pydsdl/pydsdl
            which is the root of the pydsdl submodule in the Nunavut repo.

        - **param** ``FILE_EXTENSION`` **optional str**:

            The file extension to use for generated files. If omitted then the default for the language is used.

        - **option** ``ALLOW_EXPERIMENTAL_LANGUAGES``:

            If set then unsupported languages will be allowed.

        - **option** ``CONSOLE_DEBUG``:

            If set then verbose output will be enabled.

        - **option** ``SUPPORT_ONLY``:

            If set then the library created will contain only support code needed to use the code generated for
            ``DSDL_FILES``. This allows different cyphal libraries to share a single set of support headers and avoids
            duplicate target rules. This option is mutually exclusive with ``NO_SUPPORT``.

        - **option** ``NO_SUPPORT``:

            If set then the library created will not contain support code needed to use the code generated for
            ``DSDL_FILES``. This is a mutually exclusive option with ``SUPPORT_ONLY``.

        - **option** ``EXACT_NAME``:

            If set then the target name will be exactly as specified in ``NAME``. Otherwise, the target name will be
            prefixed with an internal default.

        - **option** ``EXPORT_MANIFEST``:

            If set then a JSON file containing a list of all the inputs, outputs, and other information about the
            custom command will be written to ``${CMAKE_CURRENT_BINARY_DIR}/${OUT_CODEGEN_TARGET}.json``.

        - **option** ``OMIT_PUBLIC_REGULATED_NAMESPACE``:

            By default, ``${NUNAVUT_SUBMODULES_DIR}/pydsdl/pydsdl`` is added to the list of ``DSDL_NAMESPACES``
            even if this variable is not set. This option disables this behaviour so only explicitly listed
            ``DSDL_NAMESPACES`` values will be used.

        - **param** ``OUT_LIBRARY_TARGET`` **optional variable**:

            If set, this method write a variable named ``${OUT_LIBRARY_TARGET}`` with the interface library target name
            defined for the library in the calling scope.

        - **param** ``OUT_CODEGEN_TARGET`` **optional variable**:

            If set, this method write a variable named ``${OUT_CODEGEN_TARGET}`` with the custom target name defined for
            invoking the code generator.

#]==]
function(add_cyphal_library)
    # +-[input]----------------------------------------------------------------+
    set(options EXPORT_MANIFEST EXACT_NAME)
    set(singleValueArgs
        OUT_LIBRARY_TARGET
        OUT_CODEGEN_TARGET
    )
    set(multiValueArgs)
    list(APPEND usageLines
        "    [EXPORT_MANIFEST] [EXACT_NAME]"
        "    [OUT_LIBRARY_TARGET <library_target_variable>] [OUT_CODEGEN_TARGET <codegen_target_variable>]"
    )
    nunavut_config_args(ON options singleValueArgs multiValueArgs usageLines)

    if(NOT ARG_NAME AND EXACT_NAME)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: NAME is required if EXACT_NAME is set.")
    endif()

    # +-[body]-----------------------------------------------------------------+
    nunavut_local_args()

    if(ARG_EXACT_NAME)
        set(LOCAL_TARGET_NAME "${ARG_NAME}")
    else()
        if(NOT ARG_NAME)
            set(ARG_NAME "")
        else()
            set(ARG_NAME "-${ARG_NAME}")
        endif()

        if(ARG_SUPPORT_ONLY)
            set(LOCAL_TARGET_NAME "cyphal-support${ARG_NAME}")
        elseif(ARG_NO_SUPPORT)
            set(LOCAL_TARGET_NAME "cyphal-types${ARG_NAME}")
        else()
            set(LOCAL_TARGET_NAME "cyphal-types-and-support${ARG_NAME}")
        endif()
    endif()

    discover_inputs_and_outputs(
        LANGUAGE ${ARG_LANGUAGE}
        DSDL_FILES ${ARG_DSDL_FILES}
        DSDL_NAMESPACES ${ARG_DSDL_NAMESPACES}
        LANGUAGE_STANDARD ${ARG_LANGUAGE_STANDARD}
        OUTPUT_DIR ${ARG_OUTPUT_DIR}
        CONFIGURATION ${ARG_CONFIGURATION}
        WORKING_DIRECTORY ${ARG_WORKING_DIRECTORY}
        PYDSDL_PATH ${ARG_PYDSDL_PATH}
        FILE_EXTENSION ${ARG_FILE_EXTENSION}
        ${LOCAL_ARG_ALLOW_EXPERIMENTAL_LANGUAGES}
        ${LOCAL_ARG_CONSOLE_DEBUG}
        ${LOCAL_ARG_SUPPORT_ONLY}
        ${LOCAL_ARG_NO_SUPPORT}
        OUT_MANIFEST_DATA LOCAL_MANIFEST_DATA
        OUT_INPUTS_LIST LOCAL_LIB_INPUTS_LIST
        OUT_OUTPUTS_LIST LOCAL_LIB_OUTPUTS_LIST
    )

    # Create the custom command to generate source files.
    add_custom_command(
        OUTPUT ${LOCAL_LIB_OUTPUTS_LIST}
        COMMAND
        export PYTHONPATH=${LOCAL_PYTHON_PATH} && ${Python3_EXECUTABLE} -m nunavut
        --target-language ${ARG_LANGUAGE}
        --outdir ${ARG_OUTPUT_DIR}
        ${LOCAL_DYNAMIC_ARGS}
        ${ARG_DSDL_FILES}
        WORKING_DIRECTORY ${ARG_WORKING_DIRECTORY}
        DEPENDS ${LOCAL_LIB_INPUTS_LIST}
    )

    set(LOCAL_CODEGEN_TARGET "${LOCAL_TARGET_NAME}-generate")
    add_custom_target(${LOCAL_CODEGEN_TARGET}
        DEPENDS ${LOCAL_LIB_OUTPUTS_LIST}
    )

    # finally, define the interface library for the generated headers.
    add_library(${LOCAL_TARGET_NAME} INTERFACE ${LOCAL_LIB_OUTPUTS_LIST})

    target_include_directories(${LOCAL_TARGET_NAME} INTERFACE ${ARG_OUTPUT_DIR})

    add_dependencies(${LOCAL_TARGET_NAME} ${LOCAL_CODEGEN_TARGET})

    if(ARG_EXPORT_MANIFEST)
        set(LOCAL_MANIFEST_FILE "${CMAKE_CURRENT_BINARY_DIR}/${LOCAL_CODEGEN_TARGET}.json")
        file(WRITE ${LOCAL_MANIFEST_FILE} ${LOCAL_MANIFEST_DATA})
    endif()

    if(ARG_CONSOLE_DEBUG)
        message(STATUS "${CMAKE_CURRENT_FUNCTION}: Done adding library ${LOCAL_TARGET_NAME}.")
    endif()

    # +-[output]---------------------------------------------------------------+
    if(ARG_OUT_LIBRARY_TARGET)
        set(${ARG_OUT_LIBRARY_TARGET} ${LOCAL_TARGET_NAME} PARENT_SCOPE)
    endif()

    if(ARG_OUT_CODEGEN_TARGET)
        set(${ARG_OUT_CODEGEN_TARGET} ${LOCAL_CODEGEN_TARGET} PARENT_SCOPE)
    endif()
endfunction()
