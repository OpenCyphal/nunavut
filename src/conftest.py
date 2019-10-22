#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# This software is distributed under the terms of the MIT License.
#
"""
Enable pytest integration of doctests in source and/or in documentation.
"""
import typing
from doctest import ELLIPSIS
from fnmatch import fnmatch

from sybil import Sybil
from sybil.integration.pytest import SybilFile
from sybil.parsers.codeblock import CodeBlockParser
from sybil.parsers.doctest import DocTestParser


def _pytest_integration_that_actually_works() -> typing.Callable:
    """
    Sybil matching is pretty broken. We'll have to help it out here. The problem is that
    exclude patterns passed into the Sybil object are matched against file name stems such that
    files cannot be excluded by path.
    """

    _excludes = [
        '**/markupsafe/*',
        '**/jinja2/*',
    ]

    _sy = Sybil(
        parsers=[
            DocTestParser(optionflags=ELLIPSIS),
            CodeBlockParser(),
        ]
    )

    def pytest_collect_file(parent: str, path: str) -> typing.Optional[SybilFile]:
        if fnmatch(path, '**/nunavut/**/*.py') and not any(fnmatch(path, pattern) for pattern in _excludes):
            return SybilFile(path, parent, _sy)
        else:
            return None

    return pytest_collect_file


pytest_collect_file = _pytest_integration_that_actually_works()
