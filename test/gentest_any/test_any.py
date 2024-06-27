#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Template resolution by type tests.
"""
import json
from pathlib import Path

from nunavut import LanguageContextBuilder, Namespace
from nunavut.jinja import DSDLCodeGenerator


def test_anygen_read_namespace(gen_paths):  # type: ignore
    """
    Verifies that any dsdl type will resolve to an ``Any`` template.
    """
    root_namespace_dir = gen_paths.dsdl_dir / Path("uavcan")
    language_context = (
        LanguageContextBuilder().set_target_language_configuration_override("extension", ".json").create()
    )
    index = Namespace.read_namespace(gen_paths.out_dir, language_context, root_namespace_dir)
    generator = DSDLCodeGenerator(
        index, templates_dir=gen_paths.templates_dir, index_file=["index", "xml/default_template.xml"]
    )
    generator.generate_all(False)

    outfile = gen_paths.find_outfile_in_namespace("uavcan.time.SynchronizedTimestamp", index)

    assert outfile is not None

    with open(str(outfile), "r", encoding="utf-8") as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob["full_name"] == "uavcan.time.SynchronizedTimestamp"
    assert (gen_paths.out_dir / Path("index.json")).exists()
    assert (gen_paths.out_dir / Path("xml", "default_template.xml")).exists()
