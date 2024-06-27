#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
"""
Test the generation of serialization support generically and for python.
"""
from pathlib import Path

import pytest

from nunavut import generate_all
from nunavut.lang import LanguageContextBuilder


@pytest.mark.parametrize("lang_key", ["cpp", "c"])
def test_support_headers(gen_paths, lang_key):  # type: ignore
    """
    Test that the support headers are generated/copied.
    """
    root_namespace_dir = gen_paths.dsdl_dir / Path("basic")
    result = generate_all(
        lang_key,
        [],
        root_namespace_dir,
        gen_paths.out_dir,
        omit_serialization_support=False,
        allow_unregulated_fixed_port_id=True,
        include_experimental_languages=(lang_key == "cpp"),
    )

    ln = result.lctx.get_target_language()
    assert ln is not None
    expected_header = gen_paths.out_dir / Path(*ln.support_namespace) / Path("serialization").with_suffix(ln.extension)

    assert expected_header.exists()


@pytest.mark.parametrize("lang_key", ["cpp", "c"])
def test_gen_with_serialization_basic(gen_paths, lang_key):  # type: ignore
    """
    Sanity test. See test_gen_with_serialization_complex for details.
    """
    basic_types = [
        Path("basic", "Basic.1.0.dsdl"),
        Path("basic", "1.HelloSerialization.1.0.dsdl"),
    ]
    generate_all(
        lang_key,
        basic_types,
        gen_paths.dsdl_dir / Path("basic"),
        gen_paths.out_dir,
        allow_unregulated_fixed_port_id=True,
        include_experimental_languages=(lang_key == "cpp"),
    )


@pytest.mark.parametrize("lang_key", ["cpp", "c"])
def test_gen_with_serialization_complex(gen_paths, lang_key):  # type: ignore
    """
    Sanity test that generates some types with serialization code. We need the verification tests
    to do full tests on the code that was generated (i.e. you need a C compiler and C unit tests to
    verify the generated C serialization routines).
    """
    target_types = [
        Path("basic", "Basic.1.0.dsdl"),
        Path("basic", "1.HelloSerialization.1.0.dsdl"),
        Path("complex", "2.KitchenSink.1.0.dsdl"),
    ]
    root_paths = [gen_paths.dsdl_dir / Path("basic"), gen_paths.dsdl_dir / Path("complex")]

    result = generate_all(
        lang_key,
        target_types,
        root_paths,
        gen_paths.out_dir,
        allow_unregulated_fixed_port_id=True,
        include_experimental_languages=(lang_key == "cpp"),
    )

    assert 7 == len(result.generator_targets)
    assert 7 == len(result.generated_files)
    assert 1 == len(result.support_files)
