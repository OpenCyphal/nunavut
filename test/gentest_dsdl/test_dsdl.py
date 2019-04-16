#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
from pathlib import Path

import pytest

from pydsdlgen import create_type_map
from pydsdlgen.jinja import Generator
from pydsdl import read_namespace


@pytest.fixture
def gen_paths():  # type: ignore
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


def test_realgen(gen_paths):  # type: ignore
    """
    Sanity test that runs through the entire public, regulated set of
    UAVCAN types and generates some basic C code.
    """
    type_map = read_namespace(str(gen_paths.dsdl_dir / Path("uavcan")), '')
    target_map = create_type_map(type_map, gen_paths.out_dir, '.h')
    generator = Generator(target_map, gen_paths.templates_dir)
    generator.generate_all(False)
