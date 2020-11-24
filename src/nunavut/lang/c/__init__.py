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
import fractions
import re
import typing

import pydsdl

from ...templates import (SupportsTemplateContext, template_context_filter,
                          template_language_filter, template_language_list_filter)
from .. import Language, _UniqueNameGenerator
from .._common import IncludeGenerator

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


@template_language_filter(__name__)
def filter_id(language: Language,
              instance: typing.Any) -> str:
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

        jinja_filter_tester(filter_id, template, rendered, 'c', I=I)


    .. code-block:: python

        # Given
        I = 'if'

        # and
        template = '{{ I | id }}'

        # then
        rendered = '_if'


    .. invisible-code-block: python

        jinja_filter_tester(filter_id, template, rendered, 'c', I=I)


    .. code-block:: python

        # Given
        I = '_Reserved'

        # and
        template = '{{ I | id }}'

        # then
        rendered = '_reserved'

    .. invisible-code-block: python

        jinja_filter_tester(filter_id, template, rendered, 'c', I=I)


    :param any instance:        Any object or data that either has a name property or can be converted
                                to a string.
    :returns: A token that is a valid identifier for C, is not a reserved keyword, and is transformed
              in a deterministic manner based on the provided instance.
    """
    if hasattr(instance, 'name'):
        raw_name = str(instance.name)  # type: str
    else:
        raw_name = str(instance)

    reserved_identifiers = frozenset(language.get_reserved_identifiers())
    vne = VariableNameEncoder(language.stropping_prefix, language.stropping_suffix, language.encoding_prefix)
    return vne.strop(raw_name,
                     reserved_identifiers,
                     C_RESERVED_PATTERNS)


@template_language_filter(__name__)
def filter_macrofy(language: Language, value: str) -> str:
    """
    Filter to transform an input into a valid C preprocessor identifier token.

    .. invisible-code-block: python

        from nunavut.lang import LanguageContext, Language
        from nunavut.lang.c import filter_macrofy, filter_id
        from unittest.mock import MagicMock

    .. code-block:: python

        # Given
        template = '#ifndef {{ "my full name" | macrofy }}'

        # then
        rendered = '#ifndef MY_FULL_NAME'


    .. invisible-code-block: python

        jinja_filter_tester(filter_macrofy, template, rendered, 'c')

    Note that individual tokens are not stropped so the appearance of an identifier
    in the ``SCREAMING_SNAKE_CASE`` output my be different then the token as it appears
    on its own. For example:

    .. code-block:: python

        # "register" is reserved so it will be stropped if it appears as an
        # identifier...
        template = '''#ifndef {{ "namespaced.Type.register" | macrofy }}
        {{ "register" | id }}
        '''

        # ...but it will not be stropped within the macro.
        rendered = '''#ifndef NAMESPACED_TYPE_REGISTER
        _register
        '''

    .. invisible-code-block: python

        jinja_filter_tester([filter_macrofy, filter_id], template, rendered, 'c')

    If stropping is enabled, however, the entire token generated by this filter will be stropped:

    .. code-block:: python

        # Given
        template = '#ifndef {{ "_starts_with_underscore" | macrofy }}'

        # then
        rendered = '#ifndef _sTARTS_WITH_UNDERSCORE'

    .. invisible-code-block: python

        jinja_filter_tester(filter_macrofy, template, rendered, 'c')

    And again with stropping disabled:

    .. code-block:: python

        # Given
        template = '#ifndef {{ "_starts_with_underscore" | macrofy }}'

        # then with stropping disabled
        rendered = '#ifndef _STARTS_WITH_UNDERSCORE'

    .. invisible-code-block: python

        config_overrides = {'nunavut.lang.c': {'enable_stropping': False }}
        lctx = configurable_language_context_factory(config_overrides, 'c')
        jinja_filter_tester(filter_macrofy, template, rendered, lctx)

    :param str value: The value to transform.

    :returns: A valid C preprocessor identifier token.
    """
    macrofied_value = filter_to_screaming_snake_case(str(value))
    if not language.enable_stropping:
        return macrofied_value
    else:
        return filter_id(language, macrofied_value)


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

    def to_c_type(self,
                  value: pydsdl.PrimitiveType,
                  language: Language,
                  inttype_prefix: typing.Optional[str] = None) -> str:
        use_standard_types = language.get_config_value_as_bool('use_standard_types')
        safe_prefix = '' if not use_standard_types or inttype_prefix is None else inttype_prefix
        if isinstance(value, pydsdl.UnsignedIntegerType):
            return safe_prefix + (self.to_c_int(False) if not use_standard_types else self.to_std_int(False))
        elif isinstance(value, pydsdl.SignedIntegerType):
            return safe_prefix + (self.to_c_int(True) if not use_standard_types else self.to_std_int(True))
        elif isinstance(value, pydsdl.FloatType):
            return self.to_c_float()
        elif isinstance(value, pydsdl.BooleanType):
            return language.get_named_types()['boolean']
        elif isinstance(value, pydsdl.VoidType):
            return 'void'
        else:
            raise RuntimeError('{} is not a known PrimitiveType'.format(type(value).__name__))

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


@template_language_filter(__name__)
def filter_type_from_primitive(language: Language,
                               value: pydsdl.PrimitiveType) -> str:
    """
    Filter to transform a pydsdl :class:`~pydsdl.PrimitiveType` into
    a valid C type.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_type_from_primitive
        import pydsdl


    .. code-block:: python

        # Given
        template = '{{ unsigned_int_32_type | type_from_primitive }}'

        # then
        rendered = 'uint32_t'


    .. invisible-code-block: python

        test_type = pydsdl.UnsignedIntegerType(32, pydsdl.PrimitiveType.CastMode.TRUNCATED)
        jinja_filter_tester(filter_type_from_primitive,
                            template,
                            rendered,
                            'c',
                            unsigned_int_32_type=test_type)

    :param str value: The dsdl primitive to transform.

    :returns: A valid C99 type name.

    :raises TemplateRuntimeError: If the primitive cannot be represented as a standard C type.
    """
    return _CFit.get_best_fit(value.bit_length).to_c_type(value, language)


_snake_case_pattern_0 = re.compile(r'[\W]+')                    # 'port.SubjectIDList'  -> 'port_SubjectIDList'
_snake_case_pattern_1 = re.compile(r'(?<=[A-Z])([A-Z][a-z]+)')  # 'port_SubjectIDList'  -> 'port_SubjectID_list'
_snake_case_pattern_2 = re.compile(r'(?<=_)([A-Z])+')           # 'port_SubjectID_list' -> 'port_subjectID_list'
_snake_case_pattern_3 = re.compile(r'(?<=[a-z])([A-Z])+')       # 'port_subjectID_list' -> 'port_subject_id_list'


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

        jinja_filter_tester(filter_to_snake_case, template, rendered, 'c')


    .. code-block:: python

        # Given
        template = '{{ "scotec.mcu.TimerHelper" | to_snake_case }} b();'

        # then
        rendered = 'scotec_mcu_timer_helper b();'


    .. invisible-code-block: python

        jinja_filter_tester(filter_to_snake_case, template, rendered, 'c')

    .. code-block:: python

        # and Given
        template = '{{ "SCOTEC_MCU_TimerHelper" | to_snake_case }} b();'

        # then
        rendered = 'scotec_mcu_timer_helper b();'


    .. invisible-code-block: python

        jinja_filter_tester(filter_to_snake_case, template, rendered, 'c')

        template = '{{ " aa bb. cCcAAa_aAa_AAaAa_AAaA_a " | to_snake_case }}'
        rendered = 'aa_bb_c_cc_a_aa_a_aa_a_aa_aa_a_aa_a_a'

        jinja_filter_tester(filter_to_snake_case, template, rendered, 'c')

    :param str value: The string to transform into C snake-case.

    :returns: A valid C99 token using the snake-case convention.
    """
    pass0 = _snake_case_pattern_0.sub('_', str.strip(value))
    pass1 = _snake_case_pattern_1.sub(lambda x: '_' + x.group(0).lower(), pass0)
    pass2 = _snake_case_pattern_2.sub(lambda x: x.group(0).lower(), pass1)
    return _snake_case_pattern_3.sub(lambda x: '_' + x.group(0).lower(), pass2).lower()


def filter_to_screaming_snake_case(value: str) -> str:
    """
    Filter to transform a string into a SCREAMING_SNAKE_CASE token.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_to_screaming_snake_case

    .. code-block:: python

        # Given
        template = '{{ "scotec.mcu.Timer" | to_screaming_snake_case }} a();'

        # then
        rendered = 'SCOTEC_MCU_TIMER a();'

    .. invisible-code-block: python

        jinja_filter_tester(filter_to_screaming_snake_case, template, rendered, 'c')
    """
    return filter_to_snake_case(value).upper()


@template_context_filter
def filter_to_template_unique_name(context: SupportsTemplateContext, base_token: str) -> str:
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
        from nunavut.lang import _UniqueNameGenerator

    .. code-block:: python

        # Given
        template  = '{{ "foo" | to_template_unique_name }},{{ "Foo" | to_template_unique_name }},'
        template += '{{ "fOO" | to_template_unique_name }}'

        # then
        rendered = '_foo0_,_foo1_,_fOO0_'

    .. invisible-code-block: python

        _UniqueNameGenerator.reset()
        jinja_filter_tester(filter_to_template_unique_name, template, rendered, 'c')

    .. code-block:: python

        # Given
        template = '{{ "i like coffee" | to_template_unique_name }}'

        # then
        rendered = '_i like coffee0_'

    .. invisible-code-block: python

        _UniqueNameGenerator.reset()
        jinja_filter_tester(filter_to_template_unique_name, template, rendered, 'c')


    :param str base_token: A token to include in the base name.
    :returns: A name that is likely to be valid C identifier and is likely to
        be unique within the file generated by the current template.
    """
    if len(base_token) > 0:
        adj_base_token = base_token[0:1].lower() + base_token[1:]
    else:
        adj_base_token = base_token

    return _UniqueNameGenerator.get_instance()('c', adj_base_token, '_', '_')


def _to_short_name(language: Language, t: pydsdl.CompositeType) -> str:
    """
    Internal method for producing an un-stropped short_name.
    """
    return '{short}_{major}_{minor}'.format(short=t.short_name, major=t.version.major, minor=t.version.minor)


@template_language_filter(__name__)
def filter_short_reference_name(language: Language, t: pydsdl.CompositeType) -> str:
    """
    Provides a string that is a shorted version of the full reference name.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_short_reference_name
        from unittest.mock import MagicMock
        import pydsdl

        my_type = MagicMock(spec=pydsdl.StructureType)
        my_type.version = MagicMock()
        my_type.parent_service = None

    .. code-block:: python

        # Given a type with illegal C characters
        my_type.short_name = '2Foo'
        my_type.version.major = 1
        my_type.version.minor = 2

        # and
        template = '{{ my_type | short_reference_name }}'

        # then, with stropping enabled
        rendered = '_2Foo_1_2'

    .. invisible-code-block: python

        jinja_filter_tester(filter_short_reference_name, template, rendered, 'c', my_type=my_type)

    With stropping disabled:

    .. code-block:: python

        rendered = '2Foo_1_2'

    .. invisible-code-block: python

        config_overrides = {'nunavut.lang.c': {'enable_stropping': False }}
        lctx = configurable_language_context_factory(config_overrides, 'c')
        jinja_filter_tester(filter_short_reference_name, template, rendered, lctx, my_type=my_type)

    :param pydsdl.CompositeType t: The DSDL type to get the reference name for.
    """
    short_name = _to_short_name(language, t)
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


    .. invisible-code-block: python

        from nunavut.lang.c import filter_includes
        from unittest.mock import MagicMock
        import pydsdl

        my_type = MagicMock(spec=pydsdl.UnionType)
        my_type.version = MagicMock()
        my_type.parent_service = None

    .. code-block:: python

        # Listing the includes for a union with only integer types:
        template = '''{% for include in my_type | includes -%}
        {{include}}
        {% endfor %}'''

        # stdint.h will normally be generated
        rendered = '''<stdint.h>
        <stdlib.h>
        '''

    .. invisible-code-block: python

        jinja_filter_tester(filter_includes, template, rendered, 'c', my_type=my_type)

    .. code-block:: python

        # You can surpress std includes by setting use_standard_types to False under
        # nunavut.lang.c
        rendered = ''

    .. invisible-code-block: python

        config_overrides = {'nunavut.lang.c': {'use_standard_types': False}}
        lctx = configurable_language_context_factory(config_overrides, 'c')
        jinja_filter_tester(filter_includes, template, rendered, lctx, my_type=my_type)

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
def filter_constant_value(language: Language,
                          constant: pydsdl.Constant) -> str:
    """
    Renders the specified constant as a literal. This is a shorthand for :func:`filter_literal`.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_constant_value
        from unittest.mock import MagicMock
        import pydsdl

        my_true_constant = MagicMock()
        my_true_constant.data_type = MagicMock(spec=pydsdl.BooleanType)

    .. code-block:: python

         # given
        template = '{{ my_true_constant | constant_value }}'

        # then
        rendered = 'true'

    .. invisible-code-block: python

        jinja_filter_tester(filter_constant_value, template, rendered, 'c', my_true_constant=my_true_constant)

    Language configuration can control the output of some constant tokens. For example, to use
    non-standard true and false values in c:

    .. code-block:: python

         # given
        template = '{{ my_true_constant | constant_value }}'

        # then, if true = 'NUNAVUT_TRUE' in the named_values for nunavut.lang.c
        rendered = 'NUNAVUT_TRUE'

    .. invisible-code-block: python

        config_overrides = {'nunavut.lang.c': {'named_values': {'true': 'NUNAVUT_TRUE'}}}
        lctx = configurable_language_context_factory(config_overrides, 'c')
        jinja_filter_tester(filter_constant_value, template, rendered, lctx, my_true_constant=my_true_constant)

    """
    return filter_literal(language, constant.value.native_value, constant.data_type)


@template_language_filter(__name__)
def filter_literal(language: Language,
                   value: typing.Union[fractions.Fraction, bool],
                   ty: pydsdl.Any) -> str:
    """
    Renders the specified value of the specified type as a literal.
    """
    if isinstance(ty, pydsdl.BooleanType):
        return str(language.valuetoken_true if value else language.valuetoken_false)

    elif isinstance(ty, pydsdl.IntegerType):
        out = str(value) + 'U' * isinstance(ty, pydsdl.UnsignedIntegerType) \
            + 'L' * (ty.bit_length > 16) + 'L' * (ty.bit_length > 32)
        assert isinstance(out, str)
        return out

    elif isinstance(ty, pydsdl.FloatType):
        if value.denominator == 1:
            expr = '{}.0'.format(value.numerator)
        else:
            expr = '({}.0 / {}.0)'.format(value.numerator, value.denominator)
        cast = filter_type_from_primitive(language, ty)
        return '(({}) {})'.format(cast, expr)

    else:
        raise ValueError('Cannot construct a C literal from an instance of {}'.format(type(ty).__name__))


@template_language_filter(__name__)
def filter_full_reference_name(language: Language, t: pydsdl.CompositeType) -> str:
    """
    Provides a string that is the full namespace, typename, major, and minor version for a given composite type.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_full_reference_name
        from unittest.mock import MagicMock
        import pydsdl

        my_obj = MagicMock()
        my_obj.has_parent_service = False
        my_obj.version = MagicMock()

    .. code-block:: python

        # Given a type with illegal characters for C++
        my_obj.full_name = 'any.int.2Foo'
        my_obj.full_namespace = 'any.int'
        my_obj.version.major = 1
        my_obj.version.minor = 2

        # and
        template = '{{ my_obj | full_reference_name }}'

        # then, with stropping enabled
        rendered = 'any_int_2Foo_1_2'

    .. invisible-code-block: python

        my_obj.short_name = my_obj.full_name.split('.')[-1]
        jinja_filter_tester(filter_full_reference_name, template, rendered, 'c', my_obj=my_obj)

    :param pydsdl.CompositeType t: The DSDL type to get the fully-resolved reference name for.
    """
    ns = t.full_namespace.split('.')

    full_path = ns + [_to_short_name(language, t)]
    not_stropped = '_'.join(full_path)
    if language.enable_stropping:
        return filter_id(language, not_stropped)
    else:
        return not_stropped


def filter_to_standard_bit_length(t: pydsdl.PrimitiveType) -> int:
    """
    Returns the nearest standard bit length of a type as an int.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_to_standard_bit_length
        import pydsdl

    .. code-block: python
        # Given
        I = pydsdl.UnsignedIntegerType(7, pydsdl.PrimitiveType.CastMode.TRUNCATED)

        # and
        template = '{{ I | to_standard_bit_length }}'

        # then
        rendered = '8'

    .. invisible-code-block: python

        jinja_filter_tester(filter_to_standard_bit_length, template, rendered, 'c', I=I)

    """
    return int(_CFit.get_best_fit(t.bit_length).value)


def filter_is_zero_cost_primitive(t: pydsdl.PrimitiveType) -> bool:
    """
    Assuming that the target platform is:

    - little-endian
    - IEEE754-conformant

    ...detects whether the native in-memory representation of a value of the supplied primitive type is the same
    as its on-the-wire representation defined by the DSDL Specification.

    For instance, all conventional platforms (where stated assumptions hold) have compatible in-memory
    representation of int8, int16, int32, int64, uint8, uint16, uint32, uint64, float32, float64.
    Values of other primitive types typically require some transformations (e.g., float16).

    It follows that arrays, certain composite types, and some other entities composed of zero-cost composites
    are also zero-cost types, but such non-trivial conjectures are not recognized by this function.

    Raises a :class:`TypeError` if the argument is not a value of type :class:`pydsdl.PrimitiveType`.

    This filter should actually be a Jinja test, but language support modules currently can only export filters,
    not tests. This may change in a later release.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_is_zero_cost_primitive
        import pydsdl

    .. code-block: python
        # Given
        i7  = pydsdl.SignedIntegerType(7, pydsdl.PrimitiveType.CastMode.SATURATED)
        u32 = pydsdl.UnsignedIntegerType(32, pydsdl.PrimitiveType.CastMode.TRUNCATED)
        f16 = pydsdl.FloatType(16, pydsdl.PrimitiveType.CastMode.TRUNCATED)
        f32 = pydsdl.FloatType(32, pydsdl.PrimitiveType.CastMode.SATURATED)

        # and
        template = (
            '{{ i7  | is_zero_cost_primitive }} '
            '{{ u32 | is_zero_cost_primitive }} '
            '{{ f16 | is_zero_cost_primitive }} '
            '{{ f32 | is_zero_cost_primitive }} '
        )

        # then
        rendered = 'False True False True '

    .. invisible-code-block: python

        jinja_filter_tester(filter_is_zero_cost_primitive, template, rendered, 'c', i7=i7, u32=u32, f16=f16, f32=f32)

    """
    if isinstance(t, pydsdl.IntegerType):
        out = t.standard_bit_length
        assert isinstance(out, bool)
        return out

    if isinstance(t, pydsdl.FloatType):
        return t.bit_length in (32, 64)  # float16 is excluded

    if isinstance(t, pydsdl.BooleanType):
        return False

    raise TypeError('Zero-cost predicate is not defined on ' + type(t).__name__)
