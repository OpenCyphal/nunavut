#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
from pathlib import Path

import pytest

from pydsdlgen import generate_target_paths, parse_all
from pydsdlgen.jinja import Generator


@pytest.fixture
def gen_paths():
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


def test_realgen(gen_paths) -> None:
    """
    Sanity test that runs through the entire public, regulated set of
    UAVCAN types and generates some basic C code.
    """
    parser_result = parse_all([gen_paths.dsdl_dir / Path("uavcan")], '')
    target_map = generate_target_paths(parser_result, gen_paths.out_dir, '.h')
    generator = Generator(gen_paths.out_dir, target_map, gen_paths.templates_dir)
    generator.generate_all(False)
