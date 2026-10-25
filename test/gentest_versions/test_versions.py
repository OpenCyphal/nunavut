#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2020  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#

import pytest
from pathlib import Path

import pydsdl
import re
import nunavut

from nunavut._namespace import build_namespace_tree
from nunavut.jinja import DSDLCodeGenerator
from nunavut.lang import LanguageContextBuilder


include_pattern_map = (
    ["cpp", "VIRUSES_COVID_{major}_{minor}_HPP_INCLUDED"],
    ["c", "VIRUSES_COVID_{major}_{minor}_INCLUDED_"],  # Due to the limitations of C, collisions are likely, hence '_'
)


def test_version_info_matches_release_triplet() -> None:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", nunavut.__version__)
    assert match is not None
    assert nunavut.__version_info__ == tuple(int(group) for group in match.groups())


def test_cmake_package_version_matches_version(gen_paths) -> None:  # type: ignore
    """
    The CMake package files can't ask Python for the version before find_package() resolves, so the major.minor
    version is hard-coded. Require exactly one quoted version literal across both files (the PACKAGE_VERSION in
    NunavutConfigVersion.cmake) and require it to match __version__.
    """
    expected = ".".join(str(part) for part in nunavut.__version_info__[0:2])
    literals = []
    for cmake_file in ("NunavutConfigVersion.cmake", "NunavutConfig.cmake"):
        for line_number, line in enumerate((gen_paths.root_dir / cmake_file).read_text("utf-8").splitlines(), 1):
            for literal in re.findall(r'"(\d+(?:\.\d+)+)"', line):
                literals.append((cmake_file, line_number, line.strip(), literal))
    assert len(literals) == 1, f"Expected one version literal in the CMake package files, found: {literals}"
    cmake_file, _, line, literal = literals[0]
    assert cmake_file == "NunavutConfigVersion.cmake"
    assert line.startswith("set(PACKAGE_VERSION ")
    assert literal == expected


@pytest.mark.parametrize("lang_key,include_format", include_pattern_map)
def test_issue_136(gen_paths, lang_key: str, include_format: str):  # type: ignore
    """
    Generates a type that has two different versions using the built-in language support and verifies
    that the header include guards include the type version. This verifies fix #136 has not
    regressed.
    """
    covid_versions = [pydsdl.Version(1, 9), pydsdl.Version(1, 10)]
    root_namespace = str(gen_paths.dsdl_dir / Path("viruses"))
    compound_types = pydsdl.read_namespace(root_namespace, [], allow_unregulated_fixed_port_id=True)
    language_context = (
        LanguageContextBuilder(include_experimental_languages=True).set_target_language(lang_key).create()
    )
    namespace = build_namespace_tree(compound_types, root_namespace, gen_paths.out_dir, language_context)
    generator = DSDLCodeGenerator(namespace)
    generator.generate_all()

    for covid_version in covid_versions:

        include_guard_start = re.compile(
            r"#ifndef {}\b".format(include_format.format(major=covid_version.major, minor=covid_version.minor))
        )

        include_guard_def = re.compile(
            r"#define {}\b".format(include_format.format(major=covid_version.major, minor=covid_version.minor))
        )

        # Now read back in and verify
        outfile = gen_paths.find_outfile_in_namespace("viruses.covid", namespace, type_version=covid_version)

        assert outfile is not None

        found_open_line = 0
        found_def_line = 0
        with open(str(outfile), "r", encoding="utf-8") as header_file:
            line_no = 1
            for line in header_file:
                if include_guard_start.match(line):
                    found_open_line = line_no
                if include_guard_def.match(line):
                    found_def_line = line_no
                    break
                line_no += 1
        assert found_open_line > 0
        assert found_def_line > found_open_line
