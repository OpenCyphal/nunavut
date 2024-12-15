#!/usr/bin/env python3
#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
    Command-line helper for running verification builds.
"""

import argparse
import configparser
import functools
import logging
import os
import pathlib
import shutil
import subprocess
import sys
import textwrap
import typing


def _make_parser() -> argparse.ArgumentParser:

    script = pathlib.Path(__file__).relative_to(pathlib.Path.cwd())

    epilog = textwrap.dedent(
        f"""

        **Example Usage**::

            {script} -l c

    """
    )

    parser = argparse.ArgumentParser(
        description="CMake command-line helper for running verification builds.",
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--override",
        action="append",
        nargs="*",
        help=textwrap.dedent(
            """
        Optional configuration files to provide override values for verification arguments.
        Use this to configure common CI options without creating long CI command lines. Multiple
        overrides can be specified with the order being an ascending priority (i.e. the next override
        will overwrite any previous overrides).

        This file uses the python configparser syntax and expects a single section called 'overrides'.
        See https://docs.python.org/3/library/configparser.html for more information.

        Example ini file:

            [overrides]
            verbose: True
            remove-first: True
            force: True
            endianness: any
            language: cpp
            platform: native32
            toolchain-family: gcc

    """[1:]),
    )

    build_args = parser.add_argument_group(
        title="build options",
        description=textwrap.dedent(
            """
        Arguments that can be used in parallel builds. Each of these will change
        the name of the build directory created for the build.
    """[1:]),
    )

    build_args.add_argument(
        "--version-only",
        action="store_true",
        help=textwrap.dedent(
            f"""
        Print out the version number (stored in src/nunavut/_version.py) only and exit. This number
        will be the only output to stdout allowing build scripts to extract this string value for
        use in the build environment. For example:

            export NUNAVUT_FULL_VERSION=$({script} --version-only)

    """[1:]),
    )

    build_args.add_argument(
        "--major-minor-version-only",
        action="store_true",
        help=textwrap.dedent(
            f"""
        Print out the major and minor version number (stored in src/nunavut/_version.py) only and exit.
        This number will be the only output to stdout allowing build scripts to extract this string
        value for use in the build environment. For example:

            export NUNAVUT_MAJOR_MINOR_VERSION=$({script} --major-minor-version-only)

    """[1:]),
    )

    build_args.add_argument(
        "--version-check-only",
        help=textwrap.dedent(
            f"""
        Compares a given semantic version number with the current Nunavut version
        (stored in src/nunavut/_version.py) and returns 0 if it matches else returns 1.

            if $({script} --version-check-only 1.0.2); then echo "match"; fi

    """[1:]),
    )

    build_args.add_argument("-l", "--language", default="c", help="Value for NUNAVUT_VERIFICATION_LANG (defaults to c)")

    build_args.add_argument("-std", "--language-standard", default="", help="Language standard")

    build_args.add_argument("--build-type", help="Value for CMAKE_BUILD_TYPE")

    build_args.add_argument("--endianness", help="Value for NUNAVUT_VERIFICATION_TARGET_ENDIANNESS")

    build_args.add_argument("--platform", help="Value for NUNAVUT_VERIFICATION_TARGET_PLATFORM")

    build_args.add_argument(
        "--disable-asserts", action="store_true", help="Set NUNAVUT_VERIFICATION_SER_ASSERT=OFF (default is ON)"
    )

    build_args.add_argument(
        "--disable-fp", action="store_true", help="Set NUNAVUT_VERIFICATION_SER_FP_DISABLE=ON (default is OFF)"
    )

    build_args.add_argument(
        "--enable-ovr-var-array",
        action="store_true",
        help="Set NUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE=ON (default is OFF)",
    )

    build_args.add_argument(
        "--toolchain-family",
        choices=["gcc", "clang", "none"],
        default="gcc",
        help=textwrap.dedent(
            """
        Select the toolchain family to use. Use "none" to get the toolchain
        from the environment (i.e. set CC and CXX environment variables).
                        """[1:]),
    )

    build_args.add_argument(
        "--none",
        action="store_true",
        help=textwrap.dedent(
            """
        Dummy argument used to support matrix builds where an argument present
        in other builds is not provided in the current build.
            """[1:]),
    )

    action_args = parser.add_argument_group(
        title="behavioral options",
        description=textwrap.dedent(
            """
        Arguments that change the actions taken by the build.
    """[1:]),
    )

    action_args.add_argument("-v", "--verbose", action="count", default=0, help="Set output verbosity.")

    action_args.add_argument(
        "-f",
        "--force",
        action="store_true",
        help=textwrap.dedent(
            """
        Force recreation of verification directory if it already exists.

        ** WARNING ** This will delete the cmake build directory!

    """[1:]),
    )

    action_args.add_argument("-c", "--configure-only", action="store_true", help="Configure but do not build.")

    action_args.add_argument(
        "-b", "--build-only", action="store_true", help="Try to build without configuring. Do not try to run tests."
    )

    action_args.add_argument(
        "-t", "--test-only", action="store_true", help="Only try to run tests. Don't configure or build."
    )

    action_args.add_argument(
        "--dry-run",
        action="store_true",
        help=textwrap.dedent(
            """
        Don't actually do anything. Just log what this script would have done.
        Combine with --verbose to ensure you actually see the script's log output.
    """[1:]),
    )

    action_args.add_argument(
        "-x",
        "--no-coverage",
        action="store_true",
        help="Deprecated. Use compiler_flag_set instead.",
    )

    action_args.add_argument(
        "-cfs",
        "--compiler-flag-set",
        default="native",
        type=pathlib.Path,
        help=textwrap.dedent(
            """
        Select the compiler flag set to use. This will select the appropriate compiler flags
        for the build. The default is 'native' which is the default compiler flags for the
        build environment. Use 'native_w_cov' to enable coverage flags.
        See cmake/compiler_flag_sets for available options.
    """[1:]),
    )

    action_args.add_argument(
        "-rm",
        "--remove-first",
        action="store_true",
        help=textwrap.dedent(
            """
        If specified, any existing build directory will be deleted first. Use
        -f to skip the user prompt.

        Note: This only applies to the configure step. If you do a build-only this
        argument has no effect.
    """[1:]),
    )

    other_options = parser.add_argument_group(
        title="extra build options",
        description=textwrap.dedent(
            """
        Additional arguments for modifying how the build runs but which are used less frequently.
    """[1:]),
    )

    other_options.add_argument(
        "-j",
        "--jobs",
        type=int,
        help="The number of concurrent build jobs to request. "
        "Defaults to the number of logical CPUs on the local machine.",
    )

    other_options.add_argument("--verification-dir", default="verification", help="Path to the verification directory.")

    other_options.add_argument(
        "--use-default-generator",
        action="store_true",
        help=textwrap.dedent(
            """
        We use Ninja by default. Set this flag to omit the explicit generator override
        and use whatever the default is for cmake (i.e. normally make)
    """[1:]),
    )

    return parser


def _apply_overrides(args: argparse.Namespace) -> argparse.Namespace:
    if args.override is None:
        return args

    for override_list in args.override:
        for override in override_list:
            if not pathlib.Path(override).exists():
                raise RuntimeError(f'ini file "{override}" does not exist.')
            print(
                textwrap.dedent(
                    f"""
            *****************************************************************
            About to apply override file : {override}
            *****************************************************************
            """
                )
            )

            overrides = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
            overrides.read(override)
            if "overrides" not in overrides:
                raise RuntimeError(f'ini file "{override}" did not contain an overrides section.')
            for key, value in overrides["overrides"].items():
                corrected_key = key.replace("-", "_")
                if value.lower() == "true" or value.lower() == "false":
                    setattr(args, corrected_key, bool(value))
                else:
                    try:
                        setattr(args, corrected_key, int(value))
                    except ValueError:
                        setattr(args, corrected_key, value)

    return args


def _cmake_run(
    cmake_args: typing.List[str],
    cmake_dir: pathlib.Path,
    verbose: int,
    dry_run: bool,
    env: typing.Optional[typing.Dict] = None,
) -> int:
    """
    Simple wrapper around cmake execution logic
    """
    logging.debug(
        textwrap.dedent(
            """

    *****************************************************************
    About to run command: {}
    in directory        : {}
    *****************************************************************

    """
        ).format(" ".join(cmake_args), str(cmake_dir))
    )

    copy_of_env: typing.Dict = {}
    copy_of_env.update(os.environ)
    if env is not None:
        copy_of_env.update(env)

    if verbose > 1:
        logging.debug("        *****************************************************************")
        logging.debug("        Using Environment:")
        for key, value in copy_of_env.items():
            overridden = key in env if env is not None else False
            logging.debug("            %s = %s%s", key, value, (" (override)" if overridden else ""))
        logging.debug("        *****************************************************************\n")

    if not dry_run:
        return subprocess.run(cmake_args, cwd=cmake_dir, env=copy_of_env, check=True).returncode
    else:
        return 0


def _handle_build_dir(args: argparse.Namespace, cmake_dir: pathlib.Path) -> None:
    """
    Handle all the logic, user input, logging, and file-system operations needed to
    manage the cmake build directory ahead of invoking cmake.
    """
    if args.remove_first and cmake_dir.exists():
        okay_to_remove = False
        if not args.force:
            response = input(f"Are you sure you want to delete {cmake_dir}? [y/N]:")
            if (len(response) == 1 and response.lower() == "y") or (len(response) == 3 and response.lower() == "yes"):
                okay_to_remove = True
        else:
            okay_to_remove = True

        if okay_to_remove:
            if not args.dry_run:
                logging.info("Removing directory %s", cmake_dir)
                shutil.rmtree(cmake_dir)
            else:
                logging.info("Is dry-run. Would have removed directory %s", cmake_dir)
        else:
            raise RuntimeError(
                """
                Build directory {} already exists, -rm or --remove-first was specified,
                and permission was not granted to delete it. We cannot continue. Either
                allow re-use of this build directory or allow deletion. (use -f flag to
                skip user prompts).""".lstrip().format(
                    cmake_dir
                )
            )

    if not cmake_dir.exists():
        if not args.dry_run:
            logging.info("Creating build directory at %s", cmake_dir)
            cmake_dir.mkdir()
        else:
            logging.info("Dry run: Would have created build directory at %s", cmake_dir)
    else:
        logging.info("Using existing build directory at %s", cmake_dir)


def _cmake_configure(args: argparse.Namespace, cmake_args: typing.List[str], cmake_dir: pathlib.Path) -> int:
    """
    Format and execute cmake configure command. This also include the cmake build directory (re)creation
    logic.
    """

    if args.build_only or args.test_only:
        return 0

    cmake_logging_level = "NOTICE"

    if args.verbose == 1:
        cmake_logging_level = "STATUS"
    elif args.verbose == 2:
        cmake_logging_level = "VERBOSE"
    elif args.verbose == 3:
        cmake_logging_level = "DEBUG"
    elif args.verbose > 3:
        cmake_logging_level = "TRACE"

    _handle_build_dir(args, cmake_dir)

    cmake_configure_args = cmake_args.copy()

    cmake_configure_args.append(f"--log-level={cmake_logging_level}")
    cmake_configure_args.append(f"-DNUNAVUT_VERIFICATION_LANG={args.language}")

    if args.language_standard is not None:
        cmake_configure_args.append(f"-DNUNAVUT_VERIFICATION_LANG_STANDARD={args.language_standard}")

    if args.build_type is not None:
        cmake_configure_args.append(f"-DCMAKE_BUILD_TYPE={args.build_type}")

    if args.endianness is not None:
        cmake_configure_args.append(f"-DNUNAVUT_VERIFICATION_TARGET_ENDIANNESS={args.endianness}")

    if args.platform is not None:
        cmake_configure_args.append(f"-DNUNAVUT_VERIFICATION_TARGET_PLATFORM={args.platform}")

    if args.disable_asserts:
        cmake_configure_args.append("-DNUNAVUT_VERIFICATION_SER_ASSERT:BOOL=OFF")

    if args.disable_fp:
        cmake_configure_args.append("-DNUNAVUT_VERIFICATION_SER_FP_DISABLE:BOOL=ON")

    if args.enable_ovr_var_array:
        cmake_configure_args.append("-DNUNAVUT_VERIFICATION_OVR_VAR_ARRAY_ENABLE:BOOL=ON")

    if args.verbose > 0:
        cmake_configure_args.append("-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON")

    flag_set_dir = pathlib.Path("cmake") / pathlib.Path("compiler_flag_sets")
    flagset_file = (flag_set_dir / args.compiler_flag_set).with_suffix(".cmake")
    compiler_flag_set = (pathlib.Path(args.verification_dir) / flagset_file).resolve()
    if not compiler_flag_set.exists():
        raise RuntimeError(
            f"Compiler flag set file {str(compiler_flag_set)} does not exist in the verification directory."
        )

    cmake_configure_args.append(f"-DNUNAVUT_FLAGSET={str(compiler_flag_set)}")

    if args.toolchain_family != "none":
        toolchain_dir = pathlib.Path("cmake") / pathlib.Path("toolchains")
        if args.toolchain_family == "clang":
            toolchain_file = toolchain_dir / pathlib.Path("clang-native").with_suffix(".cmake")
        else:
            toolchain_file = toolchain_dir / pathlib.Path("gcc-native").with_suffix(".cmake")

        cmake_configure_args.append(f"-DCMAKE_TOOLCHAIN_FILE={str(toolchain_file)}")

    if not args.use_default_generator:
        cmake_configure_args.append("-DCMAKE_GENERATOR=Ninja")

    cmake_configure_args.append("..")

    return _cmake_run(cmake_configure_args, cmake_dir, args.verbose, args.dry_run)


def _cmake_build(args: argparse.Namespace, cmake_args: typing.List[str], cmake_dir: pathlib.Path) -> int:
    """
    Format and execute cmake build command. This method assumes that the cmake_dir is already properly
    configured.
    """
    if not args.configure_only and not args.test_only:
        cmake_build_args = cmake_args.copy()

        cmake_build_args += ["--build", ".", "--target", "all"]

        if args.jobs is not None and args.jobs > 0:
            cmake_build_args += ["--", f"-j{args.jobs}"]

        return _cmake_run(cmake_build_args, cmake_dir, args.verbose, args.dry_run)

    return 0


def _cmake_test(args: argparse.Namespace, cmake_args: typing.List[str], cmake_dir: pathlib.Path) -> int:
    """
    Format and execute cmake test command. This method assumes that the cmake_dir is already properly
    configured.
    """
    if not args.configure_only and not args.build_only:
        cmake_test_args = cmake_args.copy()

        cmake_test_args += ["--build", ".", "--target"]

        if args.compiler_flag_set.stem == "native_w_cov":
            cmake_test_args.append("cov_all_archive")
        else:
            cmake_test_args.append("test_all")

        return _cmake_run(cmake_test_args, cmake_dir, args.verbose, args.dry_run)

    return 0


def _create_build_dir_name(args: argparse.Namespace) -> str:
    name = f"build_{args.language}"

    if args.language_standard is not None:
        name += f"_{args.language_standard}"

    name += f"_{args.toolchain_family}"

    if args.platform is not None:
        name += f"_{args.platform}"

    if args.build_type is not None:
        name += f"_{args.build_type}"

    if args.endianness is not None:
        name += f"_{args.endianness}"

    if args.disable_asserts:
        name += "_noassert"

    if args.disable_fp:
        name += "_nofp"

    if args.enable_ovr_var_array:
        name += "_wovervararray"

    return name


@functools.lru_cache(maxsize=None)
def _get_version_string() -> typing.Tuple[str, str, str, str]:
    version: typing.Dict[str, str] = {}
    nunavut_version_file = pathlib.Path("src/nunavut/_version.py")

    with nunavut_version_file.open("r", encoding="UTF-8") as version_py:
        exec(version_py.read(), version)  # pylint: disable=exec-used

    version_string = version["__version__"]
    version_array = version_string.split(".")
    if len(version_array) not in (3, 4):
        raise RuntimeError(f"Invalid version string: {version_string}")
    if len(version_array) == 3:
        return (version_array[0], version_array[1], version_array[2], "")
    else:
        return (version_array[0], version_array[1], version_array[2], version_array[3])


def main() -> int:
    """
    Main method to execute when this package/script is invoked as a command.
    """
    args = _apply_overrides(_make_parser().parse_args())

    if args.version_only:
        sys.stdout.write(".".join(_get_version_string()))
        sys.stdout.flush()
        return 0

    if args.major_minor_version_only:
        version = _get_version_string()
        sys.stdout.write(f"{version[0]}.{version[1]}")
        sys.stdout.flush()
        return 0

    logging_level = logging.WARN

    if args.verbose == 1:
        logging_level = logging.INFO
    elif args.verbose > 1:
        logging_level = logging.DEBUG

    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging_level)

    if args.version_check_only is not None:
        version_as_string = ".".join(_get_version_string())
        logging.debug(
            "Comparing nunavut version %s to provided version %s (%s)",
                version_as_string,
                args.version_check_only,
                "matches" if (version_as_string == args.version_check_only) else "no-match")
        return 0 if (version_as_string == args.version_check_only) else 1

    logging.debug(
        textwrap.dedent(
            """

    *****************************************************************
    Commandline Arguments to {}:

    {}

    For Nunavut version {}
    *****************************************************************

    """
        ).format(os.path.basename(__file__), str(args), _get_version_string())
    )

    verification_dir = pathlib.Path.cwd() / pathlib.Path(args.verification_dir)
    cmake_dir = verification_dir / pathlib.Path(_create_build_dir_name(args))
    cmake_args = ["cmake"]

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

    raise RuntimeError("Internal logic error: only_do_x flags resulted in no action.")


if __name__ == "__main__":
    sys.exit(main())
