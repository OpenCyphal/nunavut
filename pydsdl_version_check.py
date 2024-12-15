#!/usr/bin/env python3
#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Verifies that this repo's pydsdl submodule is up to date per the version specifier in the nunavut _version package.
"""

import argparse
import logging
import re
import sys
import textwrap
from pathlib import Path
from typing import Dict

from packaging.specifiers import SpecifierSet
from packaging.version import parse as parse_version


def _make_parser() -> argparse.ArgumentParser:

    epilog = textwrap.dedent(
        f"""

        **Example Usage**::

            ./{Path(__file__).name}

    """
    )

    parser = argparse.ArgumentParser(
        description="Checks version of pydsdl submodule against the version specified in the _version package as "
        "__pydsdl_version__. Returns 0 if the submodule's version is compatible with the Nunavut spec else -1.",
        epilog=epilog,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-p",
        "--path-to-pydsdl-submodule",
        metavar="<folder>",
        type=Path,
        default=Path("submodules", "pydsdl"),
        help="Path to the pydsdl submodule version file.",
    )

    parser.add_argument(
        "-n",
        "--nunavut-version-file",
        metavar="<file>",
        type=Path,
        default=Path("src", "nunavut", "_version.py"),
        help="Path to the version package for nunavut.",
    )

    parser.add_argument("-v", "--verbose", action="count", default=0, help="Set output verbosity.")

    return parser


def _get_required_pydsdl_version(nunavut_version_file: Path) -> SpecifierSet:
    """
    Read the pydsdl version-specifier string from the _version.py file.
    """
    version: Dict[str, str] = {}

    with nunavut_version_file.open("r", encoding="UTF-8") as version_py:
        exec(version_py.read(), version)  # pylint: disable=exec-used

    version_specifier_string = version["__pydsdl_version__"]
    logging.debug(
        "Read pydsdl version specifier from %s: __pydsdl_version__ %s",
        str(nunavut_version_file),
        version_specifier_string,
    )
    specifier_pattern = r"\s*(~=|==|!=|<=|>=|<|>|===)\s*([\w.-]+)\s*"
    match = re.search(specifier_pattern, version_specifier_string)

    if not match:
        raise ValueError(f"Unknown version format for __pydsdl_version__ in {str(nunavut_version_file)}")

    return SpecifierSet(f"{match.group(1)}{match.group(2)}")


def _check_pydsdl_submodule_version(file_path: Path, required_dsdl_version: SpecifierSet) -> bool:
    """
    Make sure the pydsdl submodule version is compatible with the version specification in _version.py
    """
    # Read the file
    with file_path.open("r", encoding="UTF-8") as file:
        content = file.read()

    # Find the version specifier using regex
    specifier_pattern = r"__version__\s*=\s*[\"']([\w.-]+)[\"']"
    match = re.search(specifier_pattern, content)

    if not match:
        raise ValueError("No version specifier found in the file.")

    logging.debug("Scraped version from %s: %s", str(file_path), str(match))

    submodule_dsdl_version = parse_version(match.group(1))

    logging.debug("required pydsdl version: %s", str(required_dsdl_version))
    logging.debug("submodule pydsdl version: %s", str(submodule_dsdl_version))
    return submodule_dsdl_version in required_dsdl_version


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

    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging_level)

    submodule_root = args.path_to_pydsdl_submodule
    submodule_is_correct = _check_pydsdl_submodule_version(
        submodule_root / Path("pydsdl", "__init__.py"), _get_required_pydsdl_version(args.nunavut_version_file)
    )

    if submodule_is_correct:
        logging.debug("Submodule %s is up to date", str(submodule_root))
        return 0

    logging.error("Submodule %s is NOT up to date!", submodule_root)
    return -1


if __name__ == "__main__":
    sys.exit(main())
