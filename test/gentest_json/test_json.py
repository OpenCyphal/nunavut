#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
import json
from pathlib import Path

import pytest

from pydsdlgen import generate_target_paths, parse_all
from pydsdlgen.jinja import Generator


@pytest.fixture
def gen_paths():
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


def test_TestType_0_1(gen_paths) -> None:
    """ Generates a JSON blob and then reads it back in.

    This test uses an extremely simple DSDL type to generate JSON then
    reads this JSON back in and parses it using Python's built-in parser.
    """

    root_namespaces = [gen_paths.dsdl_dir / Path("uavcan")]
    target_map = generate_target_paths(parse_all(root_namespaces, ''), gen_paths.out_dir, '.json')
    generator = Generator(gen_paths.out_dir, target_map, gen_paths.templates_dir)
    generator.generate_all(False)

    # Now read back in and verify
    outfile = gen_paths.find_outfile_in_target_paths("uavcan.test.TestType", target_map)

    assert (outfile is not None)

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert len(json_blob) == 1

    uavcan_namespace = json_blob[0]
    assert uavcan_namespace["type"] == "namespace"
    assert uavcan_namespace["name"] == "uavcan.test"
    assert len(uavcan_namespace["contents"]) == 1

    test_type = uavcan_namespace["contents"][0]
    assert test_type["name"] == "TestType"
    assert test_type["version"]["major"] == 0
    assert test_type["version"]["minor"] == 1
    assert len(test_type["fields"]) == 1

    test_field = test_type["fields"][0]
    assert test_field["name"] == "data"
    assert test_field["type"] == "uint56"
    assert test_field["bit_length"] == 56
    assert test_field["cast_mode"] == "TRUNCATED"
