#!/usr/bin/env python3
#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2021  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    Command-line helper for running verification builds.
"""

import argparse
import logging
import os
import pathlib
import shutil
import subprocess
import sys
import textwrap
import typing


def _make_parser() -> argparse.ArgumentParser:

    epilog = textwrap.dedent('''

        **Example Usage**::

            ./.buildkite/verify.py -l c

    ''')

    parser = argparse.ArgumentParser(
        description='CMake command-line helper for running verification builds.',
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-l', '--language',
                        required=True,
                        help='Value for NUNAVUT_VERIFICATION_LANG')

    parser.add_argument('--build-type',
                        help='Value for CMAKE_BUILD_TYPE')

    parser.add_argument('--endianness',
                        help='Value for NUNAVUT_VERIFICATION_TARGET_ENDIANNESS')

    parser.add_argument('--platform',
                        help='Value for NUNAVUT_VERIFICATION_TARGET_PLATFORM')

    parser.add_argument('--disable-asserts',
                        action='store_true',
                        help='Set NUNAVUT_VERIFICATION_SER_ASSERT=OFF (default is ON)')

    parser.add_argument('--disable-fp',
                        action='store_true',
                        help='Set NUNAVUT_VERIFICATION_SER_FP_DISABLE=ON (default is OFF)')

    parser.add_argument('--enable-ovr-var-array',
                        action='store_true',
                        help='Set NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE=ON (default is OFF)')

    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        help='Set output verbosity.')

    parser.add_argument('-f', '--force',
                        action='store_true',
                        help=textwrap.dedent('''
        Force recreation of verification directory if it already exists.

        ** WARNING ** This will delete the cmake build directory!

    '''[1:]))

    parser.add_argument('-c', '--configure-only',
                        action='store_true',
                        help='Configure but do not build.')

    parser.add_argument('-b', '--build-only',
                        action='store_true',
                        help='Try to build without configuring. Do not try to run tests.')

    parser.add_argument('-t', '--test-only',
                        action='store_true',
                        help='Only try to run tests. Don\'t configure or build.')

    parser.add_argument('-x', '--no-coverage',
                        action='store_true',
                        help='Disables generation of test coverage data. This is enabled by default.')

    parser.add_argument('-j', '--jobs',
                        type=int,
                        help='The number of concurrent build jobs to request. '
                             'Defaults to the number of logical CPUs on the local machine.')

    parser.add_argument('--verification-dir',
                        default='verification',
                        help='Path to the verification directory.')

    parser.add_argument('--use-default-generator',
                        action='store_true',
                        help=textwrap.dedent('''
        We use Ninja by default. Set this flag to omit the explicit generator override
        and use whatever the default is for cmake (i.e. normally make)
    '''[1:]))

    parser.add_argument('--toolchain-family',
                        choices=['gcc', 'clang', 'none'],
                        default='gcc',
                        help=textwrap.dedent('''
        Select the toolchain family to use. Use "none" to get the toolchain
        from the environment (i.e. set CC and CXX environment variables).
                        '''[1:]))

    parser.add_argument('-rm', '--remove-first',
                        action='store_true',
                        help=textwrap.dedent('''
        If specified, any existing build directory will be deleted first. Use
        -f to skip the user prompt.

        Note: This only applies to the configure step. If you do a build-only this
        argument has no effect.
    '''[1:]))

    return parser


def _cmake_run(cmake_args: typing.List[str],
               cmake_dir: pathlib.Path,
               verbose: int,
               env: typing.Optional[typing.Dict] = None) -> int:
    """
    Simple wrapper around cmake execution logic
    """
    logging.debug(
        textwrap.dedent('''

    *****************************************************************
    About to run command: {}
    in directory        : {}
    *****************************************************************

    ''').format(' '.join(cmake_args), str(cmake_dir)))

    copy_of_env: typing.Dict = {}
    copy_of_env.update(os.environ)
    if env is not None:
        copy_of_env.update(env)

    if verbose > 1:
        logging.debug('        *****************************************************************')
        logging.debug('        Using Environment:')
        for key, value in copy_of_env.items():
            overridden = (key in env if env is not None else False)
            logging.debug('            {} = {}{}'.format(key, value, (' (override)' if overridden else '')))
        logging.debug('        *****************************************************************\n')

    return subprocess.run(
        cmake_args,
        cwd=cmake_dir,
        env=copy_of_env
    ).returncode


def _handle_build_dir(args: argparse.Namespace, cmake_dir: pathlib.Path) -> None:
    """
    Handle all the logic, user input, logging, and file-system operations needed to
    manage the cmake build directory ahead of invoking cmake.
    """
    if args.remove_first and cmake_dir.exists():
        okay_to_remove = False
        if not args.force:
            response = input('Are you sure you want to delete {}? [y/N]:'.format(cmake_dir))
            if (len(response) == 1 and response.lower() == 'y') \
                or \
               (len(response) == 3 and response.lower() == 'yes'):
                okay_to_remove = True
        else:
            okay_to_remove = True

        if okay_to_remove:
            logging.info('Removing directory {}'.format(cmake_dir))
            shutil.rmtree(cmake_dir)
        else:
            raise RuntimeError('''
                Build directory {} already exists, -rm or --remove-first was specified,
                and permission was not granted to delete it. We cannot continue. Either
                allow re-use of this build directory or allow deletion. (use -f flag to
                skip user prompts).'''.lstrip().format(cmake_dir))

    if not cmake_dir.exists():
        logging.info('Creating build directory at {}'.format(cmake_dir))
        cmake_dir.mkdir()
    else:
        logging.info('Using existing build directory at {}'.format(cmake_dir))


def _cmake_configure(args: argparse.Namespace, cmake_args: typing.List[str], cmake_dir: pathlib.Path) -> int:
    """
    Format and execute cmake configure command. This also include the cmake build directory (re)creation
    logic.
    """

    if args.build_only or args.test_only:
        return 0

    cmake_logging_level = 'NOTICE'

    if args.verbose == 1:
        cmake_logging_level = 'STATUS'
    elif args.verbose == 2:
        cmake_logging_level = 'VERBOSE'
    elif args.verbose == 3:
        cmake_logging_level = 'DEBUG'
    elif args.verbose > 3:
        cmake_logging_level = 'TRACE'

    _handle_build_dir(args, cmake_dir)

    cmake_configure_args = cmake_args.copy()

    cmake_configure_args.append('--log-level={}'.format(cmake_logging_level))
    cmake_configure_args.append('-DNUNAVUT_VERIFICATION_LANG={}'.format(args.language))

    if args.build_type is not None:
        cmake_configure_args.append('-DCMAKE_BUILD_TYPE={}'.format(args.build_type))

    if args.endianness is not None:
        cmake_configure_args.append('-DNUNAVUT_VERIFICATION_TARGET_ENDIANNESS={}'.format(args.endianness))

    if args.platform is not None:
        cmake_configure_args.append('-DNUNAVUT_VERIFICATION_TARGET_PLATFORM={}'.format(args.platform))

    if args.disable_asserts:
        cmake_configure_args.append('-DNUNAVUT_VERIFICATION_SER_ASSERT:BOOL=OFF')

    if args.disable_fp:
        cmake_configure_args.append('-DNUNAVUT_VERIFICATION_SER_FP_DISABLE:BOOL=ON')

    if args.enable_ovr_var_array:
        cmake_configure_args.append('-NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE:BOOL=ON')

    if args.verbose > 0:
        cmake_configure_args.append('-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON')

    flag_set_dir = pathlib.Path('cmake') / pathlib.Path('compiler_flag_sets')
    if args.no_coverage:
        flagset_file = (flag_set_dir / pathlib.Path('native')).with_suffix('.cmake')
    else:
        flagset_file = (flag_set_dir / pathlib.Path('native_w_cov')).with_suffix('.cmake')

    cmake_configure_args.append('-DNUNAVUT_FLAGSET={}'.format(str(flagset_file)))

    if args.toolchain_family != 'none':
        toolchain_dir = pathlib.Path('cmake') / pathlib.Path('toolchains')
        if args.toolchain_family == 'clang':
            toolchain_file = toolchain_dir / pathlib.Path('clang-native').with_suffix('.cmake')
        else:
            toolchain_file = toolchain_dir / pathlib.Path('gcc-native').with_suffix('.cmake')

        cmake_configure_args.append('-DCMAKE_TOOLCHAIN_FILE={}'.format(str(toolchain_file)))

    if not args.use_default_generator:
        cmake_configure_args.append('-DCMAKE_GENERATOR=Ninja')

    cmake_configure_args.append('..')

    return _cmake_run(cmake_configure_args, cmake_dir, args.verbose)


def _cmake_build(args: argparse.Namespace, cmake_args: typing.List[str], cmake_dir: pathlib.Path) -> int:
    """
    Format and execute cmake build command. This method assumes that the cmake_dir is already properly
    configured.
    """
    if not args.configure_only and not args.test_only:
        cmake_build_args = cmake_args.copy()

        cmake_build_args += ['--build',
                             '.',
                             '--target',
                             'all']

        if args.jobs is not None and args.jobs > 0:
            cmake_build_args += ['--', '-j{}'.format(args.jobs)]

        return _cmake_run(cmake_build_args, cmake_dir, args.verbose)

    return 0


def _cmake_test(args: argparse.Namespace, cmake_args: typing.List[str], cmake_dir: pathlib.Path) -> int:
    """
    Format and execute cmake test command. This method assumes that the cmake_dir is already properly
    configured.
    """
    if not args.configure_only and not args.build_only:
        cmake_test_args = cmake_args.copy()

        cmake_test_args += ['--build',
                            '.',
                            '--target']

        if args.no_coverage:
            cmake_test_args.append('test_all')
        else:
            cmake_test_args.append('cov_all_archive')

        return _cmake_run(cmake_test_args, cmake_dir, args.verbose)

    return 0


def _create_build_dir_name(args: argparse.Namespace) -> str:
    name = 'build_{}'.format(args.language)

    if args.build_type is not None:
        name += '_{}'.format(args.build_type)

    if args.platform is not None:
        name += '_{}'.format(args.platform)

    if args.endianness is not None:
        name += '_{}'.format(args.endianness)

    name += '_{}'.format(args.toolchain_family)

    return name


def main() -> int:
    """
    Main method to execute when this package/script is invoked as a command.
    """
    args = _make_parser().parse_args()

    logging_level = logging.WARN

    if args.verbose == 1:
        logging_level = logging.INFO
    elif args.verbose > 1:
        logging_level = logging.DEBUG

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

    verification_dir = pathlib.Path.cwd() / pathlib.Path(args.verification_dir)
    cmake_dir = verification_dir / pathlib.Path(_create_build_dir_name(args))
    cmake_args = ['cmake']

    configure_result = _cmake_configure(args, cmake_args, cmake_dir)

    if configure_result != 0:
        return configure_result
    elif args.configure_only:
        return 0

    build_result = _cmake_build(args, cmake_args, cmake_dir)

    if build_result != 0:
        return build_result
    elif args.build_only:
        return 0

    if not args.configure_only and not args.build_only:
        return _cmake_test(args, cmake_args, cmake_dir)

    raise RuntimeError('Internal logic error: only_do_x flags resulted in no action.')


if __name__ == "__main__":
    sys.exit(main())
