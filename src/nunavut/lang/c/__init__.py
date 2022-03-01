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
import fractions
import functools
import re
import typing

import pydsdl

from nunavut._utilities import YesNoDefault

from ...templates import (
    template_language_filter,
    template_language_list_filter,
    template_language_test,
    template_volatile_filter,
)
from .. import Dependencies
from .. import Language as BaseLanguage
from .._common import IncludeGenerator, TokenEncoder, UniqueNameGenerator


class Language(BaseLanguage):
    """
    Concrete, C-specific :class:`nunavut.lang.Language` object.
    """

    @staticmethod
    def _handle_stropping_failure(
        encoder: TokenEncoder, stropped: str, token_type: str, pending_error: RuntimeError
    ) -> str:
        """
        If the generic stropping results in either `^_[A-Z]` or `^__` we handle the failure
        with c-specific logic.
        """
        m = re.match(r"^_+([A-Z]?)", stropped)
        if m:
            # Resolve the conflict between C's global identifier rules and our desire to use
            # '_' as a stropping prefix:
            return "_{}{}".format(m.group(1).lower(), stropped[m.end() :])

        # we couldn't help after all. raise the pending error.
        raise pending_error

    @functools.lru_cache(maxsize=None)
    def _get_token_encoder(self) -> TokenEncoder:
        """
        Caching getter to ensure we don't have to recompile TokenEncoders for each filter invocation.
        """
        return TokenEncoder(self, stropping_failure_handler=self._handle_stropping_failure)

    def get_includes(self, dep_types: Dependencies) -> typing.List[str]:
        std_includes = []  # type: typing.List[str]
        if self.get_config_value_as_bool("use_standard_types"):
            std_includes.append("stdlib.h")
            # we always include stdlib if standard types are in use since initializers
            # require the use of NULL
            if dep_types.uses_integer:
                std_includes.append("stdint.h")
            if dep_types.uses_bool:
                std_includes.append("stdbool.h")
            if dep_types.uses_primitive_static_array:
                # We include this for memset.
                std_includes.append("string.h")
        return ["<{}>".format(include) for include in sorted(std_includes)]

    def filter_id(self, instance: typing.Any, id_type: str = "any") -> str:
        raw_name = self.default_filter_id_for_target(instance)

        vne = self._get_token_encoder()
        return vne.strop(raw_name, id_type)


@template_language_filter(__name__)
def filter_id(language: Language, instance: typing.Any, id_type: str = "any") -> str:
    """
    Filter that produces a valid C identifier for a given object. The encoding may not
    be reversible.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_id


    .. code-block:: python

        # Given
        I = 'I \u2764 c'

        # and
        template = '{{ I | id }}'

        # then
        rendered = 'I_zX2764_c'


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

    .. code-block:: python

        # Given
        I = 'EMACRO_TOKEN'

        # and
        template = '{{ I | id("macro") }}'

        # then
        rendered = '_eMACRO_TOKEN'

    .. invisible-code-block: python

        jinja_filter_tester(filter_id, template, rendered, 'c', I=I)


    :param any instance:        Any object or data that either has a name property or can be converted
                                to a string.
    :param str id_type:         A type of identifier. For C this value can be 'typedef', 'macro', 'function', or 'enum'.
                                use 'any' to apply stropping rules for all identifier types to the instance.
    :return: A token that is a valid identifier for C, is not a reserved keyword, and is transformed
              in a deterministic manner based on the provided instance.
    """
    return language.filter_id(instance, id_type)


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

    :return: A valid C preprocessor identifier token.
    """
    macrofied_value = filter_to_screaming_snake_case(str(value))
    if not language.enable_stropping:
        return macrofied_value
    else:
        return language.filter_id(macrofied_value, "macro")


_CFit_T = typing.TypeVar("_CFit_T", bound="_CFit")


@enum.unique
class _CFit(enum.Enum):
    IN_8 = 8
    IN_16 = 16
    IN_32 = 32
    IN_64 = 64

    def to_std_int(self, is_signed: bool) -> str:
        return "{}int{}_t".format(("" if is_signed else "u"), self.value)

    def to_c_int(self, is_signed: bool) -> str:
        if self.value == 8:
            intname = "char"
        elif self.value == 16:
            intname = "int"
        elif self.value == 32:
            intname = "long"
        else:
            intname = "long long"

        if not is_signed:
            intname = "unsigned " + intname

        return intname

    def to_c_float(self) -> str:
        if self.value == 8 or self.value == 16 or self.value == 32:
            return "float"
        else:
            return "double"

    def to_c_type(
        self, value: pydsdl.PrimitiveType, language: BaseLanguage, inttype_prefix: typing.Optional[str] = None
    ) -> str:
        use_standard_types = language.get_config_value_as_bool("use_standard_types")
        safe_prefix = "" if not use_standard_types or inttype_prefix is None else inttype_prefix
        if isinstance(value, pydsdl.UnsignedIntegerType):
            return safe_prefix + (self.to_c_int(False) if not use_standard_types else self.to_std_int(False))
        elif isinstance(value, pydsdl.SignedIntegerType):
            return safe_prefix + (self.to_c_int(True) if not use_standard_types else self.to_std_int(True))
        elif isinstance(value, pydsdl.FloatType):
            return self.to_c_float()
        elif isinstance(value, pydsdl.BooleanType):
            return language.get_named_types()["boolean"]
        elif isinstance(value, pydsdl.VoidType):
            return "void"
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
                "Cannot emit a standard type for a primitive that is larger than 64 bits ({}).".format(bit_length)
            )
        return cls(bestfit)


@template_language_filter(__name__)
def filter_type_from_primitive(language: Language, value: pydsdl.PrimitiveType) -> str:
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

    .. code-block:: python

        # Given
        template = '{{ int_64_type | type_from_primitive }}'

        # then
        rendered = 'int64_t'


    .. invisible-code-block: python

        test_type = pydsdl.SignedIntegerType(64, pydsdl.PrimitiveType.CastMode.SATURATED)
        jinja_filter_tester(filter_type_from_primitive,
                            template,
                            rendered,
                            'c',
                            int_64_type=test_type)

    :param str value: The dsdl primitive to transform.

    :return: A valid C99 type name.

    :raises RuntimeError: If the primitive cannot be represented as a standard C type.

        .. invisible-code-block: python

            template = '{{ unsigned_int_32_type | type_from_primitive }}'

            class UnknownType(pydsdl.IntegerType):
                def __init__(self, bit_length):
                    super().__init__(32, pydsdl.PrimitiveType.CastMode.TRUNCATED)
                    self._bit_length = bit_length

                @property
                def inclusive_value_range(self):
                    raise NotImplementedError

                def __str__(self):
                    return 'test dummy'

            try:
                jinja_filter_tester(filter_type_from_primitive,
                            template,
                            'foo',
                            'c',
                            unsigned_int_32_type=UnknownType(32))
                assert False
            except RuntimeError:
                pass

            try:
                jinja_filter_tester(filter_type_from_primitive,
                                template,
                                'foo',
                                'c',
                                unsigned_int_32_type=UnknownType(128))
                assert False
            except RuntimeError:
                pass


    """
    return _CFit.get_best_fit(value.bit_length).to_c_type(value, language)


_snake_case_pattern_0 = re.compile(r"[\W]+")  # 'port.SubjectIDList'  -> 'port_SubjectIDList'
_snake_case_pattern_1 = re.compile(r"(?<=[A-Z])([A-Z][a-z]+)")  # 'port_SubjectIDList'  -> 'port_SubjectID_list'
_snake_case_pattern_2 = re.compile(r"(?<=_)([A-Z])+")  # 'port_SubjectID_list' -> 'port_subjectID_list'
_snake_case_pattern_3 = re.compile(r"(?<=[a-z])([A-Z])+")  # 'port_subjectID_list' -> 'port_subject_id_list'


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

    :return: A valid C99 token using the snake-case convention.
    """
    pass0 = _snake_case_pattern_0.sub("_", str.strip(value))
    pass1 = _snake_case_pattern_1.sub(lambda x: "_" + x.group(0).lower(), pass0)
    pass2 = _snake_case_pattern_2.sub(lambda x: x.group(0).lower(), pass1)
    return _snake_case_pattern_3.sub(lambda x: "_" + x.group(0).lower(), pass2).lower()


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


@template_volatile_filter
def filter_to_template_unique_name(_: typing.Any, base_token: str) -> str:
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
        from nunavut.lang._common import UniqueNameGenerator

    .. code-block:: python

        # Given
        template  = '{{ "foo" | to_template_unique_name }},{{ "Foo" | to_template_unique_name }},'
        template += '{{ "fOO" | to_template_unique_name }}'

        # then
        rendered = '_foo0_,_foo1_,_fOO0_'

    .. invisible-code-block: python

        UniqueNameGenerator.reset()
        jinja_filter_tester(filter_to_template_unique_name, template, rendered, 'c')

    .. code-block:: python

        # Given
        template = '{{ "i like coffee" | to_template_unique_name }}'

        # then
        rendered = '_i like coffee0_'

    .. invisible-code-block: python

        UniqueNameGenerator.reset()
        jinja_filter_tester(filter_to_template_unique_name, template, rendered, 'c')


    :param str base_token: A token to include in the base name.
    :return: A name that is likely to be valid C identifier and is likely to
        be unique within the file generated by the current template.
    """
    if len(base_token) > 0:
        adj_base_token = base_token[0:1].lower() + base_token[1:]
    else:
        adj_base_token = base_token

    return UniqueNameGenerator.get_instance()("c", adj_base_token, "_", "_")


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
        my_type.short_name = '_Foo'
        my_type.version.major = 1
        my_type.version.minor = 2

        # and
        template = '{{ my_type | short_reference_name }}'

        # then, with stropping enabled
        rendered = '_foo_1_2'

    .. invisible-code-block: python

        jinja_filter_tester(filter_short_reference_name, template, rendered, 'c', my_type=my_type)

    With stropping disabled:

    .. code-block:: python

        rendered = '_Foo_1_2'

    .. invisible-code-block: python

        config_overrides = {'nunavut.lang.c': {'enable_stropping': False }}
        lctx = configurable_language_context_factory(config_overrides, 'c')
        jinja_filter_tester(filter_short_reference_name, template, rendered, lctx, my_type=my_type)

    :param pydsdl.CompositeType t: The DSDL type to get the reference name for.
    """
    return language.filter_short_reference_name(t)


@template_language_list_filter(__name__)
def filter_includes(language: Language, t: pydsdl.CompositeType, sort: bool = True) -> typing.List[str]:
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

        # You can suppress std includes by setting use_standard_types to False under
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

    return IncludeGenerator(language, t).generate_include_filepart_list(language.extension, sort)


def filter_to_static_assertion_value(obj: typing.Any) -> int:
    """
    .. invisible-code-block: python

        from nunavut.lang.c import filter_to_static_assertion_value

    Tries to convert a Python object into a value compatible with static comparisons in C. This allows stable comparison
    of static values in headers to promote consistency and version compatibility in generated code.

    Will raise a ValueError if the object provided does not (yet) have an available conversion in this function.

    .. invisible-code-block: python

        try:
            jinja_filter_tester(filter_to_static_assertion_value,
                                '{{ 3.14 | to_static_assertion_value }}',
                                'foo',
                                'c')
            assert False
        except ValueError:
            pass

    Currently supported types are string:

    .. code-block:: python

         # given
        template = '{{ "Any" | to_static_assertion_value }}'

        # then
        rendered = '1556001108'

    .. invisible-code-block: python

        jinja_filter_tester(filter_to_static_assertion_value, template, rendered, 'c')

    int:

    .. code-block:: python

         # given
        template = '{{ 123 | to_static_assertion_value }}'

        # then
        rendered = '123'

    .. invisible-code-block: python

        jinja_filter_tester(filter_to_static_assertion_value, template, rendered, 'c')

    and bool:

    .. code-block:: python

         # given
        template = '{{ True | to_static_assertion_value }}'

        # then
        rendered = '1'

    .. invisible-code-block: python

        jinja_filter_tester(filter_to_static_assertion_value, template, rendered, 'c')

    """

    if isinstance(obj, bool):
        return 1 if obj else 0
    if isinstance(obj, int):
        return obj
    if isinstance(obj, str):
        from zlib import crc32

        return crc32(bytearray(obj, "utf-8"))

    raise ValueError("Cannot convert object of type {} into an integer in a stable manner.".format(type(obj)))


@template_language_filter(__name__)
def filter_constant_value(language: Language, constant: pydsdl.Constant) -> str:
    """
    Renders the specified constant as a literal. This is a shorthand for :func:`filter_literal`.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_constant_value
        from unittest.mock import MagicMock, PropertyMock
        import fractions
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


    Floating point values are converted as fractions to ensure no python-specific transformations are applied:

    .. code-block:: python

         # given a float value using a fraction of 355/113
        template = '{{ almost_pi | constant_value }}'

        # ...the rendered value with include that fraction as a division statement.
        rendered = '((float) (355.0 / 113.0))'

    .. invisible-code-block: python

        almost_pi = pydsdl.Rational(fractions.Fraction('355/113'))
        almost_pi_constant = pydsdl.Constant(pydsdl.FloatType(32, pydsdl.PrimitiveType.CastMode.TRUNCATED),
                                            'almost_pi',
                                             almost_pi)

        jinja_filter_tester(filter_constant_value, template, rendered, 'c', almost_pi=almost_pi_constant)


        template = '{{ three | constant_value }}'

        # ...the rendered value with include that fraction as a division statement.
        rendered = '((float) 3.0)'

        three = pydsdl.Rational(fractions.Fraction('3.0'))
        three_constant = pydsdl.Constant(pydsdl.FloatType(32, pydsdl.PrimitiveType.CastMode.TRUNCATED),
                                         'three',
                                         three)

        jinja_filter_tester(filter_constant_value, template, rendered, 'c', three=three_constant)

    """
    return filter_literal(language, constant.value.native_value, constant.data_type)


@template_language_filter(__name__)
def filter_literal(
    language: Language,
    value: typing.Union[fractions.Fraction, bool, int],
    ty: pydsdl.Any,
    cast_format: typing.Optional[str] = None,
) -> str:
    """
    Renders the specified value of the specified type as a literal.
    """
    if cast_format is None:
        maybe_cast_format = language.get_option("cast_format")
        if not isinstance(maybe_cast_format, str):
            raise RuntimeError("cast_format language option was missing or invalid.")
        cast_format = maybe_cast_format
        del maybe_cast_format
    if isinstance(ty, pydsdl.BooleanType):
        return str(language.valuetoken_true if value else language.valuetoken_false)

    elif isinstance(ty, pydsdl.IntegerType):
        out = (
            str(value)
            + "U" * isinstance(ty, pydsdl.UnsignedIntegerType)
            + "L" * (ty.bit_length > 16)
            + "L" * (ty.bit_length > 32)
        )
        assert isinstance(out, str)
        return out

    elif isinstance(ty, pydsdl.FloatType):
        if value.denominator == 1:
            expr = "{}.0".format(value.numerator)
        else:
            expr = "({}.0 / {}.0)".format(value.numerator, value.denominator)
        cast = filter_type_from_primitive(language, ty)
        return cast_format.format(type=cast, value=expr)

    else:
        raise ValueError("Cannot construct a literal from an instance of {}".format(type(ty).__name__))


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
    ns = t.full_namespace.split(".")

    full_path = ns + [language.filter_short_reference_name(t, YesNoDefault.NO)]
    not_stropped = "_".join(full_path)
    if language.enable_stropping:
        return language.filter_id(not_stropped)
    else:
        return not_stropped


def filter_to_standard_bit_length(t: pydsdl.PrimitiveType) -> int:
    """
    Returns the nearest standard bit length of a type as an int.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_to_standard_bit_length
        import pydsdl

    .. code-block:: python

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


@template_language_test(__name__)
def is_zero_cost_primitive(language: Language, t: pydsdl.PrimitiveType) -> bool:
    """
    Assuming that the target platform is IEEE754-conformant detects whether the native in-memory representation of a
    value of the supplied primitive type is the same as its on-the-wire representation defined by the DSDL
    Specification.

    For instance; all little-endian, IEEE754-conformant platforms have compatible in-memory representations of
    int8, int16, int32, int64, uint8, uint16, uint32, uint64, float32, float64.
    Values of other primitive types typically require some transformations (e.g., float16).

    It follows that arrays, certain composite types, and some other entities composed of zero-cost composites
    are also zero-cost types, but such non-trivial conjectures are not recognized by this function.

    Raises a :class:`TypeError` if the argument is not a value of type :class:`pydsdl.PrimitiveType`.

    .. invisible-code-block: python

        from nunavut.lang.c import is_zero_cost_primitive
        import pydsdl

    .. code-block:: python

        # Given
        i7  = pydsdl.SignedIntegerType(7, pydsdl.PrimitiveType.CastMode.SATURATED)
        u32 = pydsdl.UnsignedIntegerType(32, pydsdl.PrimitiveType.CastMode.TRUNCATED)
        f16 = pydsdl.FloatType(16, pydsdl.PrimitiveType.CastMode.TRUNCATED)
        f32 = pydsdl.FloatType(32, pydsdl.PrimitiveType.CastMode.SATURATED)
        bl = pydsdl.BooleanType(pydsdl.PrimitiveType.CastMode.SATURATED)

        # and
        template = (
            '{{ i7  is zero_cost_primitive }} '
            '{{ u32 is zero_cost_primitive }} '
            '{{ f16 is zero_cost_primitive }} '
            '{{ f32 is zero_cost_primitive }} '
            '{{ bl is zero_cost_primitive }}'
        )

        # then
        rendered = 'False True False True False'

    .. invisible-code-block: python
        config_overrides = {'nunavut.lang.c': {'options': {'target_endianness': 'little' }}}
        lctx = configurable_language_context_factory(config_overrides, 'c')
        jinja_filter_tester(is_zero_cost_primitive, template, rendered, lctx, i7=i7, u32=u32, f16=f16, f32=f32, bl=bl)

        # ensure unknown types given to test raise a TypeError
        try:
            jinja_filter_tester(is_zero_cost_primitive, template, 'True', lctx, u32=int(32))
            assert False
        except TypeError:
            pass

        # big endian is never zero cost.
        config_overrides = {'nunavut.lang.c': {'options': {'target_endianness': 'big'}}}
        lctx = configurable_language_context_factory(config_overrides, 'c')
        jinja_filter_tester(is_zero_cost_primitive,
                            template,
                            'False False False False False',
                            lctx, i7=i7, u32=u32, f16=f16, f32=f32, bl=bl)

    """
    if language.get_option("target_endianness") != "little":
        # We must explicitly target a little endian platform to get
        # zero cost ser/des.
        return False

    if isinstance(t, pydsdl.IntegerType):
        out = t.standard_bit_length
        assert isinstance(out, bool)
        return out

    if isinstance(t, pydsdl.FloatType):
        return t.bit_length in (32, 64)  # float16 is excluded

    if isinstance(t, pydsdl.BooleanType):
        return False

    raise TypeError("Zero-cost predicate is not defined on " + type(t).__name__)


@template_language_filter(__name__)
def filter_is_zero_cost_primitive(language: Language, t: pydsdl.PrimitiveType) -> str:
    """
    Deprecated as a filter. Please use test version.

    .. invisible-code-block: python

        from nunavut.lang.c import filter_is_zero_cost_primitive, is_zero_cost_primitive
        import pydsdl

        u32 = pydsdl.UnsignedIntegerType(32, pydsdl.PrimitiveType.CastMode.TRUNCATED)

    .. code-block: python

        # Instead of this
        deprecated_template = '{{ u32  | is_zero_cost_primitive }}'

        # do this
        correct_template = '{{ u32 is zero_cost_primitive }}'

    .. invisible-code-block: python

        config_overrides = {'nunavut.lang.c': {'options': {'target_endianness': 'little' }}}
        lctx = configurable_language_context_factory(config_overrides, 'c')

        jinja_filter_tester(filter_is_zero_cost_primitive, deprecated_template, 'True', lctx, u32=u32)
        jinja_filter_tester(is_zero_cost_primitive, correct_template, 'True', lctx, u32=u32)

    """
    return str(is_zero_cost_primitive(language, t))
