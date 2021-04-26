#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    Filters for generating docs. All filters in this
    module will be available in the template's global namespace as ``docgen``.
"""

import string
import random
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

@template_language_filter(__name__)
def filter_tag_id(language: Language, instance: typing.Any) -> str:
    if isinstance(instance, pydsdl.ArrayType):
        return f"{str(instance.element_type).replace('.', '_').replace(' ', '_')}_array"
    else:
        return f"{instance.full_name.replace('.', '_')}_{instance.version[0]}_{instance.version[1]}"


@template_language_filter(__name__)
def filter_url_from_type(language: Language, instance: typing.Any) -> str:
    root_ns = instance.root_namespace
    tag_id = f"{instance.full_name.replace('.', '_')}_{instance.version[0]}_{instance.version[1]}"
    return f"/{root_ns}/Namespace.html#{tag_id}"

@template_language_filter(__name__)
def filter_add_uuid(language: Language, instance: typing.Any) -> str:
    return instance + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

@template_language_filter(__name__)
def filter_get_nsdoctype(language: Language, instance: typing.Any) -> str:
    for dsdl_type, _ in instance.get_nested_types():
        if dsdl_type.short_name == "_":
            return dsdl_type
    return None

@template_language_filter(__name__)
def filter_tooltip(language: Language, instance: typing.Any) -> str:
    pass
