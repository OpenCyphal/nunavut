#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
# cSpell:ignore scotec, herringtec
import json
import os
import subprocess
import typing
from pathlib import Path

import pytest
import pydsdl

import nunavut._version
from nunavut.lang import LanguageContextBuilder
from nunavut.lang._language import LanguageClassLoader


def test_DSDL_INCLUDE_PATH(gen_paths: typing.Any, run_nnvg_main: typing.Callable) -> None:
    """
    Verify that the DSDL_INCLUDE_PATH environment variable is used by nnvg.
    """

    nnvg_args0 = [
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "-l",
        "js",
        "-Xlang",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    with pytest.raises(pydsdl.FrontendError):
        run_nnvg_main(gen_paths, nnvg_args0, raise_argument_error=True)

    scotec_path = (gen_paths.dsdl_dir / Path("scotec")).as_posix()
    herringtec_path = (gen_paths.dsdl_dir / Path("herringtec")).as_posix()
    env = {"DSDL_INCLUDE_PATH": f"{herringtec_path}{os.pathsep}{scotec_path}"}
    run_nnvg_main(gen_paths, nnvg_args0, env=env)


def test_CYPHAL_PATH(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verify that the CYPHAL_PATH environment variable is used by nnvg.
    """

    nnvg_args0 = [
        "--allow-unregulated-fixed-port-id",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "-l",
        "js",
        "-Xlang",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    with pytest.raises(subprocess.CalledProcessError):
        run_nnvg(gen_paths, nnvg_args0, raise_called_process_error=True)

    env = {"CYPHAL_PATH": f"{gen_paths.dsdl_dir}"}
    run_nnvg(gen_paths, nnvg_args0, env=env)


def test_nnvg_heals_missing_dot_in_extension(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    nnvg check for a missing dot in the -e arg and adds it for you. This test
    verifies that logic.
    """
    nnvg_args = [
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "-e",
        "js",
        "-Xlang",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    # This will fail if the dot isn't added by nnvg
    run_nnvg(gen_paths, nnvg_args)


@pytest.mark.parametrize("generate_support", ["as-needed", "never", "always", "only"])
def test_list_inputs(gen_paths: typing.Any, run_nnvg_main: typing.Callable, generate_support: str) -> None:
    """
    Verifies nnvg's --list-input mode.
    """
    code_templates = [gen_paths.templates_dir / Path("Any.j2")]

    types = [
        gen_paths.dsdl_dir / Path("uavcan") / Path("test") / Path("TestType.0.8.dsdl"),
        gen_paths.dsdl_dir / Path("scotec") / Path("Timer.1.0.dsdl"),
    ]

    support_files = [gen_paths.lang_src_dir / Path("c") / Path("support") / Path("serialization").with_suffix(".j2")]

    nnvg_args = [
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "c",
        "-Xlang",  # this test' Any template needs javascript support.
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-inputs",
        f"--generate-support={generate_support}",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    # Always types because we use the types to determine what support to include.
    if generate_support == "never":
        expected_output = types + code_templates
    elif generate_support == "only":
        expected_output = types + support_files
    else:
        expected_output = types + code_templates + support_files

    completed = run_nnvg_main(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert len(expected_output) == len(completed_wo_empty)
    assert sorted(expected_output) == sorted(completed_wo_empty)


def test_list_inputs_w_namespaces(gen_paths: typing.Any, run_nnvg_main: typing.Callable) -> None:
    """
    This covers some extra logic in nnvg when handling list-input with namespaces.
    """
    expected_output = sorted(
        [
            gen_paths.templates_dir / Path("Any.j2"),
            gen_paths.dsdl_dir / Path("uavcan") / Path("test") / Path("TestType.0.8.dsdl"),
            gen_paths.dsdl_dir / Path("scotec") / Path("Timer.1.0.dsdl"),
        ]
    )

    nnvg_args = [
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "-l",
        "js",
        "-Xlang",
        "--omit-serialization-support",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-inputs",
        "--generate-namespace-types",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    completed = run_nnvg_main(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_list_outputs(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verifies nnvg's --list-output mode.
    """
    expected_output = sorted(
        [
            gen_paths.out_dir / Path("uavcan") / Path("test") / Path("TestType_0_8.json"),
            gen_paths.out_dir / Path("scotec") / Path("Timer_1_0.json"),
        ]
    )

    nnvg_args = [
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "-e",
        ".json",
        "-l",
        "js",
        "-Xlang",
        "--omit-serialization-support",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-outputs",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_list_support_outputs_builtin(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verifies nnvg's --list-output mode for internal language support.
    """
    support_path = gen_paths.out_dir / Path("nunavut") / Path("support")
    expected_output = sorted([support_path / Path("serialization").with_suffix(".h")])

    nnvg_args = [
        "-O",
        gen_paths.out_dir.as_posix(),
        "-e",
        ".h",
        "--list-outputs",
        "--generate-support=only",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == completed_wo_empty


def test_list_outputs_builtin(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verifies nnvg's --list-output mode for internal language support.
    """
    support_path = gen_paths.out_dir / Path("nunavut") / Path("support")
    expected_output = sorted(
        [
            support_path / Path("serialization").with_suffix(".h"),
            gen_paths.out_dir / Path("uavcan") / Path("test") / Path("TestType_0_8").with_suffix(".h"),
            gen_paths.out_dir / Path("scotec") / Path("Timer_1_0").with_suffix(".h"),
        ]
    )

    nnvg_args = [
        "-O",
        gen_paths.out_dir.as_posix(),
        "-e",
        ".h",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-outputs",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_list_outputs_builtin_pod(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verifies nnvg's --list-output mode for internal language support.
    """
    expected_output = sorted(
        [
            gen_paths.out_dir / Path("uavcan") / Path("test") / Path("TestType_0_8").with_suffix(".h"),
            gen_paths.out_dir / Path("scotec") / Path("Timer_1_0").with_suffix(".h"),
        ]
    )

    nnvg_args = [
        "-O",
        gen_paths.out_dir.as_posix(),
        "-e",
        ".h",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-outputs",
        "--omit-serialization-support",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_version(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verifies nnvg's --version
    """
    nnvg_args = ["--version"]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8")
    assert nunavut._version.__version__ == completed  # pylint: disable=protected-access


def test_target_language(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verifies the behavior when target language support is provided.
    """
    expected_output = sorted(
        [
            gen_paths.out_dir / Path("uavcan") / Path("test") / Path("TestType_0_8.hpp"),
            gen_paths.out_dir / Path("scotec") / Path("Timer_1_0.hpp"),
        ]
    )

    nnvg_args = [
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-outputs",
        "--omit-serialization-support",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_language_option_defaults(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verifies expected language option defaults are available.
    """

    expected_output = gen_paths.out_dir / Path("uavcan") / Path("test") / Path("TestType_0_8.hpp")

    nnvg_args = [
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    with open(expected_output, "r", encoding="utf-8") as generated:
        generated_results = json.load(generated)
        assert generated_results["target_endianness"] == "any"
        assert not generated_results["omit_float_serialization_support"]
        assert not generated_results["enable_serialization_asserts"]


@pytest.mark.parametrize("target_endianness_override", ["any", "big", "little"])
def test_language_option_overrides(
    target_endianness_override: str, gen_paths: typing.Any, run_nnvg: typing.Callable
) -> None:
    """
    Verifies expected language option defaults can be overridden.
    """

    expected_output = gen_paths.out_dir / Path("uavcan") / Path("test") / Path("TestType_0_8.hpp")

    nnvg_args = [
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--target-endianness",
        target_endianness_override,
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    with open(expected_output, "r", encoding="utf-8") as generated:
        generated_results = json.load(generated)
        assert generated_results["target_endianness"] == target_endianness_override


def test_language_option_target_endianness_illegal_option(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verifies an illegal --target-endianness option is rejected.
    """

    nnvg_args = [
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--target-endianness",
        "mixed",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    with pytest.raises(subprocess.CalledProcessError):
        run_nnvg(gen_paths, nnvg_args, raise_called_process_error=True).stdout.decode("utf-8").split(";")


def test_language_option_omit_floatingpoint(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verifies that the --omit-float-serialization-support option is wired up in nnvg.
    """

    expected_output = gen_paths.out_dir / Path("uavcan") / Path("test") / Path("TestType_0_8.hpp")

    nnvg_args = [
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--omit-float-serialization-support",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    with open(expected_output, "r", encoding="utf-8") as generated:
        generated_results = json.load(generated)
        assert generated_results["omit_float_serialization_support"]


def test_language_option_generate_asserts(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verifies that the --enable-serialization-asserts option is wired up in nnvg.
    """

    expected_output = gen_paths.out_dir / Path("uavcan") / Path("test") / Path("TestType_0_8.hpp")

    nnvg_args = [
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--enable-serialization-asserts",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    with open(expected_output, "r", encoding="utf-8") as generated:
        generated_results = json.load(generated)
        assert generated_results["enable_serialization_asserts"]


def test_generate_support_only(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verifies expected language option defaults can be overridden.
    """
    support_path = gen_paths.out_dir / Path("nunavut") / Path("support")
    expected_output = sorted([support_path / Path("serialization").with_suffix(".h")])

    nnvg_args = ["-O", gen_paths.out_dir.as_posix(), "--target-language", "c", "--generate-support=only"]

    run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    for expected_output_path in expected_output:
        assert expected_output_path.exists()


@pytest.mark.parametrize("generate_support", ["as-needed", "never", "always", "only"])
@pytest.mark.parametrize("omit_serialization", [True, False])
def test_generate_support(
    generate_support: str, omit_serialization: bool, gen_paths: typing.Any, run_nnvg: typing.Callable
) -> None:
    """
    Verifies expected language option defaults can be overridden.
    """
    support_path = gen_paths.out_dir / Path("nunavut") / Path("support")
    test_type_path = gen_paths.out_dir / Path("uavcan") / Path("test")
    support_output = [support_path / Path("serialization").with_suffix(".h")]
    type_output = [test_type_path / Path("TestType_0_8.h")]

    nnvg_args = [
        "-O",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "c",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        f"--generate-support={generate_support}",
    ]

    if omit_serialization:
        nnvg_args.append("--omit-serialization-support")

    nnvg_args.append((gen_paths.dsdl_dir / Path("uavcan")).as_posix())

    # TODO: a more generalized test is needed as the C language doesn't have any language support files
    #       to cover cases where serialization is omitted but language support is not.
    run_nnvg(gen_paths, nnvg_args)
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


def test_issue_73(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verify that https://github.com/OpenCyphal/nunavut/issues/73 hasn't regressed.
    """
    nnvg_args = [
        "-O",
        gen_paths.out_dir.as_posix(),
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-inputs",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")


def test_issue_116(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verify nnvg will infer target language when given only a file extension.
    See https://github.com/OpenCyphal/nunavut/issues/116 for issue that this is a fix
    for.
    """
    expected_output = sorted(
        [
            gen_paths.out_dir / Path("uavcan") / Path("test") / Path("TestType_0_8.h"),
            gen_paths.out_dir / Path("scotec") / Path("Timer_1_0.h"),
        ]
    )

    # Happy path
    nnvg_args = [
        "-O",
        gen_paths.out_dir.as_posix(),
        "-e",
        ".h",
        "-I",
        gen_paths.dsdl_dir / Path("scotec").as_posix(),
        "--list-outputs",
        "--omit-serialization-support",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)

    # Warning path
    nnvg_args = [
        "-O",
        gen_paths.out_dir.as_posix(),
        "-l",
        "blarg",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-outputs",
        "--omit-serialization-support",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    try:
        run_nnvg(gen_paths, nnvg_args, raise_called_process_error=True).stdout.decode("utf-8").split(";")
        pytest.fail("nnvg completed normally when it should have failed to find a template.")
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode("UTF-8")
        assert "language blarg is not a supported language" in error_output


def test_language_allow_unregulated_fixed_portid(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Covers nnvg --allow-unregulated-fixed-port-id switch
    """
    expected_output = [
        gen_paths.out_dir / Path("fixedid") / Path("Timer_1_0.hpp")
    ]

    nnvg_args = [
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "--target-language",
        "cpp",
        "--experimental-languages",
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-outputs",
        "--allow-unregulated-fixed-port-id",
        "--omit-serialization-support",
        (gen_paths.dsdl_dir / Path("fixedid")).as_posix(),
    ]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    completed_wo_empty = sorted([Path(i) for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_list_configuration(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verifies nnvg's --list-configuration option
    """
    import yaml  # pylint: disable=import-outside-toplevel

    nnvg_args = ["--list-configuration"]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
    parsed_config = yaml.load("\n".join(completed), yaml.Loader)
    default_target_section_name = LanguageClassLoader.to_language_module_name(
        LanguageContextBuilder.DEFAULT_TARGET_LANGUAGE
    )
    assert len(parsed_config[default_target_section_name]) > 0
    print(yaml.dump(parsed_config))


def test_support_templates_dir(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Use the --support-templates option to find templates for support generation
    """
    nnvg_args = [
        "--target-language",
        "js",
        "--experimental-languages",
        "--templates",
        gen_paths.templates_dir.as_posix(),
        "--support-templates",
        gen_paths.support_templates_dir.as_posix(),
        "-O",
        gen_paths.out_dir.as_posix(),
        "-I",
        (gen_paths.dsdl_dir / Path("scotec")).as_posix(),
        "--list-inputs",
        (gen_paths.dsdl_dir / Path("uavcan")).as_posix(),
    ]

    run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(";")
