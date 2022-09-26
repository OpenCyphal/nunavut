#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2020  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
Contains supporting C++ headers to distribute with generated types.
"""

import pathlib
import typing

from nunavut._utilities import ResourceType, empty_list_support_files, iter_package_resources

__version__ = "1.0.0"
"""Version of the c++ support headers."""


def list_support_files(resource_type: ResourceType = ResourceType.ANY) -> typing.Generator[pathlib.Path, None, None]:
    """
    Get a list of C++ support headers embedded in this package.

    .. invisible-code-block: python

        from nunavut.lang.cpp.support import list_support_files
        import pathlib
        support_file_count = 0

    .. code-block:: python

        for path in list_support_files():
            support_file_count += 1
            assert path.parent.stem == 'support'
            assert (path.suffix == '.hpp' or path.suffix == '.j2')

    .. invisible-code-block: python

        assert support_file_count > 0

        support_file_count = 0
        for path in list_support_files(ResourceType.CONFIGURATION):
            support_file_count +=1
        assert support_file_count == 0

        support_file_count = 0
        for path in list_support_files(ResourceType.SERIALIZATION_SUPPORT):
            support_file_count +=1
        assert support_file_count > 0

        support_file_count = 0
        for path in list_support_files(ResourceType.TYPE_SUPPORT):
            support_file_count +=1
        assert support_file_count > 0

    :return: A list of C++ support header resources.
    """

    # for now we say all .hpp resources are type support and all .j2 are serialization support.
    # We are allowed to change this logic anyway we want without breaking changes.
    if resource_type is ResourceType.SERIALIZATION_SUPPORT:
        return iter_package_resources(__name__, ".j2")
    if resource_type is ResourceType.TYPE_SUPPORT:
        return iter_package_resources(__name__, ".hpp")
    if resource_type is ResourceType.ANY:
        return iter_package_resources(__name__, ".hpp", ".j2")
    else:
        return empty_list_support_files()
