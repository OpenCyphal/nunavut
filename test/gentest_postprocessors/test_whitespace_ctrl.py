
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
import pathlib
import typing


def get_path_to_TestType_0_2(gen_paths: typing.Any) -> pathlib.Path:
    uavcan_dir = pathlib.Path(gen_paths.out_dir / pathlib.Path('uavcan'))
    return uavcan_dir / pathlib.Path('test') / pathlib.Path('TestType_0_2').with_suffix('.json')


def test_no_trim_blocks(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """ Ensure trim-blocks is False if --trim-blocks is not supplied.
    """

    testtype_path = get_path_to_TestType_0_2(gen_paths)
    nnvg_args0 = ['--templates', str(gen_paths.templates_dir),
                  '-O', str(gen_paths.out_dir),
                  '-e', '.json',
                  '-l', 'js',
                  '-Xlang',
                  str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    run_nnvg(gen_paths, nnvg_args0)

    with open(str(testtype_path), 'r') as testtype_file:
        lines = testtype_file.readlines()

    assert 98 == len(lines)


def test_trim_blocks(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """ Ensure the --trim-blocks switch is hooked up and functional.
    """

    testtype_path = get_path_to_TestType_0_2(gen_paths)
    nnvg_args0 = ['--templates', str(gen_paths.templates_dir),
                  '-O', str(gen_paths.out_dir),
                  '-e', '.json',
                  '-l', 'js',
                  '-Xlang',
                  '--trim-blocks',
                  str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    run_nnvg(gen_paths, nnvg_args0)

    with open(str(testtype_path), 'r') as testtype_file:
        lines = testtype_file.readlines()

    assert 7 == len(lines)


def test_no_lstrip_blocks(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """ Ensure that lstrip_blocks if false if --lstrip-blocks is not supplied.
    """

    testtype_path = get_path_to_TestType_0_2(gen_paths)
    nnvg_args0 = ['--templates', str(gen_paths.templates_dir),
                  '-O', str(gen_paths.out_dir),
                  '-e', '.json',
                  '-l', 'js',
                  '-Xlang',
                  str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    run_nnvg(gen_paths, nnvg_args0)

    with open(str(testtype_path), 'r') as testtype_file:
        lines = testtype_file.readlines()

    assert "     \n" == lines[2]


def test_lstrip_blocks(gen_paths: typing.Any, run_nnvg: typing.Callable) -> None:
    """ Ensure the --lstrip-blocks switch is hooked up and functional.
    """

    testtype_path = get_path_to_TestType_0_2(gen_paths)
    nnvg_args0 = ['--templates', str(gen_paths.templates_dir),
                  '-O', str(gen_paths.out_dir),
                  '-e', '.json',
                  '-l', 'js',
                  '-Xlang',
                  '--lstrip-blocks',
                  str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    run_nnvg(gen_paths, nnvg_args0)

    with open(str(testtype_path), 'r') as testtype_file:
        lines = testtype_file.readlines()

    assert "\n" == lines[2]
