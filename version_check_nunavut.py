#!/usr/bin/env python3
#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
    Helper for getting and comparing the version of Nunavut.
"""

import argparse
import functools
import logging
import pathlib
import sys
import textwrap
import typing


def _make_parser() -> argparse.ArgumentParser:

    script = pathlib.Path(__file__).relative_to(pathlib.Path.cwd())

    epilog = textwrap.dedent(
        f"""

        **Example Usage**::

            {script} --version-only

    """
    )

    parser = argparse.ArgumentParser(
        description="CMake command-line helper for running verification builds.",
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--version-only",
        action="store_true",
        help=textwrap.dedent(
            f"""
        Print out the version number (stored in src/nunavut/_version.py) only and exit. This number
        will be the only output to stdout allowing build scripts to extract this string value for
        use in the build environment. For example:

            export NUNAVUT_FULL_VERSION=$({script} --version-only)

    """[
                1:
            ]
        ),
    )

    parser.add_argument(
        "--major-minor-version-only",
        action="store_true",
        help=textwrap.dedent(
            f"""
        Print out the major and minor version number (stored in src/nunavut/_version.py) only and exit.
        This number will be the only output to stdout allowing build scripts to extract this string
        value for use in the build environment. For example:

            export NUNAVUT_MAJOR_MINOR_VERSION=$({script} --major-minor-version-only)

    """[
                1:
            ]
        ),
    )

    parser.add_argument(
        "--version-check",
        help=textwrap.dedent(
            f"""
        Compares a given semantic version number with the current Nunavut version
        (stored in src/nunavut/_version.py) and returns 0 if it matches else returns 1.

            if $({script} --version-check 1.0.2); then echo "match"; fi

    """[
                1:
            ]
        ),
    )

    parser.add_argument("-v", "--verbose", action="count", default=0, help="Set output verbosity.")

    return parser


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
    args = _make_parser().parse_args()

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

    version_as_string = ".".join(_get_version_string())

    logging.debug(
        "Comparing nunavut version %s to provided version %s (%s)",
        version_as_string,
        args.version_check,
        "matches" if (version_as_string == args.version_check) else "no-match",
    )

    return 0 if (version_as_string == args.version_check) else 1


if __name__ == "__main__":
    sys.exit(main())
