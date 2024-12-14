#!/usr/bin/env python3
#
# Copyright (C) 2018  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#

import sys
from typing import Dict
import re

import setuptools

if int(setuptools.__version__.split(".")[0]) < 30:
    print(
        "A newer version of setuptools is required. The current version does not support declarative config.",
        file=sys.stderr,
    )
    sys.exit(1)

version = {}  # type: Dict
version_file_path = "src/nunavut/_version.py"

with open(version_file_path, encoding="utf-8") as fp:
    exec(fp.read(), version)  # pylint: disable=W0122


specifier_pattern = r"(~=|==|!=|<=|>=|<|>|===)\s*([\w.-]+)"
match = re.search(specifier_pattern, version['__pydsdl_version__'])

if not match:
    raise ValueError(f"Unknown version format for __pydsdl_version__ in {version_file_path}")

pydsdl_version_specifier = f"pydsdl {match.group(1)} {match.group(2)}"
package_data = {"": ["*.j2", "**/*.css", "**/*.js", "*.ini", "*.json", "*.hpp", "*.h"]}

if sys.version_info < (3, 9):
    # For version 3.8 we need to add importlib_resources as a dependency. This seems to blow away the values
    # in setup.cfg so we need to specify them here.
    setuptools.setup(
        version=version["__version__"],
        package_data=package_data,
        install_requires=["importlib_resources", pydsdl_version_specifier],
    )
else:
    # For version 3.9 and later we don't need to add importlib_resources as a dependency.
    setuptools.setup(
        version=version["__version__"],
        package_data=package_data,
        install_requires=[pydsdl_version_specifier],
    )
