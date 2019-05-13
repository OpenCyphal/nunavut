.. _nnvgj:

################################################
nnvg
################################################

.. toctree::
   :maxdepth: 2
   :hidden:

   nunavut/lib
   templates
   appendix
   dev


*************************************
Usage
*************************************

.. argparse::
   :filename: nnvg
   :func: _make_parser
   :prog: nnvg

CMake Integration
======================================

The following cmake function demonstrates how to integrate pydsdelgen with a cmake build system::

    #
    # :function: create_dsdl_target
    # Creates a target that will generate source code from dsdl definitions.
    #
    # The source is generated to files with ${NNVGJ_EXTENSION} as the extension.
    #
    # :param str ARG_TARGET_NAME:               The name to give the target.
    # :param Path ARG_OUTPUT_FOLDER:            The directory to generate all source under.
    # :param Path ARG_TEMPLATES_DIR:            A directory containing the templates to use to generate the source.
    # :param Path ARG_DSDL_ROOT_DIR:            A directory containing the root namespace dsdl.
    # :param ...:                               A list of paths to use when looking up dependent DSDL types.
    # :returns: Sets a variable "ARG_TARGET_NAME"-OUTPUT in the parent scope to the list of files the target
    #           will generate. For example, if ARG_TARGET_NAME == 'foo-bar' then after calling this function
    #           ${foo-bar-OUTPUT} will be set to the list of output files.
    #
    function (create_dsdl_target ARG_TARGET_NAME ARG_OUTPUT_FOLDER ARG_TEMPLATES_DIR ARG_DSDL_ROOT_DIR)

        set(LOOKUP_DIR_CMD_ARGS "")

        if (${ARGC} GREATER 5)
            foreach(ARG_N RANGE 5 ${ARGC}-1)
                list(APPEND LOOKUP_DIR_CMD_ARGS " -I ${ARGV${ARG_N}}")
            endforeach(ARG_N)
        endif()

        execute_process(COMMAND ${PYTHON} ${NNVGJ}
                                            --list-outputs
                                            --output-extension ${NNVGJ_EXTENSION}
                                            -O ${ARG_OUTPUT_FOLDER}
                                            ${LOOKUP_DIR_CMD_ARGS}
                                            ${ARG_DSDL_ROOT_DIR}
                        OUTPUT_VARIABLE OUTPUT_FILES
                        RESULT_VARIABLE LIST_OUTPUTS_RESULT)

        if(NOT LIST_OUTPUTS_RESULT EQUAL 0)
            message(FATAL_ERROR "Failed to retrieve a list of headers nnvg would "
                                "generate for the ${ARG_TARGET_NAME} target (${LIST_OUTPUTS_RESULT})"
                                " (${PYTHON} ${NNVGJ})")
        endif()

        execute_process(COMMAND ${PYTHON} ${NNVGJ}
                                            --list-inputs
                                            -O ${ARG_OUTPUT_FOLDER}
                                            --templates ${ARG_TEMPLATES_DIR}
                                            ${LOOKUP_DIR_CMD_ARGS}
                                            ${ARG_DSDL_ROOT_DIR}
                        OUTPUT_VARIABLE INPUT_FILES
                        RESULT_VARIABLE LIST_INPUTS_RESULT)

        if(NOT LIST_INPUTS_RESULT EQUAL 0)
            message(FATAL_ERROR "Failed to resolve inputs using nnvg for the ${ARG_TARGET_NAME} "
                                "target (${LIST_INPUTS_RESULT})"
                                " (${PYTHON} ${NNVGJ})")
        endif()

        add_custom_command(OUTPUT ${OUTPUT_FILES}
                        COMMAND ${PYTHON} ${NNVGJ}
                                            --templates ${ARG_TEMPLATES_DIR}
                                            --output-extension ${NNVGJ_EXTENSION}
                                            -O ${ARG_OUTPUT_FOLDER}
                                            ${LOOKUP_DIR_CMD_ARGS}
                                            ${ARG_DSDL_ROOT_DIR}
                        DEPENDS ${INPUT_FILES}
                        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                        COMMENT "Running nnvg")

        add_custom_target(${ARG_TARGET_NAME} ALL DEPENDS ${OUTPUT_FILES})

        set(${ARG_TARGET_NAME}-OUTPUT ${OUTPUT_FILES} PARENT_SCOPE)

    endfunction(create_dsdl_target)

This will setup a target that will trigger rebuilds of ``${ARG_TARGET_NAME}`` if any of the
templates or dsdl files are modified. Unfortunately, cmake only allows for this list to be
generated when the build files are being generated so you'll need to re-run cmake if adding
or removing templates or dsdl types.
