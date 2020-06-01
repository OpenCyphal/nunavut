#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    Filters for generating C++. All filters in this
    module will be available in the template's global namespace as ``cpp``.
"""

import functools
import io
import math
import re
import typing

import pydsdl

from .. import Language, _UniqueNameGenerator
from .._common import IncludeGenerator
from ...templates import (template_language_filter,
                          template_language_list_filter)
from ..c import C_RESERVED_PATTERNS, VariableNameEncoder, _CFit

CPP_RESERVED_PATTERNS = frozenset([*C_RESERVED_PATTERNS])

CPP_NO_DOUBLE_DASH_RULE = re.compile(r'(__)')


@template_language_filter(__name__)
def filter_id(language: Language,
              instance: typing.Any) -> str:
    """
    Filter that produces a valid C and/or C++ identifier for a given object. The encoding may not
    be reversable.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_id


    .. code-block:: python

        # Given
        I = 'I like c++'

        # and
        template = '{{ I | id }}'

        # then
        rendered = 'I_like_cZX002BZX002B'


    .. invisible-code-block: python

        jinja_filter_tester(filter_id, template, rendered, 'cpp', I=I)


    .. code-block:: python

        # Given
        I = 'if'

        # and
        template = '{{ I | id }}'

        # then
        rendered = '_if'


    .. invisible-code-block: python

        jinja_filter_tester(filter_id, template, rendered, 'cpp', I=I)


    .. code-block:: python

        # Given
        I = '_Reserved'

        # and
        template = '{{ I | id }}'

        # then
        rendered = '_reserved'

    .. invisible-code-block: python

        jinja_filter_tester(filter_id, template, rendered, 'cpp', I=I)

    :param any instance:        Any object or data that either has a name property or can be converted
                                to a string.
    :returns: A token that is a valid identifier for C and C++, is not a reserved keyword, and is transformed
              in a deterministic manner based on the provided instance.
    """
    if hasattr(instance, 'name'):
        raw_name = str(instance.name)  # type: str
    else:
        raw_name = str(instance)

    vne = VariableNameEncoder(language.stropping_prefix, language.stropping_suffix, language.encoding_prefix)
    reserved_identifiers = frozenset(language.get_reserved_identifiers())
    out = vne.strop(raw_name,
                    reserved_identifiers,
                    CPP_RESERVED_PATTERNS)
    return CPP_NO_DOUBLE_DASH_RULE.sub('_' + vne.encode_character('_'), out)


@template_language_filter(__name__)
def filter_open_namespace(language: Language,
                          full_namespace: str,
                          bracket_on_next_line: bool = True,
                          linesep: str = '\n') -> str:
    """
    Emits c++ opening namspace syntax parsed from a pydsdl "full_namespace",
    dot-seperated  value.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_open_namespace
        T = lambda : None;
        setattr(T, 'full_namespace)', '')

    .. code-block:: python

        # Given
        T.full_namespace = 'uavcan.foo'

        # and
        template = '{{ T.full_namespace | open_namespace }}'

        # then
        rendered = '''namespace uavcan
        {
        namespace foo
        {
        '''

    .. invisible-code-block: python

        jinja_filter_tester(filter_open_namespace, template, rendered, 'cpp', T=T)

    :param str full_namespace: A dot-seperated namespace string.
    :param bool bracket_on_next_line: If True (the default) then the opening
        brackets are placed on a newline after the namespace keyword.
    :param str linesep: The line-seperator to use when emitting new lines.
                        By default this is ``\\n``.

    :returns: C++ namespace declarations with opening brackets.
    """

    with io.StringIO() as content:
        for name in full_namespace.split('.'):
            content.write('namespace ')
            if language.enable_stropping:
                content.write(filter_id(language, name))
            else:
                content.write(name)
            if bracket_on_next_line:
                content.write(linesep)
            else:
                content.write(' ')
            content.write('{')
            content.write(linesep)
        return content.getvalue()


@template_language_filter(__name__)
def filter_close_namespace(language: Language,
                           full_namespace: str,
                           omit_comments: bool = False,
                           linesep: str = '\n') -> str:
    """
    Emits c++ closing namspace syntax parsed from a pydsdl "full_namespace",
    dot-seperated  value.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_close_namespace
        T = lambda : None;
        setattr(T, 'full_namespace)', '')

    .. code-block:: python

        # Given
        T.full_namespace = 'uavcan.foo'

        # and
        template = '{{ T.full_namespace | close_namespace }}'

        # then
        rendered = '''} // namespace foo
        } // namespace uavcan
        '''

    .. invisible-code-block: python

        jinja_filter_tester(filter_close_namespace, template, rendered, 'cpp', T=T)


    :param str full_namespace: A dot-seperated namespace string.
    :param bool omit_comments: If True then the comments following the closing
                               bracket are omitted.
    :param str linesep: The line-seperator to use when emitting new lines.
                        By default this is ``\\n``

    :returns: C++ namespace declarations with opening brackets.
    """
    with io.StringIO() as content:
        for name in reversed(full_namespace.split('.')):
            content.write('}')
            if not omit_comments:
                content.write(' // namespace ')
                if language.enable_stropping:
                    content.write(filter_id(language, name))
                else:
                    content.write(name)
            content.write(linesep)
        return content.getvalue()


@template_language_filter(__name__)
def filter_full_reference_name(language: Language, t: pydsdl.CompositeType) -> str:
    """
    Provides a string that is the full namespace, typename, major, and minor version for a given composite type.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_full_reference_name
        from unittest.mock import MagicMock
        import pydsdl

        my_obj = MagicMock()
        my_obj.parent_service = None
        my_obj.version = MagicMock()

    .. code-block:: python

        # Given a type with illegal characters for C++
        my_obj.full_name = 'any.int.2Foo'
        my_obj.version.major = 1
        my_obj.version.minor = 2

        # and
        template = '{{ my_obj | full_reference_name }}'

        # then, with stropping enabled
        rendered = 'any::_int::_2Foo_1_2'

    .. invisible-code-block: python

        my_obj.short_name = my_obj.full_name.split('.')[-1]
        jinja_filter_tester(filter_full_reference_name, template, rendered, 'cpp', my_obj=my_obj)

        my_obj = MagicMock()
        my_obj.version = MagicMock()
        my_obj.parent_service = None

    .. invisible-code-block: python

        my_obj = MagicMock(spec=pydsdl.CompositeType)
        my_obj.version = MagicMock()
        my_service = MagicMock(spec=pydsdl.ServiceType)
        my_service.parent_service = None
        my_service.version = MagicMock()
        my_service.attributes = { 'Request': my_obj }
        my_obj.parent_service = my_service

    Note that for service types

    .. code-block:: python

        # Given a service type
        my_service.full_name = 'my.Service'
        my_service.version.major = 1
        my_service.version.minor = 8

        # and
        template = '{{ my_service.attributes["Request"] | full_reference_name }}'

        # then
        rendered = 'my::Service_1_8::Request'

    .. invisible-code-block: python

        my_service.short_name = my_service.full_name.split('.')[-1]
        my_obj.short_name = 'Request'
        my_obj.full_name = my_service.full_name + '.' + my_obj.short_name

        jinja_filter_tester(filter_full_reference_name, template, rendered, 'cpp', my_service=my_service)

    :param pydsdl.CompositeType t: The DSDL type to get the fully-resolved reference name for.
    """
    ns_parts = t.full_name.split('.')
    if language.enable_stropping:
        ns = list(map(functools.partial(filter_id, language), ns_parts[:-1]))
    else:
        ns = ns_parts[:-1]

    if t.parent_service is not None:
        assert len(ns) > 0  # Well-formed DSDL will never have a request or response type that isn't nested.
        ns = ns[:-1] + [filter_short_reference_name(language, t.parent_service)]

    full_path = ns + [filter_short_reference_name(language, t)]
    return '::'.join(full_path)


@template_language_filter(__name__)
def filter_short_reference_name(language: Language, t: pydsdl.CompositeType) -> str:
    """
    Provides a string that is a shorted version of the full reference name. This type is unique only within its
    namespace.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_short_reference_name
        from unittest.mock import MagicMock
        import pydsdl

        my_type = MagicMock(spec=pydsdl.StructureType)
        my_type.version = MagicMock()
        my_type.parent_service = None

    .. code-block:: python

        # Given a type with illegal C++ characters
        my_type.short_name = '2Foo'
        my_type.version.major = 1
        my_type.version.minor = 2

        # and
        template = '{{ my_type | short_reference_name }}'

        # then, with stropping enabled
        rendered = '_2Foo_1_2'

    .. invisible-code-block: python

        jinja_filter_tester(filter_short_reference_name, template, rendered, 'cpp', my_type=my_type)

        my_type = MagicMock(spec=pydsdl.StructureType)
        my_type.version = MagicMock()
        my_type.parent_service = None

    :param pydsdl.CompositeType t: The DSDL type to get the reference name for.
    """
    if t.parent_service is None:
        short_name = '{short}_{major}_{minor}'.format(short=t.short_name, major=t.version.major, minor=t.version.minor)
    else:
        short_name = t.short_name
    if language.enable_stropping:
        return filter_id(language, short_name)
    else:
        return short_name


@template_language_list_filter(__name__)
def filter_includes(language: Language,
                    t: pydsdl.CompositeType,
                    sort: bool = True) -> typing.List[str]:
    """
    Returns a list of all include paths for a given type.

    :param pydsdl.CompositeType t: The type to scan for dependencies.
    :param bool sort: If true the returned list will be sorted.
    :return: a list of include headers needed for a given type.
    """

    include_gen = IncludeGenerator(language,
                                   t,
                                   filter_id,
                                   filter_short_reference_name)
    return include_gen.generate_include_filepart_list(language.extension, sort)


@template_language_filter(__name__)
def filter_declaration(language: Language,
                       instance: pydsdl.Any) -> str:
    """
    Emit a declaration statement for the given instance.
    """
    if isinstance(instance, pydsdl.PrimitiveType) or isinstance(instance, pydsdl.VoidType):
        return filter_type_from_primitive(language, instance)
    elif isinstance(instance, pydsdl.VariableLengthArrayType):
        return 'std::vector<{}>'.format(filter_declaration(language, instance.element_type))
    elif isinstance(instance, pydsdl.ArrayType):
        return 'std::array<{},{}>'.format(
            filter_declaration(language, instance.element_type),
            instance.capacity)
    else:
        return filter_full_reference_name(language, instance)


@template_language_filter(__name__)
def filter_definition_begin(language: Language, instance: pydsdl.CompositeType) -> str:
    """
    Emit the start of a definition statement for a composite type.

     .. invisible-code-block: python

        from nunavut.lang.cpp import filter_definition_begin
        from unittest.mock import MagicMock
        import pytest
        import pydsdl

        my_type = MagicMock(spec=pydsdl.StructureType)
        my_type.version = MagicMock()
        my_type.parent_service = None

        with pytest.raises(ValueError):
            jinja_filter_tester(filter_definition_begin,
                                '{{ my_type | definition_begin }}',
                                '',
                                'cpp',
                                my_type=MagicMock())

    .. code-block:: python

        # Given a pydsdl.CompositeType "my_type":
        my_type.short_name = 'Foo'
        my_type.version.major = 1
        my_type.version.minor = 0

        # and
        template = '{{ my_type | definition_begin }}'

        # then
        rendered = 'struct Foo_1_0'

    .. invisible-code-block: python

        jinja_filter_tester(filter_definition_begin, template, rendered, 'cpp', my_type=my_type)

        my_union_type = MagicMock(spec=pydsdl.UnionType)
        my_union_type.version = MagicMock()
        my_union_type.parent_service = None

    .. code-block:: python

        # Also, given a pydsdl.UnionType "my_union_type":
        my_union_type.short_name = 'Foo'
        my_union_type.version.major = 1
        my_union_type.version.minor = 0

        # and
        union_template = '{{ my_union_type | definition_begin }}'

        # then
        rendered = 'struct Foo_1_0'

    .. invisible-code-block: python

        jinja_filter_tester(filter_definition_begin, union_template, rendered, 'cpp', my_union_type=my_union_type)

        my_service_type = MagicMock(spec=pydsdl.ServiceType)
        my_service_type.version = MagicMock()
        my_service_type.parent_service = None

    .. code-block:: python

        # Finally, given a pydsdl.Servicetype "my_service_type":
        my_service_type.short_name = 'Foo'
        my_service_type.version.major = 1
        my_service_type.version.minor = 0

        # and
        template = '{{ my_service_type | definition_begin }}'

        # then
        rendered = 'namespace Foo_1_0'

    .. invisible-code-block: python

        jinja_filter_tester(filter_definition_begin, template, rendered, 'cpp', my_service_type=my_service_type)

    """
    short_name = filter_short_reference_name(language, instance)
    if isinstance(instance, pydsdl.StructureType) or isinstance(instance, pydsdl.UnionType):
        return 'struct {}'.format(short_name)
    elif isinstance(instance, pydsdl.ServiceType):
        return 'namespace {}'.format(short_name)
    else:
        raise ValueError('{} types cannot be redefined.'.format(type(instance).__name__))


@template_language_filter(__name__)
def filter_definition_end(language: Language, instance: pydsdl.CompositeType) -> str:
    """
    Emit the end of a definition statement for a composite type.

     .. invisible-code-block: python

        from nunavut.lang.cpp import filter_definition_end
        from unittest.mock import MagicMock
        import pytest
        import pydsdl


        with pytest.raises(ValueError):
            jinja_filter_tester(filter_definition_end, '{{ my_type | definition_end }}', '', 'cpp', my_type=MagicMock())

        my_type = MagicMock(spec=pydsdl.StructureType)
        my_type.version = MagicMock()
        my_type.short_name = 'Foo'
        my_type.version.major = 1
        my_type.version.minor = 0

        jinja_filter_tester(filter_definition_end, '{{ my_type | definition_end }}', ';', 'cpp', my_type=my_type)

        my_type = MagicMock(spec=pydsdl.UnionType)
        my_type.version = MagicMock()
        my_type.short_name = 'Foo'
        my_type.version.major = 1
        my_type.version.minor = 0

        jinja_filter_tester(filter_definition_end, '{{ my_type | definition_end }}', ';', 'cpp', my_type=my_type)

        my_type = MagicMock(spec=pydsdl.ServiceType)
        my_type.version = MagicMock()
        my_type.parent_service = None
        my_type.short_name = 'Foo'
        my_type.version.major = 1
        my_type.version.minor = 0

        jinja_filter_tester(filter_definition_end,
                            '{{ my_type | definition_end }}',
                            ' // namespace Foo_1_0',
                            'cpp',
                            my_type=my_type)

    """
    if isinstance(instance, pydsdl.StructureType) or isinstance(instance, pydsdl.UnionType):
        return ';'
    elif isinstance(instance, pydsdl.ServiceType):
        return ' // namespace {}'.format(filter_short_reference_name(language, instance))
    else:
        raise ValueError('{} types cannot be redefined.'.format(type(instance).__name__))


@template_language_filter(__name__)
def filter_type_from_primitive(language: Language,
                               value: pydsdl.PrimitiveType) -> str:
    return _CFit.get_best_fit(value.bit_length).to_c_type(value, language)


def filter_to_namespace_qualifier(namespace_list: typing.List[str]) -> str:
    """
    Converts a list of namespace names into a qualifer string. For example:

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_to_namespace_qualifier
        import pydsdl


    .. code-block:: python

        my_namespace = ['foo', 'bar']
        template = '{{ my_namespace | to_namespace_qualifier }}myType()'
        expected = 'foo::bar::myType()'

    .. invisible-code-block: python

        jinja_filter_tester(filter_to_namespace_qualifier, template, expected, 'cpp', my_namespace=my_namespace)

    This filter gracefully handles empty namespace lists:

    .. code-block:: python

        my_namespace = []
        template = '{{ my_namespace | to_namespace_qualifier }}myType()'
        expected = 'myType()'

    .. invisible-code-block: python

        jinja_filter_tester(filter_to_namespace_qualifier, template, expected, 'cpp', my_namespace=my_namespace)

    """
    if namespace_list is None or len(namespace_list) == 0:
        return ''
    else:
        return '::'.join(namespace_list) + '::'


def filter_to_template_unique_name(base_token: str) -> str:
    """
    Filter that takes a base token and forms a name that is very
    likely to be unique within the template the filter is invoked. This
    name is also very likely to be a valid C++ identifier.

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

        from nunavut.lang.cpp import filter_to_template_unique_name
        from nunavut.lang import _UniqueNameGenerator

    .. code-block:: python

        # Given
        template  = '{{ "foo" | to_template_unique_name }},{{ "Foo" | to_template_unique_name }},'
        template += '{{ "fOO" | to_template_unique_name }}'

        # then
        rendered = '_foo0_,_foo1_,_fOO0_'

    .. invisible-code-block: python

        _UniqueNameGenerator.reset()
        jinja_filter_tester(filter_to_template_unique_name, template, rendered, 'cpp')

    .. code-block:: python

        # Given
        template = '{{ "i like coffee" | to_template_unique_name }}'

        # then
        rendered = '_i like coffee0_'

    .. invisible-code-block: python

        _UniqueNameGenerator.reset()
        jinja_filter_tester(filter_to_template_unique_name, template, rendered, 'cpp')


    :param str base_token: A token to include in the base name.
    :returns: A name that is likely to be valid C++ identifier and is likely to
        be unique within the file generated by the current template.
    """
    if len(base_token) > 0:
        adj_base_token = base_token[0:1].lower() + base_token[1:]
    else:
        adj_base_token = base_token

    return _UniqueNameGenerator.get_instance()('cpp', adj_base_token, '_', '_')


def filter_as_boolean_value(value: bool) -> str:
    """
    Filter a boolean expression to produce a valid C++ "true" or "false" token.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_as_boolean_value

    .. code-block:: python

        assert "true" == filter_as_boolean_value(True)
        assert "false" == filter_as_boolean_value(False)

    """
    return ('true' if value else 'false')


@template_language_filter(__name__)
def filter_indent(language: Language,
                  text: str,
                  depth: int = 1) -> str:
    """
    Emit indent characters as configured for the language.

    :param text: The text to indent.
    :param depth: The number of indents. For example, if depth is 2 and the indent for this language is
        4 spaces then the text will be indented by 8 spaces.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_indent

    .. code-block:: python

        # Given a string with an existing indent of 4 spaces...
        template  = '{{ "    int a = 1;" | indent }}'

        # then if cpp.indent == 4 we expect no change.
        rendered = '    int a = 1;'

    .. invisible-code-block: python

        assert_language_config_value('cpp', 'indent', '4', 'this test expected an indent of 4')
        jinja_filter_tester(filter_indent, template, rendered, 'cpp')

    .. code-block:: python

        # If the indent is only 3 spaces...
        template  = '{{ "   int a = 1;" | indent }}'

        # then if cpp.indent == 4 we expect 4 spaces (i.e. not 7 spaces)
        rendered = '    int a = 1;'

    .. invisible-code-block: python

        jinja_filter_tester(filter_indent, template, rendered, 'cpp')

    .. code-block:: python

        # We can also specify multiple indents...
        template  = '{{ "int a = 1;" | indent(2) }}'

        rendered = '        int a = 1;'

    .. invisible-code-block: python

        jinja_filter_tester(filter_indent, template, rendered, 'cpp')

    .. code-block:: python

        # ...or no indent
        template  = '{{ "    int a = 1;" | indent(0) }}'

        rendered = 'int a = 1;'

    .. invisible-code-block: python

        jinja_filter_tester(filter_indent, template, rendered, 'cpp')


    """
    configured_indent = int(str(language.get_config_value('indent')))
    lines = text.splitlines(keepends=True)
    result = ''
    for i in range(0, len(lines)):
        line = lines[i].lstrip()
        result += (' ' * (depth * configured_indent)) + line
    return result


def _minimum_required_capacity_bits_for_composite(t: pydsdl.CompositeType) -> int:
    required_bits = 0
    if isinstance(t, pydsdl.StructureType):
        for field in t.fields:
            required_bits += _minimum_required_capacity_bits(field.data_type)
    elif isinstance(t, pydsdl.UnionType):
        required_bits = t.tag_field_type.bit_length
    else:
        raise TypeError('Unknown CompositeType passed into filter')
    return required_bits


def _minimum_required_capacity_bits(t: pydsdl.SerializableType) -> int:
    if isinstance(t, pydsdl.VoidType) or isinstance(t, pydsdl.PrimitiveType):
        return typing.cast(int, t.bit_length)
    elif isinstance(t, pydsdl.FixedLengthArrayType):
        return typing.cast(int, t.capacity) * \
            _minimum_required_capacity_bits(t.element_type)
    elif isinstance(t, pydsdl.VariableLengthArrayType):
        # at minimum a variable length array requires 0 bits.
        return math.ceil(math.log2(t.capacity + 1))
    elif isinstance(t, pydsdl.CompositeType):
        return _minimum_required_capacity_bits_for_composite(t)
    else:
        raise TypeError('Unknown SerializableType passed into filter')


def filter_minimum_required_capacity_bits(t: pydsdl.SerializableType) -> int:
    return _minimum_required_capacity_bits(t)
