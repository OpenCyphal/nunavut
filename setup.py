#!/usr/bin/env python3
#
# Copyright (C) 2018  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#

import sys
from typing import Dict

import setuptools

if int(setuptools.__version__.split(".")[0]) < 30:
    print(
        "A newer version of setuptools is required. The current version does not support declarative config.",
        file=sys.stderr,
    )
    sys.exit(1)

version = {}  # type: Dict
with open("src/nunavut/_version.py", encoding="utf-8") as fp:
    exec(fp.read(), version)  # pylint: disable=W0122

setuptools.setup(
    version=version["__version__"],
    package_data={"": ["*.j2", "**/*.css", "**/*.js", "*.ini", "*.yaml", "*.hpp", "*.h"]},
)
