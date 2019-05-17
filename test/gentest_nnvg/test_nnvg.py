#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
import pathlib
import subprocess
import pytest

import fixtures
import nunavut.version

@pytest.fixture
def gen_paths():  # type: ignore
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


def test_UAVCAN_DSDL_INCLUDE_PATH(gen_paths: fixtures.GenTestPaths) -> None:
    """
        Verify that UAVCAN_DSDL_INCLUDE_PATH is used by nnvg.
    """

    nnvg_args0 = ['--templates', str(gen_paths.templates_dir),
                  '-O', str(gen_paths.out_dir),
                  '-e', '.json',
                  str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    with pytest.raises(subprocess.CalledProcessError):
        fixtures.run_nnvg(gen_paths, nnvg_args0)

    scotec_path = str(gen_paths.dsdl_dir / pathlib.Path('scotec'))
    herringtec_path = str(gen_paths.dsdl_dir / pathlib.Path('herringtec'))
    env = {'UAVCAN_DSDL_INCLUDE_PATH': '{}:{}'.format(herringtec_path, scotec_path)}
    fixtures.run_nnvg(gen_paths, nnvg_args0, env=env)


def test_nnvg_heals_missing_dot_in_extension(gen_paths: fixtures.GenTestPaths) -> None:
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
    fixtures.run_nnvg(gen_paths, nnvg_args)


def test_list_inputs(gen_paths: fixtures.GenTestPaths) -> None:
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

    completed = fixtures.run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    completed_wo_empty = sorted([i for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_list_inputs_w_namespaces(gen_paths: fixtures.GenTestPaths) -> None:
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

    completed = fixtures.run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    completed_wo_empty = sorted([i for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_list_outputs(gen_paths: fixtures.GenTestPaths) -> None:
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

    completed = fixtures.run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8").split(';')
    completed_wo_empty = sorted([i for i in completed if len(i) > 0])
    assert expected_output == sorted(completed_wo_empty)


def test_version(gen_paths: fixtures.GenTestPaths) -> None:
    """
        Verifies nnvg's --version
    """
    nnvg_args = ['--version']

    completed = fixtures.run_nnvg(gen_paths, nnvg_args).stdout.decode("utf-8")
    structured_string = '.'.join(map(str, nunavut.version.__version__))
    assert structured_string == completed
