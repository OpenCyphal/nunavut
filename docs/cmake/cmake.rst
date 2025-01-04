################################################
CMake Integration
################################################

.. _fetch_content:

*************************************
FetchContent Example
*************************************

Under the :github_link:`docs/cmake` folder of the Nunavut repo is an example project that uses
`CMake's FetchContent <https://cmake.org/cmake/help/latest/module/FetchContent.html>`__ module to integrate
:ref:`nnvg` code generation into a CMake project.

.. _fetch_content_cmake_lists:

====================================
CMakeLists Figure
====================================

This example ``CMakeLists.txt`` builds the :github_link:`upstream <docs/cmake>` example binary using only cmake, git,
and python. It demonstrates both how to integrate with :ref:`nnvg` and how to run Nunavut from source which avoids
managing Python environments for your build.

.. literalinclude :: CMakeLists.txt
    :language: cmake

:download:`CMakeLists.txt <CMakeLists.txt>`

====================================
CMake Presets Figure
====================================

This isn't required but the following presets file demonstrates how you can use
`CMake presets <https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html>`__ to easily switch between offline and
online builds when using `CMake's FetchContent <https://cmake.org/cmake/help/latest/module/FetchContent.html>`__ module.
See the :ref:`fetch_content_cmake_lists` figure for more context.

.. literalinclude :: CMakePresets.json
    :language: json

:download:`CMakePresets.json <CMakePresets.json>`

*************************************
NunavutConfig
*************************************

Use either `CMake's FetchContent <https://cmake.org/cmake/help/latest/module/FetchContent.html>`__
(see :ref:`fetch_content`) or `find_package(nunavut) <https://cmake.org/cmake/help/latest/command/find_package.html>`__,
to load the Nunavut cmake functions and variables documented here into your project.

.. cmake-module:: ../../NunavutConfig.cmake
