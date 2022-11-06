#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2020  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
"""
Contains supporting C headers to distribute with generated types.
"""
import pathlib
import typing

from nunavut._utilities import ResourceType, empty_list_support_files, iter_package_resources

__version__ = "1.0.0"
"""Version of the c support headers."""


def list_support_files(resource_type: ResourceType = ResourceType.ANY) -> typing.Generator[pathlib.Path, None, None]:
    """
    Get a list of C support headers embedded in this package.
    :param resource_type: A type of support file to list.

    .. invisible-code-block: python

        from nunavut.lang.c.support import list_support_files
        import pathlib
        support_file_count = 0

    .. code-block:: python

        for path in list_support_files():
            support_file_count += 1
            assert path.parent.stem == 'support'
            assert (path.suffix == '.h' or path.suffix == '.j2')

    .. invisible-code-block: python

        assert support_file_count > 0

    :return: A list of C support header resources.
    """
    # The c support only has serialization support resources
    if resource_type not in (ResourceType.ANY, ResourceType.SERIALIZATION_SUPPORT):
        return empty_list_support_files()
    else:
        return iter_package_resources(__name__, ".h", ".j2")
