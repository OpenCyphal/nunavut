.. _dsdlgenj:

################################################
dsdlgenj
################################################

.. toctree::
   :maxdepth: 2
   :hidden:

   pydsdlgen/lib
   templates
   appendix
   dev


*************************************
Usage
*************************************

.. argparse::
   :filename: dsdlgenj
   :func: _make_parser
   :prog: dsdlgenj

CMake Integration
======================================

The following cmake function demonstrates how to integrate pydsdelgen with a cmake build system::

    #
    # :function: create_dsdl_target
    # Creates a target that will generate source code from dsdl definitions.
    #
    # The source is generated to files with ${DSDLGENJ_EXTENSION} as the extension.
    #
    # :param str ARG_TARGET_NAME:               The name to give the target.
    # :param Path ARG_TEMPLATES_DIR:            A directory containing the templates to use to generate the source.
    # :param Path ARG_DSDL_ROOT_DIR:            A directory containing the root namespace dsdl.
    # :param ...:                               A list of paths to use when looking up dependent DSDL types.
    #
    function (create_dsdl_target ARG_TARGET_NAME ARG_TEMPLATES_DIR ARG_DSDL_ROOT_DIR)

        set(OUTPUT "${CMAKE_BINARY_DIR}/dsdlgen_${ARG_TARGET_NAME}")

        set(LOOKUP_DIR_CMD_ARGS "")

        if (${ARGC} GREATER 3)
            foreach(ARG_N RANGE 3 ${ARGC}-1)
                list(APPEND LOOKUP_DIR_CMD_ARGS " -I ${ARGV${ARG_N}}")
            endforeach(ARG_N)
        endif()

        execute_process(COMMAND ${DSDLGENJ} --list-outputs
                                            -O ${OUTPUT}
                                            ${LOOKUP_DIR_CMD_ARGS}
                                            ${ARG_DSDL_ROOT_DIR}
                        OUTPUT_VARIABLE OUTPUT_FILES
                        RESULT_VARIABLE LIST_OUTPUTS_RESULT)

        if(NOT LIST_OUTPUTS_RESULT EQUAL 0)
            message(FATAL_ERROR "Failed to retrieve a list of headers the ${DSDLGENJ} would "
                                "generate for the ${ARG_TARGET_NAME} target (${LIST_OUTPUTS_RESULT})")
        endif()

        execute_process(COMMAND ${DSDLGENJ} --list-inputs
                                            -O ${OUTPUT}
                                            --templates ${ARG_TEMPLATES_DIR}
                                            ${LOOKUP_DIR_CMD_ARGS}
                                            ${ARG_DSDL_ROOT_DIR}
                        OUTPUT_VARIABLE INPUT_FILES
                        RESULT_VARIABLE LIST_INPUTS_RESULT)

        if(NOT LIST_INPUTS_RESULT EQUAL 0)
            message(FATAL_ERROR "Failed to resolve inputs using ${DSDLGENJ} for the ${ARG_TARGET_NAME} "
                                "target (${LIST_INPUTS_RESULT})")
        endif()

        add_custom_command(OUTPUT ${OUTPUT_FILES}
                       COMMAND ${DSDLGENJ} --templates ${ARG_TEMPLATES_DIR}
                                           --output-extension ${DSDLGENJ_EXTENSION}
                                           -O ${OUTPUT}
                                           ${LOOKUP_DIR_CMD_ARGS}
                                           ${ARG_DSDL_ROOT_DIR}
                       DEPENDS ${INPUT_FILES}
                       WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                       COMMENT "Running ${DSDLGENJ}")

        add_custom_target(${ARG_TARGET_NAME} DEPENDS ${OUTPUT_FILES})

    endfunction(create_dsdl_target)

This will setup a target that will trigger rebuilds of ``${ARG_TARGET_NAME}`` if any of the
templates or dsdl files are modified. Unfortunatly, cmake only allows for this list to be
generated when the build files are being generated so you'll need to re-run cmake if adding
or removing templates or dsdl types.
