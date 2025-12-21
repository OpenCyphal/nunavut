#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2020  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
"""
Empty python package to ensure the support generator doesn't explode.
"""
import pathlib
import typing
from nunavut._utilities import (
    ResourceType,
    empty_list_support_files,
    iter_package_resources,
)

__version__ = "1.0.0"
"""Version of the LUA dissectors."""


def list_support_files(
    resource_type: ResourceType = ResourceType.ANY,
) -> typing.Generator[pathlib.Path, None, None]:
    """
    Get a list of Lua support modules embedded in this package.
    """
    if resource_type is ResourceType.SERIALIZATION_SUPPORT:
        # Return serialization support files (nunavut_support.j2)
        for path in iter_package_resources(__name__, ".j2"):
            if path.name != "cyphal.j2":
                yield path
    elif resource_type is ResourceType.TYPE_SUPPORT:
        # Return cyphal.j2 which aggregates all registered types
        for path in iter_package_resources(__name__, ".j2"):
            if path.name == "cyphal.j2":
                yield path
    elif resource_type is ResourceType.ANY:
        # Return all support files
        return iter_package_resources(__name__, ".j2")
    else:
        return empty_list_support_files()
