#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# This software is distributed under the terms of the MIT License.
#
"""
Enable pytest integration of doctests in source and/or in documentation.
"""

import os
#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
import pathlib
import subprocess
import tempfile
import typing

import pytest
from sybil import Sybil
from sybil.parsers.codeblock import CodeBlockParser
from sybil.parsers.doctest import DocTestParser

from nunavut import Namespace

pytest_collect_file = Sybil(
    parsers=[
        DocTestParser(),
        CodeBlockParser(),
    ],
    pattern='*.py',
    excludes=['test/fixtues/*']
).pytest()


@pytest.fixture
def run_nnvg(request):  # type: ignore
    def _run_nnvg(gen_paths: typing.Any,
                  args: typing.List[str],
                  check_result: bool = True,
                  env: typing.Optional[typing.Dict[str, str]] = None) -> subprocess.CompletedProcess:
        """
        Helper to invoke nnvg for unit testing within the proper python coverage wrapper.
        """
        setup = gen_paths.root_dir / pathlib.Path('setup').with_suffix('.cfg')
        coverage_args = ['coverage', 'run', '--parallel-mode', '--rcfile={}'.format(str(setup)), '-m', 'nunavut']
        this_env = os.environ.copy()
        if env is not None:
            this_env.update(env)
        return subprocess.run(coverage_args + args,
                              check=check_result,
                              stdout=subprocess.PIPE,
                              env=this_env)
    return _run_nnvg


class GenTestPaths:
    """Helper to generate common paths used in our unit tests."""

    def __init__(self, test_file: str):
        test_file_path = pathlib.Path(test_file)
        self.test_name = test_file_path.parent.stem
        self.test_dir = test_file_path.parent
        self.root_dir = self.test_dir.resolve().parent.parent
        self.templates_dir = self.test_dir / pathlib.Path('templates')
        self.dsdl_dir = self.test_dir / pathlib.Path('dsdl')

        self._out_dir = None  # type: typing.Optional[tempfile.TemporaryDirectory]
        self._build_dir = None  # type: typing.Optional[pathlib.Path]
        self._dsdl_dir = None  # type: typing.Optional[pathlib.Path]
        print('Paths for test "{}" under dir {}'.format(self.test_name, self.test_dir))
        print('(root directory: {})'.format(self.root_dir))

    @property
    def out_dir(self) -> pathlib.Path:
        """
        The directory to place test output under for this test case.
        """
        if self._out_dir is None:
            self._out_dir = tempfile.TemporaryDirectory(dir=str(self.build_dir))
            print('GenTestPaths.out_dir is {} for test {}'.format(self._out_dir.name, self.test_name))
        return pathlib.Path(self._out_dir.name)

    @property
    def build_dir(self) -> pathlib.Path:
        if self._build_dir is None:
            self._build_dir = self._ensure_dir(self.root_dir / pathlib.Path('build'))
        return self._build_dir

    @staticmethod
    def find_outfile_in_namespace(typename: str, namespace: Namespace) -> typing.Optional[str]:
        for dsdl_type, outfile in namespace.get_all_types():
            if dsdl_type.full_name == typename:
                return str(outfile)
        return None

    @staticmethod
    def _ensure_dir(path_dir: pathlib.Path) -> pathlib.Path:
        try:
            path_dir.mkdir()
        except FileExistsError:
            pass
        if not path_dir.exists() or not path_dir.is_dir():
            raise RuntimeWarning('Test directory "{}" was not setup properly. Tests may fail.'.format(path_dir))
        return path_dir


@pytest.fixture(scope='function')
def gen_paths(request):  # type: ignore
    return GenTestPaths(request.module.__file__)
