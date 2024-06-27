#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#

from pathlib import Path

import json

from nunavut import Namespace
from nunavut.lang import LanguageContextBuilder
from nunavut.jinja import DSDLCodeGenerator
from nunavut._utilities import TEMPLATE_SUFFIX


class a:
    pass


class b(a):
    pass


class c(a):
    pass


class d(b, c):
    pass


def test_bfs_of_type_for_template(gen_paths):  # type: ignore
    """
    Verifies that our template to type lookup logic does a breadth-first search for a valid
    template when searching type names.
    """
    language_context = LanguageContextBuilder().set_target_language("c").create()
    empty_namespace = Namespace("", gen_paths.out_dir, language_context)
    generator = DSDLCodeGenerator(empty_namespace, templates_dir=gen_paths.templates_dir)
    subject = d()
    template_file = generator.filter_type_to_template(subject)
    assert str(Path("c").with_suffix(TEMPLATE_SUFFIX)) == template_file
    assert generator.filter_type_to_template(subject) == template_file


def test_one_template(gen_paths):  # type: ignore
    """
    Verifies that we can use only a SeralizableType.j2 as the only template when
    no service types are present.
    """
    root_namespace_dir = gen_paths.dsdl_dir / Path("uavcan")
    language_context = LanguageContextBuilder().set_target_language("c").create()
    namespace = Namespace.read_namespace(gen_paths.out_dir, language_context, root_namespace_dir, [])
    generator = DSDLCodeGenerator(namespace, templates_dir=gen_paths.templates_dir)
    generator.generate_all(False)

    outfile = gen_paths.find_outfile_in_namespace("uavcan.time.TimeSystem", namespace)
    assert outfile is not None

    with Path(outfile).open("r", encoding="utf-8") as json_file:
        json_blob = json.load(json_file)

    assert json_blob["uavcan.time.TimeSystem"]["namespace"] == "uavcan.time"
    assert json_blob["uavcan.time.TimeSystem"]["is_serializable"]


def test_get_templates(gen_paths):  # type: ignore
    """
    Verifies the nunavut.jinja.DSDLCodeGenerator.get_templates() method.
    """
    root_namespace_dir = gen_paths.dsdl_dir / Path("uavcan")
    root_namespace = str(root_namespace_dir)
    language_context = LanguageContextBuilder().set_target_language("c").create()
    namespace = Namespace.read_namespace(gen_paths.out_dir, language_context, root_namespace, [])
    generator = DSDLCodeGenerator(namespace, templates_dir=gen_paths.templates_dir)

    templates = generator.get_templates()

    count = len(list(templates))
    assert count > 0

    # Do it twice just to cover in-memory cache
    templates = generator.get_templates()

    assert count == len(list(templates))
