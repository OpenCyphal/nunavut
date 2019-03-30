#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

cmake_minimum_required(VERSION 3.5.1)

project(pydsdlgen NONE)

# +---------------------------------------------------------------------------+
# | EXTERNAL DEPENDENCIES
# +---------------------------------------------------------------------------+
#
# Tell cmake where to find our custom scripts.
#
set(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")

#
# Update and make sure our submodule dependencies are updated.
#
find_package(Submodules QUIET)

if(NOT EXISTS "${PROJECT_SOURCE_DIR}/test/gentest_dsdl/dsdl/README.md")
	message(FATAL_ERROR "The dsdl submodule was not downloaded! GIT_SUBMODULE was turned off or failed. Please update submodules and try again.")
endif()

#
# Program : virtualenv
#
# We require virtual env to allow python to run naturally but without polluting
# the host system. This is also the most pythonic way to ensure that the tests are 
# run against what gets installed and not just what's in source.
#
find_package(Virtualenv REQUIRED)

execute_process(COMMAND ${VIRTUALENV_EXECUTABLE} -p python3 --no-download ${VIRTUALENV_ROOT}
                WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

set(PYTHON_REQUIREMENTS ${CMAKE_CURRENT_SOURCE_DIR}/requirements.txt)

#
# I Like to use visual studio code for Python development.
# You don't have to.
#
find_package(Code QUIET)

# Binaries we expect to have in our virtual environment
#
set(PYTHON ${VIRTUALENV_ROOT}/bin/python3)
set(PIP ${VIRTUALENV_ROOT}/bin/pip3)
set(PYTEST ${PYTHON} -m pytest)
set(PYCOVERAGE ${VIRTUALENV_ROOT}/bin/coverage)
set(PYCOVERALLS ${VIRTUALENV_ROOT}/bin/coveralls)
set(MYPY ${VIRTUALENV_ROOT}/bin/mypy)
set(FLAKE8 ${VIRTUALENV_ROOT}/bin/flake8)

#
# Pypi: pull python dependencies from PyPi
#
# Pull packages we need to support our build and test environment.
#
execute_process(COMMAND ${PIP} --disable-pip-version-check --isolated install -r ${PYTHON_REQUIREMENTS}
                WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

#
# Pypi: perform editiable install to the local virtualenv to test
#       what the end-user will see after installing.
#
execute_process(COMMAND ${PIP} --disable-pip-version-check --isolated install -e ${CMAKE_CURRENT_SOURCE_DIR}
                WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})


# +---------------------------------------------------------------------------+
# | PYTHON LINTING AND STATIC ANALYSIS
# +---------------------------------------------------------------------------+
file(GLOB LINTER_INPUTS
    "${CMAKE_CURRENT_SOURCE_DIR}/src/pydsdlgen/*.py"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/pydsdlgen/jinja/*.py"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/pydsdlgen/jinja/lang/*.py"
)

list(APPEND LINTER_INPUTS ${CMAKE_CURRENT_SOURCE_DIR}/src/dsdlgenj)
set(LINTER_OUTPUTS ${MYPY_REPORT_COVERAGE})

set(MYPY_REPORT_DIR ${CMAKE_BINARY_DIR}/mypy-reports)
set(MYPY_REPORT_COVERAGE ${MYPY_REPORT_DIR}/coverage.json)

add_custom_command(OUTPUT ${MYPY_REPORT_COVERAGE}
                   COMMAND ${MYPY} 
                        --cache-dir ${CMAKE_BINARY_DIR}
                        --linecoverage-report ${MYPY_REPORT_DIR}
                        ${LINTER_INPUTS}
                   DEPENDS ${LINTER_INPUTS}
                   WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                   COMMENT "Running mypy on source")

set(FLAKE8_REPORT ${CMAKE_BINARY_DIR}/flake8.txt)

list(APPEND LINTER_OUTPUTS ${MYPY_REPORT_COVERAGE})

add_custom_command(OUTPUT ${FLAKE8_REPORT}
                   COMMAND ${FLAKE8} 
                        --benchmark 
                        --tee
                        --output-file=${FLAKE8_REPORT}
                        ${LINTER_INPUTS}
                   DEPENDS ${LINTER_INPUTS}
                   WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                   COMMENT "Running flake8 on source")

# alias for all static analysis and linters
add_custom_target(linting DEPENDS ${LINTER_OUTPUTS})

# +---------------------------------------------------------------------------+
# | SOURCE GENERATION FOR TESTING
# +---------------------------------------------------------------------------+
enable_testing()

set(pydsdlgen_BASE "${VIRTUALENV_ROOT}/bin")
set(pydsdlgen_SCRIPT_NAME dsdlgenj)
set(pydsdlgen_SCRIPT "${pydsdlgen_BASE}/${pydsdlgen_SCRIPT_NAME}")

#
# dsdlgenj invocation. while we could support multiple templating languages we
# currently only support Jinja. Not sure why we'd want more than one other than
# a future where we were migrating off of Jinja and supporting it as legacy.
#
# Conventions:
#   1. Generation tests must be in a folder named ${CMAKE_CURRENT_SOURCE_DIR}/test/gentest_${ARG_TESTNAME}
#   2. Under this test folder there must be a "dsdl" folder with a "uavcan" root namespace containing the dsdl
#      to be used as test fixtures.
#   3. Under this test folder there must be a "templates" folder with the j2 (jinja2) templates to be used
#      as test fixtures.
#
function(make_gentest ARG_TESTNAME ARG_OUTPUT_EXTENSION)

    set(ROOTINPUTS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/test/gentest_${ARG_TESTNAME}/dsdl/uavcan)
    set(TEMPLATES_DIR ${CMAKE_CURRENT_SOURCE_DIR}/test/gentest_${ARG_TESTNAME}/templates)

    set(OUTPUT "${CMAKE_BINARY_DIR}/testgen_${ARG_TESTNAME}")
    
    execute_process(COMMAND ${PYTHON} ${pydsdlgen_SCRIPT} ${ROOTINPUTS_DIR} --list-outputs -O ${OUTPUT}
                    OUTPUT_VARIABLE OUTPUT_FILES
                    RESULT_VARIABLE LIST_OUTPUTS_RESULT)

    if(NOT LIST_OUTPUTS_RESULT EQUAL 0)
        message(FATAL_ERROR "Failed to retrieve a list of headers the ${pydsdlgen_SCRIPT_NAME} would generate for the ${ARG_TESTNAME} test (${LIST_OUTPUTS_RESULT})")
    endif()

    if("${OUTPUT_FILES}" STREQUAL "")
        message(FATAL_ERROR "No header files would be generated for DSDL input \"${ROOTINPUTS_DIR}\"")
    endif()

    execute_process(COMMAND ${PYTHON} ${pydsdlgen_SCRIPT} ${ROOTINPUTS_DIR} --list-inputs -O ${OUTPUT} --templates ${TEMPLATES_DIR} 
                    OUTPUT_VARIABLE INPUT_FILES
                    RESULT_VARIABLE LIST_INPUTS_RESULT)

    if(NOT LIST_INPUTS_RESULT EQUAL 0)
        message(FATAL_ERROR "Failed to resolve inputs using ${pydsdlgen_SCRIPT_NAME} ${ARG_TESTNAME} test (${LIST_INPUTS_RESULT})")
    endif()

    if("${INPUT_FILES}" STREQUAL "")
        message(FATAL_ERROR "No inputs resolved for the arguments given to pydsdlgen \"--templates ${TEMPLATES_DIR} ${ROOTINPUTS_DIR}\"")
    endif()

    add_custom_command(OUTPUT ${OUTPUT_FILES}
                       COMMAND ${PYCOVERAGE} run
                                             -a
                                             --rcfile=${PYTEST_COV_CONFIG}
                               ${pydsdlgen_SCRIPT}
                                            --templates ${TEMPLATES_DIR}
                                            --output-extension ${ARG_OUTPUT_EXTENSION}
                                            ${ROOTINPUTS_DIR}
                                            -O ${OUTPUT} 
                                            -v
                       DEPENDS ${INPUT_FILES}
                       WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                       COMMENT "Running ${pydsdlgen_SCRIPT_NAME}")

    add_custom_target(testgen_${ARG_TESTNAME} DEPENDS ${OUTPUT_FILES})

    add_dependencies(testgen testgen_${ARG_TESTNAME})

endfunction(make_gentest)


# +---------------------------------------------------------------------------+
# | BUILD AND RUN UNIT TESTS
# +---------------------------------------------------------------------------+

#
# Test : All Python Unit Tests
#


#
# Define a phony target that will run all testgen_[generation test name] targets. Dependencies
# are automatically added by the make_gentest function.
#
add_custom_target(testgen)

#
# Verifies generating all standard, regulated dsdl types as C headers.
#
make_gentest(dsdl .h)

#
# Verifies genearting some test types as JSON.
#
make_gentest(json .json)

#
# Run all Python tests in the pydsdlgen library (Gentests cover the script form).
#
add_test(NAME test_pydsdlgen
    COMMAND ${PYTEST} --cov=pydsdlgen
                      --cov-config=${CMAKE_CURRENT_SOURCE_DIR}/tox.ini
                      --cov-append
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/test)


# +---------------------------------------------------------------------------+
# | GENERATE DOCUMENTATION
# +---------------------------------------------------------------------------+

find_package(Sphinx QUIET)

if(SPHINX_FOUND)
    set(SPHINX_OUTDIR ${CMAKE_CURRENT_BINARY_DIR}/sphinx)

    add_custom_target(create-sphinx-dir ALL
                      COMMAND ${CMAKE_COMMAND} -E make_directory ${SPHINX_OUTDIR})

    # Images, templates, styles, etc for sphinx docs.
    set(SPHINX_RESOURCES_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/docs")

    # configured documentation tools and intermediate build results
    set(BINARY_BUILD_DIR "${SPHINX_OUTDIR}/_build")

    # Sphinx cache with pickled ReST documents
    set(SPHINX_CACHE_DIR "${SPHINX_OUTDIR}/_doctrees")

    # HTML output directory
    set(SPHINX_HTML_DIR "${SPHINX_OUTDIR}/html")

    add_custom_target(docgen ALL
        ${SPHINX_EXECUTABLE}
            -b html
            -d "${SPHINX_CACHE_DIR}"
            "${CMAKE_CURRENT_SOURCE_DIR}/src"
            "${SPHINX_HTML_DIR}"
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/src
        DEPENDS create-sphinx-dir
        COMMENT "Building HTML documentation with Sphinx")
endif()

# +---------------------------------------------------------------------------+
# | GENERATE REPORTS
# +---------------------------------------------------------------------------+
#
# Report on coverage achieved in all python testing.
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
                    ${PYCOVERALLS} --rcfile=${PYTEST_COV_CONFIG}
                    DEPENDS testgen ${LINTER_OUTPUTS} ${PYTEST_COV_CONFIG}
                    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
                    COMMENT "Committing coverage data to coveralls.")
