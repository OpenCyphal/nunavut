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
import pathlib
import re
import typing

import pydsdl

from ... import SupportsTemplateEnv, templateEnvironmentFilter
from ..c import (C_RESERVED_IDENTIFIERS, C_RESERVED_PATTERNS,
                 VariableNameEncoder)
from ...lang import LanguageContext


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


def filter_open_namespace(full_namespace: str, bracket_on_next_line: bool = True, linesep: str = '\n') -> str:
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
            content.write(name)
            if bracket_on_next_line:
                content.write(linesep)
            else:
                content.write(' ')
            content.write('{')
            content.write(linesep)
        return content.getvalue()


def filter_close_namespace(full_namespace: str, omit_comments: bool = False, linesep: str = '\n') -> str:
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
                content.write(name)
            content.write(linesep)
        return content.getvalue()


def filter_full_reference_name(t: pydsdl.CompositeType, stropping: bool = True) -> str:
    """
    Provides a string that is the full namespace, typename, major, and minor version for a given composite type.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_full_reference_name

        dummy = lambda: None
        dummy_version = lambda: None
        setattr(dummy, 'version', dummy_version)

    .. code-block:: python

        # Given
        full_name = 'any.int.2Foo'
        major = 1
        minor = 2

        # and
        template = '{{ my_obj | full_reference_name }}'

        # then
        rendered = 'any::_int::_2Foo_1_2'

    .. invisible-code-block: python


        setattr(dummy_version, 'major', major)
        setattr(dummy_version, 'minor', minor)
        setattr(dummy, 'full_name', full_name)
        setattr(dummy, 'short_name', full_name.split('.')[-1])
        jinja_filter_tester(filter_full_reference_name, template, rendered, my_obj=dummy)


    .. code-block:: python

        # Given
        full_name = 'any.int.2Foo'
        major = 1
        minor = 2

        # and
        template = '{{ my_obj | full_reference_name(stropping=False) }}'

        # then
        rendered = 'any::int::2Foo_1_2'

    .. invisible-code-block: python


        setattr(dummy_version, 'major', major)
        setattr(dummy_version, 'minor', minor)
        setattr(dummy, 'full_name', full_name)
        setattr(dummy, 'short_name', full_name.split('.')[-1])
        jinja_filter_tester(filter_full_reference_name, template, rendered, my_obj=dummy)

    :param pydsdl.CompositeType t: The DSDL type to get the fully-resolved reference name for.
    :param bool stropping: If True then the :func:`filter_id` filter is applied to each component in the identifier.
    """
    ns_parts = t.full_name.split('.')
    if len(ns_parts) > 1:
        if stropping:
            ns = list(map(filter_id, ns_parts[:-1]))
        else:
            ns = ns_parts[:-1]

    return '::'.join(ns + [filter_short_reference_name(t, stropping)])


def filter_short_reference_name(t: pydsdl.CompositeType, stropping: bool = True) -> str:
    """
    Provides a string that is a shorted version of the full reference name. This type is unique only within its
    namespace.

     .. invisible-code-block: python

        from nunavut.lang.cpp import filter_short_reference_name

        dummy = lambda: None
        dummy_version = lambda: None
        setattr(dummy, 'version', dummy_version)

    .. code-block:: python

        # Given
        short_name = '2Foo'
        major = 1
        minor = 2

        # and
        template = '{{ my_obj | short_reference_name }}'

        # then
        rendered = '_2Foo_1_2'

    .. invisible-code-block: python

        setattr(dummy_version, 'major', major)
        setattr(dummy_version, 'minor', minor)
        setattr(dummy, 'short_name', short_name)
        jinja_filter_tester(filter_short_reference_name, template, rendered, my_obj=dummy)


    .. code-block:: python

        # Given
        short_name = '2Foo'
        major = 1
        minor = 2

        # and
        template = '{{ my_obj | short_reference_name(stropping=False) }}'

        # then
        rendered = '2Foo_1_2'

    .. invisible-code-block: python

        setattr(dummy_version, 'major', major)
        setattr(dummy_version, 'minor', minor)
        setattr(dummy, 'short_name', short_name)
        jinja_filter_tester(filter_short_reference_name, template, rendered, my_obj=dummy)

    :param pydsdl.CompositeType t: The DSDL type to get the reference name for.
    """
    short_name = '{short}_{major}_{minor}'.format(short=t.short_name, major=t.version.major, minor=t.version.minor)
    if stropping:
        return filter_id(short_name)
    else:
        return short_name


@templateEnvironmentFilter
def filter_includes(env: SupportsTemplateEnv,
                    t: pydsdl.CompositeType,
                    sort: bool = True,
                    stropping: bool = True) -> typing.List[str]:
    """
    Returns a list of all include paths for a given type.

    :param pydsdl.CompositeType t: The type to scan for dependencies.
    :param bool sort: If true the returned list will be sorted.
    :param bool strop: If true the list will contained stropped identifiers.
    :return: a list of include headers needed for a given type.
    """
    # Make a list of all attributes defined by this type
    if isinstance(t, pydsdl.ServiceType):
        atr = t.request_type.attributes + t.response_type.attributes
    else:
        atr = t.attributes

    dep_types = \
        [(x.data_type, filter_short_reference_name(x.data_type))
            for x in atr if isinstance(x.data_type, pydsdl.CompositeType)]
    dep_types += \
        [(x.data_type.element_type, filter_short_reference_name(x.data_type.element_type))
            for x in atr if
            isinstance(x.data_type, pydsdl.ArrayType) and isinstance(x.data_type.element_type, pydsdl.CompositeType)]

    def make_ns_list(dt: pydsdl.SerializableType) -> typing.List[str]:
        if stropping:
            return [filter_id(x) for x in dt.full_namespace.split('.')]
        else:
            return typing.cast(typing.List[str], dt.full_namespace.split('.'))

    suffix = LanguageContext.get_from_globals(env.globals).get_output_extension()
    path_list = [str(pathlib.Path(*make_ns_list(dt)) / pathlib.Path(sr).with_suffix(suffix))
                 for dt, sr in dep_types]

    if sort:
        path_list = sorted(path_list)
    return path_list
