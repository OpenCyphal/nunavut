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
    resource_type: int = ResourceType.ANY.value,
) -> typing.Generator[pathlib.Path, None, None]:
    """
    Get a list of Python support modules embedded in this package.
    """
    if resource_type & ResourceType.SERIALIZATION_SUPPORT.value:
        return iter_package_resources(__name__, ".j2")
    return empty_list_support_files()  # pragma: no cover
