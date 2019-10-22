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
import os
import typing
import re

from .c import VariableNameEncoder, C_RESERVED_IDENTIFIERS, C_RESERVED_PATTERNS


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


def _common_filter_id(instance: typing.Any,
                      stropping_prefix: str,
                      encoding_prefix: str,
                      scoping_token: typing.Optional[str] = None) -> str:
    if hasattr(instance, 'name'):
        raw_name = str(instance.name)  # type: str
    else:
        raw_name = str(instance)

    vne = VariableNameEncoder(stropping_prefix, '', encoding_prefix, scoping_token=scoping_token)
    out = vne.strop(raw_name, CPP_RESERVED_IDENTIFIERS, CPP_RESERVED_PATTERNS)
    return CPP_NO_DOUBLE_DASH_RULE.sub('_' + vne.encode_character('_'), out)


def filter_id(instance: typing.Any, stropping_prefix: str = '_', encoding_prefix: str = 'ZX') -> str:
    """
    Filter that produces a valid C and/or C++ identifier for a given object. The encoding may not
    be reversable.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_id

    >>> filter_id('I like c++')
    'I_like_cZX002BZX002B'

    >>> filter_id('if')
    '_if'

    >>> filter_id('if', 'stropped_')
    'stropped_if'

    >>> filter_id('_Reserved')
    '_reserved'

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
    return _common_filter_id(instance, stropping_prefix, encoding_prefix)


def filter_ns_id(instance: typing.Any,
                 stropping_prefix: str = '_',
                 encoding_prefix: str = 'ZX',
                 scoping_token: str = '::') -> str:
    """
    Filter that produces a valid C++ identifier for a given object preserving namespacing if present.
    Example:

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_ns_id
        from nunavut.lang.cpp import filter_id

    >>> filter_ns_id('foo::I_\\u2764_c++::Bar')
    'foo::I_ZX005Cu2764_cZX002BZX002B::Bar'

    whereas using :func:`filter_id` yields the following:

    >>> filter_id('foo::I_\\u2764_c++::Bar')
    'fooZX003AZX003AI_ZX005Cu2764_cZX002BZX002BZX003AZX003ABar'

    :param any instance:        Any object or data that either has a name property or can be converted
                                to a string.
    :param str stropping_prefix: String prepended to the resolved instance name if the encoded value
                                is a reserved keyword in C.
    :param str encoding_prefix: The string to insert before any four digit unicode number used to represent
                                an illegal character.
                                Note that the caller must ensure the prefix itself consists of only valid
                                characters for C identifiers.
    :param str scoping_token:   A token used to scope terms in the identifier. These tokens are not stropped
                                and are used to separate individual identifiers which are stropped.
    :returns: A token that is a valid identifier for c++, is not a reserved keyword, and is transformed
              in a deterministic manner based on the provided instance.
    """
    return _common_filter_id(instance, stropping_prefix, encoding_prefix, scoping_token)


def filter_open_namespace(full_namespace: str, bracket_on_next_line: bool = True) -> str:
    """
        Emits c++ opening namspace syntax parsed from a pydsdl "full_namespace",
        dot-seperated  value.

        The following example assumes a string "uavcan.foo" as ``full_namespace``.

        Example::

            {{T.full_namespace | cpp.open_namespace}}

        Result Example::

            namespace uavcan
            {
            namespace foo
            {

        :param str full_namespace: A dot-seperated namespace string.
        :param bool bracket_on_next_line: If True (the default) then the opening
            brackets are placed on a newline after the namespace keyword.

        :returns: C++ namespace declarations with opening brackets.
    """

    with io.StringIO() as content:
        for name in full_namespace.split('.'):
            content.write('namespace ')
            content.write(name)
            if bracket_on_next_line:
                content.write(os.linesep)
            else:
                content.write(' ')
            content.write('{')
            content.write(os.linesep)
        return content.getvalue()


def filter_close_namespace(full_namespace: str, omit_comments: bool = False) -> str:
    """
        Emits c++ closing namspace syntax parsed from a pydsdl "full_namespace",
        dot-seperated  value.

        The following example assumes a string "uavcan.foo" as ``full_namespace``.

        Example::

            {{T.full_namespace | cpp.close_namespace}}

        Result Example::

            } // namespace foo
            } // namespace uavcan

        :param str full_namespace: A dot-seperated namespace string.
        :param omit_comments: If True then the comments following the closing
                              bracket are omitted.

        :returns: C++ namespace declarations with opening brackets.
    """
    with io.StringIO() as content:
        for name in reversed(full_namespace.split('.')):
            content.write('}')
            if not omit_comments:
                content.write(' // ')
                content.write(name)
            content.write(os.linesep)
        return content.getvalue()
