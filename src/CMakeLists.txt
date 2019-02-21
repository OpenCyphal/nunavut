#
# Copyright (C) 2014 Pavel Kirienko <pavel.kirienko@gmail.com>
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

cmake_minimum_required(VERSION 3.5.1)

project(dsdl2cpp CXX)

# +---------------------------------------------------------------------------+
# | EXTERNAL DEPENDENCIES
# +---------------------------------------------------------------------------+
#
# Program : virtualenv
#
# We require virtual env to allow python to run naturally but without polluting
# the host system.
#
find_program(VIRTUALENV virtualenv REQUIRED)

set(VIRTUALENV_OUTPUT ${CMAKE_BINARY_DIR}/python_venv)

execute_process(COMMAND ${VIRTUALENV} -p python3 ${VIRTUALENV_OUTPUT}
                WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

set(PYTHON ${VIRTUALENV_OUTPUT}/bin/python3)
set(PYTHON_REQUIREMENTS ${CMAKE_CURRENT_SOURCE_DIR}/requirements.txt)
set(PIP ${VIRTUALENV_OUTPUT}/bin/pip3)
set(PYTEST ${VIRTUALENV_OUTPUT}/bin/py.test)x

#
# Pypi: pull python dependencies from PyPi
#
# Pull packages we need to support our build and test environment.
#
execute_process(COMMAND ${PIP} --disable-pip-version-check --isolated install -r ${PYTHON_REQUIREMENTS}
                WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

#
# Git submodule management.
#
# (Taken from gitlab's ["modern CMake"](https://cliutils.gitlab.io/modern-cmake/))
#
# It would probably be better to model each of these submodules as cmake external projects
# (like we do for googletest) but for now they are just git submodules.
#
find_package(Git QUIET)

if(GIT_FOUND AND EXISTS "${PROJECT_SOURCE_DIR}/.git")
#   Update submodules as needed
    option(GIT_SUBMODULE "Check submodules during build" ON)
    if(GIT_SUBMODULE)
        message(STATUS "Submodule update")
        execute_process(COMMAND ${GIT_EXECUTABLE} submodule update --init --recursive
                        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                        RESULT_VARIABLE GIT_SUBMOD_RESULT)
        if(NOT GIT_SUBMOD_RESULT EQUAL "0")
            message(FATAL_ERROR "git submodule update --init failed with ${GIT_SUBMOD_RESULT}, please checkout submodules")
        endif()
    endif()
endif()

if(NOT EXISTS "${PROJECT_SOURCE_DIR}/submodules/pydsdl/README.md")
    message(FATAL_ERROR "The pydsdl submodule was not downloaded! GIT_SUBMODULE was turned off or failed. Please update submodules and try again.")
endif()

if(NOT EXISTS "${PROJECT_SOURCE_DIR}/submodules/dsdl/README.md")
    message(FATAL_ERROR "The dsdl submodule was not downloaded! GIT_SUBMODULE was turned off or failed. Please update submodules and try again.")
endif()

#
# Setup pydsdl from submodule into the build's virtual environment.
#
# This does an "editable" install.
#
execute_process(COMMAND ${PIP} --disable-pip-version-check --isolated install -e ${PROJECT_SOURCE_DIR}/submodules/pydsdl/
                WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

# +---------------------------------------------------------------------------+
# | SOURCE GENERATION
# +---------------------------------------------------------------------------+
#
# DSDLC compiler invocation
#
set(DSDLC_PYDSDL_PATH "${CMAKE_CURRENT_SOURCE_DIR}/submodules/pydsdl")
set(DSDLC_INPUTS "${CMAKE_CURRENT_SOURCE_DIR}/submodules/dsdl/uavcan")
set(DSDLC_OUTPUT "${CMAKE_BINARY_DIR}/dsdlc_generated")
set(DSDLC_SCRIPT "${CMAKE_CURRENT_SOURCE_DIR}/commons/dsdl_compiler/libuavcan_dsdlc")
set(DSDLC_TEMPLATE "${LIBUAVCAN_INCLUDE}/uavcan/data_type_template.tmpl")
set(DSDLC_INPUT_FILES "${CMAKE_CURRENT_SOURCE_DIR}/libuavcan")

foreach(DSDLC_INPUT ${DSDLC_INPUTS})
    file(GLOB_RECURSE DSDLC_NEW_INPUT_FILES ${CMAKE_CURRENT_SOURCE_DIR} "${DSDLC_INPUT}/*.uavcan")
    set(DSDLC_INPUT_FILES ${DSDLC_INPUT_FILES} ${DSDLC_NEW_INPUT_FILES})
endforeach(DSDLC_INPUT)

execute_process(COMMAND ${PYTHON} ${DSDLC_SCRIPT} --pydsdl-path ${DSDLC_PYDSDL_PATH} ${DSDLC_INPUTS} --dry-run
                OUTPUT_VARIABLE DSDLC_OUTPUT_FILES
                RESULT_VARIABLE DSDLC_DRY_RUN_RESULT)

if(NOT DSDLC_DRY_RUN_RESULT EQUAL 0)
    message(FATAL_ERROR "Failed to retrieve a list of headers the dsdlc would generate (${DSDLC_DRY_RUN_RESULT})")
endif()

if("${DSDLC_OUTPUT_FILES}" STREQUAL "")
    message(FATAL_ERROR "No header files would be generated for DSDL input \"${DSDLC_INPUTS}\"")
endif()

add_custom_command(OUTPUT ${DSDLC_OUTPUT_FILES}
                   COMMAND ${PYTHON} ${DSDLC_SCRIPT} --pydsdl-path ${DSDLC_PYDSDL_PATH} -T ${DSDLC_TEMPLATE} ${DSDLC_INPUTS} -O${DSDLC_OUTPUT} -v
                   DEPENDS ${DSDLC_INPUT_FILES} ${DSDLC_TEMPLATE}
                   WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                   COMMENT "Running dsdl compiler")

add_custom_target(libuavcan_dsdlc DEPENDS ${DSDLC_OUTPUT_FILES})

#
# dsdl2cpp invocation (work-in-progress)
#
set(DSDL2CPP_INPUTS "${CMAKE_CURRENT_SOURCE_DIR}/submodules/dsdl/uavcan")
set(DSDL2CPP_OUTPUT "${CMAKE_BINARY_DIR}/dsdl2cpp_out")
set(DSDL2CPP_BASE "${CMAKE_CURRENT_SOURCE_DIR}/commons/dsdl2cpp")
set(DSDL2CPP_SCRIPT "${DSDL2CPP_BASE}/dsdl2cpp")
set(DSDL2CPP_TEMPLATE_DIR "${LIBUAVCAN_INCLUDE}/uavcan/templates")
set(DSDL2CPP_INPUT_FILES "${CMAKE_CURRENT_SOURCE_DIR}/libuavcan")

file(GLOB DSDL2CPP_TEMPLATE_FILES ${DSDL2CPP_TEMPLATE_DIR} "*.j2")

foreach(DSDL2CPP_INPUT ${DSDLC_INPUTS})
    file(GLOB_RECURSE DSDL2CPP_NEW_INPUT_FILES ${CMAKE_CURRENT_SOURCE_DIR} "${DSDL2CPP_INPUT}/*.uavcan")
    list(APPEND DSDL2CPP_INPUT_FILES ${DSDL2CPP_NEW_INPUT_FILES})
endforeach(DSDL2CPP_INPUT)

execute_process(COMMAND ${PYTHON} ${DSDL2CPP_SCRIPT} ${DSDL2CPP_INPUTS} --list-outputs -O ${DSDL2CPP_OUTPUT}
                OUTPUT_VARIABLE DSDL2CPP_OUTPUT_FILES
                RESULT_VARIABLE DSDL2CPP_LIST_OUTPUTS_RESULT)

if(NOT DSDL2CPP_LIST_OUTPUTS_RESULT EQUAL 0)
    message(FATAL_ERROR "Failed to retrieve a list of headers the dsdl2cpp would generate (${DSDL2CPP_LIST_OUTPUTS_RESULT})")
endif()

if("${DSDL2CPP_OUTPUT_FILES}" STREQUAL "")
    message(FATAL_ERROR "No header files would be generated for DSDL input \"${DSDL2CPP_INPUTS}\"")
endif()

add_custom_command(OUTPUT ${DSDL2CPP_OUTPUT_FILES}
                   COMMAND ${PYTHON} ${DSDL2CPP_SCRIPT} --templates ${DSDL2CPP_TEMPLATE_DIR} ${DSDL2CPP_INPUTS} -O ${DSDL2CPP_OUTPUT} -v
                   DEPENDS ${DSDL2CPP_INPUT_FILES} ${DSDL2CPP_TEMPLATE_FILES}
                   WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                   COMMENT "Running dsdl2cpp")

add_custom_target(libuavcan_dsdl2cpp DEPENDS ${DSDL2CPP_OUTPUT_FILES})

# +---------------------------------------------------------------------------+
# | BUILD AND RUN NATIVE UNIT TESTS
# +---------------------------------------------------------------------------+
#
# Set flags
#
include_directories(
    ${DSDL2CPP_OUTPUT}
    ${DSDLC_OUTPUT}
)

#
# Test : All C++ Unit Tests
#
file(GLOB_RECURSE TEST_CXX_FILES RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "test/native/*.cpp")
add_executable(libuavcan_test_native ${TEST_CXX_FILES})
add_dependencies(libuavcan_test_native libuavcan_dsdlc libuavcan_dsdl2cpp)
target_link_libraries(libuavcan_test_native gmock_main)

add_test(NAME libuavcan_test_native
         COMMAND libuavcan_test_native
         WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR})

#
# Test : All Python Unit Tests
#
set(PYTEST_COV_CONFIG ${CMAKE_BINARY_DIR}/coveragerc)
file(WRITE ${PYTEST_COV_CONFIG}
     "[run]\ndata_file = ${CMAKE_BINARY_DIR}/.coverage")
add_test(NAME dsdl2cpp_test
        COMMAND ${PYTEST} --cov=libdsdl2cpp --cov-report html:${CMAKE_BINARY_DIR}/htmlcov --cov-config ${CMAKE_BINARY_DIR}/coveragerc ${DSDL2CPP_BASE}
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
