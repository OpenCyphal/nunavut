#
# Find virtualenv. If found provide a way to setup a virtualenv for the build.
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

find_program(VIRTUALENV virtualenv)

if(VIRTUALENV)

    if (NOT DEFINED VIRTUALENV_OUTPUT)
        set(VIRTUALENV_OUTPUT ${NUNAVUT_PROJECT_ROOT}/.pyenv)
    else()
        message(STATUS "Using predefined VIRTUALENV_OUTPUT=${VIRTUALENV_OUTPUT}")
    endif()

    set(VIRTUALENV_PYTHON_BIN ${VIRTUALENV_OUTPUT}/bin)
    set(PYTHON ${VIRTUALENV_PYTHON_BIN}/python)
    set(PIP ${VIRTUALENV_PYTHON_BIN}/pip)

    if(NOT EXISTS ${VIRTUALENV_OUTPUT})
        message(STATUS "virtualenv found. Creating a virtual environment and installing core requirements.")

        execute_process(COMMAND ${VIRTUALENV} -p ${PYTHON3} ${VIRTUALENV_OUTPUT}
                        WORKING_DIRECTORY ${NUNAVUT_PROJECT_ROOT}
                        RESULT_VARIABLE VIRTUALENV_CREATE_RESULT)
        
        if(NOT VIRTUALENV_CREATE_RESULT EQUAL 0)
            message(FATAL_ERROR "Failed to create a virtualenv (${VIRTUALENV_CREATE_RESULT})")
        endif()

    else()
        message(STATUS "virtualenv ${VIRTUALENV_OUTPUT} exists. Not recreating (delete this directory to re-create).")
    endif()

endif()

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(nnvg
    REQUIRED_VARS VIRTUALENV VIRTUALENV_PYTHON_BIN
)
