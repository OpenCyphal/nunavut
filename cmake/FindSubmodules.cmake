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
    set(GIT_AND_GITDIR_FOUND 1)
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

mark_as_advanced(GIT_AND_GITDIR_FOUND)

include(FindPackageHandleStandardArgs)
 
find_package_handle_standard_args(Submodules
    FOUND_VAR SUBMODULES_FOUND
    REQUIRED_VARS GIT_FOUND GIT_AND_GITDIR_FOUND
)
 