#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
from pathlib import Path
from typing import Dict
from pydsdl.serializable import CompositeType


class GenTestPaths:
    """Helper to generate common paths used in our unit tests."""

    def __init__(self, test_file: str):
        test_file_path = Path(test_file)
        self.test_name = test_file_path.parent.stem
        self.test_dir = test_file_path.parent
        self.root_dir = self.test_dir.resolve().parent.parent
        self._build_dir = None
        self._test_dir = None
        self._out_dir = None
        self._templates_dir = None
        self._dsdl_dir = None
        print('Paths for test "{}" under dir {}'.format(self.test_name, self.test_dir))
        print('(root directory: {})'.format(self.root_dir))

    @property
    def build_dir(self) -> Path:
        if self._build_dir is None:
            self._build_dir = self._ensure_dir(self.root_dir / Path('build'))
        return self._build_dir

    @property
    def test_output(self) -> Path:
        if self._test_dir is None:
            self._test_dir = self._ensure_dir(self.build_dir / Path('test_output'))
        return self._test_dir

    @property
    def out_dir(self) -> Path:
        if self._out_dir is None:
            self._out_dir = self._ensure_dir(self.build_dir / self.test_output / Path(self.test_name))
        return self._out_dir

    @property
    def templates_dir(self) -> Path:
        if self._templates_dir is None:
            self._templates_dir = self._ensure_dir(self.test_dir / Path('templates'))
        return self._templates_dir

    @property
    def dsdl_dir(self) -> Path:
        if self._dsdl_dir is None:
            self._dsdl_dir = self._ensure_dir(self.test_dir / Path('dsdl'))
        return self._dsdl_dir

    @staticmethod
    def find_outfile_in_type_map(typename: str, type_map: Dict[CompositeType, str]) -> str:
        for dsdl_type, outfile in type_map.items():
            if dsdl_type.full_name == typename:
                return outfile
        return None

    @staticmethod
    def _ensure_dir(path_dir: Path) -> Path:
        try:
            path_dir.mkdir()
        except FileExistsError:
            pass
        if not path_dir.exists() or not path_dir.is_dir():
            raise RuntimeWarning('Test directory "{}" was not setup properly. Tests may fail.'.format(path_dir))
        return path_dir
