#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Command line script.
"""

import sys

from .cli.runners import main as cli_main


sys.exit(cli_main())
