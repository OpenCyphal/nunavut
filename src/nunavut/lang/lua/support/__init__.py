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
    if resource_type not in (ResourceType.ANY, ResourceType.SERIALIZATION_SUPPORT):
        return empty_list_support_files()
    return iter_package_resources(__name__, ".j2")
