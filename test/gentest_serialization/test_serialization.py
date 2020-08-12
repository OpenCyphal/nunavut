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
from nunavut.lang import LanguageContext
import pytest


@pytest.mark.parametrize('lang_key', ['cpp', 'c'])
def test_support_headers(gen_paths, lang_key):  # type: ignore
    """
    Test that the support headers are generated/copied.
    """
    ln = LanguageContext(lang_key).get_target_language()
    assert ln is not None
    expected_header = gen_paths.out_dir / \
        Path('nunavut') / \
        Path('support') / \
        Path('serialization').with_suffix(ln.extension)
    root_namespace_dir = gen_paths.dsdl_dir / Path("basic")
    generate_types(lang_key,
                   root_namespace_dir,
                   gen_paths.out_dir,
                   omit_serialization_support=False,
                   allow_unregulated_fixed_port_id=True)

    assert expected_header.exists()
