#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Code generator built on top of pydsdl.

Nunavut uses pydsdl to generate text files using templates. While these
text files are often source code this module could also be used to generate
documentation or data interchange formats like JSON or XML.

The input to the nunavut library is a list of templates and a list of
``pydsdl.pydsdl.CompositeType`` objects. The latter is typically obtained
by calling pydsdl::

    from pydsdl import read_namespace

    compound_types = read_namespace(root_namespace, include_paths)

Next a :class:`nunavut.LanguageContext` is needed which is used to
configure all Nunavut objects for a specific target language

    .. code-block:: python

        from nunavut import LanguageContextBuilder

        # Here we are going to generate C headers.
        language_context = LanguageContextBuilder().set_target_language("c").create()

:class:`nunavut.AbstractGenerator` objects require
a :class:`nunavut.Namespace` tree which can be built from the
pydsdl type map using :meth:`nunavut.build_namespace_tree`::

    from nunavut import build_namespace_tree

    root_namespace = build_namespace_tree(compound_types,
                                          root_ns_folder,
                                          out_dir,
                                          language_context)

Putting this all together, the typical use of this library looks something like this::

    from pydsdl import read_namespace
    from nunavut import build_namespace_tree
    from nunavut.lang import LanguageContextBuilder
    from nunavut.jinja import DSDLCodeGenerator

    # parse the dsdl
    compound_types = read_namespace(root_namespace, include_paths)

    # select a target language
    language_context = LanguageContextBuilder().set_target_language("c").create()


    # build the namespace tree
    root_namespace = build_namespace_tree(compound_types,
                                          root_ns_folder,
                                          out_dir,
                                          language_context)

    # give the root namespace to the generator and...
    generator = DSDLCodeGenerator(root_namespace)

    # generate all the code!
    generator.generate_all()

"""
import sys as _sys

from ._generators import AbstractGenerator
from ._generators import generate_types
from ._namespace import Namespace
from ._namespace import build_namespace_tree
from ._utilities import TEMPLATE_SUFFIX
from ._utilities import YesNoDefault
from ._utilities import DefaultValue
from ._version import __author__
from ._version import __copyright__
from ._version import __email__
from ._version import __license__
from ._version import __version__
from .jinja import CodeGenerator
from .jinja import DSDLCodeGenerator
from .jinja import SupportGenerator
from .lang import Language
from .lang import LanguageContext
from .lang import LanguageContextBuilder
from .lang import UnsupportedLanguageError
from .lang._config import LanguageConfig
from ._exceptions import InternalError

if _sys.version_info[:2] < (3, 7):  # pragma: no cover
    print("A newer version of Python is required", file=_sys.stderr)
    _sys.exit(1)

__version_info__ = tuple(map(int, __version__.split(".")[:3]))

__all__ = [
    "AbstractGenerator",
    "build_namespace_tree",
    "CodeGenerator",
    "DSDLCodeGenerator",
    "generate_types",
    "LanguageConfig",
    "DefaultValue",
    "Language",
    "LanguageContext",
    "LanguageContextBuilder",
    "Namespace",
    "SupportGenerator",
    "TEMPLATE_SUFFIX",
    "UnsupportedLanguageError",
    "YesNoDefault",
    "InternalError",
    "__author__",
    "__copyright__",
    "__email__",
    "__license__",
    "__version__",
    "__version_info__",
]
