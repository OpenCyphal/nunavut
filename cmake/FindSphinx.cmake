#
# Borrowed, with much thanks, from 
# https://eb2.co/blog/2012/03/sphinx-and-cmake-beautiful-documentation-for-c---projects/
#
find_program(SPHINX_EXECUTABLE NAMES sphinx-build
    HINTS
    ${VIRTUALENV_ROOT} $ENV{SPHINX_DIR}
    PATH_SUFFIXES bin
    DOC "Sphinx documentation generator"
)

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(Sphinx
    FOUND_VAR SPHINX_FOUND
    REQUIRED_VARS SPHINX_EXECUTABLE
)

mark_as_advanced(SPHINX_EXECUTABLE)
