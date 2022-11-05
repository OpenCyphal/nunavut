#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    Filters for generating docs. All filters in this
    module will be available in the template's global namespace as ``ln.html``.
"""

import html
import logging
import re
import typing

import pydsdl

import nunavut
from nunavut._templates import template_volatile_filter
from nunavut.jinja.jinja2 import TemplateAssertionError
from nunavut.lang._common import UniqueNameGenerator

logger = logging.getLogger(__name__)


def filter_extent(instance: pydsdl.Any) -> int:
    try:
        return instance.extent or 0
    except TypeError as e:
        raise TemplateAssertionError(e)


def filter_max_bit_length(instance: pydsdl.Any) -> int:
    try:
        return instance.bit_length_set.max or 0
    except TypeError as e:
        raise TemplateAssertionError(e)


def filter_tag_id(instance: pydsdl.Any) -> str:
    if isinstance(instance, pydsdl.ArrayType):
        return "{}_array".format(str(instance.element_type).replace(".", "_").replace(" ", "_"))
    else:
        return "{}_{}_{}".format(
            instance.full_name.replace(".", "_"),
            instance.version[0],
            instance.version[1],
        )


def filter_url_from_type(instance: pydsdl.Any) -> str:
    root_ns = instance.root_namespace
    tag_id = "{}_{}_{}".format(instance.full_name.replace(".", "_"), instance.version[0], instance.version[1])
    return "../{}/#{}".format(root_ns, tag_id)


@template_volatile_filter
def filter_make_unique(_: typing.Any, base_token: str) -> str:
    """
    Filter that takes a base token and forms a name that is very
    likely to be unique within the template the filter is invoked.

    .. IMPORTANT::

        The exact tokens generated may change between major or minor versions
        of this library. The only guarantee provided is that the tokens
        will be stable for the same version of this library given the same
        input.

        Also note that name uniqueness is only likely within a given template.
        Between templates there is no guarantee of uniqueness and,
        since this library does not lex generated source, there is no guarantee
        that the generated name does not conflict with a name generated by
        another means.

    .. invisible-code-block: python

        from nunavut.lang.html import filter_make_unique
        from nunavut.lang._common import UniqueNameGenerator

    .. code-block:: python

        # Given
        template  = '{{ "foo" | make_unique }},{{ "Foo" | make_unique }},'
        template += '{{ "fOO" | make_unique }}'

        # then
        rendered = 'foo0,foo1,fOO0'

    .. invisible-code-block: python

        UniqueNameGenerator.reset()
        jinja_filter_tester(filter_make_unique, template, rendered, 'html')

    .. code-block:: python

        # Given
        template = '{{ "coffee > tea" | make_unique }}'

        # then
        rendered = 'coffee &gt; tea0'

    .. invisible-code-block: python

        UniqueNameGenerator.reset()
        jinja_filter_tester(filter_make_unique, template, rendered, 'html')


    :param str base_token: A token to include in the base name.
    :return: A name that is likely to be unique within the file generated by the current
             template.
    """
    if len(base_token) > 0:
        adj_base_token = base_token[0:1].lower() + base_token[1:]
    else:
        adj_base_token = base_token

    escaped_base_token = html.escape(adj_base_token)

    return UniqueNameGenerator.get_instance()("html", escaped_base_token, "", "")


def filter_namespace_doc(ns: nunavut.Namespace) -> str:
    result = ""
    for t, _ in ns.get_nested_types():
        if t.short_name == "_":
            result = t.doc
            break
    return result


def filter_display_type(instance: pydsdl.Any) -> str:
    # TODO: this whole thing needs to be in the template.
    if isinstance(instance, pydsdl.FixedLengthArrayType):
        capacity = '<span style="color: green">[{}]</span>'.format(instance.capacity)
        return filter_display_type(instance.element_type) + capacity
    elif isinstance(instance, pydsdl.VariableLengthArrayType):
        capacity = '<span style="color: green">[<={}]</span>'.format(instance.capacity)
        return filter_display_type(instance.element_type) + capacity
    elif isinstance(instance, pydsdl.PaddingField):
        return '<span style="color: gray">{}</span>'.format(instance)
    elif isinstance(instance, pydsdl.Field):
        return "{} {}".format(filter_display_type(instance.data_type), instance.name)
    elif isinstance(instance, pydsdl.Constant):
        name = '<span style="color: darkmagenta">{}</span>'.format(instance.name)
        value = '<span style="color: darkcyan">{}</span>'.format(instance.value)
        return "{} {} = {}".format(filter_display_type(instance.data_type), name, value)
    elif isinstance(instance, pydsdl.PrimitiveType):
        if instance.cast_mode == instance.cast_mode.SATURATED:
            is_saturated = '<span style="color: gray">saturated</span> '
        else:
            is_saturated = '<span style="color: orange">truncated</span> '
        type_name = '<span style="color: green">{}</span>'.format(str(instance).split()[-1])
        return "{}{}".format(is_saturated, type_name)
    else:
        return str(instance)


def _natural_sort(instance: typing.List[pydsdl.Any], key: typing.Callable = lambda s: s) -> typing.List[pydsdl.Any]:
    def natural_sort_key(s: str, _nsre: typing.Pattern = re.compile("([0-9]+)")) -> typing.List[pydsdl.Any]:
        _key = key(s)

        return [int(text) if text.isdigit() else text.lower() for text in _nsre.split(_key)]

    return sorted(instance, key=natural_sort_key)


def filter_natural_sort_namespace(instance: typing.List[pydsdl.Any]) -> typing.List[pydsdl.Any]:
    """
    Namespaces come in plain lists; sort by name only.
    """
    return _natural_sort(instance, key=lambda s: s.full_name)


def filter_natural_sort_type(instance: pydsdl.Any) -> typing.List[pydsdl.Any]:
    """
    Types come in tuples (type, path). Sort by type name.
    """
    return _natural_sort(instance, key=lambda s: s[0].full_name)
