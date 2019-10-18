#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
import json
from pathlib import Path

import pytest

from pydsdl import read_namespace
from nunavut import build_namespace_tree
from nunavut.lang import LanguageContext
from nunavut.jinja import Generator


def test_TestType_0_1(gen_paths):  # type: ignore
    """ Generates a JSON blob and then reads it back in.

    This test uses an extremely simple DSDL type to generate JSON then
    reads this JSON back in and parses it using Python's built-in parser.
    """

    root_namespace_dir = gen_paths.dsdl_dir / Path("uavcan")
    root_namespace = str(root_namespace_dir)
    language_context = LanguageContext(extension='.json')
    namespace = build_namespace_tree(read_namespace(root_namespace, ''),
                                     root_namespace_dir,
                                     gen_paths.out_dir,
                                     language_context)
    generator = Generator(namespace, False, language_context, gen_paths.templates_dir)
    generator.generate_all(False)

    # Now read back in and verify
    outfile = gen_paths.find_outfile_in_namespace("uavcan.test.TestType", namespace)

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
    assert len(test_type["attributes"]) == 2

    test_attr_0 = test_type["attributes"][0]
    assert test_attr_0["name"] == "data"
    assert test_attr_0["type"] == "uint56"
    assert test_attr_0["bit_length"] == 56
    assert test_attr_0["cast_mode"] == "TRUNCATED"

    test_attr_1 = test_type["attributes"][1]
    assert test_attr_1["name"] == "const_bool_example"
    assert test_attr_1["type"] == "uint1"
    assert test_attr_1["bit_length"] == 1
    assert test_attr_1["cast_mode"] == "SATURATED"
