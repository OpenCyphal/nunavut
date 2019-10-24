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
import re
import typing

import pydsdl

from . import _UniqueNameGenerator
from .. import SupportsTemplateEnv, templateEnvironmentFilter

# Taken from https://en.cppreference.com/w/c/keyword
C_RESERVED_IDENTIFIERS = frozenset([
    'asm',
    'auto',
    'break',
    'case',
    'char',
    'const',
    'continue',
    'default',
    'defined',
    'do',
    'double',
    'error',
    'else',
    'elif',
    'endif',
    'enum',
    'extern',
    'float',
    'for',
    'fortran',
    'goto',
    'if',
    'ifdef',
    'ifndef',
    'include',
    'inline',
    'int',
    'line',
    'long',
    'pragma',
    'register',
    'restrict',
    'return',
    'short',
    'signed',
    'sizeof',
    'static',
    'struct',
    'switch',
    'typedef',
    'undef',
    'union',
    'unsigned',
    'void',
    'volatile',
    'while',
    '_Alignas',
    '_Alignof',
    '_Atomic',
    '_Bool',
    '_Complex',
    '_Generic',
    '_Imaginary',
    '_Noreturn',
    '_Pragma',
    '_Static_assert',
    '_Thread_local'
])

# Taken from https://en.cppreference.com/w/c/language/identifier
# cspell: disable
C_RESERVED_PATTERNS = frozenset(map(functools.partial(re.compile, flags=0), [
    r'^(is|to|str|mem|wcs|atomic_|cnd_|mtx_|thrd_|tss_|memory_|memory_order_)[a-z]',
    r'^u?int[a-zA-Z_0-9]*_t',
    r'^E[A-Z0-9]+',
    r'^FE_[A-Z]',
    r'^U?INT[a-zA-Z_0-9]*_(MAX|MIN|C)',
    r'^(PRI|SCN)[a-zX]',
    r'^LC_[A-Z]',
    r'^SIG_?[A-Z]',
    r'^TIME_[A-Z]',
    r'^ATOMIC_[A-Z]'
]))
# cspell: enable


class VariableNameEncoder:
    '''
    One-way transform from an arbitrary string of unicode characters into a valid
    C identifier (without the use of digraphs).
    '''
    _token_pattern = re.compile(r'(^\d{1})|( +)|[^a-zA-Z0-9_]')  # type: typing.Pattern

    _token_start_pattern = re.compile(r'(^__)|(^_[A-Z])')

    def __init__(self,
                 stropping_prefix: str,
                 stropping_suffix: str,
                 encoding_prefix: str,
                 enforce_c_prefix_rules: bool = True) -> None:
        self._stropping_prefix = stropping_prefix
        self._stropping_suffix = stropping_suffix
        self._encoding_prefix = encoding_prefix
        self._enforce_c_prefix_rules = enforce_c_prefix_rules
        if self._token_start_pattern.match(self._encoding_prefix):
            raise RuntimeError('{} is not allowed as a prefix since it can result in illegal identifiers.'.format(
                self._encoding_prefix))

    def _filter_id_illegal_character_replacement(self, m: typing.Match) -> str:
        if m.group(1) is not None:
            return '_{}'.format(m.group(1))
        elif m.group(2) is not None:
            return '_' * len(m.group(2))
        else:
            return self.encode_character(m.group(0))

    def _filter_id_for_illegal_start(self, m: typing.Match) -> str:
        '''
        In C r'^__' and r'^_[A-Z]' are always reserved. This will substitute
        out these start conditions if found.
        '''
        if m.group(1) is not None:
            return '_{}'.format(self.encode_character('_'))
        elif m.group(2) is not None:
            return '_{}'.format(m.group(2)[1].lower())
        else:
            raise RuntimeError('unknown match')

    @staticmethod
    def _matches(input_string: str, reserved_patterns: typing.Optional[typing.FrozenSet[typing.Pattern]]) -> bool:
        if reserved_patterns is not None:
            for pattern in reserved_patterns:
                if pattern.match(input_string):
                    return True
        return False

    def encode_character(self, c: str) -> str:
        return '{}{:04X}'.format(self._encoding_prefix, ord(c))

    def strop(self,
              token: str,
              reserved_words: typing.FrozenSet[str],
              reserved_patterns: typing.Optional[typing.FrozenSet[typing.Pattern]] = None) -> str:
        encoded = str(self._token_pattern.sub(self._filter_id_illegal_character_replacement, token))
        if encoded in reserved_words or self._matches(encoded, reserved_patterns):
            stropped = (self._stropping_prefix + encoded + self._stropping_suffix)
        else:
            stropped = encoded
        if self._enforce_c_prefix_rules:
            return str(self._token_start_pattern.sub(self._filter_id_for_illegal_start, stropped))
        else:
            return stropped


def filter_id(instance: typing.Any, stropping_prefix: str = '_', encoding_prefix: str = 'ZX') -> str:
    """
    Filter that produces a valid C identifier for a given object. The encoding may not
    be reversable.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_id


    .. code-block:: python

        # Given
        I = 'I \u2764 c'

        # and
        template = '{{ I | id }}'

        # then
        rendered = 'I_ZX2764_c'


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
                                is a reserved keyword in C.
    :param str encoding_prefix: The string to insert before any four digit unicode number used to represent
                                an illegal character.
                                Note that the caller must ensure the prefix itself consists of only valid
                                characters for C identifiers.
    :returns: A token that is a valid identifier for C, is not a reserved keyword, and is transformed
              in a deterministic manner based on the provided instance.
    """
    if hasattr(instance, 'name'):
        raw_name = str(instance.name)  # type: str
    else:
        raw_name = str(instance)

    return VariableNameEncoder(stropping_prefix, '', encoding_prefix).strop(raw_name,
                                                                            C_RESERVED_IDENTIFIERS,
                                                                            C_RESERVED_PATTERNS)


def filter_macrofy(value: str) -> str:
    """
    Filter to transform an input into a valid C preprocessor identifier token.


    .. invisible-code-block: python

        from nunavut.lang.c import filter_macrofy


    .. code-block:: python

        # Given
        template = '#ifndef {{ "my full name" | macrofy }}'

        # then
        rendered = '#ifndef MY_FULL_NAME'


    .. invisible-code-block: python

        jinja_filter_tester(filter_macrofy, template, rendered)


    :param str value: The value to transform.

    :returns: A valid C preprocessor identifier token.
    """
    return value.replace(' ', '_').replace('.', '_').upper()


_CFit_T = typing.TypeVar('_CFit_T', bound='_CFit')


@enum.unique
class _CFit(enum.Enum):
    IN_8 = 8
    IN_16 = 16
    IN_32 = 32
    IN_64 = 64

    def to_std_int(self, is_signed: bool) -> str:
        return "{}int{}_t".format(('' if is_signed else 'u'), self.value)

    def to_c_int(self, is_signed: bool) -> str:
        if self.value == 8:
            intname = 'char'
        elif self.value == 16:
            intname = 'int'
        elif self.value == 32:
            intname = 'long'
        else:
            intname = 'long long'

        if not is_signed:
            intname = 'unsigned ' + intname

        return intname

    def to_c_float(self) -> str:
        if self.value == 8 or self.value == 16 or self.value == 32:
            return 'float'
        else:
            return 'double'

    def to_c_type(self, value: pydsdl.PrimitiveType, use_standard_types: bool = True) -> str:
        if isinstance(value, pydsdl.UnsignedIntegerType):
            return (self.to_c_int(False) if not use_standard_types else self.to_std_int(False))
        elif isinstance(value, pydsdl.SignedIntegerType):
            return (self.to_c_int(True) if not use_standard_types else self.to_std_int(True))
        elif isinstance(value, pydsdl.FloatType):
            return self.to_c_float()
        elif isinstance(value, pydsdl.BooleanType):
            return ('BOOL' if not use_standard_types else 'bool')
        else:
            raise RuntimeError("{} is not a known PrimitiveType".format(type(value).__name__))

    @classmethod
    def get_best_fit(cls: typing.Type[_CFit_T], bit_length: int) -> _CFit_T:
        if bit_length <= 8:
            bestfit = _CFit.IN_8
        elif bit_length <= 16:
            bestfit = _CFit.IN_16
        elif bit_length <= 32:
            bestfit = _CFit.IN_32
        elif bit_length <= 64:
            bestfit = _CFit.IN_64
        else:
            raise RuntimeError(
                "Cannot emit a standard type for a primitive that is larger than 64 bits ({}).".format(
                    bit_length
                )
            )
        return cls(bestfit)


def filter_type_from_primitive(value: pydsdl.PrimitiveType, use_standard_types: bool = True) -> str:
    """
    Filter to transform a pydsdl :class:`~pydsdl.PrimitiveType` into
    a valid C type.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_type_from_primitive
        import pydsdl


    .. code-block:: python

        # Given
        template = '{{ unsigned_int_32_type | type_from_primitive(use_standard_types=True) }}'

        # then
        rendered = 'uint32_t'


    .. invisible-code-block: python

        test_type = pydsdl.UnsignedIntegerType(32, pydsdl.PrimitiveType.CastMode.TRUNCATED)
        jinja_filter_tester(filter_type_from_primitive,
                            template,
                            rendered,
                            unsigned_int_32_type=test_type)

    .. code-block:: python

        # Given
        template = '{{ unsigned_int_32_type | type_from_primitive(use_standard_types=False) }}'

        # then
        rendered = 'unsigned long'


    .. invisible-code-block: python

        test_type = pydsdl.UnsignedIntegerType(32, pydsdl.PrimitiveType.CastMode.TRUNCATED)
        jinja_filter_tester(filter_type_from_primitive,
                            template,
                            rendered,
                            unsigned_int_32_type=test_type)


    :param str value: The dsdl primitive to transform.

    :returns: A valid C99 type name.

    :raises TemplateRuntimeError: If the primitive cannot be represented as a standard C type.
    """
    return _CFit.get_best_fit(value.bit_length).to_c_type(value, use_standard_types)


_snake_case_pattern_0 = re.compile(r'[\W]+')
_snake_case_pattern_1 = re.compile(r'(?<=_)([A-Z])+')
_snake_case_pattern_2 = re.compile(r'(?<!_)([A-Z])+')


def filter_to_snake_case(value: str) -> str:
    """
    Filter to transform a string into a snake-case token.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_to_snake_case

    .. code-block:: python

        # Given
        template = '{{ "scotec.mcu.Timer" | to_snake_case }} a();'

        # then
        rendered = 'scotec_mcu_timer a();'

    .. invisible-code-block: python

        jinja_filter_tester(filter_to_snake_case, template, rendered)


    .. code-block:: python

        # Given
        template = '{{ "scotec.mcu.TimerHelper" | to_snake_case }} b();'

        # then
        rendered = 'scotec_mcu_timer_helper b();'


    .. invisible-code-block: python

        jinja_filter_tester(filter_to_snake_case, template, rendered)

        template = '{{ " aa bb. cCcAAa_aAa_AAaAa_AAaA_a " | to_snake_case }}'
        rendered = 'aa_bb_c_cc_aaa_a_aa_aaa_aa_aaa_a_a'

        jinja_filter_tester(filter_to_snake_case, template, rendered)

    :param str value: The string to transform into C snake-case.

    :returns: A valid C99 token using the snake-case convention.
    """
    pass0 = _snake_case_pattern_0.sub('_', str.strip(value))
    pass1 = _snake_case_pattern_1.sub(lambda x: x.group(0).lower(), pass0)
    return _snake_case_pattern_2.sub(lambda x: '_' + x.group(0).lower(), pass1)


@templateEnvironmentFilter
def filter_to_template_unique_name(env: SupportsTemplateEnv, base_token: str) -> str:
    """
    Filter that takes a base token and forms a name that is very
    likely to be unique within the template the filter is invoked. This
    name is also very likely to be a valid C identifier.

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

        from nunavut.lang.c import filter_to_template_unique_name

    .. code-block:: python

        # Given
        template  = '{{ "foo" | to_template_unique_name }},{{ "Foo" | to_template_unique_name }},'
        template += '{{ "fOO" | to_template_unique_name }}'

        # then
        rendered = '_foo0_,_foo1_,_fOO0_'

    .. invisible-code-block: python

        jinja_filter_tester(filter_to_template_unique_name, template, rendered)

    .. code-block:: python

        # Given
        template = '{{ "i like coffee" | to_template_unique_name }}'

        # then
        rendered = '_i like coffee0_'

    .. invisible-code-block: python

        jinja_filter_tester(filter_to_template_unique_name, template, rendered)


    :param str base_token: A token to include in the base name.
    :returns: A name that is likely to be valid C identifier and is likely to
        be unique within the file generated by the current template.
    """
    if len(base_token) > 0:
        adj_base_token = base_token[0:1].lower() + base_token[1:]
    else:
        adj_base_token = base_token

    return _UniqueNameGenerator.ensure_generator_in_globals(env.globals)('c', adj_base_token, '_', '_')
