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


def filter_id(instance: typing.Any, stropping_prefix: str = '_', encoding_prefix: str = 'ZX') -> str:
    """
    Filter that produces a valid C and/or C++ identifier for a given object. The encoding may not
    be reversable.

    Example::

        {{ "I like c++" | cpp.id }}
        {{ "if" | cpp.id }}
        {{ "if" | cpp.id('stropped_') }}
        {{ "_Reserved" | cpp.id }}

    Results Example::

       I_like_cZX0043ZX0043
       _if
       stropped_if
       _reserved

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
