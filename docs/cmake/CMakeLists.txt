#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#

cmake_minimum_required(VERSION 3.27.0 FATAL_ERROR)

project("Nunavut Cmake Example"
        VERSION 1.0
        LANGUAGES C
        HOMEPAGE_URL https://github.com/OpenCyphal/nunavut
        DESCRIPTION "Demonstration of running Nunavut from source using the CMAKE FetchContent module."
)

# This example demonstrates how to integrate Nunavut into a CMake project using the FetchContent module where only Cmake
# itself and Python are needed to run the code generation step. This is useful for projects that do not have a managed
# Python environment; allowing a default Python installation as might be found in a modern Linux distribution to be used
# without pip or setup-tools and without modifying the global Python environment. We do this by pulling Nunavut and
# Pydsdl from git and running Nunavut from source as ``python -m nunavut`` (which is the same as running the ``nnvg``
# script for an installed version of Nunavut).

# +---------------------------------------------------------------------------+
# | External Dependencies
# +---------------------------------------------------------------------------+
include(FetchContent)

# See CMakePresets.json for a convenient way to control online/offline mode.
# Documentation for this feature can be found here:
# https://cmake.org/cmake/help/latest/module/FetchContent.html#variable:FETCHCONTENT_FULLY_DISCONNECTED
if (${FETCHCONTENT_FULLY_DISCONNECTED})
    message(STATUS "☑️ FetchContent OFFLINE")
else()
    message(STATUS "✅ FetchContent ONLINE")
endif()

# We'll use LOCAL_EXTERNAL_ROOT by convention to refer to a folder under which all FetchContent projects will be stored.
# You can add this to .gitignore to avoid checking in the external source or you can check it in based on your project's
# needs. If checked in then the build will not need network access nor will it fail if github is unavailable. Because of
# this we highly recommend such a configuration. See the provided CMakePresets.json in this folder for a convenient way
# to switch between online and offline builds. This file defines presets such that:
#
#    cmake -B build -G Ninja --preset Connected
#
# will configure the build and go online to synchronize resources where:
#
#    cmake -B build -G Ninja --preset Disconnected
#
# will configure the build to stay offline and use whatever is available under the external folder.
set(LOCAL_EXTERNAL_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/external)

# Add Nunavut as a CMake module path. It contains the NunavutConfig.cmake file.
list(APPEND CMAKE_PREFIX_PATH "${CMAKE_CURRENT_SOURCE_DIR}/external/nunavut")

# We'll declare the Nunavut git repository in Github as the source we use in this example. From there we get all of
# Nunavut and submodules under `${LOCAL_EXTERNAL_ROOT}/nunavut/submodules` or just `submodules/` when the path is
# relative to the Nunavut repo itself.
FetchContent_Declare(
    Nunavut
    GIT_REPOSITORY  "https://github.com/OpenCyphal/nunavut"
    GIT_TAG         "8b67b5f4e79db6b41ed537f18a3173f5f52f61ae" # <-- Here we've specified a specific git hash. This is
                                                               #     the strongest declaration of a fetched dependency.
                                                               #     Using a hash says we don't care if there are bugs
                                                               #     that are patched later. We want total build
                                                               #     reproducibility (caveat: https://github.blog/news-insights/company-news/sha-1-collision-detection-on-github-com/)
    SOURCE_DIR      "${LOCAL_EXTERNAL_ROOT}/nunavut"
    GIT_SUBMODULES
        submodules/public_regulated_data_types                 # <-- You can use the public regulated types in Nunavut
                                                               #     or you can pull your version in as a separate
                                                               #     FetchContent_Declare call. If you pull your own
                                                               #     be sure to set OMIT_PUBLIC_REGULATED_NAMESPACE
                                                               #     when calling add_cyphal_library.
        submodules/pydsdl                                      # <-- By pulling in pydsdl from Nunavut we get the
                                                               #     correct version and `add_cyphal_library` (see
                                                               #     below) automatically finds it. If you want to
                                                               #     pull in your own version `add_cyphal_library`
                                                               #     lets you change the path using the PYDSDL_PATH
                                                               #     argument.
    GIT_SHALLOW ON
    GIT_SUBMODULES_RECURSE OFF
    FIND_PACKAGE_ARGS 3.0
)

# Now we'll make the dependencies available. If FETCHCONTENT_FULLY_DISCONNECTED is set to OFF then this will pull the
# dependencies from github. As mentioned above, we recommend checking in these dependencies and committing them to your
# own repository to maximize build availability and reproducibility but to also run an online version of your build in a
# CI pipeline to ensure ongoing compatibility.
FetchContent_MakeAvailable(
    Nunavut
)

# +---------------------------------------------------------------------------+
# | Using NunavutConfig.cmake
# +---------------------------------------------------------------------------+

# We'll define the custom types we want to generate code for. These are the types that are not part of the public
# regulated data types. In this case we have two custom types that are part of the ecorp namespace.
set(LOCAL_ECORP_CUSTOM_TYPES
    ${CMAKE_CURRENT_SOURCE_DIR}/custom_types/ecorp/customer/record.2.8.dsdl
    ${CMAKE_CURRENT_SOURCE_DIR}/custom_types/ecorp/fintech/mortgage/property.4.2.dsdl
)

# Now we'll add a library target that will also setup a code gen target as a dependency. We'll add the public
# regulated types as a dependency so that the generated code can use those. This will generate code only for the
# custom types we've defined and their dependencies.
add_cyphal_library(
    NAME ecorp      # <------------------------------------------ Make sure this is unique for each cyphal library you
                    #                                             define, if you are defining more than one.
    DSDL_FILES ${LOCAL_ECORP_CUSTOM_TYPES}
    DSDL_NAMESPACES # <------------------------------------------ Here we list all valid namespace roots. Any direct
                    #                                             or dependent type that cannot be found under one of
                    #                                             these roots will cause the code-gen rule to fail.
                    #                                             The "uavcan" namespace under public_regulated_types
                    #                                             is automatically added to this list unless we set the
                    #                                             OMIT_PUBLIC_REGULATED_NAMESPACE option.
        ${CMAKE_CURRENT_SOURCE_DIR}/custom_types/ecorp
    LANGUAGE_STANDARD c11
    LANGUAGE c
    OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR}/include    # <-------- This is also the include path added to the interface
                                                      #           library for including generated code.
    OUT_LIBRARY_TARGET CYPHAL_GENERATED_HEADERS_ECORP # <-------- ${CYPHAL_GENERATED_HEADERS_ECORP} will resolve to the
                                                      #           name of the interface library defined after this
                                                      #           function exits (successfully).
    EXPORT_MANIFEST                                   # <-------- Optional. Writes a json file in the build output that
                                                      #           dumps all configuration used by Nunavut, all template
                                                      #           files, all dsdl files, and all output files that were
                                                      #           or would be generated (think of this as the nnvg
                                                      #           equivalent of compile_commands.json).
)


# +---------------------------------------------------------------------------+
# | Example Application
# +---------------------------------------------------------------------------+
# By way of demonstration, we'll add a little executable...
add_executable(ecorp_pi main.c)

# We then add a link to the headers interface library so the ecorp_pi executable will inherit the paths to the generated
# headers. This also ensures the code generation step will occur before the ecorp_pi compilation step. Note that, while
# this example uses dynamic resolution of all dsdl resources at configure-time, code generation is deferred to
# build-time.
target_link_libraries(ecorp_pi PUBLIC ${CYPHAL_GENERATED_HEADERS_ECORP})
