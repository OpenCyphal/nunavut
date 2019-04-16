#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
import json
from pathlib import Path

import pytest

from pydsdl import read_namespace
from pydsdlgen import create_type_map
from pydsdlgen.jinja import Generator


@pytest.fixture
def gen_paths():  # type: ignore
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


def test_anygen(gen_paths):  # type: ignore
    """
    Verifies that any dsdl type will resolve to an ``Any`` template.
    """
    type_map = read_namespace(str(gen_paths.dsdl_dir / Path("uavcan")), '')
    target_map = create_type_map(type_map, gen_paths.out_dir, '.h')
    generator = Generator(target_map, gen_paths.templates_dir)
    generator.generate_all(False)

    outfile = gen_paths.find_outfile_in_type_map("uavcan.time.SynchronizedTimestamp", target_map)

    assert (outfile is not None)

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob["full_name"] == "uavcan.time.SynchronizedTimestamp"
