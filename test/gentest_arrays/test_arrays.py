#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2021  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#

import re
import typing
from pathlib import Path

import pydsdl
from nunavut._namespace import build_namespace_tree
from nunavut.jinja import DSDLCodeGenerator
from nunavut.lang import LanguageContextBuilder, Language


def assert_pattern_match_in_file(file: typing.Optional[Path], *patterns: "re.Pattern") -> None:
    """
    Assert that a given pattern is found within a given file at least once. The pattern
    is matched for each line in the file (i.e. multi-line matches are not supported).
    """
    assert file is not None
    results = {}  # type: typing.Dict[re.Pattern, bool]
    for pattern in patterns:
        results[pattern] = False

    with open(str(file), "r") as file_handle:
        for line in file_handle:
            for pattern in patterns:
                if pattern.match(line):
                    results[pattern] = True

    for key, value in results.items():
        assert value, 'pattern "{}" was not found in file "{}"'.format(str(key), str(file))


def test_default_array_type_cpp(gen_paths):  # type: ignore
    """
    Verify that the default array type for C++ is as expected.
    """
    root_namespace = str(gen_paths.dsdl_dir / Path("radar"))
    compound_types = pydsdl.read_namespace(root_namespace, [], allow_unregulated_fixed_port_id=True)
    language_context = LanguageContextBuilder(include_experimental_languages=True).set_target_language("cpp").create()
    namespace = build_namespace_tree(compound_types, root_namespace, gen_paths.out_dir, language_context)
    generator = DSDLCodeGenerator(namespace)
    generator.generate_all(False)

    assert_pattern_match_in_file(
        gen_paths.find_outfile_in_namespace("radar.Phased", namespace),
        re.compile(r"\s*using *bank_normal_rads *= *std::array<float,3>;\s*"),
    )


def test_var_array_override_cpp(gen_paths):  # type: ignore
    """
    Make sure we can override the type generated for variable-length
    arrays.
    """
    language_option_overrides = {
        "variable_array_type_include": '"scotec/array.hpp"',
        "variable_array_type_template": "scotec::TerribleArray<{TYPE}, {MAX_SIZE}, {REBIND_ALLOCATOR}>",
        "variable_array_type_constructor_args": "{MAX_SIZE}",
        "allocator_include": '"scotec/alloc.hpp"',
        "allocator_type": "TerribleAllocator",
        "allocator_is_default_constructible": True,
        "ctor_convention": "uses-leading-allocator"
    }
    root_namespace = str(gen_paths.dsdl_dir / Path("radar"))
    compound_types = pydsdl.read_namespace(root_namespace, [], allow_unregulated_fixed_port_id=True)
    language_context = (
        LanguageContextBuilder(include_experimental_languages=True)
        .set_target_language("cpp")
        .set_target_language_configuration_override(Language.WKCV_LANGUAGE_OPTIONS, language_option_overrides)
        .create()
    )

    namespace = build_namespace_tree(compound_types, root_namespace, gen_paths.out_dir, language_context)
    generator = DSDLCodeGenerator(namespace)
    generator.generate_all(False)

    assert_pattern_match_in_file(
        gen_paths.find_outfile_in_namespace("radar.Phased", namespace),
        re.compile(r'^#include "scotec/alloc.hpp"$'),
        re.compile(r'^#include "scotec/array.hpp"$'),
        re.compile(r".*\bconst allocator_type& allocator = allocator_type()"),
        re.compile(r"\s*using *antennae_per_bank *= *scotec::TerribleArray<float, *2677, *std::allocator_traits<allocator_type>::rebind_alloc<float>>;\s*"),
        re.compile(r"\s*using *bank_normal_rads *= *std::array<float,3>;\s*"),
        re.compile(r"\s*\: antennae_per_bank{std::allocator_arg, *allocator, *2677}\s*"),

    )
