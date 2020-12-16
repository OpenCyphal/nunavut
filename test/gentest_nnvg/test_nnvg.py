#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
import json
import pathlib
import subprocess
import typing

import pytest

import nunavut.version


def test_UAVCAN_DSDL_INCLUDE_PATH(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        Verify that UAVCAN_DSDL_INCLUDE_PATH is used by nnvg.
    """

    nnvg_args0 = ['--templates', str(gen_paths.templates_dir),
                  '-O', str(gen_paths.out_dir),
                  '-e', '.json',
                  str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    with pytest.raises(subprocess.CalledProcessError):
        run_nnvg(gen_paths, nnvg_args0)

    scotec_path = str(gen_paths.dsdl_dir / pathlib.Path('scotec'))
    herringtec_path = str(gen_paths.dsdl_dir / pathlib.Path('herringtec'))
    env = {'UAVCAN_DSDL_INCLUDE_PATH': '{}:{}'.format(herringtec_path, scotec_path)}
    run_nnvg(gen_paths, nnvg_args0, env=env)


def test_nnvg_heals_missing_dot_in_extension(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        nnvg check for a missing dot in the -e arg and adds it for you. This test
        verifies that logic.
    """
    nnvg_args = ['--templates', str(gen_paths.templates_dir),
                 '-O', str(gen_paths.out_dir),
                 '-e', 'json',
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    # This will fail if the dot isn't added by nnvg
    run_nnvg(gen_paths, nnvg_args)


def test_list_inputs(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        Verifies nnvg's --list-input mode.
    """
    expected_output = sorted([
        str(gen_paths.templates_dir / pathlib.Path('Any.j2')),
        str(gen_paths.dsdl_dir / pathlib.Path('uavcan') / pathlib.Path('test') / pathlib.Path('TestType.0.8.uavcan')),
    ])

    # when #58 is fixed `str(gen_paths.dsdl_dir / pathlib.Path('scotec') / pathlib.Path('Timer.1.0.uavcan'))`
    # should be added to this list.
    nnvg_args = ['--templates', str(gen_paths.templates_dir),
                 '-O', str(gen_paths.out_dir),
                 '-e', '.json',
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 '--list-inputs',
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    completed_wo_empty = sorted([i for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_list_inputs_w_namespaces(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        This covers some extra logic in nnvg when handling list-input with namespaces.
    """
    expected_output = sorted([
        str(gen_paths.templates_dir / pathlib.Path('Any.j2')),
        str(gen_paths.dsdl_dir / pathlib.Path('uavcan') / pathlib.Path('test') / pathlib.Path('TestType.0.8.uavcan')),
        str(gen_paths.dsdl_dir / pathlib.Path('uavcan')),
        str(gen_paths.dsdl_dir / pathlib.Path('uavcan') / pathlib.Path('test'))
    ])

    # when #58 is fixed `str(gen_paths.dsdl_dir / pathlib.Path('scotec') / pathlib.Path('Timer.1.0.uavcan'))`
    # and `str(gen_paths.dsdl_dir / pathlib.Path('scotec')` should be added to this list.
    nnvg_args = ['--templates', str(gen_paths.templates_dir),
                 '-O', str(gen_paths.out_dir),
                 '-e', '.json',
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 '--list-inputs',
                 '--generate-namespace-types',
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    completed_wo_empty = sorted([i for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_list_outputs(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        Verifies nnvg's --list-output mode.
    """
    expected_output = sorted([
        str(gen_paths.out_dir / pathlib.Path('uavcan') / pathlib.Path('test') / pathlib.Path('TestType_0_8.json')),
    ])

    nnvg_args = ['--templates', str(gen_paths.templates_dir),
                 '-O', str(gen_paths.out_dir),
                 '-e', '.json',
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 '--list-outputs',
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    completed_wo_empty = sorted([i for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_version(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        Verifies nnvg's --version
    """
    nnvg_args = ['--version']

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8")
    assert nunavut.version.__version__ == completed


def test_target_language(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        Verifies the behavior when target language support is provided.
    """
    expected_output = sorted([
        str(gen_paths.out_dir / pathlib.Path('uavcan') / pathlib.Path('test') / pathlib.Path('TestType_0_8.hpp')),
    ])

    nnvg_args = ['--templates', str(gen_paths.templates_dir),
                 '-O', str(gen_paths.out_dir),
                 '--target-language', 'cpp',
                 '--experimental-language', 'cpp',
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 '--list-outputs',
                 '--omit-serialization-support',
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    completed_wo_empty = sorted([i for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_language_option_defaults(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        Verifies expected language option defaults are available.
    """

    expected_output = str(gen_paths.out_dir / pathlib.Path('uavcan') / pathlib.Path('test') / pathlib.Path('TestType_0_8.hpp'))

    nnvg_args = ['--templates', str(gen_paths.templates_dir),
                 '-O', str(gen_paths.out_dir),
                 '--target-language', 'cpp',
                 '--experimental-language', 'cpp',
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    with open(expected_output, 'r') as generated:
        generated_results = json.load(generated)
        assert generated_results['target_endianness'] == 'any'
        assert not generated_results['omit_float_serialization_support']
        assert not generated_results['enable_serialization_asserts']


@pytest.mark.parametrize('target_endianness_override', ['any', 'big', 'little'])
def test_language_option_overrides(target_endianness_override: str, gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        Verifies expected language option defaults can be overridden.
    """

    expected_output = str(gen_paths.out_dir / pathlib.Path('uavcan') / pathlib.Path('test') / pathlib.Path('TestType_0_8.hpp'))

    nnvg_args = ['--templates', str(gen_paths.templates_dir),
                 '-O', str(gen_paths.out_dir),
                 '--target-language', 'cpp',
                 '--experimental-language', 'cpp',
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 '--target-endianness', target_endianness_override,
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    with open(expected_output, 'r') as generated:
        generated_results = json.load(generated)
        assert generated_results['target_endianness'] == target_endianness_override


def test_language_option_target_endianness_illegal_option(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        Verifies an illegal --target-endianness option is rejected.
    """

    nnvg_args = ['--templates', str(gen_paths.templates_dir),
                 '-O', str(gen_paths.out_dir),
                 '--target-language', 'cpp',
                 '--experimental-language', 'cpp',
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 '--target-endianness', 'mixed',
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    with pytest.raises(subprocess.CalledProcessError):
        run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')


def test_language_option_omit_floatingpoint(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        Verifies that the --omit-float-serialization-support option is wired up in nnvg.
    """

    expected_output = str(gen_paths.out_dir / pathlib.Path('uavcan') / pathlib.Path('test') / pathlib.Path('TestType_0_8.hpp'))

    nnvg_args = ['--templates', str(gen_paths.templates_dir),
                 '-O', str(gen_paths.out_dir),
                 '--target-language', 'cpp',
                 '--experimental-language', 'cpp',
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 '--omit-float-serialization-support',
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    with open(expected_output, 'r') as generated:
        generated_results = json.load(generated)
        assert generated_results['omit_float_serialization_support']


def test_language_option_generate_asserts(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        Verifies that the --enable-serialization-asserts option is wired up in nnvg.
    """

    expected_output = str(gen_paths.out_dir / pathlib.Path('uavcan') / pathlib.Path('test') / pathlib.Path('TestType_0_8.hpp'))

    nnvg_args = ['--templates', str(gen_paths.templates_dir),
                 '-O', str(gen_paths.out_dir),
                 '--target-language', 'cpp',
                 '--experimental-language', 'cpp',
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 '--enable-serialization-asserts',
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    with open(expected_output, 'r') as generated:
        generated_results = json.load(generated)
        assert generated_results['enable_serialization_asserts']


def test_issue_73(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        Verify that https://github.com/UAVCAN/nunavut/issues/73 hasn't regressed.
    """
    nnvg_args = ['--templates', str(gen_paths.templates_dir),
                 '-O', str(gen_paths.out_dir),
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 '--list-inputs',
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')


def test_issue_116(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
    Verify nnvg will infer target language when given only a file extension.
    See https://github.com/UAVCAN/nunavut/issues/116 for issue that this is a fix
    for.
    """
    expected_output = sorted([
        str(gen_paths.out_dir / pathlib.Path('uavcan') / pathlib.Path('test') / pathlib.Path('TestType_0_8.h')),
    ])

    # Happy path
    nnvg_args = ['-O', str(gen_paths.out_dir),
                 '-e', '.h',
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 '--list-outputs',
                 '--omit-serialization-support',
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    completed_wo_empty = sorted([i for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)

    # Warning path
    nnvg_args = ['-O', str(gen_paths.out_dir),
                 '-e', '.blarg',
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 '--list-outputs',
                 '--omit-serialization-support',
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    try:
        run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
        pytest.fail('nnvg completed normally when it should have failed to find a template.')
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode('UTF-8')
        assert 'No target language was given' in error_output


def test_language_allow_unregulated_fixed_portid(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """
        Covers nnvg --allow-unregulated-fixed-port-id switch
    """
    expected_output = sorted([
        str(gen_paths.out_dir / pathlib.Path('fixedid') / pathlib.Path('Timer_1_0.hpp')),
    ])

    nnvg_args = ['--templates', str(gen_paths.templates_dir),
                 '-O', str(gen_paths.out_dir),
                 '--target-language', 'cpp',
                 '--experimental-language', 'cpp',
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 '--list-outputs',
                 '--allow-unregulated-fixed-port-id',
                 '--omit-serialization-support',
                 str(gen_paths.dsdl_dir / pathlib.Path("fixedid"))]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    completed_wo_empty = sorted([i for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)
