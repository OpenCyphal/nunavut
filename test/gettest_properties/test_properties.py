#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2020  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#

import pathlib
from pathlib import Path

import pydsdl
import pytest
import yaml
import re

from nunavut import build_namespace_tree
from nunavut.jinja import DSDLCodeGenerator
from nunavut.lang import Language, LanguageClassLoader, LanguageContextBuilder


def test_issue_277(gen_paths):  # type: ignore
    """
    Writes a temporary yaml file to override configuration and verifies the values made it through to the generated
    C++ output.
    """

    override_language_options = {
        "variable_array_type_template": "MyCrazyArray<{TYPE}, {REBIND_ALLOCATOR}>",
        "variable_array_type_include": '"MyCrazyArray.hpp"',
        "variable_array_type_constructor_args": "g_bad_global_thing",
        "allocator_include": '"MyCrazyAllocator.hpp"',
        "allocator_type": "MyCrazyAllocator",
        "allocator_is_default_constructible": True,
        "ctor_convention": "uses-leading-allocator"
    }

    vla_decl_pattern = re.compile(r"\b|^MyCrazyArray\B")
    vla_include_pattern = re.compile(r"^#include\s+\"MyCrazyArray\.hpp\"$")
    alloc_include_pattern = re.compile(r"^#include\s+\"MyCrazyAllocator\.hpp\"$")
    vla_constructor_args_pattern = re.compile(r".*\bstd::allocator_arg, allocator, g_bad_global_thing\b")

    overrides_file = gen_paths.out_dir / pathlib.Path("overrides_test_issue_277.yaml")

    overrides_data = {
        LanguageClassLoader.to_language_module_name("cpp"): {Language.WKCV_LANGUAGE_OPTIONS: override_language_options}
    }

    with open(overrides_file, "w") as overrides_handle:
        yaml.dump(overrides_data, overrides_handle)

    root_namespace = str(gen_paths.dsdl_dir / Path("proptest"))
    compound_types = pydsdl.read_namespace(root_namespace, [], allow_unregulated_fixed_port_id=True)
    language_context = (
        LanguageContextBuilder(include_experimental_languages=True)
        .set_target_language("cpp")
        .set_additional_config_files([overrides_file])
        .create()
    )
    namespace = build_namespace_tree(compound_types, root_namespace, gen_paths.out_dir, language_context)
    generator = DSDLCodeGenerator(namespace)
    generator.generate_all(omit_serialization_support=True)

    # Now read back in and verify
    outfile = gen_paths.find_outfile_in_namespace("proptest.hasvla", namespace)

    assert outfile is not None


    found_vla_decl = False
    found_vla_include = False
    found_alloc_include = False
    found_vla_constructor_args = False
    with open(str(outfile), "r") as header_file:
        for line in header_file:
            if not found_vla_decl and vla_decl_pattern.search(line):
                found_vla_decl = True
            if not found_vla_include and vla_include_pattern.search(line):
                found_vla_include = True
            if not found_alloc_include and alloc_include_pattern.search(line):
                found_alloc_include = True
            if not found_vla_constructor_args and vla_constructor_args_pattern.search(line):
                found_vla_constructor_args = True

    assert found_vla_decl
    assert found_vla_include
    assert found_alloc_include
    assert found_vla_constructor_args
