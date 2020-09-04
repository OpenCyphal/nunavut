#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
Test the generation of serialization support generically and for python.
"""
import pathlib
from pathlib import Path

import pytest

from nunavut import generate_types
from nunavut.lang import LanguageContext


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


@pytest.mark.parametrize('lang_key', ['cpp', 'c'])
def test_gen_with_serialization_basic(gen_paths, lang_key):  # type: ignore
    """
    Sanity test. See test_gen_with_serialization_complex for details.
    """
    basic_types = gen_paths.dsdl_dir / pathlib.Path('basic')
    generate_types(lang_key,
                   basic_types,
                   gen_paths.out_dir,
                   omit_serialization_support=False,
                   allow_unregulated_fixed_port_id=True)


@pytest.mark.parametrize('lang_key', ['cpp', 'c'])
def test_gen_with_serialization_complex(gen_paths, lang_key):  # type: ignore
    """
    Sanity test that generates some types with serialization code. We need the verification tests
    to do full tests on the code that was generated (i.e. you need a C compiler and C unit tests to
    verify the generated C serialization routines).
    """
    basic_types = gen_paths.dsdl_dir / pathlib.Path('basic')
    complex_types = gen_paths.dsdl_dir / pathlib.Path('complex')
    generate_types(lang_key,
                   complex_types,
                   gen_paths.out_dir,
                   lookup_directories=[str(basic_types)],
                   omit_serialization_support=False,
                   allow_unregulated_fixed_port_id=True)
