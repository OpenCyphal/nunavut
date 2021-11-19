#
# Find tox.
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

set(PYTHON3_MINIMUM_VERSION 3.6)

find_program(TOX tox)

if(TOX)

    set(TOX_LOCAL_OUTPUT ${NUNAVUT_PROJECT_ROOT}/.tox/local)

    set(TOX_LOCAL_PYTHON_BIN ${TOX_LOCAL_OUTPUT}/bin)

    execute_process(COMMAND ${TOX} --version
                    OUTPUT_VARIABLE TOX_VERSION
                    RESULT_VARIABLE TOX_VERSION_RESULT)

    if(TOX_VERSION_RESULT EQUAL 0)
        message(STATUS "${TOX} --version: ${TOX_VERSION}")
    else()
        message(WARNING "${TOX} --version command failed.")
    endif()

    execute_process(COMMAND ${TOX} -e local
                    WORKING_DIRECTORY ${NUNAVUT_PROJECT_ROOT}
                    RESULT_VARIABLE TOX_LOCAL_RESULT)

    if(NOT TOX_LOCAL_RESULT EQUAL 0)
        message(FATAL_ERROR "Failed to run tox local (${TOX_LOCAL_RESULT})")
    endif()

    # switch over to the virtual environment's python version.
    set(PYTHON ${TOX_LOCAL_PYTHON_BIN}/python)

endif()

# +---------------------------------------------------------------------------+
# | CONFIGURE: VALIDATE TOX AND PYTHON
# +---------------------------------------------------------------------------+

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(tox
    REQUIRED_VARS TOX TOX_LOCAL_PYTHON_BIN
)

execute_process(COMMAND ${PYTHON} --version
                OUTPUT_VARIABLE PYTHON3_VERSION
                RESULT_VARIABLE PYTHON3_VERSION_RESULT)

if(PYTHON3_VERSION_RESULT EQUAL 0)
    string(REPLACE "Python" "" PYTHON3_VERSION ${PYTHON3_VERSION})
    string(STRIP ${PYTHON3_VERSION} PYTHON3_VERSION)
    message(STATUS "${TOX_LOCAL_PYTHON_BIN} --version: ${PYTHON3_VERSION}")
endif()

if(PYTHON3_VERSION VERSION_LESS ${PYTHON3_MINIMUM_VERSION})
    message(FATAL_ERROR "Nunavut requires Python ${PYTHON3_MINIMUM_VERSION} or greater. (found ${PYTHON3_VERSION})")
endif()
