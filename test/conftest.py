#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# This software is distributed under the terms of the MIT License.
#
"""
Fixtures for our tests.
"""

import os
import pathlib
import subprocess
import tempfile
import textwrap
import typing

import pytest

from nunavut import Namespace


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

    def __init__(self, test_file: str, keep_temporaries: bool, param_index: int):
        test_file_path = pathlib.Path(test_file)
        self.test_name = '{}_{}'.format(test_file_path.parent.stem, param_index)
        self.test_dir = test_file_path.parent
        self.root_dir = self.test_dir.resolve().parent.parent
        self.templates_dir = self.test_dir / pathlib.Path('templates')
        self.dsdl_dir = self.test_dir / pathlib.Path('dsdl')

        self._keep_temp = keep_temporaries
        self._out_dir = None  # type: typing.Optional[typing.Any]
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
            if self._keep_temp:
                self._out_dir = lambda: None
                test_output_dir = self._ensure_dir(self.build_dir / pathlib.Path(self.test_name))
                setattr(self._out_dir, 'name', str(test_output_dir))
            else:
                self._out_dir = tempfile.TemporaryDirectory(dir=str(self.build_dir))
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
    return GenTestPaths(request.module.__file__, request.config.option.keep_generated, request.param_index)


def pytest_addoption(parser):  # type: ignore
    parser.addoption("--keep-generated", action="store_true", help=textwrap.dedent('''
        If set then the temporary directory used to generate files for each test will be left after
        the test has completed. Normally this directory is temporary and therefore cleaned up automatically.

        :: WARNING ::
        This will leave orphaned files on disk. They won't be big but there will be a lot of them.

        :: WARNING ::
        Do not run tests in parallel when using this option.
    '''))
