#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2021  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

import re
import typing
from pathlib import Path

import pydsdl
from nunavut import build_namespace_tree
from nunavut.jinja import DSDLCodeGenerator
from nunavut.lang import LanguageContext


def assert_pattern_match_in_file(file: typing.Optional[Path], * patterns: re.Pattern) -> None:
    """
    Assert that a given pattern is found within a given file at least once. The pattern
    is matched for each line in the file (i.e. multi-line matches are not supported).
    """
    assert (file is not None)
    results = {}  # type: typing.Dict[re.Pattern, bool]
    for pattern in patterns:
        results[pattern] = False

    with open(str(file), 'r') as file_handle:
        for line in file_handle:
            for pattern in patterns:
                if pattern.match(line):
                    results[pattern] = True

    for key, value in results.items():
        assert value, 'pattern \"{}\" was not found in file \"{}\"'.format(
            str(key),
            str(file))


def test_default_array_type_cpp(gen_paths):  # type: ignore
    """
    Verify that the default array type for C++ is as expected.
    """
    root_namespace = str(gen_paths.dsdl_dir / Path("radar"))
    compound_types = pydsdl.read_namespace(root_namespace, [], allow_unregulated_fixed_port_id=True)
    language_context = LanguageContext('cpp')
    namespace = build_namespace_tree(compound_types,
                                     root_namespace,
                                     gen_paths.out_dir,
                                     language_context)
    generator = DSDLCodeGenerator(namespace)
    generator.generate_all(False)

    assert_pattern_match_in_file(
        gen_paths.find_outfile_in_namespace("radar.Phased", namespace),
        re.compile(r'\s*std::array<float,3>\s+bank_normal_rads;\s*')
    )


def test_var_array_override_cpp(gen_paths):  # type: ignore
    """
    Make sure we can override the type generated for variable-length
    arrays.
    """
    language_option_overrides = {'variable_array_type': 'scotec::TerribleArray<{TYPE},{MAX_SIZE}>'}
    root_namespace = str(gen_paths.dsdl_dir / Path("radar"))
    compound_types = pydsdl.read_namespace(root_namespace, [], allow_unregulated_fixed_port_id=True)
    language_context = LanguageContext('cpp',
                                       language_options=language_option_overrides)

    namespace = build_namespace_tree(compound_types,
                                     root_namespace,
                                     gen_paths.out_dir,
                                     language_context)
    generator = DSDLCodeGenerator(namespace)
    generator.generate_all(False)

    assert_pattern_match_in_file(
        gen_paths.find_outfile_in_namespace("radar.Phased", namespace),
        re.compile(r'\s*scotec::TerribleArray<float,2677>\s+antennae_per_bank;\s*'),
        re.compile(r'\s*std::array<float,3>\s+bank_normal_rads;\s*')
    )
