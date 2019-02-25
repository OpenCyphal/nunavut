#
# Common logic for adding Python virtual environment support to our
# cmake environment.
#
# If found then the following variables are set:
#   VIRTUALENV_FOUND      1
#   VIRTUALENV_EXECUTABLE Path to the virtualenv executable
#   VIRTUALENV_ROOT       Path to the root of the virtual environment
#                         for this project.
#
find_program(VIRTUALENV_EXECUTABLE virtualenv QUIET)

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(Virtualenv
    FOUND_VAR VIRTUALENV_FOUND
    REQUIRED_VARS VIRTUALENV_EXECUTABLE
)

set(VIRTUALENV_ROOT ${CMAKE_BINARY_DIR}/.venv)
