#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
from pathlib import Path

import pytest

from nunavut import generate_types


@pytest.mark.parametrize('lang_key,generate_support', [('cpp', False), ('cpp', True)])
def test_realgen(gen_paths, lang_key, generate_support):  # type: ignore
    """
    Sanity test that runs through the entire public, regulated set of
    UAVCAN types and generates some basic C code.
    """
    root_namespace_dir = gen_paths.root_dir / Path("submodules") / Path("public_regulated_data_types") / Path("uavcan")
    generate_types(lang_key, root_namespace_dir, gen_paths.out_dir, omit_serialization_support=not generate_support)
