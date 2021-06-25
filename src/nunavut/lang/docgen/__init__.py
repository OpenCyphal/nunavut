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
import typing

import pydsdl

from ...templates import template_language_filter, template_language_test
from .. import Language


@template_language_test(__name__)
def is_composite(language: Language, instance: typing.Any) -> bool:
    return isinstance(instance, pydsdl.CompositeType)


@template_language_test(__name__)
def is_array(language: Language, instance: typing.Any) -> bool:
    return isinstance(instance, pydsdl.ArrayType)


@template_language_test(__name__)
def is_service(language: Language, instance: typing.Any) -> bool:
    return isinstance(instance, pydsdl.ServiceType)


@template_language_test(__name__)
def is_service_req(language: Language, instance: typing.Any) -> bool:
    return instance.has_parent_service and instance.full_name.split(".")[-1] == "Request"


@template_language_test(__name__)
def is_field(language: Language, instance: typing.Any) -> bool:
    return isinstance(instance, pydsdl.Field)


@template_language_test(__name__)
def is_deprecated(language: Language, instance: typing.Any) -> bool:
    if isinstance(instance, pydsdl.CompositeType):
        return instance.deprecated
    elif isinstance(instance, pydsdl.ArrayType) and isinstance(instance.element_type, pydsdl.CompositeType):
        return instance.element_type.deprecated
    else:
        return False


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
    return f"../{root_ns}/Namespace.html#{tag_id}"


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
def filter_namespace_doc(language: Language, instance: typing.Any) -> str:
    for t, _ in instance.get_nested_types():
        if t.short_name == "_":
            return t.doc
    return ""


@template_language_filter(__name__)
def filter_display_type(language: Language, instance: typing.Any) -> str:
    if isinstance(instance, pydsdl.FixedLengthArrayType):
        capacity = f'<span style="color: green">[{instance.capacity}]</span>'
        return filter_display_type(language, instance.element_type) + capacity
    elif isinstance(instance, pydsdl.VariableLengthArrayType):
        capacity = f'<span style="color: green">[<={instance.capacity}]</span>'
        return filter_display_type(language, instance.element_type) + capacity
    elif isinstance(instance, pydsdl.PaddingField):
        return f'<span style="color: gray">{instance}</span>'
    elif isinstance(instance, pydsdl.Field):
        return f"{filter_display_type(language, instance.data_type)} {instance.name}"
    elif isinstance(instance, pydsdl.Constant):
        name = f'<span style="color: darkmagenta">{instance.name}</span>'
        value = f'<span style="color: darkcyan">{instance.value}</span>'
        return f"{filter_display_type(language, instance.data_type)} {name} = {value}"
    elif isinstance(instance, pydsdl.PrimitiveType):
        if instance.cast_mode == instance.cast_mode.SATURATED:
            is_saturated = '<span style="color: gray">saturated</span> '
        else:
            is_saturated = '<span style="color: orange">truncated</span> '
        type_name = \
            f'<span style="color: green">{str(instance).split()[-1]}</span>'
        return f"{is_saturated}{type_name}"
    else:
        return str(instance)
