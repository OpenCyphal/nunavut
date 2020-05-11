#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
Test the generation of serialization support generically and for python.
"""
from pathlib import Path

from nunavut import generate_types
import pytest


@pytest.mark.parametrize('lang_key', ['cpp'])
def test_hello_serialization(gen_paths, lang_key):  # type: ignore
    """
    don't know yet
    """
    root_namespace_dir = gen_paths.dsdl_dir / Path("basic")
    generate_types(lang_key,
                   root_namespace_dir,
                   gen_paths.out_dir,
                   omit_serialization_support=False,
                   allow_unregulated_fixed_port_id=True)
