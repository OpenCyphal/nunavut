#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
from pathlib import Path

import pytest

from nunavut import build_namespace_tree
from nunavut.lang import LanguageContext
from nunavut.jinja import Generator
from pydsdl import read_namespace


def test_realgen(gen_paths):  # type: ignore
    """
    Sanity test that runs through the entire public, regulated set of
    UAVCAN types and generates some basic C code.
    """
    root_namespace_dir = gen_paths.dsdl_dir / Path("uavcan")
    type_map = read_namespace(str(root_namespace_dir), '')
    language_context = LanguageContext(extension='.h')
    namespace = build_namespace_tree(type_map,
                                     root_namespace_dir,
                                     gen_paths.out_dir,
                                     language_context)
    generator = Generator(namespace, False, language_context, gen_paths.templates_dir)
    generator.generate_all(False)
