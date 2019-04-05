#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

from pathlib import Path

import pytest
import json

from pydsdl import read_namespace, FrontendError
from pydsdlgen import create_type_map
from pydsdlgen.jinja import Generator

import subprocess


@pytest.fixture
def gen_paths():
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


def test_two_root_error(gen_paths) -> None:
    """ Verifies that we are trying to use a type outside of the root.
    """
    root_namespace = str(gen_paths.dsdl_dir / Path("scotec"))
    with pytest.raises(FrontendError):
        read_namespace(root_namespace, [], allow_unregulated_fixed_port_id=True)


def test_three_roots(gen_paths) -> None:
    """ Generates a type that uses another type from a different root namespace.
    """

    root_namespace = str(gen_paths.dsdl_dir / Path("scotec"))
    includes = [str(gen_paths.dsdl_dir / Path("huckco")),
                str(gen_paths.dsdl_dir / Path("esmeinc"))]
    compound_types = read_namespace(root_namespace, includes, allow_unregulated_fixed_port_id=True)
    target_map = create_type_map(compound_types, gen_paths.out_dir, '.json')
    generator = Generator(target_map, gen_paths.templates_dir)
    generator.generate_all(False)

    # Now read back in and verify
    outfile = gen_paths.find_outfile_in_type_map("scotec.FatherType", target_map)

    assert (outfile is not None)

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert len(json_blob) > 0
    assert len(json_blob['scotec.FatherType']['fields']) == 2
    assert json_blob['scotec.FatherType']['fields'][0]['type'] == 'huckco.SonType.0.1'
    assert json_blob['scotec.FatherType']['fields'][1]['type'] == 'esmeinc.DaughterType.0.1'


def test_three_roots_using_dsdlgenj(gen_paths) -> None:
    dsdlgen_cmd = ['dsdlgenj',
                   '--templates', str(gen_paths.templates_dir),
                   '-I', str(gen_paths.dsdl_dir / Path("huckco")),
                   '-I', str(gen_paths.dsdl_dir / Path("esmeinc")),
                   '-O', str(gen_paths.out_dir),
                   str(gen_paths.dsdl_dir / Path("scotec"))]

    subprocess.run(dsdlgen_cmd, check=True)
