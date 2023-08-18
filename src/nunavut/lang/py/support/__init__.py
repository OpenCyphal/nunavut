#
# Copyright (C) 2023  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
"""
Contains supporting Python modules to distribute with generated types.
The contained support modules are not part of Nunavut, and one should not attempt to import them,
as they may depend on modules that are not available in the local environment.
"""
import pathlib
import typing
from nunavut._utilities import (
    ResourceType,
    empty_list_support_files,
    iter_package_resources,
)

__version__ = "1.0.0"
"""Version of the Python support module."""


def list_support_files(
    resource_type: ResourceType = ResourceType.ANY,
) -> typing.Generator[pathlib.Path, None, None]:
    """
    Get a list of Python support modules embedded in this package.
    """
    if resource_type not in (ResourceType.ANY, ResourceType.SERIALIZATION_SUPPORT):
        return empty_list_support_files()
    return iter_package_resources(__name__, ".j2")
