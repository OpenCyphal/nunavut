#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
from typing import List, Dict, NamedTuple, NewType
import os
import errno
from pathlib import Path, PurePath
from pydsdl.data_type import CompoundType
from pydsdl import parse_namespace

__all__ = ["generators"]

# +---------------------------------------------------------------------------+


def _build_paths(paths: List[str], resolve_paths: bool, required: bool) -> List[str]:
    """
    Helper method to build pathlib objects from input strings and handle
    various path flags.

    paths           -- A list of path-like strings.
    resolve_paths   -- If True then each Path object will be resolved. For most platforms
                       this yields absolute paths.
    required        -- If True and if the Path constructed ends up pointing to a non-existent
                       file or folder then FileNotFoundError will be raised.

    raises FileNotFoundError if required is True and a path to a non-existent resource is found.
    """
    result: List[str] = []
    for path_string in paths:
        path = Path(path_string)
        if resolve_paths:
            path = path.resolve()

        if required and not path.exists:
            raise FileNotFoundError("{} did not exist.".format(path_string))

        result.append(str(path))

    return result


def parse_all(root_namespaces: List[str], extra_includes: List[str], output_dir: str, extension: str, resolve_paths: bool = True) -> Dict[CompoundType, Path]:
    """
    Parses all root namespaces.
    Raises FileNotFoundError if any of the root namespace folders were not found.
    """
    if not extension.startswith('.'):
        raise ValueError("extension must begin with .")

    base_path = PurePath(output_dir)

    root_namespace_paths = _build_paths(root_namespaces, resolve_paths, True)

    extra_include_paths = _build_paths(extra_includes, resolve_paths, False)

    type_to_output_map = dict()

    for root_namespace_path in root_namespace_paths:
        types = parse_namespace(root_namespace_path, extra_include_paths)
        if len(types) == 0:
            raise RuntimeError(
                "Root namespace {} yielded no types.".format(root_namespace_path))
        for type in types:
            output_path = Path(
                base_path / PurePath(*type.name_components).with_suffix(extension))
            if resolve_paths:
                output_path = output_path.resolve()
            type_to_output_map[type] = output_path

    return type_to_output_map

# +---------------------------------------------------------------------------+
import pytest
import unittest.mock

def _unittest_parse_all() -> None:
    """
    Expect a ValueError if the extension argument is malformed.
    """
    with pytest.raises(ValueError):
        parse_all([], [], "", "badext")

def _unittest_parse_all_no_types() -> None:
    """
    Expect a RuntimeError if valid arguments yield no types.
    """
    with pytest.raises(Exception):
        # use CWD to provide a valid directory with
        # no .uavcan files.
        parse_all([os.getcwd()], [], "", ".ext")
