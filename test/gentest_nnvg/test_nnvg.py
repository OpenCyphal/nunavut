#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
# cSpell:ignore scotec, herringtec
"""
Tests similar to test_nnvg_legacy.py but written after the 3.0 refactor.
"""
import json
import os
import subprocess
from argparse import ArgumentError
from pathlib import Path
from typing import Any, Callable

import pydsdl
import pytest

import nunavut._version
from nunavut.lang import LanguageContextBuilder, UnsupportedLanguageError
from nunavut.lang._language import LanguageClassLoader


def test_realgen_using_nnvg(gen_paths: Any, run_nnvg: Callable) -> None:
    """
    Sanity test that nnvg can generate code from known types.
    """
    public_regulated_data_types = gen_paths.root_dir / Path("submodules") / Path("public_regulated_data_types")

    nnvg_args0 = [
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "-l",
        "c",
        "-I",
        "uavcan",
        "reg",
    ]

    with pytest.raises(subprocess.CalledProcessError):
        run_nnvg(
            gen_paths,
            nnvg_args0 + ["--no-target-namespaces"],
            raise_called_process_error=True,
            cwd=public_regulated_data_types,
        )

    run_nnvg(gen_paths, nnvg_args0, cwd=public_regulated_data_types)

    note = gen_paths.out_dir / Path("reg") / Path("udral") / Path("physics") / Path("acoustics") / Path("Note_0_1.h")
    assert note.exists()


def test_DSDL_INCLUDE_PATH(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verify that the DSDL_INCLUDE_PATH environment variable is used by nnvg.
    """

    nnvg_args0 = [
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--support-templates",
        gen_paths.support_templates_dir.as_posix(),
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "-l",
        "js",
        "-Xlang",
        (gen_paths.dsdl_dir / Path("uavcan")).relative_to(Path.cwd()).as_posix(),
    ]

    with pytest.raises(pydsdl.FrontendError):
        assert 0 == run_nnvg_main(gen_paths, nnvg_args0).returncode

    scotec_path = (gen_paths.dsdl_dir / Path("scotec")).relative_to(Path.cwd()).as_posix()
    herringtec_path = (gen_paths.dsdl_dir / Path("herringtec")).relative_to(Path.cwd()).as_posix()
    env = {"DSDL_INCLUDE_PATH": f"{herringtec_path}{os.pathsep}{scotec_path}"}
    assert 0 == run_nnvg_main(gen_paths, nnvg_args0, env=env).returncode


def test_CYPHAL_PATH(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verify that the CYPHAL_PATH environment variable is used by nnvg.
    """

    nnvg_args0 = [
        "--allow-unregulated-fixed-port-id",
        "--no-target-namespaces",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "-l",
        "js",
        "-Xlang",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("uavcan")).relative_to(Path.cwd()).as_posix(),
        (gen_paths.dsdl_dir / Path("uavcan", "test", "TestType.0.8.dsdl")).as_posix(),
    ]

    with pytest.raises(pydsdl.FrontendError):
        run_nnvg_main(gen_paths, nnvg_args0)

    env = {"CYPHAL_PATH": f"{gen_paths.dsdl_dir}"}
    assert 0 == run_nnvg_main(gen_paths, nnvg_args0, env=env).returncode


def test_nnvg_heals_missing_dot_in_extension(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    nnvg check for a missing dot in the --output-extension arg and adds it for you. This test
    verifies that logic.
    """
    nnvg_args = [
        "--no-target-namespaces",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--output-extension",
        "js",
        "-Xlang",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
        "uavcan/test/TestType.0.8.dsdl",
    ]

    # This will fail if the dot isn't added by nnvg
    assert 0 == run_nnvg_main(gen_paths, nnvg_args).returncode


@pytest.mark.parametrize("generate_support", ["as-needed", "never", "always", "only"])
def test_list_inputs(gen_paths: Any, run_nnvg_main: Callable, generate_support: str) -> None:
    """
    Verifies nnvg's --list-input mode.
    """
    code_templates = [gen_paths.templates_dir / Path("Any.j2")]

    types = [
        gen_paths.dsdl_dir / Path("uavcan") / Path("test") / Path("TestType.0.8.dsdl"),
        gen_paths.dsdl_dir / Path("scotec") / Path("Timer.1.0.dsdl"),
    ]

    support_files = [gen_paths.support_templates_dir / Path("serialization").with_suffix(".j2")]

    # should be added to this list.
    nnvg_args = [
        "--no-target-namespaces",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--support-templates",
        gen_paths.support_templates_dir.as_posix(),
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "js",
        "-Xlang",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
        "--list-inputs",
        f"--generate-support={generate_support}",
        "uavcan/test/TestType.0.8.dsdl",
    ]

    # Always types because we use the types to determine what support to include.
    if generate_support == "never":
        expected_output = types + code_templates
    elif generate_support == "only":
        expected_output = types + support_files
    else:
        expected_output = types + code_templates + support_files

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert sorted(expected_output) == sorted(completed_wo_empty)


def test_list_inputs_w_namespaces(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    This covers some extra logic in nnvg when handling list-input with namespaces.
    """
    expected_output = sorted(
        [
            gen_paths.templates_dir / Path("Any.j2"),
            gen_paths.dsdl_dir / Path("uavcan", "test", "TestType.0.8.dsdl"),
            gen_paths.dsdl_dir / Path("scotec", "Timer.1.0.dsdl"),
        ]
    )

    nnvg_args = [
        "--no-target-namespaces",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "-l",
        "js",
        "-Xlang",
        "--omit-serialization-support",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-inputs",
        "--generate-namespace-types",
        f"{(gen_paths.dsdl_dir / Path('uavcan')).as_posix()}:{Path('test', 'TestType.0.8.dsdl').as_posix()}",
    ]

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == completed_wo_empty


def test_list_outputs(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verifies nnvg's --list-output mode.
    """
    expected_output = sorted(
        [
            gen_paths.out_dir / Path("uavcan", "test", "TestType_0_8.json"),
            gen_paths.out_dir / Path("scotec", "Timer_1_0.json"),
        ]
    )

    nnvg_args = [
        "--no-target-namespaces",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--output-extension",
        ".json",
        "-l",
        "js",
        "-Xlang",
        "--omit-serialization-support",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-outputs",
        f"{(gen_paths.dsdl_dir / Path('uavcan')).as_posix()}:{Path('test', 'TestType.0.8.dsdl').as_posix()}",
    ]

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == completed_wo_empty


def test_list_support_outputs_builtin(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verifies nnvg's --list-output mode for internal language support.
    """
    support_path = gen_paths.out_dir / Path("nunavut") / Path("support")
    expected_output = sorted([support_path / Path("serialization").with_suffix(".h")])

    nnvg_args = [
        "--no-target-namespaces",
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--output-extension",
        ".h",
        "--list-outputs",
        "--generate-support=only",
    ]

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == completed_wo_empty


def test_do_nothing(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verifies nnvg's behavior no work is done.
    """
    nnvg_args = [
        "--no-target-namespaces",
        "--verbose",
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--output-extension",
        ".h",
        "--list-outputs",
        "--generate-support=never",
    ]

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert [] == completed_wo_empty


def test_list_outputs_builtin(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verifies nnvg's --list-output mode for internal language support.
    """
    expected_output = sorted(
        [
            gen_paths.out_dir / Path("nunavut", "support", "serialization").with_suffix(".h"),
            gen_paths.out_dir / Path("scotec", "Timer_1_0").with_suffix(".h"),
            gen_paths.out_dir / Path("uavcan", "test", "TestType_0_8").with_suffix(".h"),
        ]
    )

    nnvg_args = [
        "--no-target-namespaces",
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--output-extension",
        ".h",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-outputs",
        f"{(gen_paths.dsdl_dir / Path('uavcan')).as_posix()}:{Path('test', 'TestType.0.8.dsdl').as_posix()}",
    ]

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_list_outputs_builtin_pod(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verifies nnvg's --list-output mode for internal language support.
    """
    expected_output = sorted(
        [
            gen_paths.out_dir / Path("uavcan", "test", "TestType_0_8").with_suffix(".h"),
            gen_paths.out_dir / Path("scotec", "Timer_1_0").with_suffix(".h"),
        ]
    )

    nnvg_args = [
        "--no-target-namespaces",
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--output-extension",
        ".h",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
        "--list-outputs",
        "--omit-serialization-support",
        Path("uavcan", "test", "TestType.0.8.dsdl").as_posix(),
    ]

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == completed_wo_empty


def test_version(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verifies nnvg's --version
    """
    nnvg_args = ["--version"]

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8")
    assert nunavut._version.__version__ == completed  # pylint: disable=protected-access


@pytest.mark.parametrize("omit_serialization_support", [True, False])
@pytest.mark.parametrize("omit_dependencies", [True, False])
def test_target_language(
    gen_paths: Any, run_nnvg_main: Callable, omit_serialization_support: bool, omit_dependencies: bool
) -> None:
    """
    Verifies the behavior when target language support is provided.
    """
    expected_output = [
        gen_paths.out_dir / Path("uavcan", "test", "TestType_0_8").with_suffix(".hpp"),
    ]

    if not omit_dependencies:
        expected_output.append(gen_paths.out_dir / Path("scotec", "Timer_1_0").with_suffix(".hpp"))

    if not omit_serialization_support:
        expected_output.append(gen_paths.out_dir / Path("nunavut", "support", "serialization").with_suffix(".hpp"))

    expected_output = sorted(expected_output)

    nnvg_args = [
        "--no-target-namespaces",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-outputs",
        f"{(gen_paths.dsdl_dir / Path('uavcan')).as_posix()}:{Path('test', 'TestType.0.8.dsdl').as_posix()}",
    ]

    if omit_dependencies:
        nnvg_args.append("--omit-dependencies")

    if omit_serialization_support:
        nnvg_args.append("--omit-serialization-support")

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == completed_wo_empty


def test_language_option_defaults(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verifies expected language option defaults are available.
    """

    expected_output = sorted(
        [
            gen_paths.out_dir / Path("uavcan", "test", "TestType_0_8").with_suffix(".hpp"),
            gen_paths.out_dir / Path("scotec", "Timer_1_0").with_suffix(".hpp"),
        ]
    )

    nnvg_args = [
        "--no-target-namespaces",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
        Path("uavcan", "test", "TestType.0.8.dsdl").as_posix(),
    ]

    assert 0 == run_nnvg_main(gen_paths, nnvg_args).returncode
    for expected_output_path in expected_output:
        assert expected_output_path.exists()
        with expected_output_path.open("r", encoding="utf-8") as generated:
            generated_results = json.load(generated)
            assert generated_results["target_endianness"] == "any"
            assert not generated_results["omit_float_serialization_support"]
            assert not generated_results["enable_serialization_asserts"]


@pytest.mark.parametrize("target_endianness_override", ["any", "big", "little"])
def test_language_option_overrides(target_endianness_override: str, gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verifies expected language option defaults can be overridden.
    """

    expected_output = gen_paths.out_dir / Path("uavcan") / Path("test") / Path("TestType_0_8.hpp")

    nnvg_args = [
        "--no-target-namespaces",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
        "--target-endianness",
        target_endianness_override,
        Path("uavcan", "test", "TestType.0.8.dsdl").as_posix(),
    ]

    assert 0 == run_nnvg_main(gen_paths, nnvg_args).returncode
    assert expected_output.exists()
    with expected_output.open("r", encoding="utf-8") as generated:
        generated_results = json.load(generated)
        assert generated_results["target_endianness"] == target_endianness_override


def test_language_option_target_endianness_illegal_option(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verifies an illegal --target-endianness option is rejected.
    """

    nnvg_args = [
        "--no-target-namespaces",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--target-endianness",
        "mixed",
        Path("uavcan", "test", "TestType.0.8.dsdl").as_posix(),
    ]

    with pytest.raises(ArgumentError, match=r".*invalid choice.*"):
        assert 0 == run_nnvg_main(gen_paths, nnvg_args, raise_argument_error=True)


def test_language_option_omit_floatingpoint(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verifies that the --omit-float-serialization-support option is wired up in nnvg.
    """

    expected_output = gen_paths.out_dir / Path("uavcan") / Path("test") / Path("TestType_0_8.hpp")

    nnvg_args = [
        "--no-target-namespaces",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
        "--omit-float-serialization-support",
        Path("uavcan", "test", "TestType.0.8.dsdl").as_posix(),
    ]

    assert 0 == run_nnvg_main(gen_paths, nnvg_args).returncode
    with expected_output.open("r", encoding="utf-8") as generated:
        generated_results = json.load(generated)
        assert generated_results["omit_float_serialization_support"]


def test_language_option_generate_asserts(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verifies that the --enable-serialization-asserts option is wired up in nnvg.
    """

    expected_output = gen_paths.out_dir / Path("uavcan") / Path("test") / Path("TestType_0_8.hpp")

    nnvg_args = [
        "--no-target-namespaces",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
        "--enable-serialization-asserts",
        Path("uavcan", "test", "TestType.0.8.dsdl").as_posix(),
    ]

    assert 0 == run_nnvg_main(gen_paths, nnvg_args).returncode
    with expected_output.open("r", encoding="utf-8") as generated:
        generated_results = json.load(generated)
        assert generated_results["enable_serialization_asserts"]


def test_generate_support_only(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verifies expected language option defaults can be overridden.
    """
    support_path = gen_paths.out_dir / Path("nunavut") / Path("support")
    expected_output = sorted([support_path / Path("serialization").with_suffix(".h")])

    nnvg_args = [
        "--no-target-namespaces",
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "c",
        "--generate-support=only",
    ]

    assert 0 == run_nnvg_main(gen_paths, nnvg_args).returncode
    for expected_output_path in expected_output:
        assert expected_output_path.exists()


@pytest.mark.parametrize("generate_support", ["as-needed", "never", "always", "only"])
@pytest.mark.parametrize("omit_serialization", [True, False])
def test_generate_support(
    generate_support: str, omit_serialization: bool, gen_paths: Any, run_nnvg_main: Callable
) -> None:
    """
    Verifies expected language option defaults can be overridden.
    """
    support_path = gen_paths.out_dir / Path("nunavut") / Path("support")
    test_type_path = gen_paths.out_dir / Path("uavcan") / Path("test")
    support_output = [support_path / Path("serialization").with_suffix(".h")]
    type_output = [test_type_path / Path("TestType_0_8.h")]

    nnvg_args = [
        "--no-target-namespaces",
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "c",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
        f"--generate-support={generate_support}",
    ]

    if omit_serialization:
        nnvg_args.append("--omit-serialization-support")

    nnvg_args.append("uavcan/test/TestType.0.8.dsdl")

    # TODO: a more generalized test is needed as the C language doesn't have any language support files
    #       to cover cases where serialization is omitted but language support is not.
    assert 0 == run_nnvg_main(gen_paths, nnvg_args).returncode
    for support_output_path in support_output:
        if generate_support == "never":
            assert not support_output_path.exists()
        else:
            assert support_output_path.exists() != omit_serialization

    for type_output_path in type_output:
        if generate_support != "only":
            assert type_output_path.exists()
        else:
            assert not type_output_path.exists()


def test_issue_73(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verify that https://github.com/OpenCyphal/nunavut/issues/73 hasn't regressed.
    """
    nnvg_args = [
        "--no-target-namespaces",
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
        "--list-inputs",
        Path("uavcan", "test", "TestType.0.8.dsdl").as_posix(),
    ]

    assert 0 == run_nnvg_main(gen_paths, nnvg_args).returncode


def test_issue_116(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verify nnvg will infer target language when given only a file extension.
    See https://github.com/OpenCyphal/nunavut/issues/116 for issue that this is a fix
    for.
    """
    expected_output = sorted(
        [
            gen_paths.out_dir / Path("uavcan", "test", "TestType_0_8").with_suffix(".h"),
            gen_paths.out_dir / Path("scotec", "Timer_1_0").with_suffix(".h"),
        ]
    )

    # Happy path
    nnvg_args = [
        "--no-target-namespaces",
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--output-extension",
        ".h",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
        "--list-outputs",
        "--omit-serialization-support",
        Path("uavcan", "test", "TestType.0.8.dsdl").as_posix(),
    ]

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == completed_wo_empty

    # Warning path
    nnvg_args = [
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "-l",
        "blarg",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-outputs",
        "--omit-serialization-support",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    with pytest.raises(UnsupportedLanguageError, match=r"language blarg is not a supported language"):
        assert 0 == run_nnvg_main(gen_paths, nnvg_args).returncode


def test_language_allow_unregulated_fixed_port_id(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Covers nnvg --allow-unregulated-fixed-port-id switch
    """
    expected_output = [
        gen_paths.out_dir / Path("fixedid") / Path("Timer_1_0.hpp"),
    ]

    nnvg_args = [
        "--no-target-namespaces",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "--lookup-dir",
        (gen_paths.dsdl_dir / Path("fixedid")).as_posix(),
        "--list-outputs",
        "--omit-serialization-support",
        (gen_paths.dsdl_dir / Path("fixedid", "100.Timer.1.0.dsdl")).as_posix(),
    ]

    with pytest.raises(pydsdl.FrontendError):
        assert 0 == run_nnvg_main(gen_paths, nnvg_args).returncode

    nnvg_args.append("--allow-unregulated-fixed-port-id")

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == completed_wo_empty


def test_list_configuration(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Verifies nnvg's --list-configuration option
    """
    import yaml  # pylint: disable=import-outside-toplevel

    nnvg_args = ["--no-target-namespaces", "--list-configuration"]

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8").split(";")
    parsed_config = yaml.load("\n".join(completed), yaml.Loader)
    default_target_section_name = LanguageClassLoader.to_language_module_name(
        LanguageContextBuilder.DEFAULT_TARGET_LANGUAGE
    )
    assert len(parsed_config[default_target_section_name]) > 0
    print(yaml.dump(parsed_config))


def test_colon_syntax(gen_paths: Any, run_nnvg_main: Callable) -> None:
    """
    Test the colon syntax for specifying DSDL files.
    """
    expected_output = [
        gen_paths.out_dir / Path("herringtec") / Path("Carp_1_0.h"),
        gen_paths.out_dir / Path("herringtec") / Path("Timer_2_1.h"),
    ]

    nnvg_args = [
        "--no-target-namespaces",
        "--outdir",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "c",
        "--omit-serialization-support",
        "--list-outputs",
        f"{(gen_paths.dsdl_dir / Path('herringtec')).as_posix()}:{Path('Timer.2.1.dsdl').as_posix()}",
        Path("herringtec", "Carp.1.0.dsdl").as_posix(),
    ]

    result = run_nnvg_main(gen_paths, nnvg_args)
    assert 0 == result.returncode
    completed = result.stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == completed_wo_empty
