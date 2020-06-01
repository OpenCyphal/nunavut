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
import pkg_resources

__version__ = "1.0.0"
"""Version of the c support headers."""


def list_support_files() -> typing.Generator[pathlib.Path, None, None]:
    """
    Get a list of C support headers embedded in this package.

    .. invisible-code-block: python

        from nunavut.lang.c.support import list_support_files
        import pathlib
        support_file_count = 0

    .. code-block:: python

        for path in list_support_files():
            support_file_count += 1
            assert path.parent.stem == 'support'
            assert path.suffix == '.h'

    .. invisible-code-block: python

        assert support_file_count > 0

    :return: A list of C support header resources.
    """
    for resource in pkg_resources.resource_listdir(__name__, '.'):
        if resource.endswith('.h'):
            yield pathlib.Path(pkg_resources.resource_filename(__name__, str(resource)))
