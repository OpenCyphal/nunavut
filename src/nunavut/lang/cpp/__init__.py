#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    Filters for generating C++. All filters in this
    module will be available in the template's global namespace as ``cpp``.
"""

import io
import re
import typing

import pydsdl

from ... import SupportsTemplateEnv, templateEnvironmentFilter
from ..c import (C_RESERVED_IDENTIFIERS, C_RESERVED_PATTERNS,
                 VariableNameEncoder, _CFit)
from ...lang import LanguageContext
from ._support import IncludeGenerator


# Taken from https://en.cppreference.com/w/cpp/keyword
CPP_RESERVED_IDENTIFIERS = frozenset([
    *C_RESERVED_IDENTIFIERS,
    'alignas',
    'alignof',
    'and',
    'and_eq',
    'asm',
    'atomic_cancel',
    'atomic_commit',
    'atomic_noexcept',
    'auto',
    'bitand',
    'bitor',
    'bool',
    'break',
    'case',
    'catch',
    'char',
    'char8_t',
    'char16_t',
    'char32_t',
    'class',
    'compl',
    'concept',
    'const',
    'consteval',
    'constexpr',
    'constinit',
    'const_cast',
    'continue',
    'co_await',
    'co_return',
    'co_yield',
    'decltype',
    'default',
    'delete',
    'do',
    'double',
    'dynamic_cast',
    'else',
    'enum',
    'explicit',
    'export',
    'extern',
    'false',
    'float',
    'for',
    'friend',
    'goto',
    'if',
    'inline',
    'int',
    'long',
    'mutable',
    'namespace',
    'new',
    'noexcept',
    'not',
    'not_eq',
    'nullptr',
    'operator',
    'or',
    'or_eq',
    'private',
    'protected',
    'public',
    'reflexpr',
    'register',
    'reinterpret_cast',
    'requires',
    'return',
    'short',
    'signed',
    'sizeof',
    'static',
    'static_assert',
    'static_cast',
    'struct',
    'switch',
    'synchronized',
    'template',
    'this',
    'thread_local',
    'throw',
    'true',
    'try',
    'typedef',
    'typeid',
    'typename',
    'union',
    'unsigned',
    'using',
    'virtual',
    'void',
    'volatile',
    'wchar_t',
    'while',
    'xor',
    'xor_eq',
    'override',
    'final',
    'import',
    'module',
    'transaction_safe',
    'transaction_safe_dynamic',
    '_Pragma',
    'if',
    'elif',
    'else',
    'endif',
    'ifdef',
    'ifndef',
    'define',
    'undef',
    'include',
    'line',
    'error',
    'pragma',
    'defined',
    '__has_include',
    '__has_cpp_attribute'
])

CPP_RESERVED_PATTERNS = frozenset([*C_RESERVED_PATTERNS])

CPP_NO_DOUBLE_DASH_RULE = re.compile(r'(__)')


def filter_id(instance: typing.Any, stropping_prefix: str = '_', encoding_prefix: str = 'ZX') -> str:
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

        jinja_filter_tester(filter_id, template, rendered, I=I)


    .. code-block:: python

        # Given
        I = 'if'

        # and
        template = '{{ I | id }}'

        # then
        rendered = '_if'


    .. invisible-code-block: python

        jinja_filter_tester(filter_id, template, rendered, I=I)


    .. code-block:: python

        # Given
        I = 'if'

        # and
        template = '{{ I | id("stropped_") }}'

        # then
        rendered = 'stropped_if'

    .. invisible-code-block: python

        jinja_filter_tester(filter_id, template, rendered, I=I)


    .. code-block:: python

        # Given
        I = '_Reserved'

        # and
        template = '{{ I | id }}'

        # then
        rendered = '_reserved'

    .. invisible-code-block: python

        jinja_filter_tester(filter_id, template, rendered, I=I)

    :param any instance:        Any object or data that either has a name property or can be converted
                                to a string.
    :param str stropping_prefix: String prepended to the resolved instance name if the encoded value
                                is a reserved keyword in C or C++.
    :param str encoding_prefix: The string to insert before any four digit unicode number used to represent
                                an illegal character.
                                Note that the caller must ensure the prefix itself consists of only valid
                                characters for C and C++ identifiers.
    :returns: A token that is a valid identifier for C and C++, is not a reserved keyword, and is transformed
              in a deterministic manner based on the provided instance.
    """
    if hasattr(instance, 'name'):
        raw_name = str(instance.name)  # type: str
    else:
        raw_name = str(instance)

    vne = VariableNameEncoder(stropping_prefix, '', encoding_prefix)
    out = vne.strop(raw_name, CPP_RESERVED_IDENTIFIERS, CPP_RESERVED_PATTERNS)
    return CPP_NO_DOUBLE_DASH_RULE.sub('_' + vne.encode_character('_'), out)


def filter_open_namespace(full_namespace: str,
                          bracket_on_next_line: bool = True,
                          linesep: str = '\n',
                          stropping: bool = True) -> str:
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

        jinja_filter_tester(filter_open_namespace, template, rendered, T=T)

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
            if stropping:
                content.write(filter_id(name))
            else:
                content.write(name)
            if bracket_on_next_line:
                content.write(linesep)
            else:
                content.write(' ')
            content.write('{')
            content.write(linesep)
        return content.getvalue()


def filter_close_namespace(full_namespace: str,
                           omit_comments: bool = False,
                           linesep: str = '\n',
                           stropping: bool = True) -> str:
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

        jinja_filter_tester(filter_close_namespace, template, rendered, T=T)


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
                if stropping:
                    content.write(filter_id(name))
                else:
                    content.write(name)
            content.write(linesep)
        return content.getvalue()


def filter_full_reference_name(t: pydsdl.CompositeType, stropping: bool = True) -> str:
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
        jinja_filter_tester(filter_full_reference_name, template, rendered, my_obj=my_obj)

        my_obj = MagicMock()
        my_obj.version = MagicMock()
        my_obj.parent_service = None

    .. code-block:: python

        # Given a type with illegal characters for C++
        my_obj.full_name = 'any.int.2Foo'
        my_obj.version.major = 1
        my_obj.version.minor = 2

        # and
        template = '{{ my_obj | full_reference_name(stropping=False) }}'

        # then, with stropping disabled
        rendered = 'any::int::2Foo_1_2'

    .. invisible-code-block: python

        my_obj.short_name = my_obj.full_name.split('.')[-1]
        jinja_filter_tester(filter_full_reference_name, template, rendered, my_obj=my_obj)

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

        jinja_filter_tester(filter_full_reference_name, template, rendered, my_service=my_service)

    :param pydsdl.CompositeType t: The DSDL type to get the fully-resolved reference name for.
    :param bool stropping: If True then the :func:`filter_id` filter is applied to each component in the identifier.
    """
    ns_parts = t.full_name.split('.')
    if stropping:
        ns = list(map(filter_id, ns_parts[:-1]))
    else:
        ns = ns_parts[:-1]

    if t.parent_service is not None:
        assert len(ns) > 0  # Well-formed DSDL will never have a request or response type that isn't nested.
        ns = ns[:-1] + [filter_short_reference_name(t.parent_service, stropping=stropping)]

    full_path = ns + [filter_short_reference_name(t, stropping)]
    return '::'.join(full_path)


def filter_short_reference_name(t: pydsdl.CompositeType, stropping: bool = True) -> str:
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

        jinja_filter_tester(filter_short_reference_name, template, rendered, my_type=my_type)

        my_type = MagicMock(spec=pydsdl.StructureType)
        my_type.version = MagicMock()
        my_type.parent_service = None

    .. code-block:: python

        # Given a type with illegal C++ characters
        my_type.short_name = '2Foo'
        my_type.version.major = 1
        my_type.version.minor = 2

        # and
        template = '{{ my_type | short_reference_name(stropping=False) }}'

        # then
        rendered = '2Foo_1_2'

    .. invisible-code-block: python

        jinja_filter_tester(filter_short_reference_name, template, rendered, my_type=my_type)

    :param pydsdl.CompositeType t: The DSDL type to get the reference name for.
    """
    if t.parent_service is None:
        short_name = '{short}_{major}_{minor}'.format(short=t.short_name, major=t.version.major, minor=t.version.minor)
    else:
        short_name = t.short_name
    if stropping:
        return filter_id(short_name)
    else:
        return short_name


@templateEnvironmentFilter
def filter_includes(env: SupportsTemplateEnv,
                    t: pydsdl.CompositeType,
                    sort: bool = True,
                    prefer_system_includes: bool = False,
                    use_standard_types: bool = True,
                    stropping: bool = True) -> typing.List[str]:
    """
    Returns a list of all include paths for a given type.

    :param pydsdl.CompositeType t: The type to scan for dependencies.
    :param bool sort: If true the returned list will be sorted.
    :param bool strop: If true the list will contained stropped identifiers.
    :return: a list of include headers needed for a given type.
    """

    include_gen = IncludeGenerator(t, filter_id, filter_short_reference_name, use_standard_types, stropping)
    return include_gen.generate_include_filepart_list(LanguageContext.get_from_globals(
        env.globals).get_output_extension(),
        sort,
        prefer_system_includes)


def filter_declaration(instance: pydsdl.Any, use_standard_types: bool = True) -> str:
    """
    Emit a declaration statement for the given instance.
    """
    if isinstance(instance, pydsdl.PrimitiveType) or isinstance(instance, pydsdl.VoidType):
        return filter_type_from_primitive(instance, use_standard_types)
    elif isinstance(instance, pydsdl.VariableLengthArrayType):
        return 'std::vector<{}>'.format(filter_declaration(instance.element_type, use_standard_types))
    elif isinstance(instance, pydsdl.ArrayType):
        return 'std::Array<{}>'.format(filter_declaration(instance.element_type, use_standard_types))
    else:
        return filter_full_reference_name(instance)


def filter_definition_begin(instance: pydsdl.CompositeType) -> str:
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
            jinja_filter_tester(filter_definition_begin, '{{ my_type | definition_begin }}', '', my_type=MagicMock())

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

        jinja_filter_tester(filter_definition_begin, template, rendered, my_type=my_type)

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
        rendered = 'union Foo_1_0'

    .. invisible-code-block: python

        jinja_filter_tester(filter_definition_begin, union_template, rendered, my_union_type=my_union_type)

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

        jinja_filter_tester(filter_definition_begin, template, rendered, my_service_type=my_service_type)

    """
    short_name = filter_short_reference_name(instance)
    if isinstance(instance, pydsdl.StructureType):
        return 'struct {}'.format(short_name)
    elif isinstance(instance, pydsdl.UnionType):
        return 'union {}'.format(short_name)
    elif isinstance(instance, pydsdl.ServiceType):
        return 'namespace {}'.format(short_name)
    else:
        raise ValueError('{} types cannot be redefined.'.format(type(instance).__name__))


def filter_definition_end(instance: pydsdl.CompositeType) -> str:
    """
    Emit the end of a definition statement for a composite type.

     .. invisible-code-block: python

        from nunavut.lang.cpp import filter_definition_end
        from unittest.mock import MagicMock
        import pytest
        import pydsdl


        with pytest.raises(ValueError):
            jinja_filter_tester(filter_definition_end, '{{ my_type | definition_end }}', '', my_type=MagicMock())

        my_type = MagicMock(spec=pydsdl.StructureType)
        my_type.version = MagicMock()
        my_type.short_name = 'Foo'
        my_type.version.major = 1
        my_type.version.minor = 0

        jinja_filter_tester(filter_definition_end, '{{ my_type | definition_end }}', ';', my_type=my_type)

        my_type = MagicMock(spec=pydsdl.UnionType)
        my_type.version = MagicMock()
        my_type.short_name = 'Foo'
        my_type.version.major = 1
        my_type.version.minor = 0

        jinja_filter_tester(filter_definition_end, '{{ my_type | definition_end }}', ';', my_type=my_type)

        my_type = MagicMock(spec=pydsdl.ServiceType)
        my_type.version = MagicMock()
        my_type.parent_service = None
        my_type.short_name = 'Foo'
        my_type.version.major = 1
        my_type.version.minor = 0

        jinja_filter_tester(filter_definition_end,
                            '{{ my_type | definition_end }}',
                            ' // namespace Foo_1_0',
                            my_type=my_type)

    """
    if isinstance(instance, pydsdl.StructureType) or isinstance(instance, pydsdl.UnionType):
        return ';'
    elif isinstance(instance, pydsdl.ServiceType):
        return ' // namespace {}'.format(filter_short_reference_name(instance))
    else:
        raise ValueError('{} types cannot be redefined.'.format(type(instance).__name__))


def filter_type_from_primitive(value: pydsdl.PrimitiveType, use_standard_types: bool = True) -> str:
    return _CFit.get_best_fit(value.bit_length).to_c_type(value, use_standard_types)
