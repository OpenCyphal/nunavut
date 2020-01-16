#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
import json
from pathlib import Path

from pydsdl import read_namespace

from nunavut import build_namespace_tree
from nunavut.jinja import Generator
from nunavut.lang import LanguageContext


def test_instance_tests(gen_paths):  # type: ignore
    """
    Verifies that instance tests are added for pydsdl.SerializableType and
    all of its subclasses.
    """
    root_namespace_dir = gen_paths.dsdl_dir / Path("buncho")
    type_map = read_namespace(str(root_namespace_dir), '')
    language_context = LanguageContext('js')
    namespace = build_namespace_tree(type_map,
                                     root_namespace_dir,
                                     gen_paths.out_dir,
                                     language_context)
    generator = Generator(namespace, templates_dir=gen_paths.templates_dir)
    generator.generate_all(False)

    outfile = gen_paths.find_outfile_in_namespace("buncho.serializables", namespace)

    assert (outfile is not None)

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob["this_field_is_an_int32"]["isSerializableType"] is True
    assert json_blob["this_field_is_an_int32"]["isIntegerType"] is True
    assert json_blob["this_field_is_an_int32"]["isFloatType"] is False
    assert json_blob["this_field_is_an_int32"]["isIntegerType_field"] is True

    assert json_blob["this_field_is_a_float"]["isSerializableType"] is True
    assert json_blob["this_field_is_a_float"]["isIntegerType"] is False
    assert json_blob["this_field_is_a_float"]["isIntegerType_field"] is False
    assert json_blob["this_field_is_a_float"]["isFloatType"] is True
