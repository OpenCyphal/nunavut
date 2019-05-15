#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
import pathlib
import subprocess
import typing
import pydsdl
from nunavut import Namespace


class GenTestPaths:
    """Helper to generate common paths used in our unit tests."""

    def __init__(self, test_file: str):
        test_file_path = pathlib.Path(test_file)
        self.test_name = test_file_path.parent.stem
        self.test_dir = test_file_path.parent
        self.root_dir = self.test_dir.resolve().parent.parent

        self._build_dir = None  # type: typing.Optional[pathlib.Path]
        self._out_dir = None  # type: typing.Optional[pathlib.Path]
        self._templates_dir = None  # type: typing.Optional[pathlib.Path]
        self._dsdl_dir = None  # type: typing.Optional[pathlib.Path]
        print('Paths for test "{}" under dir {}'.format(self.test_name, self.test_dir))
        print('(root directory: {})'.format(self.root_dir))

    @property
    def build_dir(self) -> pathlib.Path:
        if self._build_dir is None:
            self._build_dir = self._ensure_dir(self.root_dir / pathlib.Path('build'))
        return self._build_dir

    @property
    def out_dir(self) -> pathlib.Path:
        """
        The directory to place test output under for this test case.
        """
        if self._out_dir is None:
            test_output_base = self._ensure_dir(self.build_dir / pathlib.Path('test_output'))
            self._out_dir = self._ensure_dir(self.build_dir / test_output_base / pathlib.Path(self.test_name))
        return self._out_dir

    @property
    def templates_dir(self) -> pathlib.Path:
        if self._templates_dir is None:
            self._templates_dir = self._ensure_dir(self.test_dir / pathlib.Path('templates'))
        return self._templates_dir

    @property
    def dsdl_dir(self) -> pathlib.Path:
        if self._dsdl_dir is None:
            self._dsdl_dir = self._ensure_dir(self.test_dir / pathlib.Path('dsdl'))
        return self._dsdl_dir

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


class DummyType(pydsdl.Any):
    """Fake dsdl 'any' type for testing."""

    def __init__(self, namespace: str = 'uavcan', name: str = 'Dummy'):
        self._full_name = '{}.{}'.format(namespace, name)

    # +-----------------------------------------------------------------------+
    # | DUCK TYPEING: CompositeType
    # +-----------------------------------------------------------------------+
    @property
    def full_name(self) -> str:
        return self._full_name

    # +-----------------------------------------------------------------------+
    # | PYTHON DATA MODEL
    # +-----------------------------------------------------------------------+

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DummyType):
            return self._full_name == other._full_name
        else:
            return False

    def __str__(self) -> str:
        return self.full_name

    def __hash__(self) -> int:
        return hash(self._full_name)


def run_nnvg(gen_paths: GenTestPaths, args: typing.List[str], check_result: bool = True) -> None:
    """
    Helper to invoke nnvg for unit testing within the proper python coverage wrapper.
    """
    setup = gen_paths.root_dir / pathlib.Path('setup').with_suffix('.cfg')
    coverage_args = ['coverage', 'run', '--parallel-mode', '--rcfile={}'.format(str(setup))]
    nnvg_script = gen_paths.root_dir / pathlib.Path('src') / pathlib.Path('nnvg')
    subprocess.run(coverage_args + [str(nnvg_script)] + args, check=check_result)
