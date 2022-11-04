#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
import json
from pathlib import Path

from pydsdl import read_namespace
from nunavut import build_namespace_tree
from nunavut.jinja import DSDLCodeGenerator
from nunavut.lang import LanguageContextBuilder

import pytest


@pytest.mark.parametrize("lang_key", [("cpp")])
def test_anygen(gen_paths, lang_key):  # type: ignore
    """
    Verifies that any dsdl type will resolve to an ``Any`` template.
    """
    root_namespace_dir = gen_paths.dsdl_dir / Path("uavcan")
    type_map = read_namespace(str(root_namespace_dir), [])
    language_context = (
        LanguageContextBuilder().set_target_language_configuration_override("extension", ".json").create()
    )
    namespace = build_namespace_tree(type_map, root_namespace_dir, str(gen_paths.out_dir), language_context)
    generator = DSDLCodeGenerator(namespace, templates_dir=gen_paths.templates_dir)
    generator.generate_all(False)

    outfile = gen_paths.find_outfile_in_namespace("uavcan.time.SynchronizedTimestamp", namespace)

    assert outfile is not None

    with open(str(outfile), "r") as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob["full_name"] == "uavcan.time.SynchronizedTimestamp"
