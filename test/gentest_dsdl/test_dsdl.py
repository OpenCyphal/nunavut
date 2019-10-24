#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
from pathlib import Path

import pytest
from pydsdl import read_namespace

from nunavut import build_namespace_tree
from nunavut.jinja import Generator
from nunavut.lang import LanguageContext


@pytest.mark.parametrize('lang_key', ['cpp'])
def test_realgen(gen_paths, lang_key):  # type: ignore
    """
    Sanity test that runs through the entire public, regulated set of
    UAVCAN types and generates some basic C code.
    """
    root_namespace_dir = gen_paths.root_dir / Path("submodules") / Path("public_regulated_data_types") / Path("uavcan")
    type_map = read_namespace(str(root_namespace_dir), '')
    language_context = LanguageContext(lang_key)
    namespace = build_namespace_tree(type_map,
                                     root_namespace_dir,
                                     gen_paths.out_dir,
                                     language_context)
    generator = Generator(namespace, False, language_context)
    generator.generate_all(False)
