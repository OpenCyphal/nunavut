#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
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
                 '-I', str(gen_paths.dsdl_dir / pathlib.Path('scotec')),
                 '--list-outputs',
                 '--omit-serialization-support',
                 str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    completed = run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    completed_wo_empty = sorted([i for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


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
