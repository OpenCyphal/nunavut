#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#

cmake_minimum_required(VERSION 3.25.0 FATAL_ERROR)

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
    COMMAND ${Python3_EXECUTABLE} ${PACKAGE_PREFIX_DIR}/version_check_nunavut.py --major-minor-version-only
    OUTPUT_VARIABLE NUNAVUT_VERSION_MAJOR_MINOR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    WORKING_DIRECTORY "${PACKAGE_PREFIX_DIR}"
)

execute_process(
    COMMAND ${Python3_EXECUTABLE} ${PACKAGE_PREFIX_DIR}/version_check_nunavut.py --version-only
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

list(APPEND NUNAVUT_CONFIGURE_OPTIONS
    ALLOW_EXPERIMENTAL_LANGUAGES
    CONSOLE_DEBUG
    SUPPORT_ONLY
    NO_SUPPORT
    OMIT_PUBLIC_REGULATED_NAMESPACE
    OMIT_DEPENDENCIES
)
list(APPEND NUNAVUT_CONFIGURE_SINGLE_VALUE_ARGS
    LANGUAGE
    OUTPUT_DIR
    LANGUAGE_STANDARD
    PYDSDL_PATH
    WORKING_DIRECTORY
    FILE_EXTENSION
)
list(APPEND NUNAVUT_CONFIGURE_MULTI_VALUE_ARGS
    CONFIGURATION
    DSDL_FILES
    DSDL_NAMESPACES
)

# Forward option arguments to an inner function
macro(_forward_option arg_list arg_key)
    if (NOT DEFINED ${arg_list})
        set(${arg_list})
    endif()
    if (NUNV_ARG_${arg_key})
        list(APPEND ${arg_list} ${arg_key})
    endif()
endmacro()

# Forward single-value arguments to an inner function. Compliant with CMP0174.
macro(_forward_single_value_arg arg_list arg_key)
    if (NOT DEFINED ${arg_list})
        set(${arg_list})
    endif()
    if (NUNV_ARG_${arg_key})
        list(APPEND ${arg_list} ${arg_key} "${NUNV_ARG_${arg_key}}")
    endif()
endmacro()

# Helper for populating a list of key[i]=value[i+1] pairs to ensure only one key/value
# pair exists. This also raises errors if a duplicate key insertion is attempted with a
# different value but has no effect if a duplicate key insertion with the same value is
# attempted (idempotence).
macro(_add_single_value_once arg_list arg_key arg_value)
    if (NOT ${arg_list})
        set(${arg_list})
    endif()
    list(FIND ${arg_list} ${arg_key} arg_list_index)
    if (arg_list_index GREATER -1)
        list(LENGTH ${arg_list} arg_list_length)
        math(EXPR arg_list_index "${arg_list_index} + 1")
        if (arg_list_length GREATER arg_list_index)
            list(GET ${arg_list} ${arg_list_index} arg_list_value_at_index)
            if (NOT ${arg_list_value_at_index} STREQUAL ${arg_value})
                message(FATAL_ERROR "Attempted to set ${arg_key}=${arg_value} when ${arg_key}=${arg_list_value_at_index} was already set?")
            endif()
        else()
            message(FATAL_ERROR "${arg_key} was set as an option but it is supposed to have a single value?")
        endif()
    else()
        list(APPEND ${arg_list} ${arg_key} ${arg_value})
    endif()
endmacro()

# Helper for populating a list without creating duplicate values.
macro(_add_option_once arg_list arg_key)
    if (NOT ${arg_list})
        set(${arg_list})
    endif()
    list(FIND ${arg_list} ${arg_key} arg_list_index)
    if (arg_list_index EQUAL -1)
        list(APPEND ${arg_list} ${arg_key})
    endif()
endmacro()


# transform a JSON array into a CMAKE list
macro(_nunavut_json_array_to_list _json_array _list)
    string(JSON _json_array_type ERROR_VARIABLE _json_error TYPE ${${_json_array}})

    if(_json_error)
        message(FATAL_ERROR "_nunavut_json_array_to_list: Failed to parse JSON array: ${_json_error}")
    endif()

    if(NOT ${_json_array_type} STREQUAL "ARRAY")
        message(FATAL_ERROR "_nunavut_json_array_to_list: Expected JSON array but got ${_json_array_type}.")
    endif()

    string(JSON _json_array_length ERROR_VARIABLE _json_error LENGTH ${${_json_array}})

    if(_json_error)
        message(FATAL_ERROR "_nunavut_json_array_to_list: Failed to get length of JSON array: ${_json_error}")
    endif()

    set(_local_list "")

    math(EXPR _json_array_stop " ${_json_array_length} - 1")
    foreach(_index RANGE 0 ${_json_array_stop})
        string(JSON _item ERROR_VARIABLE _json_error GET ${${_json_array}} ${_index})

        if(_json_error)
            message(FATAL_ERROR "_nunavut_json_array_to_list: Failed to get item from JSON array: ${_json_error}")
        endif()

        list(APPEND _local_list "${_item}")
    endforeach()

    set(${_list} ${_local_list})
endmacro()

# Used internally to unify argument handling for standards nunavut cli arguments across all cmake functions.
# Defines the following, local variables:
# NUNV_LOCAL_PYTHON_PATH            - The pythonpath to use when invoking Nunavut from source.
# NUNV_LOCAL_LOOKUP_DIRS            - list if --lookup-dir arguments
# NUNV_LOCAL_DYNAMIC_ARGS           - all other arguments to pass to Nunavut
# NUNV_LOCAL_DEBUG_COMMAND_OPTIONS  - Additional options to use when setting up the custom command.
macro(_nunavut_config_args options singleValueArgs multiValueArgs usageLines)
    set(NUNV_LOCAL_DYNAMIC_ARGS "")
    set(NUNV_LOCAL_LOOKUP_DIRS "")

    list(APPEND ${options} ${NUNAVUT_CONFIGURE_OPTIONS})
    list(APPEND ${singleValueArgs} ${NUNAVUT_CONFIGURE_SINGLE_VALUE_ARGS})
    list(APPEND ${multiValueArgs} ${NUNAVUT_CONFIGURE_MULTI_VALUE_ARGS})
    list(INSERT ${usageLines} 0
        "USAGE:"
        "    ${CMAKE_CURRENT_FUNCTION}"
        "    LANGUAGE <language> DSDL_FILES <dsdl_files> [DSDL_NAMESPACES <dsdl_namespaces>]"
        "    [LANGUAGE_STANDARD <language_standard>] [OUTPUT_DIR <output_dir>] [CONFIGURATION <configuration>]"
        "    [WORKING_DIRECTORY <working_directory>] [PYDSDL_PATH <pydsdl_path>] [FILE_EXTENSION <file_extension>]"
        "    [ALLOW_EXPERIMENTAL_LANGUAGES] [CONSOLE_DEBUG] [SUPPORT_ONLY|NO_SUPPORT] [OMIT_DEPENDENCIES]"
    )

    cmake_parse_arguments(PARSE_ARGV 0 NUNV_ARG "${${options}}" "${${singleValueArgs}}" "${${multiValueArgs}}")

    if(NOT NUNV_ARG_LANGUAGE)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: LANGUAGE is required.")
    endif()

    if(${NUNV_ARG_LANGUAGE} STREQUAL "cpp")
        if (NOT NUNV_ARG_ALLOW_EXPERIMENTAL_LANGUAGES)
            list(FIND NUNV_LOCAL_DYNAMIC_ARGS "--include-experimental-languages" NUNV_LOCAL_DYNAMIC_ARG_INDEX)
            if(NUNV_LOCAL_DYNAMIC_ARG_INDEX EQUAL -1)
                message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: C++ support is experimental and must be enabled by setting the ALLOW_EXPERIMENTAL_LANGUAGES option.")
            endif()
        endif()
    elseif(NOT ${NUNV_ARG_LANGUAGE} STREQUAL "c")
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: LANGUAGE must be 'c' or 'cpp'.")
    endif()

    if(NOT NUNV_ARG_OUTPUT_DIR)
        set(NUNV_ARG_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated")
    endif()

    if(NOT NUNV_ARG_WORKING_DIRECTORY)
        set(NUNV_ARG_WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}")
    endif()

    if(NUNV_ARG_SUPPORT_ONLY AND NUNV_ARG_NO_SUPPORT)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: SUPPORT_ONLY and NO_SUPPORT are mutually exclusive.")
    endif()

    if(NOT NUNV_ARG_DSDL_FILES AND NOT NUNV_ARG_SUPPORT_ONLY)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: DSDL_FILES is required.")
    endif()

    if(NUNV_ARG_UNPARSED_ARGUMENTS)
        list(INSERT ${usageLines} 0 "Unknown arguments found: ${NUNV_ARG_UNPARSED_ARGUMENTS}")
        string(JOIN "\n" NUNV_LOCAL_USAGE_MESSAGE ${${usageLines}})
        message(FATAL_ERROR "${NUNV_LOCAL_USAGE_MESSAGE}\n")
    endif()

    if(NUNV_ARG_DSDL_NAMESPACES)
        foreach(NUNV_LOCAL_DSDL_NAMESPACE IN LISTS NUNV_ARG_DSDL_NAMESPACES)
            list(APPEND NUNV_LOCAL_LOOKUP_DIRS "--lookup-dir" "${NUNV_LOCAL_DSDL_NAMESPACE}")
        endforeach()
    endif()

    if(NOT NUNV_ARG_OMIT_PUBLIC_REGULATED_NAMESPACE)
        list(APPEND NUNV_LOCAL_LOOKUP_DIRS "--lookup-dir" "${NUNAVUT_SUBMODULES_DIR}/public_regulated_data_types/uavcan")
    endif()

    if(NUNV_ARG_LANGUAGE)
        _add_single_value_once(NUNV_LOCAL_DYNAMIC_ARGS "--target-language" "${NUNV_ARG_LANGUAGE}")
    endif()

    if(NUNV_ARG_OUTPUT_DIR)
        _add_single_value_once(NUNV_LOCAL_DYNAMIC_ARGS "--outdir" "${NUNV_ARG_OUTPUT_DIR}")
    endif()

    if(NUNV_ARG_LANGUAGE_STANDARD)
        _add_single_value_once(NUNV_LOCAL_DYNAMIC_ARGS "--language-standard" "${NUNV_ARG_LANGUAGE_STANDARD}")
    endif()

    if(NUNV_ARG_CONFIGURATION)
        foreach(NUNV_LOCAL_CONFIGURATION IN LISTS NUNV_ARG_CONFIGURATION)
            list(APPEND NUNV_LOCAL_DYNAMIC_ARGS "--configuration" "${NUNV_LOCAL_CONFIGURATION}")
        endforeach()
    endif()

    if(NUNV_ARG_ALLOW_EXPERIMENTAL_LANGUAGES)
        _add_option_once(NUNV_LOCAL_DYNAMIC_ARGS "--include-experimental-languages")
    endif()

    if(NUNV_ARG_SUPPORT_ONLY)
        _add_single_value_once(NUNV_LOCAL_DYNAMIC_ARGS "--generate-support" "only")
    endif()

    if(NUNV_ARG_NO_SUPPORT)
        _add_single_value_once(NUNV_LOCAL_DYNAMIC_ARGS "--generate-support" "never")
    endif()

    if(NUNV_ARG_FILE_EXTENSION)
        _add_single_value_once(NUNV_LOCAL_DYNAMIC_ARGS "--output-extension" ${NUNV_ARG_FILE_EXTENSION})
    endif()

    # Setup running nunavut and pydsdl from source
    set(NUNV_LOCAL_PYTHON_PATH "${NUNAVUT_SOURCE_DIR}")

    if(NUNV_ARG_PYDSDL_PATH)
        set(NUNV_LOCAL_PYTHON_PATH "${NUNV_LOCAL_PYTHON_PATH}${NUNAVUT_PATH_LIST_SEP}${NUNV_ARG_PYDSDL_PATH}")
    else()
        set(NUNV_LOCAL_PYTHON_PATH "${NUNV_LOCAL_PYTHON_PATH}${NUNAVUT_PATH_LIST_SEP}${NUNAVUT_SUBMODULES_DIR}/pydsdl")
    endif()

    set(ENV{PYTHONPATH} ${NUNV_LOCAL_PYTHON_PATH})

    # Setup additional debug options if requested.
    set(NUNV_LOCAL_DEBUG_COMMAND_OPTIONS "")

    if(NUNV_ARG_CONSOLE_DEBUG)
        list(APPEND NUNV_LOCAL_DEBUG_COMMAND_OPTIONS "COMMAND_ECHO" "STDOUT" "ECHO_OUTPUT_VARIABLE")
    endif()

    if(NUNV_ARG_OMIT_DEPENDENCIES)
        _add_option_once(NUNV_LOCAL_DYNAMIC_ARGS "--omit-dependencies")
    endif()
endmacro()

# ###################################################################################

#[==[.rst:
    .. cmake:variable:: NUNAVUT_SUBMODULES_DIR

        Set by the Nunavut package, this is the path to the submodules folder in the nunavut repository.

#]==]
set(NUNAVUT_SUBMODULES_DIR ${CMAKE_CURRENT_LIST_DIR}/submodules)

#[==[.rst:
    .. cmake:envvar:: NUNAVUT_EXTRA_GENERATOR_ARGS

        If defined, this environment variable is used as additional command-line arguments which are passed
        to Nunavut when generating code. This can also be specified as a cache variable (e.g.
        ``cmake -DNUNAVUT_EXTRA_GENERATOR_ARGS``) which will override any value set in the environment.
        As an environment variable, this list of args must use the system's list separator (``NUNAVUT_PATH_LIST_SEP``)
        to specify multiple arguments. As a cache variable, cmake's semicolon list separator must be used.

#]==]

#[==[.rst:
    .. cmake:variable:: NUNAVUT_PATH_LIST_SEP

        Platform-specific list separator determed by the Nunavut package and used to parse lists read from the
        environment or form lists set in the environment. Users shouldn't need to use this variable but it can
        be overridden if the Nunavut cmake package's automatic detection is incorrect.

#]==]

#[==[.rst:

    .. cmake:command:: discover_inputs_and_outputs

        Invoke the nunavut CLI to discover all dsdl inputs for a given set of namespaces and the outputs that these
        would generate from a codegen build step.

        .. note::

            The :cmake:command:`add_cyphal_library` function uses this method internally so it is not necessary to use
            this method if defining a library using that function.

        - **param** ``LANGUAGE`` **str**:

            The language to generate code for. Supported types are ``c`` and ``cpp``.

        - **param** ``DSDL_FILES`` **list[path]**:

            A list of DSDL files to generate code for.

        - **param** ``DSDL_NAMESPACES`` **optional list[path]**:

            A list of namespaces to search for dependencies in. Unless ``OMIT_PUBLIC_REGULATED_NAMESPACE`` is set, this
            will always include ``${NUNAVUT_SUBMODULES_DIR}/public_regulated_data_types/uavcan``

        - **param** ``LANGUAGE_STANDARD`` **optional str**:

            The language standard to use.

        - **param** ``OUTPUT_DIR`` **optional path**:

            The directory to write generated code to. If omitted then ``${CMAKE_CURRENT_BINARY_DIR}/generated`` is used.

        - **param** ``CONFIGURATION`` **optional list[path]**:

            A list of configuration files to pass into nunavut. See the nunavut documentation for more information about
            configuration files.

        - **param** ``WORKING_DIRECTORY`` **optional path**:

            The working directory to use when invoking the Nunavut tool. If omitted then ``${CMAKE_CURRENT_SOURCE_DIR}``
            is used.

        - **param** ``PYDSDL_PATH`` **optional path**:

            The path to the PyDSDL tool. If omitted then this is set to ${NUNAVUT_SUBMODULES_DIR}/pydsdl
            which is the root of the pydsdl submodule in the Nunavut repo.

        - **param** ``FILE_EXTENSION`` **optional str**:

            The file extension to use for generated files. If omitted then the default for the language is used.

        - **param** ``EXPORT_CONFIGURE_MANIFEST`` **optional path**:

            A folder under which a json file containing a list of all the inputs, outputs, and other information about
            the configure-step execution of nunavut will be written to. This file will be named
            ``${EXPORT_CONFIGURE_MANIFEST}/generate_commands.json`` and cannot contain generator expressions as this
            file is created at configure-time.

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

            By default, ``${NUNAVUT_SUBMODULES_DIR}/public_regulated_data_types/uavcan`` is added to the list of
            ``DSDL_NAMESPACES`` even if this variable is not set. This option disables this behaviour so only explicitly
            listed ``DSDL_NAMESPACES`` values will be used.

        - **option** ``OMIT_DEPENDENCIES``:

            Disables the generation of dependent types. This is useful when setting up build rules for a project where
            the dependent types are generated separately.

        - **param** ``OUT_MANIFEST_DATA`` **optional variable:**

            If set, this method writes a variable named ``${OUT_MANIFEST_DATA}`` with the json string containing the
            entire manifest read in from the nunavut CLI invocation.

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
        EXPORT_CONFIGURE_MANIFEST
        OUT_MANIFEST_DATA
        OUT_INPUTS_LIST
        OUT_OUTPUTS_LIST
    )
    set(multiValueArgs)
    list(APPEND usageLines
        "    [EXPORT_CONFIGURE_MANIFEST <path>] [OUT_INPUTS_LIST <inputs_list_variable>]"
        "    [OUT_OUTPUTS_LIST <outputs_list_variable>] [OUT_MANIFEST_DATA <manifest_variable>]"
    )
    _nunavut_config_args(options singleValueArgs multiValueArgs usageLines)

    # +-[body]-----------------------------------------------------------------+

    if(NUNV_ARG_EXPORT_CONFIGURE_MANIFEST)
        _add_option_once(NUNV_LOCAL_DYNAMIC_ARGS "--list-configuration")
        _add_single_value_once(NUNV_LOCAL_DYNAMIC_ARGS "--list-format" "json-pretty")
        list(APPEND NUNV_LOCAL_DYNAMIC_ARGS "--list-to-file" ${NUNV_ARG_EXPORT_CONFIGURE_MANIFEST}/generate_commands.json)
    else()
        _add_single_value_once(NUNV_LOCAL_DYNAMIC_ARGS "--list-format" "json")
    endif()

    # List all inputs to use as the dependencies for the custom command.
    execute_process(
        COMMAND
        ${Python3_EXECUTABLE} -m nunavut
        --list-inputs
        --list-outputs
        --dry-run
        ${NUNV_LOCAL_DYNAMIC_ARGS}
        ${NUNV_LOCAL_LOOKUP_DIRS}
        ${NUNV_ARG_DSDL_FILES}
        ${NUNV_LOCAL_DEBUG_COMMAND_OPTIONS}
        WORKING_DIRECTORY ${NUNV_ARG_WORKING_DIRECTORY}
        OUTPUT_VARIABLE NUNV_LOCAL_LIB_INPUTS_AND_OUTPUTS
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ENCODING UTF8
    )

    string(JSON NUNV_LOCAL_LIB_INPUTS ERROR_VARIABLE NUNV_LOCAL_LIB_READ_INPUTS_ERROR GET ${NUNV_LOCAL_LIB_INPUTS_AND_OUTPUTS} "inputs")

    if(NUNV_LOCAL_LIB_READ_INPUTS_ERROR)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: Failed to read inputs from nunavut: ${NUNV_LOCAL_LIB_READ_INPUTS_ERROR}")
    endif()

    _nunavut_json_array_to_list(NUNV_LOCAL_LIB_INPUTS NUNV_LOCAL_LIB_INPUTS_LIST)
    list(LENGTH NUNV_LOCAL_LIB_INPUTS_LIST NUNV_LOCAL_LIB_INPUTS_LENGTH)

    if(${NUNV_LOCAL_LIB_INPUTS_LENGTH} EQUAL 0)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: No input files found for ${NUNV_LOCAL_TARGET_NAME} (${NUNV_LOCAL_LIB_INPUTS_LIST}).")
    endif()

    if(NUNV_ARG_CONSOLE_DEBUG)
        message(STATUS "\n${CMAKE_CURRENT_FUNCTION}: Found input files: ${NUNV_LOCAL_LIB_INPUTS_LIST}")
    endif()

    string(JSON NUNV_LOCAL_LIB_OUTPUTS ERROR_VARIABLE NUNV_LOCAL_LIB_READ_OUTPUTS_ERROR GET ${NUNV_LOCAL_LIB_INPUTS_AND_OUTPUTS} "outputs")

    if(NUNV_LOCAL_LIB_READ_OUTPUTS_ERROR)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: Failed to read outputs from nunavut: ${NUNV_LOCAL_LIB_READ_OUTPUTS_ERROR}")
    endif()

    _nunavut_json_array_to_list(NUNV_LOCAL_LIB_OUTPUTS NUNV_LOCAL_LIB_OUTPUTS_LIST)
    list(LENGTH NUNV_LOCAL_LIB_OUTPUTS_LIST NUNV_LOCAL_LIB_OUTPUTS_LENGTH)

    if(${NUNV_LOCAL_LIB_OUTPUTS_LENGTH} EQUAL 0)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: No output files found for ${NUNV_LOCAL_TARGET_NAME}.")
    endif()

    if(NUNV_ARG_CONSOLE_DEBUG)
        message(STATUS "\n${CMAKE_CURRENT_FUNCTION}: Found output files: ${NUNV_LOCAL_LIB_OUTPUTS_LIST}")
    endif()

    # +-[output]---------------------------------------------------------------+
    if(NUNV_ARG_OUT_MANIFEST_DATA)
        set(${NUNV_ARG_OUT_MANIFEST_DATA} ${NUNV_LOCAL_LIB_INPUTS_AND_OUTPUTS} PARENT_SCOPE)
    endif()

    if(NUNV_ARG_OUT_INPUTS_LIST)
        set(${NUNV_ARG_OUT_INPUTS_LIST} ${NUNV_LOCAL_LIB_INPUTS_LIST} PARENT_SCOPE)
    endif()

    if(NUNV_ARG_OUT_OUTPUTS_LIST)
        set(${NUNV_ARG_OUT_OUTPUTS_LIST} ${NUNV_LOCAL_LIB_OUTPUTS_LIST} PARENT_SCOPE)
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

        - **param** ``EXPORT_CONFIGURE_MANIFEST`` **optional path**:

            A folder under which a json file containing a list of all the inputs, outputs, and other information about
            the configure-step execution of nunavut will be written to. This file will be named
            ``${EXPORT_CONFIGURE_MANIFEST}/${OUT_CODEGEN_TARGET}.json`` and cannot contain generator expressions as this
            file is created at configure-time (see ``EXPORT_GENERATE_MANIFEST`` for the compile-time equivalent).

        - **param** ``EXPORT_GENERATE_MANIFEST`` **optional path**:

            A folder under which a json file containing a list of all the inputs, outputs, and other information about
            the code-generation-step execution of nunavut will be written to. This file will be named
            ``${EXPORT_GENERATE_MANIFEST}/${OUT_CODEGEN_TARGET}.json`` and may contain generator expressions as this
            file is created only when executing the code gen build rule.

        - **param** ``CONFIGURATION`` **optional list[path]**:

            A list of configuration files to pass into nunavut. See the nunavut documentation for more information about
            configuration files.

        - **param** ``WORKING_DIRECTORY`` **optional path**:

            The working directory to use when invoking the Nunavut tool. If omitted then ``${CMAKE_CURRENT_SOURCE_DIR}``
            is used.

        - **param** ``PYDSDL_PATH`` **optional path**:

            The path to the PyDSDL tool. If omitted then this is set to ${NUNAVUT_SUBMODULES_DIR}/pydsdl
            which is the root of the pydsdl submodule in the Nunavut repo.

        - **param** ``FILE_EXTENSION`` **optional str**:

            The file extension to use for generated files. If omitted then the default for the language is used.

        - **param** ``EXTRA_GENERATOR_ARGS`` **optional list[str]**:

            Additional command-line arguments to pass to the Nunavut CLI when generating code. These args are not
            used for invoking the Nunavut CLI to discover dependencies.

            These are combined with any arguments specified by a :cmake:variable:`NUNAVUT_EXTRA_GENERATOR_ARGS`
            environment variable.

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

        - **option** ``OMIT_PUBLIC_REGULATED_NAMESPACE``:

            By default, ``${NUNAVUT_SUBMODULES_DIR}/public_regulated_data_types/uavcan`` is added to the list of
            ``DSDL_NAMESPACES`` even if this variable is not set. This option disables this behaviour so only explicitly
            listed ``DSDL_NAMESPACES`` values will be used.

        - **option, mutually exclusive** (one of ``ENDIAN_ANY`` | ``ENDIAN_LITTLE`` | ``ENDIAN_BIG``):

            If one of these is set then the endianness argument is passed into the nunavut CLI otherwise endianess is
            taken from language configuration.

        - **option** ``OMIT_DEPENDENCIES``:

            Disables the generation of dependent types. This is useful when setting up build rules for a project where
            the dependent types are generated separately.

        - **param** ``OUT_LIBRARY_TARGET`` **optional variable**:

            If set, this method write a variable named ``${OUT_LIBRARY_TARGET}`` with the interface library target name
            defined for the library in the calling scope.

        - **param** ``OUT_CODEGEN_TARGET`` **optional variable**:

            If set, this method write a variable named ``${OUT_CODEGEN_TARGET}`` with the custom target name defined for
            invoking the code generator.

#]==]
function(add_cyphal_library)
    # +-[input]----------------------------------------------------------------+
    set(options
        EXACT_NAME
        ENDIAN_ANY
        ENDIAN_LITTLE
        ENDIAN_BIG
    )
    set(singleValueArgs
        NAME
        EXPORT_CONFIGURE_MANIFEST
        EXPORT_GENERATE_MANIFEST
        OUT_LIBRARY_TARGET
        OUT_CODEGEN_TARGET
    )
    set(multiValueArgs EXTRA_GENERATOR_ARGS)
    list(APPEND usageLines
        "    NAME <name> [EXACT_NAME] "
        "    [EXPORT_GENERATE_MANIFEST <path>] [EXTRA_GENERATOR_ARGS <argument list>]"
        "    [ENDIAN_ANY|ENDIAN_LITTLE|ENDIAN_BIG]"
        "    [OUT_LIBRARY_TARGET <library_target_variable>] [OUT_CODEGEN_TARGET <codegen_target_variable>]"
    )
    _nunavut_config_args(options singleValueArgs multiValueArgs usageLines)

    # +-[body]-----------------------------------------------------------------+
    if(NUNV_ARG_ENDIAN_ANY)
        if (NUNV_ARG_ENDIAN_BIG OR NUNV_ARG_ENDIAN_LITTLE)
            message(FATAL_ERROR "ENDIAN_ANY|ENDIAN_LITTLE|ENDIAN_BIG options are mutually exclusive. Provide only one or none.")
        endif()
        list(APPEND NUNV_LOCAL_DYNAMIC_ARGS "--target-endianness" "any")
    elseif(NUNV_ARG_ENDIAN_BIG)
        if (NUNV_ARG_ENDIAN_ANY OR NUNV_ARG_ENDIAN_LITTLE)
            message(FATAL_ERROR "ENDIAN_ANY|ENDIAN_LITTLE|ENDIAN_BIG options are mutually exclusive. Provide only one or none.")
        endif()
        list(APPEND NUNV_LOCAL_DYNAMIC_ARGS "--target-endianness" "big")
    elseif(NUNV_ARG_ENDIAN_LITTLE)
        if (NUNV_ARG_ENDIAN_ANY OR NUNV_ARG_ENDIAN_BIG)
            message(FATAL_ERROR "ENDIAN_ANY|ENDIAN_LITTLE|ENDIAN_BIG options are mutually exclusive. Provide only one or none.")
        endif()
        list(APPEND NUNV_LOCAL_DYNAMIC_ARGS "--target-endianness" "little")
    endif()

    if(NOT NUNV_ARG_NAME AND EXACT_NAME)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: NAME is required if EXACT_NAME is set.")
    endif()

    if(NOT NUNV_ARG_EXTRA_GENERATOR_ARGS)
        # silence use of undefined warning
        set(NUNV_ARG_EXTRA_GENERATOR_ARGS)
    endif()

    if(NOT NUNV_ARG_NAME)
        message(FATAL_ERROR "${CMAKE_CURRENT_FUNCTION}: NAME is required.")
    endif()

    if(NUNV_ARG_EXACT_NAME)
        set(NUNV_LOCAL_TARGET_NAME "${NUNV_ARG_NAME}")
    else()
        if(NOT NUNV_ARG_NAME)
            set(NUNV_ARG_NAME "")
        else()
            set(NUNV_ARG_NAME "-${NUNV_ARG_NAME}")
        endif()

        if(NUNV_ARG_SUPPORT_ONLY)
            set(NUNV_LOCAL_TARGET_NAME "cyphal-support${NUNV_ARG_NAME}")
        elseif(NUNV_ARG_NO_SUPPORT)
            set(NUNV_LOCAL_TARGET_NAME "cyphal-types${NUNV_ARG_NAME}")
        else()
            set(NUNV_LOCAL_TARGET_NAME "cyphal-types-and-support${NUNV_ARG_NAME}")
        endif()
    endif()

    _forward_single_value_arg(NUNV_LOCAL_FORWARDED_ARGS LANGUAGE)
    _forward_single_value_arg(NUNV_LOCAL_FORWARDED_ARGS OUTPUT_DIR)
    _forward_single_value_arg(NUNV_LOCAL_FORWARDED_ARGS LANGUAGE_STANDARD)
    _forward_single_value_arg(NUNV_LOCAL_FORWARDED_ARGS PYDSDL_PATH)
    _forward_single_value_arg(NUNV_LOCAL_FORWARDED_ARGS WORKING_DIRECTORY)
    _forward_single_value_arg(NUNV_LOCAL_FORWARDED_ARGS FILE_EXTENSION)
    _forward_single_value_arg(NUNV_LOCAL_FORWARDED_ARGS EXPORT_CONFIGURE_MANIFEST)

    _forward_single_value_arg(NUNV_LOCAL_FORWARDED_ARGS CONFIGURATION)
    _forward_single_value_arg(NUNV_LOCAL_FORWARDED_ARGS DSDL_FILES)
    _forward_single_value_arg(NUNV_LOCAL_FORWARDED_ARGS DSDL_NAMESPACES)

    _forward_option(NUNV_LOCAL_FORWARDED_ARGS ALLOW_EXPERIMENTAL_LANGUAGES)
    _forward_option(NUNV_LOCAL_FORWARDED_ARGS CONSOLE_DEBUG)
    _forward_option(NUNV_LOCAL_FORWARDED_ARGS SUPPORT_ONLY)
    _forward_option(NUNV_LOCAL_FORWARDED_ARGS NO_SUPPORT)
    _forward_option(NUNV_LOCAL_FORWARDED_ARGS OMIT_PUBLIC_REGULATED_NAMESPACE)
    _forward_option(NUNV_LOCAL_FORWARDED_ARGS OMIT_DEPENDENCIES)

    list(APPEND NUNV_LOCAL_DYNAMIC_ARGS ${NUNV_ARG_EXTRA_GENERATOR_ARGS})

    if (DEFINED NUNAVUT_EXTRA_GENERATOR_ARGS)
        message(DEBUG "Got from cache: NUNAVUT_EXTRA_GENERATOR_ARGS=${NUNAVUT_EXTRA_GENERATOR_ARGS}")
        list(APPEND NUNV_LOCAL_DYNAMIC_ARGS ${NUNAVUT_EXTRA_GENERATOR_ARGS})
    elseif (DEFINED ENV{NUNAVUT_EXTRA_GENERATOR_ARGS})
        if (NOT NUNAVUT_PATH_LIST_SEP STREQUAL ";")
            string(REPLACE ${NUNAVUT_PATH_LIST_SEP} ";" LOCAL_NUNAVUT_EXTRA_GENERATOR_ARGS $ENV{NUNAVUT_EXTRA_GENERATOR_ARGS})
        else()
            set(LOCAL_NUNAVUT_EXTRA_GENERATOR_ARGS $ENV{NUNAVUT_EXTRA_GENERATOR_ARGS})
        endif()
        message(DEBUG "Got from environment: NUNAVUT_EXTRA_GENERATOR_ARGS=${LOCAL_NUNAVUT_EXTRA_GENERATOR_ARGS}")
        list(APPEND NUNV_LOCAL_DYNAMIC_ARGS ${LOCAL_NUNAVUT_EXTRA_GENERATOR_ARGS})
    endif()

    set(NUNV_LOCAL_CODEGEN_TARGET "${NUNV_LOCAL_TARGET_NAME}-generate")

    set(NUNV_LOCAL_LIB_BYPRODUCTS_LIST)
    if(NUNV_ARG_EXPORT_GENERATE_MANIFEST)
        _add_option_once(NUNV_LOCAL_DYNAMIC_ARGS "--list-configuration")
        _add_single_value_once(NUNV_LOCAL_DYNAMIC_ARGS "--list-format" "json-pretty")
        set(LOCAL_GENERATE_MANIFEST_PATH ${NUNV_ARG_EXPORT_GENERATE_MANIFEST}/${NUNV_LOCAL_CODEGEN_TARGET}.json)
        list(APPEND NUNV_LOCAL_LIB_BYPRODUCTS_LIST ${LOCAL_GENERATE_MANIFEST_PATH})
        list(APPEND NUNV_LOCAL_DYNAMIC_ARGS "--list-to-file" ${LOCAL_GENERATE_MANIFEST_PATH})
    endif()

    discover_inputs_and_outputs(
        ${NUNV_LOCAL_FORWARDED_ARGS}
        OUT_MANIFEST_DATA NUNV_LOCAL_MANIFEST_DATA
        OUT_INPUTS_LIST NUNV_LOCAL_LIB_INPUTS_LIST
        OUT_OUTPUTS_LIST NUNV_LOCAL_LIB_OUTPUTS_LIST
    )

    # Create the custom command to generate source files.
    add_custom_command(
        OUTPUT ${NUNV_LOCAL_LIB_OUTPUTS_LIST}
        BYPRODUCTS ${NUNV_LOCAL_LIB_BYPRODUCTS_LIST}
        COMMAND
        export PYTHONPATH=${NUNV_LOCAL_PYTHON_PATH} && ${Python3_EXECUTABLE} -m nunavut
        ${NUNV_LOCAL_DYNAMIC_ARGS}
        ${NUNV_LOCAL_LOOKUP_DIRS}
        ${NUNV_ARG_DSDL_FILES}
        WORKING_DIRECTORY ${NUNV_ARG_WORKING_DIRECTORY}
        DEPENDS ${NUNV_LOCAL_LIB_INPUTS_LIST}
    )

    add_custom_target(${NUNV_LOCAL_CODEGEN_TARGET}
        DEPENDS ${NUNV_LOCAL_LIB_OUTPUTS_LIST}
    )

    # finally, define the interface library for the generated headers.
    add_library(${NUNV_LOCAL_TARGET_NAME} INTERFACE ${NUNV_LOCAL_LIB_OUTPUTS_LIST})

    target_include_directories(${NUNV_LOCAL_TARGET_NAME} INTERFACE ${NUNV_ARG_OUTPUT_DIR})

    add_dependencies(${NUNV_LOCAL_TARGET_NAME} ${NUNV_LOCAL_CODEGEN_TARGET})

    if(NUNV_ARG_CONSOLE_DEBUG)
        message(STATUS "${CMAKE_CURRENT_FUNCTION}: Done adding library ${NUNV_LOCAL_TARGET_NAME}.")
    endif()

    # +-[output]---------------------------------------------------------------+
    if(NUNV_ARG_OUT_LIBRARY_TARGET)
        set(${NUNV_ARG_OUT_LIBRARY_TARGET} ${NUNV_LOCAL_TARGET_NAME} PARENT_SCOPE)
    endif()

    if(NUNV_ARG_OUT_CODEGEN_TARGET)
        set(${NUNV_ARG_OUT_CODEGEN_TARGET} ${NUNV_LOCAL_CODEGEN_TARGET} PARENT_SCOPE)
    endif()
endfunction()
