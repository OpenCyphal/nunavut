#
# Find the newest python3 version available.
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

set(PYTHON3_MINIMUM_VERSION 3.5)

find_program(PYTHON3 python3.8)

if (NOT PYTHON3)
    find_program(PYTHON3 python3.7)
endif()

if (NOT PYTHON3)
    find_program(PYTHON3 python3.6)
endif()

if (NOT PYTHON3)
    find_program(PYTHON3 python3.5)
endif()

if (NOT PYTHON3)
    find_program(PYTHON3 python3)
endif()

if (NOT PYTHON3)
    message(FATAL_ERROR "Could not find python3.")
endif()

# +---------------------------------------------------------------------------+
# | CONFIGURE: VALIDATE NNVG
# +---------------------------------------------------------------------------+

execute_process(COMMAND ${PYTHON3} --version
                OUTPUT_VARIABLE PYTHON3_VERSION
                RESULT_VARIABLE PYTHON3_VERSION_RESULT)

if(PYTHON3_VERSION_RESULT EQUAL 0)
    string(REPLACE "Python" "" PYTHON3_VERSION ${PYTHON3_VERSION})
    string(STRIP ${PYTHON3_VERSION} PYTHON3_VERSION)
    message(STATUS "${PYTHON3} --version: ${PYTHON3_VERSION}")
endif()


include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(nnvg
    REQUIRED_VARS PYTHON3_VERSION
)

if(PYTHON3_VERSION VERSION_LESS ${PYTHON3_MINIMUM_VERSION})
    message(FATAL_ERROR "Nunavut requires Python ${PYTHON3_MINIMUM_VERSION} or greater. (found ${PYTHON3_VERSION})")
endif()
