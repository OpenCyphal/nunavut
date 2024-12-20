#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#

import json
from pathlib import Path

import pytest
from pydsdl import FrontendError, read_namespace

from nunavut._namespace import build_namespace_tree
from nunavut.jinja import DSDLCodeGenerator
from nunavut.lang import LanguageContextBuilder


def test_two_root_error(gen_paths):  # type: ignore
    """ Verifies that we are trying to use a type outside of the root.
    """
    root_namespace = str(gen_paths.dsdl_dir / Path("scotec"))
    with pytest.raises(FrontendError):
        read_namespace(root_namespace, [], allow_unregulated_fixed_port_id=True)


def test_three_roots(gen_paths):  # type: ignore
    """ Generates a type that uses another type from a different root namespace.
    """

    root_namespace = str(gen_paths.dsdl_dir / Path("scotec"))
    includes = [str(gen_paths.dsdl_dir / Path("huckco")),
                str(gen_paths.dsdl_dir / Path("esmeinc"))]
    compound_types = read_namespace(root_namespace, includes, allow_unregulated_fixed_port_id=True)
    language_context = LanguageContextBuilder(include_experimental_languages=True).set_target_language("js").create()
    namespace = build_namespace_tree(compound_types,
                                     root_namespace,
                                     gen_paths.out_dir,
                                     language_context)
    generator = DSDLCodeGenerator(namespace, templates_dir=gen_paths.templates_dir)
    generator.generate_all(False)

    # Now read back in and verify
    outfile = gen_paths.find_outfile_in_namespace("scotec.FatherType", namespace)

    assert outfile is not None

    with open(str(outfile), 'r', encoding="utf-8") as json_file:
        json_blob = json.load(json_file)

    assert len(json_blob) > 0
    assert len(json_blob['scotec.FatherType']['attributes']) == 2
    assert json_blob['scotec.FatherType']['attributes'][0]['type'] == 'huckco.SonType.0.1'
    assert json_blob['scotec.FatherType']['attributes'][1]['type'] == 'esmeinc.DaughterType.0.1'


def test_three_roots_using_nnvg(gen_paths, run_nnvg):  # type: ignore
    nnvg_cmd = ['--templates', str(gen_paths.templates_dir),
                '-I', str(gen_paths.dsdl_dir / Path("huckco")),
                '-I', str(gen_paths.dsdl_dir / Path("esmeinc")),
                '-O', str(gen_paths.out_dir),
                '-e', str('.json'),
                "-Xlang",
                str(gen_paths.dsdl_dir / Path("scotec"))]

    run_nnvg(gen_paths, nnvg_cmd)


def test_same_type_different_paths(gen_paths, run_nnvg_main):  # type: ignore

    expected_output = [gen_paths.out_dir / Path("esmeinc") / Path("DaughterType_0_1").with_suffix(".json")]

    nnvg_args = ['--templates', str(gen_paths.templates_dir),
                '-I', (gen_paths.dsdl_dir / Path("esmeinc")).as_posix(),
                '-I', (gen_paths.dsdl_dir / Path("family") / Path("esmeinc")).as_posix(),
                '-O', (gen_paths.out_dir).as_posix(),
                "--list-outputs",
                "-l", "js",
                "-Xlang",
                "--omit-serialization-support",
                '-e', str('.json'),
                (Path("esmeinc") / Path("DaughterType.0.1.dsdl")).as_posix()]

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == completed_wo_empty
