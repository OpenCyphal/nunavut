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
``pydsdl.CompositeType`` objects. Typical use of this library is simply
invoking the ``nunavut.generate_all`` method.

"""

import sys as _sys
import re as _re

from ._generators import (
    AbstractGenerator,
    basic_language_context_builder_from_args,
    generate_all,
    generate_all_for_language,
    generate_all_from_namespace,
    generate_all_from_namespace_with_generators,
)
from ._namespace import Namespace
from ._utilities import TEMPLATE_SUFFIX, DefaultValue, ResourceSearchPolicy, ResourceType, YesNoDefault
from ._version import __author__, __copyright__, __email__, __license__, __version__
from .jinja import CodeGenerator, DSDLCodeGenerator, SupportGenerator
from .lang import Language, LanguageContext, LanguageContextBuilder, UnsupportedLanguageError
from .lang._config import LanguageConfig

if _sys.version_info[:2] < (3, 10):  # pragma: no cover
    print("Python 3.10 or newer is required", file=_sys.stderr)
    _sys.exit(1)

_version_info_match = _re.match(r"^(\d+)\.(\d+)\.(\d+)", __version__)
if _version_info_match is None:  # pragma: no cover
    raise ValueError(f"Invalid version string: {__version__}")
__version_info__ = tuple(map(int, _version_info_match.groups()))

__all__ = [
    "AbstractGenerator",
    "CodeGenerator",
    "DefaultValue",
    "DSDLCodeGenerator",
    "generate_all",
    "generate_all_for_language",
    "generate_all_from_namespace",
    "generate_all_from_namespace_with_generators",
    "basic_language_context_builder_from_args",
    "Language",
    "LanguageConfig",
    "LanguageContext",
    "LanguageContextBuilder",
    "Namespace",
    "ResourceType",
    "ResourceSearchPolicy",
    "SupportGenerator",
    "TEMPLATE_SUFFIX",
    "UnsupportedLanguageError",
    "YesNoDefault",
    "__author__",
    "__copyright__",
    "__email__",
    "__license__",
    "__version__",
    "__version_info__",
]
