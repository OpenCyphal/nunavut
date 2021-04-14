#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    Filters for generating C. All filters in this
    module will be available in the template's global namespace as ``c``.
"""

import enum
import functools
import fractions
import re
import typing

import pydsdl

from ...templates import (SupportsTemplateContext, template_context_filter,
                          template_language_filter, template_language_list_filter)
from .. import Language, _UniqueNameGenerator
from .._common import IncludeGenerator

@template_language_filter(__name__)
def filter_idk(language: Language,
               instance: typing.Any) -> str:
    pass
