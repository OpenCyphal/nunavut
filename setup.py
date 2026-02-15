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

setuptools.setup(
    version=version["__version__"],
    package_data=package_data,
    install_requires=[pydsdl_version_specifier],
)
