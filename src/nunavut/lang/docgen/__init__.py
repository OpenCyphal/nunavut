#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    Filters for generating docs. All filters in this
    module will be available in the template's global namespace as ``docgen``.
"""

import enum
import functools
import fractions
import re
import typing

import pydsdl

from ...templates import (template_language_filter, template_language_list_filter)
from .. import Language, _UniqueNameGenerator
from .._common import IncludeGenerator

@template_language_filter(__name__)
def filter_is_composite(language: Language, instance: typing.Any) -> bool:
    return isinstance(instance, pydsdl.CompositeType)

@template_language_filter(__name__)
def filter_is_array(language: Language, instance: typing.Any) -> bool:
    return isinstance(instance, pydsdl.ArrayType)

@template_language_filter(__name__)
def filter_is_service(language: Language, instance: typing.Any) -> bool:
    return isinstance(instance, pydsdl.ServiceType)

@template_language_filter(__name__)
def filter_is_field(language: Language, instance: typing.Any) -> bool:
    return isinstance(instance, pydsdl.Field)

@template_language_filter(__name__)
def filter_extent(language: Language, instance: typing.Any) -> str:
    try:
        return instance.bit_length_set.max or 0
    except TypeError:
        print(instance)
        return "unknown"
