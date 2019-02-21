#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

cmake_minimum_required(VERSION 3.5.1)

project(dsdl2cpp NONE)

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

execute_process(COMMAND ${VIRTUALENV} -p python3 --no-download ${VIRTUALENV_OUTPUT}
                WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

set(PYTHON_REQUIREMENTS ${CMAKE_CURRENT_SOURCE_DIR}/requirements.txt)

#
# Binaries we expect to have in our virtual environment
#
set(PYTHON ${VIRTUALENV_OUTPUT}/bin/python3)
set(PIP ${VIRTUALENV_OUTPUT}/bin/pip3)
set(PYTEST ${VIRTUALENV_OUTPUT}/bin/py.test)
set(PYCOVERAGE ${VIRTUALENV_OUTPUT}/bin/coverage)
set(PYCOVERALLS ${VIRTUALENV_OUTPUT}/bin/coveralls)

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
set(SUBMODULES_DIR ${PROJECT_SOURCE_DIR}/submodules)

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

if(NOT EXISTS "${SUBMODULES_DIR}/pydsdl/README.md")
    message(FATAL_ERROR "The pydsdl submodule was not downloaded! GIT_SUBMODULE was turned off or failed. Please update submodules and try again.")
endif()

#
# Setup pydsdl from submodule into the build's virtual environment.
#
# This does an "editable" install.
#
execute_process(COMMAND ${PIP} --disable-pip-version-check --isolated install -e ${PROJECT_SOURCE_DIR}/submodules/pydsdl/
                WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

# +---------------------------------------------------------------------------+
# | SOURCE GENERATION FOR TESTING
# +---------------------------------------------------------------------------+
enable_testing()

set(DSDL2CPP_BASE "${CMAKE_CURRENT_SOURCE_DIR}/src")
set(DSDL2CPP_SCRIPT "${DSDL2CPP_BASE}/dsdl2cpp")

#
# dsdl2cpp invocation (work-in-progress)
#
function(make_gentest ARG_TESTNAME ARG_ROOTINPUTS_DIR ARG_TEMPLATES_DIR)
    set(OUTPUT "${CMAKE_BINARY_DIR}/testgen_${ARG_TESTNAME}")
    
    execute_process(COMMAND ${PYTHON} ${DSDL2CPP_SCRIPT} ${ARG_ROOTINPUTS_DIR} --list-outputs -O ${OUTPUT}
                    OUTPUT_VARIABLE OUTPUT_FILES
                    RESULT_VARIABLE LIST_OUTPUTS_RESULT)

    if(NOT LIST_OUTPUTS_RESULT EQUAL 0)
        message(FATAL_ERROR "Failed to retrieve a list of headers the dsdl2cpp would generate for the ${ARG_TESTNAME} test (${LIST_OUTPUTS_RESULT})")
    endif()

    if("${OUTPUT_FILES}" STREQUAL "")
        message(FATAL_ERROR "No header files would be generated for DSDL input \"${ARG_ROOTINPUTS_DIR}\"")
    endif()

    execute_process(COMMAND ${PYTHON} ${DSDL2CPP_SCRIPT} ${ARG_ROOTINPUTS_DIR} --list-inputs -O ${OUTPUT} --templates ${ARG_TEMPLATES_DIR} 
                    OUTPUT_VARIABLE INPUT_FILES
                    RESULT_VARIABLE LIST_INPUTS_RESULT)

    if(NOT LIST_INPUTS_RESULT EQUAL 0)
        message(FATAL_ERROR "Failed to resolve inputs using dsdl2cpp ${ARG_TESTNAME} test (${LIST_INPUTS_RESULT})")
    endif()

    if("${INPUT_FILES}" STREQUAL "")
        message(FATAL_ERROR "No inputs resolved for the arguments given to dsdl2cpp \"--templates ${ARG_TEMPLATES_DIR} ${ARG_ROOTINPUTS_DIR}\"")
    endif()

    add_custom_command(OUTPUT ${OUTPUT_FILES}
                       COMMAND ${PYCOVERAGE} run
                                             -a
                                             --rcfile=${PYTEST_COV_CONFIG}
                               ${DSDL2CPP_SCRIPT}
                                            --templates ${ARG_TEMPLATES_DIR} 
                                            ${ARG_ROOTINPUTS_DIR}
                                            -O ${OUTPUT} 
                                            -v
                       DEPENDS ${INPUT_FILES}
                       WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                       COMMENT "Running dsdl2cpp")

    add_custom_target(testgen_${ARG_TESTNAME} DEPENDS ${OUTPUT_FILES})

    add_dependencies(testgen testgen_${ARG_TESTNAME})

endfunction(make_gentest)

# +---------------------------------------------------------------------------+
# | BUILD AND RUN UNIT TESTS
# +---------------------------------------------------------------------------+

#
# Test : All Python Unit Tests
#
set(PYTEST_COV_CONFIG ${CMAKE_BINARY_DIR}/coveragerc)
set(PYCOVERAGE_DATA_FILE ${CMAKE_BINARY_DIR}/.coverage)

file(WRITE ${PYTEST_COV_CONFIG}
     "\n\
[run]\n\
    data_file=${PYCOVERAGE_DATA_FILE}\n\
    branch=True\n\
    omit=\n\
      ${VIRTUALENV_OUTPUT}/*\n\
      ${SUBMODULES_DIR}/*\n\
")

#
# Define a phony target that will run all testgen_[generation test name] targets. Dependencies
# are automatically added by the make_gentest function.
#
add_custom_target(testgen)

#
# A DSDL generation test that verifies a simple message.
#
make_gentest(simple_message ${CMAKE_CURRENT_SOURCE_DIR}/test/gentest0/uavcan  ${CMAKE_CURRENT_SOURCE_DIR}/test/gentest0/templates)

#
# Run all Python tests in the dsdl2cpp library (Gentests cover the script form).
#
add_test(NAME test_libdsdl2cpp
    COMMAND ${PYTEST} --cov=libdsdl2cpp 
                      --cov-config ${PYTEST_COV_CONFIG}
                      --cov-append
                      ${DSDL2CPP_BASE}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/src)

# +---------------------------------------------------------------------------+
# | GENERATE REPORTS
# +---------------------------------------------------------------------------+
#
# Report on coverage achived in all python testing.
#
add_custom_command( OUTPUT ${CMAKE_BINARY_DIR}/htmlcov-testgen/index.html
                    COMMAND ${PYCOVERAGE} html 
                        --rcfile=${PYTEST_COV_CONFIG} 
                        -d ${CMAKE_BINARY_DIR}/htmlcov-testgen
                    DEPENDS testgen
                    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                    COMMENT "Generating HTML coverage report for testgen runs")

add_custom_target(testgen_report DEPENDS ${CMAKE_BINARY_DIR}/htmlcov-testgen/index.html)

add_custom_target(  upload_to_coveralls_io
                    ${PYCOVERALLS}
                    DEPENDS testgen
                    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
                    COMMENT "Committing coverage data to coveralls.")
