#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Empty python package to ensure the support generator doesn't explode.
"""
import pathlib
import typing

from nunavut._utilities import ResourceType, empty_list_support_files

__version__ = "1.0.0"
"""Version of the html support headers."""


def list_support_files(resource_type: int = ResourceType.ANY.value) -> typing.Generator[pathlib.Path, None, None]:
    """
    Get a list of HTML support files embedded in this package.
    :param resource_type: A type of support file to list.
    """
    # pylint: disable=unused-argument
    return empty_list_support_files()  # pragma: no cover
