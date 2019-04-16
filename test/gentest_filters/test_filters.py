#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

import pytest
import json

from pydsdl import read_namespace
from pydsdlgen import build_namespace_tree
from pydsdlgen.jinja import Generator
from pydsdlgen.jinja.jinja2.exceptions import TemplateAssertionError

from pathlib import Path


@pytest.fixture
def gen_paths():  # type: ignore
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


def test_template_assert(gen_paths):  # type: ignore
    """
    Tests our template assertion extension.
    """
    root_path = str(gen_paths.dsdl_dir / Path("uavcan"))
    compound_types = read_namespace(root_path, [])
    namespace = build_namespace_tree(compound_types,
                                     root_path,
                                     gen_paths.out_dir,
                                     '.json',
                                     '_')
    template_path = gen_paths.templates_dir / Path('assert')
    generator = Generator(namespace, False, template_path)
    try:
        generator.generate_all()
        assert False
    except TemplateAssertionError as e:
        e.filename == str(template_path / "Any.j2")
        e.filename == 2
        e.message == 'Template assertion failed.'


def test_type_to_include(gen_paths):  # type: ignore
    """Test the type_to_include filter."""
    root_path = str(gen_paths.dsdl_dir / Path("uavcan"))
    compound_types = read_namespace(root_path, [])
    namespace = build_namespace_tree(compound_types,
                                     root_path,
                                     gen_paths.out_dir,
                                     '.json',
                                     '_')
    template_path = gen_paths.templates_dir / Path('type_to_include')
    generator = Generator(namespace, False, template_path)
    generator.generate_all()
    outfile = gen_paths.find_outfile_in_namespace("uavcan.time.SynchronizedTimestamp", namespace)

    assert (outfile is not None)

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob['include'] == "uavcan/time/SynchronizedTimestamp_1_0.json"
