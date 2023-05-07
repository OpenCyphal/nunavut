# Copyright (c) 2019 OpenCyphal
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@opencyphal.org>

import sys
import pytest

if sys.version_info < (3, 8):
    pytest.skip("Python codegen targets a newer version of the language", allow_module_level=True)
