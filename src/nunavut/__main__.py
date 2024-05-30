#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
    Command-line entrypoint.
"""

import sys

from .cli import main

sys.exit(main())
