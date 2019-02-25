#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
from pathlib import Path
from typing import Dict
from pydsdl.data_type import CompoundType


class GenTestPaths:
    """Helper to generate common paths used in our unit tests."""

    def __init__(self, test_file: str):
        test_file_path: Path = Path(test_file)
        self.test_name = test_file_path.parent.stem
        self.test_dir = test_file_path.parent
        self.root_dir = Path(__file__).resolve().parent.parent.parent
        self.out_dir = self.root_dir / Path("build") / Path("test_output") / Path(self.test_name)
        self.templates_dir = self.test_dir / Path("templates")
        self.dsdl_dir = self.test_dir / Path("dsdl")

    def find_outfile_in_target_paths(self, typename: str, target_paths: Dict[CompoundType, str]) -> str:
        for dsdl_type, outfile in target_paths.items():
            if dsdl_type.full_name == typename:
                return outfile
        return None
