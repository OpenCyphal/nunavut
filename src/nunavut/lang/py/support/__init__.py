#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2021  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
Contains supporting Python routines to distribute with generated types.
"""
import pathlib
import typing
from nunavut._utilities import iter_package_resources

# Re-export support utilities for use in pyuavcan.dsdl
# Need to suppress flake8 warning for these "unused" imports
from .nunavut_support import serialize as serialize # noqa:F401
from .nunavut_support import deserialize as deserialize # noqa:F401

from .nunavut_support import CompositeObject as CompositeObject # noqa:F401
from .nunavut_support import ServiceObject as ServiceObject # noqa:F401

from .nunavut_support import CompositeObjectTypeVar as CompositeObjectTypeVar # noqa:F401

from .nunavut_support import FixedPortObject as FixedPortObject # noqa:F401
from .nunavut_support import FixedPortCompositeObject as FixedPortCompositeObject # noqa:F401
from .nunavut_support import FixedPortServiceObject as FixedPortServiceObject # noqa:F401

from .nunavut_support import get_fixed_port_id as get_fixed_port_id # noqa:F401
from .nunavut_support import get_model as get_model # noqa:F401
from .nunavut_support import get_class as get_class # noqa:F401
from .nunavut_support import get_extent_bytes as get_extent_bytes # noqa:F401

from .nunavut_support import get_attribute as get_attribute # noqa:F401
from .nunavut_support import set_attribute as set_attribute # noqa:F401


__version__ = "1.0.0"
"""Version of the Python support routines."""


def list_support_files() -> typing.Generator[pathlib.Path, None, None]:
    """
    Get a list of Python support routines embedded in this package.

    .. invisible-code-block: python

        from nunavut.lang.py.support import list_support_files
        import pathlib
        support_file_count = 0

    .. code-block:: python

        for path in list_support_files():
            support_file_count += 1
            assert path.parent.stem == 'support'
            assert (path.suffix == '.py' or path.suffix == '.j2')

    .. invisible-code-block: python

        assert support_file_count > 0

    :return: A list of Python support routine resources.
    """
    return iter_package_resources(__name__, ".py", ".j2")
