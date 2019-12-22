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

__version__ = "1.0.0"
"""Version of the c++ support headers."""


def copy_support_headers(target_namespace: typing.List[str],
                         copy_to_folder: pathlib.Path,
                         allow_overwrite: bool) -> typing.List[pathlib.Path]:
    """
    Copy C++ support headers out of the Nunavut package and into the folder specified.

    .. invisible-code-block: python

        from nunavut.lang.cpp.support import copy_support_headers
        import pathlib
        import pytest

    .. code-block:: python

        # copied with contain headers like 'test_out_dir/nunavut/support/serialization.hpp'
        copied = copy_support_headers(['nunavut', 'support'], gen_paths.out_dir, True)

        # To prevent overwrites set the allow_overwrite parameter to False
        with pytest.raises(PermissionError):
            copied = copy_support_headers(['nunavut', 'support'], gen_paths.out_dir, False)

    .. invisible-code-block: python

        assert len(copied) > 0
        for header in copied:
            assert(header.is_file)

    :param pathlib.Path copy_to_folder: The folder to copy the headers into.
    :param bool allow_overwrite: If True then this method will copy the support files over
        existing files of the same name.
    :return: A list of paths to the copied headers.
    :raises: PermissionError if :attr:`allow_overwrite` is False and the file exists.
    """
    import pkg_resources
    import shutil
    copied = []  # type: typing.List[pathlib.Path]
    resources = list_support_headers([])
    try:
        copy_to_folder.mkdir()
    except FileExistsError:
        pass
    namespaced_path = copy_to_folder
    for namespace_part in target_namespace:
        namespaced_path = namespaced_path / pathlib.Path(namespace_part)
        try:
            namespaced_path.mkdir()
        except FileExistsError:
            pass
    for resource in resources:
        target = namespaced_path / pathlib.Path(resource)
        if not allow_overwrite and target.exists():
            raise PermissionError('{} exists. Refusing to overwrite.'.format(str(target)))
        shutil.copy(pkg_resources.resource_filename(__name__, str(resource)), str(namespaced_path))
        copied.append(target)
    return copied


def list_support_headers(target_namespace: typing.List[str]) -> typing.List[pathlib.Path]:
    """
    Get a list of C++ support headers embedded in this package.

    .. invisible-code-block: python

        from nunavut.lang.cpp.support import list_support_headers
        import pathlib

    .. code-block:: python

        paths = list_support_headers([])
        for path in paths:
            assert pathlib.Path('') == path.parent

        paths = list_support_headers(['nunavut'])
        for path in paths:
            assert pathlib.Path('nunavut') == path.parent

        paths = list_support_headers(['nunavut', 'support'])
        for path in paths:
            assert pathlib.Path('nunavut') / pathlib.Path('support') == path.parent

    :return: A list of C++ support header resources.
    """
    import pkg_resources
    namespace_path = pathlib.Path('')
    for namespace_part in target_namespace:
        namespace_path = namespace_path / pathlib.Path(namespace_part)
    headers = []  # type: typing.List[pathlib.Path]
    resources = [r for r in pkg_resources.resource_listdir(__name__, '.') if r.endswith('.hpp')]
    for resource in resources:
        headers.append(namespace_path / pathlib.Path(resource))
    return headers
