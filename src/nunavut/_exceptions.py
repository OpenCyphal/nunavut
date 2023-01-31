#
# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2023  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
"""
Exception types thrown by the core library.

"""


class InternalError(RuntimeError):
    """Internal, opaque error within Nunavut.

    This exception is a "should never happen" exception. If caught you've probably hit a bug.
    This is the only exception type within the library that can be use where no unit tests are covering the error
    (i.e. pragma: no cover branches).
    """
