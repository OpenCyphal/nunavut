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
import re
import typing

import pydsdl

from ...templates import (template_language_filter,
                          template_language_list_filter)
from .. import Language, _UniqueNameGenerator
from .._common import IncludeGenerator
from ..c import C_RESERVED_PATTERNS, VariableNameEncoder, _CFit
from ..c import filter_literal as c_filter_literal

CPP_RESERVED_PATTERNS = frozenset([*C_RESERVED_PATTERNS])

CPP_NO_DOUBLE_DASH_RULE = re.compile(r'(__)')

DEFAULT_ARRAY_TYPE = 'std::array<{TYPE},{MAX_SIZE}>'


@template_language_filter(__name__)
def filter_constant_value(language: Language,
                          constant: pydsdl.Constant) -> str:
    """
    Renders the specified value of the specified type as a literal.
    """
    return c_filter_literal(language, constant.value.native_value, constant.data_type)


def filter_to_standard_bit_length(t: pydsdl.PrimitiveType) -> int:
    """
    Returns the nearest standard bit length of a type as an int.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_to_standard_bit_length
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

        from nunavut.lang.cpp import filter_is_zero_cost_primitive
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


@template_language_filter(__name__)
def filter_id(language: Language,
              instance: typing.Any) -> str:
    """
    Filter that produces a valid C and/or C++ identifier for a given object. The encoding may not
    be reversible.

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
def filter_type(language: Language,
                obj: typing.Any) -> str:
    """
    Tries to convert a Python object into a c++ typename.

    Will raise a ValueError if the object provided does not (yet) have an available conversion in this function.

    Currently supported types are string:

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_type

    .. code-block:: python

         # given
        template = '{{ "Any" | type }}'

        # then
        rendered = "const char* const"

    .. invisible-code-block: python

        jinja_filter_tester(filter_type, template, rendered, 'cpp')

    int:

    .. code-block:: python

         # given
        template = '{{ 123 | type }}'

        # then
        rendered = 'long long'

    .. invisible-code-block: python

        jinja_filter_tester(filter_type, template, rendered, 'cpp')

    and bool:

    .. code-block:: python

         # given
        template = '{{ True | type }}'

        # then
        rendered = 'bool'

    .. invisible-code-block: python

        jinja_filter_tester(filter_type, template, rendered, 'cpp')

    """

    if isinstance(obj, bool):
        return "bool"
    if isinstance(obj, int):
        return "long long"
    if isinstance(obj, str):
        return "const char* const"

    return filter_type_from_primitive(language, obj)


@template_language_filter(__name__)
def filter_open_namespace(language: Language,
                          full_namespace: str,
                          bracket_on_next_line: bool = True,
                          linesep: str = '\n') -> str:
    """
    Emits c++ opening namespace syntax parsed from a pydsdl "full_namespace",
    dot-separated  value.

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
        {'''

    .. invisible-code-block: python

        # stropping doesn't change our example here.

        lctx = configurable_language_context_factory({'nunavut.lang.cpp': {'enable_stropping': False}}, 'cpp')
        jinja_filter_tester(filter_open_namespace, template, rendered, lctx, T=T)

        lctx = configurable_language_context_factory({'nunavut.lang.cpp': {'enable_stropping': True}}, 'cpp')
        jinja_filter_tester(filter_open_namespace, template, rendered, lctx, T=T)

    :param str full_namespace: A dot-separated namespace string.
    :param bool bracket_on_next_line: If True (the default) then the opening
        brackets are placed on a newline after the namespace keyword.
    :param str linesep: The line-separator to use when emitting new lines.
                        By default this is ``\\n``.

    :returns: C++ namespace declarations with opening brackets.
    """

    with io.StringIO() as content:
        first = True
        for name in full_namespace.split('.'):
            if first:
                first = False
            else:
                content.write(linesep)
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
        return content.getvalue()


@template_language_filter(__name__)
def filter_close_namespace(language: Language,
                           full_namespace: str,
                           omit_comments: bool = False,
                           linesep: str = '\n') -> str:
    """
    Emits c++ closing namespace syntax parsed from a pydsdl "full_namespace",
    dot-separated  value.

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
        } // namespace uavcan'''

    .. invisible-code-block: python

        jinja_filter_tester(filter_close_namespace, template, rendered, 'cpp', T=T)


    :param str full_namespace: A dot-separated namespace string.
    :param bool omit_comments: If True then the comments following the closing
                               bracket are omitted.
    :param str linesep: The line-separator to use when emitting new lines.
                        By default this is ``\\n``

    :returns: C++ namespace declarations with opening brackets.
    """
    with io.StringIO() as content:
        first = True
        for name in reversed(full_namespace.split('.')):
            if first:
                first = False
            else:
                content.write(linesep)

            content.write('}')
            if not omit_comments:
                content.write(' // namespace ')
                if language.enable_stropping:
                    content.write(filter_id(language, name))
                else:
                    content.write(name)
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
        my_obj.has_parent_service = False
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
        my_obj.full_namespace = '.'.join(my_obj.full_name.split('.')[:-1])

        jinja_filter_tester(filter_full_reference_name, template, rendered, 'cpp', my_obj=my_obj)

    :param pydsdl.CompositeType t: The DSDL type to get the fully-resolved reference name for.
    """
    ns_parts = t.full_namespace.split('.')
    if language.enable_stropping:
        ns = list(map(functools.partial(filter_id, language), ns_parts))
    else:
        ns = ns_parts

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
    short_name = '{short}_{major}_{minor}'.format(short=t.short_name, major=t.version.major, minor=t.version.minor)
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
        variable_array_type = language.get_option('variable_array_type')

        if not isinstance(variable_array_type, str):
            raise RuntimeError('variable_array_type language option was missing or invalid.')
        return variable_array_type.format(
            TYPE=filter_declaration(language, instance.element_type),
            MAX_SIZE=instance.capacity)
    elif isinstance(instance, pydsdl.ArrayType):
        return DEFAULT_ARRAY_TYPE.format(
            TYPE=filter_declaration(language, instance.element_type),
            MAX_SIZE=instance.capacity)
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

        # Finally, given a pydsdl.ServiceType "my_service_type":
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
    if isinstance(instance, pydsdl.DelimitedType) or isinstance(instance, pydsdl.StructureType) \
            or isinstance(instance, pydsdl.UnionType):
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
    if isinstance(instance, pydsdl.DelimitedType) or isinstance(instance, pydsdl.StructureType) \
            or isinstance(instance, pydsdl.UnionType):
        return ';'
    elif isinstance(instance, pydsdl.ServiceType):
        return ' // namespace {}'.format(filter_short_reference_name(language, instance))
    else:
        raise ValueError('{} types cannot be redefined.'.format(type(instance).__name__))


@template_language_filter(__name__)
def filter_type_from_primitive(language: Language,
                               value: pydsdl.PrimitiveType) -> str:
    """
    Filter to transform a pydsdl :class:`~pydsdl.PrimitiveType` into
    a valid C++ type.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_type_from_primitive
        import pydsdl


    .. code-block:: python

        # Given
        template = '{{ unsigned_int_32_type | type_from_primitive }}'

        # then
        rendered = 'std::uint32_t'

    .. invisible-code-block: python

        test_type = pydsdl.UnsignedIntegerType(32, pydsdl.PrimitiveType.CastMode.TRUNCATED)
        jinja_filter_tester(filter_type_from_primitive,
                            template,
                            rendered,
                            'cpp',
                            unsigned_int_32_type=test_type)

    Also note that this is sensitive to the ``use_standard_types`` configuration in the language properties:

    .. code-block:: python

        # rendered will be different if use_standard_types is False
        rendered = 'unsigned long'

    .. invisible-code-block: python

        lctx = configurable_language_context_factory({'nunavut.lang.cpp': {'use_standard_types': False}}, 'cpp')
        jinja_filter_tester(filter_type_from_primitive,
                            template,
                            rendered,
                            lctx,
                            unsigned_int_32_type=test_type)

    :param str value: The dsdl primitive to transform.

    :returns: A valid C++ type name.

    :raises TemplateRuntimeError: If the primitive cannot be represented as a standard C++ type.
    """
    return _CFit.get_best_fit(value.bit_length).to_c_type(value, language, 'std::')


def filter_to_namespace_qualifier(namespace_list: typing.List[str]) -> str:
    """
    Converts a list of namespace names into a qualifier string. For example:

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


def filter_minimum_required_capacity_bits(t: pydsdl.SerializableType) -> int:
    """
    Returns the minimum number of bits required to store the deserialized value of a
    pydsdl :class:`~pydsdl.SerializableType`. This capacity may be too small for some
    instances of the value (e.g. variable length arrays).

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_minimum_required_capacity_bits
        import pydsdl
        import pytest

    .. code-block:: python

        # Given
        template = '{{ unsigned_int_32_type | minimum_required_capacity_bits }}'

        # then
        rendered = '32'

    .. invisible-code-block: python

        uint32_truncated_type = pydsdl.UnsignedIntegerType(32, pydsdl.PrimitiveType.CastMode.TRUNCATED)
        jinja_filter_tester(filter_minimum_required_capacity_bits,
                            template,
                            rendered,
                            'cpp',
                            unsigned_int_32_type=uint32_truncated_type)

        # Cover the other cases here. We don't need to pain the user with these gory
        # details so we'll keep them in the hidden block.
        assert filter_minimum_required_capacity_bits(pydsdl.VoidType(1)) == 1
        assert filter_minimum_required_capacity_bits(pydsdl.FixedLengthArrayType(uint32_truncated_type, 2)) == 64
        assert filter_minimum_required_capacity_bits(pydsdl.VariableLengthArrayType(uint32_truncated_type, 2)) == 8

        field_one = pydsdl.Field(pydsdl.UnsignedIntegerType(32, pydsdl.PrimitiveType.CastMode.TRUNCATED), 'one')
        field_two = pydsdl.Field(pydsdl.UnsignedIntegerType(64, pydsdl.PrimitiveType.CastMode.TRUNCATED), 'two')

        test_struct = pydsdl.StructureType(
            name='uavcan.foo',
            version=pydsdl.Version(0, 1),
            attributes=[field_one, field_two],
            deprecated=False,
            fixed_port_id=None,
            source_file_path='',
            has_parent_service = False
        )

        test_union = pydsdl.UnionType(
            name='uavcan.foo',
            version=pydsdl.Version(0, 1),
            attributes=[field_one, field_two],
            deprecated=False,
            fixed_port_id=None,
            source_file_path='',
            has_parent_service = False
        )

        assert filter_minimum_required_capacity_bits(test_struct) == 96
        assert filter_minimum_required_capacity_bits(test_union) == 32 + 8

    :param pydsdl.SerializableType t: The dsdl type.

    :returns: The minimum, required bits needed to store some values of the given type.
    """
    return typing.cast(int, min(t.bit_length_set))
