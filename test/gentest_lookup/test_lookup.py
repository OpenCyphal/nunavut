#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

from pathlib import Path

import pytest
import json

from pydsdl import read_namespace
from pydsdlgen import create_type_map
from pydsdlgen.jinja import Generator


class a:
    pass


class b(a):
    pass


class c(a):
    pass


class d(b, c):
    pass


@pytest.fixture
def gen_paths():
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


def test_bfs_of_type_for_template(gen_paths) -> None:
    """ Verifies that our template to type lookup logic does a breadth-first search for a valid
    template when searching type names.
    """
    target_map = dict()
    generator = Generator(target_map, gen_paths.templates_dir)
    subject = d()
    template_file = generator.filter_pydsdl_type_to_template(subject)
    assert str(Path('c').with_suffix(Generator.TEMPLATE_SUFFIX)) == template_file
    assert generator.filter_pydsdl_type_to_template(subject) == template_file


def test_one_template(gen_paths) -> None:
    """ Verifies that we can use only a SeralizableType.j2 as the only template when
    no service types are present.
    """
    root_namespace = str(gen_paths.dsdl_dir / Path("uavcan"))
    serializable_types = read_namespace(root_namespace, [])
    target_map = create_type_map(serializable_types, gen_paths.out_dir, '.json')
    generator = Generator(target_map, gen_paths.templates_dir)
    generator.generate_all(False)

    outfile = gen_paths.find_outfile_in_type_map("uavcan.time.TimeSystem", target_map)
    assert (outfile is not None)

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob['uavcan.time.TimeSystem']['namespace'] == 'uavcan.time'
    assert json_blob['uavcan.time.TimeSystem']['is_serializable']


def test_get_templates(gen_paths) -> None:
    """
    Verifies the pydsdlgen.jinja.Generator.get_templates() method.
    """
    root_namespace = str(gen_paths.dsdl_dir / Path("uavcan"))
    serializable_types = read_namespace(root_namespace, [])
    target_map = create_type_map(serializable_types, gen_paths.out_dir, '.json')
    generator = Generator(target_map, gen_paths.templates_dir)

    templates = generator.get_templates()

    count = 0
    for template in templates:
        count += 1
    assert count > 0

    # Do it twice just to cover in-memory cache
    templates = generator.get_templates()

    count = 0
    for template in templates:
        count += 1
    assert count > 0
