#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
"""
    Filters for generating C++. All filters in this
    module will be available in the template's global namespace as ``cpp``.
"""


import fractions
import functools
import io
import re
import textwrap
import typing

import pydsdl

from nunavut._dependencies import Dependencies
from nunavut._templates import (
    template_environment_list_filter,
    template_language_filter,
    template_language_list_filter,
    template_language_test,
)
from nunavut._utilities import YesNoDefault
from nunavut.jinja.environment import Environment
from nunavut.lang._common import IncludeGenerator, TokenEncoder, UniqueNameGenerator
from nunavut.lang._config import ConstructorConvention, SpecialMethod
from nunavut.lang._language import Language as BaseLanguage
from nunavut.lang.c import _CFit
from nunavut.lang.c import filter_literal as c_filter_literal


class Language(BaseLanguage):
    """
    Concrete, C++-specific :class:`nunavut.lang.Language` object.
    """

    CPP_STD_EXTRACT_NUMBER_PATTERN = re.compile(r"(?:gnu|c)\+\+(\d(?:\w))")

    @staticmethod
    def _handle_stropping_or_encoding_failure(
        encoder: TokenEncoder, stropped: str, token_type: str, pending_error: RuntimeError
    ) -> str:
        """
        If the generic stropping fails we take one last look to see if there is something c++-specific we can do.
        """
        # Note that this is imprecise because C++ does not allow identifiers to start with an underscore if they are in
        # the global namespace, however, we don't have an AST for the C++ we're generating so there's no way to know if
        # the given token is global. Since this library is about generating code from DSDL and no DSDL identifier should
        # be in the global namespace (except for the top-level namespace for the datatypes) we assume that the token is
        # not.
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
        return TokenEncoder(
            self,
            stropping_failure_handler=self._handle_stropping_or_encoding_failure,
            encoding_failure_handler=self._handle_stropping_or_encoding_failure,
        )

    def _standard_version(self) -> int:
        """
        .. invisible-code-block: python

           from nunavut.lang import LanguageContextBuilder

           # test c++17
           language = LanguageContextBuilder(include_experimental_languages=True)\
               .set_target_language("cpp")\
               .set_target_language_configuration_override("options", { "std":"c++17"})\
               .create()\
               .get_target_language()

           assert language._standard_version() == 17

           # test c++14
           language = LanguageContextBuilder(include_experimental_languages=True)\
               .set_target_language("cpp")\
               .set_target_language_configuration_override("options", { "std":"c++14"})\
               .create()\
               .get_target_language()
           assert language._standard_version() == 14

           # test gnu++20
           language = LanguageContextBuilder(include_experimental_languages=True)\
               .set_target_language("cpp")\
               .set_target_language_configuration_override("options", { "std":"gnu++20"})\
               .create()\
               .get_target_language()

           assert language._standard_version() == 20
        """
        std = str(self.get_option("std", ""))

        match = self.CPP_STD_EXTRACT_NUMBER_PATTERN.match(std)

        if match is not None and len(match.groups()) >= 1:
            return int(match.group(1))
        else:
            return 0

    def _has_variant(self) -> bool:
        """
        .. invisible-code-block: python

           from nunavut.lang import LanguageClassLoader

           # test c++17
           language = LanguageContextBuilder(include_experimental_languages=True)\
               .set_target_language("cpp")\
               .set_target_language_configuration_override("options", { "std":"c++17"})\
               .create()\
               .get_target_language()

           assert language._has_variant()

           # test c++14
           language = LanguageContextBuilder(include_experimental_languages=True)\
               .set_target_language("cpp")\
               .set_target_language_configuration_override("options", { "std":"c++14"})\
               .create()\
               .get_target_language()

           assert not language._has_variant()

           # test gnu++20
           language = LanguageContextBuilder(include_experimental_languages=True)\
               .set_target_language("cpp")\
               .set_target_language_configuration_override("options", { "std":"gnu++20"})\
               .create()\
               .get_target_language()

           assert language._has_variant()
        """
        return self._standard_version() >= 17

    def _add_additional_globals(self, globals_map: typing.Dict[str, typing.Any]) -> None:
        """
        Make additional globals available in the cpp jinja templates
        """
        globals_map["ConstructorConvention"] = ConstructorConvention
        globals_map["SpecialMethod"] = SpecialMethod

    def get_includes(self, dep_types: Dependencies) -> typing.List[str]:
        """
        Get includes for c++ source.

        .. invisible-code-block: python

            from nunavut.lang import Language, LanguageContextBuilder
            from nunavut._dependencies import Dependencies

            def do_includes_test(override_vla_include, override_allocator_include):

                foobar_vla_header_name = "foobar_vla.hpp"
                foobar_allocator_header_name = "foobar_allocator.hpp"
                language_options = {
                    "variable_array_type_include": '' if not override_vla_include else foobar_vla_header_name,
                    "allocator_include": '' if not override_allocator_include else foobar_allocator_header_name
                }

                lang_cpp = (
                    LanguageContextBuilder(include_experimental_languages=True)
                        .set_target_language("cpp")
                        .set_target_language_configuration_override("options", language_options)
                        .create()
                        .get_target_language()
                )

                test_dependencies = Dependencies()
                test_dependencies.uses_variable_length_array = True

                # If we override the include we should not provide the default
                # variable array include.

                found_foobar_vla_header_name = False
                found_foobar_allocator_header_name = False
                for include in lang_cpp.get_includes(test_dependencies):
                    if foobar_vla_header_name in include:
                        found_foobar_vla_header_name = True
                    if foobar_allocator_header_name in include:
                        found_foobar_allocator_header_name = True

                if override_vla_include:
                    assert found_foobar_vla_header_name
                else:
                    assert not found_foobar_vla_header_name

                if override_allocator_include:
                    assert found_foobar_allocator_header_name
                else:
                    assert not found_foobar_allocator_header_name

            do_includes_test(True, True)
            do_includes_test(True, False)
            do_includes_test(False, False)
            do_includes_test(False, True)
        """
        std_includes = []  # type: typing.List[str]
        std_includes.append("limits")  # we always include limits to support static assertions
        if self.get_config_value_as_bool("use_standard_types"):
            if dep_types.uses_integer:
                std_includes.append("cstdint")
            if dep_types.uses_array or dep_types.uses_primitive_static_array:
                std_includes.append("array")
            if dep_types.uses_boolean_static_array:
                std_includes.append("bitset")
        if dep_types.uses_union and self._has_variant():
            std_includes.append("variant")
        includes_formatted = ["<{}>".format(include) for include in sorted(std_includes)]

        allocator_include = str(self.get_option("allocator_include", ""))
        if len(allocator_include) > 0:
            includes_formatted.append(allocator_include)

        if dep_types.uses_variable_length_array:
            variable_array_include = str(self.get_option("variable_array_type_include", ""))
            if len(variable_array_include) > 0:
                includes_formatted.append(variable_array_include)

        return includes_formatted

    def filter_id(self, instance: typing.Any, id_type: str = "any") -> str:
        raw_name = self.default_filter_id_for_target(instance)

        return self._get_token_encoder().strop(raw_name, id_type)

    def create_bitset_decl(self, type: str, max_size: int) -> str:
        return "std::bitset<{MAX_SIZE}>".format(MAX_SIZE=max_size)

    def create_array_decl(self, type: str, max_size: int) -> str:
        return "std::array<{TYPE},{MAX_SIZE}>".format(TYPE=type, MAX_SIZE=max_size)

    def create_vla_decl(self, type: str, max_size: int) -> str:
        variable_array_type_template = self.get_option("variable_array_type_template")
        if not isinstance(variable_array_type_template, str) or len(variable_array_type_template) == 0:
            raise RuntimeError("You must specify a value for the 'variable_array_type_template' option.")
        rebind_allocator = "std::allocator_traits<allocator_type>::rebind_alloc<{TYPE}>".format(TYPE=type)
        return variable_array_type_template.format(TYPE=type, MAX_SIZE=max_size, REBIND_ALLOCATOR=rebind_allocator)


@template_language_test(__name__)
def uses_std_variant(language: Language) -> bool:
    """
    Uses query for std variant.

    If the language options contain an ``std`` entry for C++ and the specified standard includes the
    ``std::variant`` type added to the language at C++17 then this value is true. The logic included
    in this filter can be stated as "options has key std and the value for options.std evaluates to
    C++ version 17 or greater" but the implementation is able to parse out actual compiler flags like
    ``gnu++20`` and is aware of any overrides to suppress use of the standard variant type even if
    available.

    Example:

        .. code-block:: python

            template = '''
                {%- ifuses "std_variant" -%}
                    #include <variant>
                {%- else -%}
                    #include "user_variant.h"
                {%- endifuses -%}
            '''

        .. invisible-code-block: python

            # test c++17
            options = {"std": "c++17"}
            lctx = (
                LanguageContextBuilder(include_experimental_languages=True)
                    .set_target_language("cpp")
                    .set_target_language_configuration_override(Language.WKCV_LANGUAGE_OPTIONS, options)
                    .create()
            )
            jinja_filter_tester(None, template, '#include <variant>', lctx)

            # test c++14
            options = {"std": "c++14"}
            lctx = (
                LanguageContextBuilder(include_experimental_languages=True)
                    .set_target_language("cpp")
                    .set_target_language_configuration_override(Language.WKCV_LANGUAGE_OPTIONS, options)
                    .create()
            )
            jinja_filter_tester(None, template, '#include "user_variant.h"', lctx)

    """
    return language._has_variant()


@template_language_filter(__name__)
def filter_constant_value(language: Language, constant: pydsdl.Constant) -> str:
    """
    Renders the specified value of the specified type as a literal.
    """
    return c_filter_literal(language, constant.value.native_value, constant.data_type)


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
    return c_filter_literal(language, value, ty, cast_format)


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


@template_language_filter(__name__)
def filter_id(language: Language, instance: typing.Any, id_type: str = "any") -> str:
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
        rendered = 'I_like_czX002BzX002B'


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
        I = 'I   really like \t coffee'

        # and
        template = '{{ I | id }}'

        # then
        rendered = 'I_really_like_coffee'

    .. invisible-code-block: python

        jinja_filter_tester(filter_id, template, rendered, 'cpp', I=I)

    :param any instance:        Any object or data that either has a name property or can be converted
                                to a string.
    :return: A token that is a valid identifier for C and C++, is not a reserved keyword, and is transformed
              in a deterministic manner based on the provided instance.
    """
    return language.filter_id(instance, id_type)


@template_language_filter(__name__)
def filter_type(language: Language, obj: typing.Any) -> str:
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
def filter_open_namespace(
    language: Language, full_namespace: str, bracket_on_next_line: bool = True, linesep: str = "\n"
) -> str:
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

        lctx = (
            LanguageContextBuilder(include_experimental_languages=True)
                .set_target_language("cpp")
                .set_target_language_configuration_override(Language.WKCV_ENABLE_STROPPING, False)
                .create()
        )
        jinja_filter_tester(filter_open_namespace, template, rendered, lctx, T=T)

        lctx = (
            LanguageContextBuilder(include_experimental_languages=True)
                .set_target_language("cpp")
                .set_target_language_configuration_override(Language.WKCV_ENABLE_STROPPING, True)
                .create()
        )
        jinja_filter_tester(filter_open_namespace, template, rendered, lctx, T=T)

    :param str full_namespace: A dot-separated namespace string.
    :param bool bracket_on_next_line: If True (the default) then the opening
        brackets are placed on a newline after the namespace keyword.
    :param str linesep: The line-separator to use when emitting new lines.
                        By default this is ``\\n``.

    :return: C++ namespace declarations with opening brackets.
    """

    with io.StringIO() as content:
        first = True
        for name in full_namespace.split("."):
            if first:
                first = False
            else:
                content.write(linesep)
            content.write("namespace ")
            if language.enable_stropping:
                content.write(language.filter_id(name))
            else:
                content.write(name)
            if bracket_on_next_line:
                content.write(linesep)
            else:
                content.write(" ")
            content.write("{")
        return content.getvalue()


@template_language_filter(__name__)
def filter_close_namespace(
    language: Language, full_namespace: str, omit_comments: bool = False, linesep: str = "\n"
) -> str:
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

    :return: C++ namespace declarations with opening brackets.
    """
    with io.StringIO() as content:
        first = True
        for name in reversed(full_namespace.split(".")):
            if first:
                first = False
            else:
                content.write(linesep)

            content.write("}")
            if not omit_comments:
                content.write(" // namespace ")
                if language.enable_stropping:
                    content.write(language.filter_id(name))
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
    ns_parts = t.full_namespace.split(".")
    if language.enable_stropping:
        ns = list(map(functools.partial(filter_id, language), ns_parts))
    else:
        ns = ns_parts

    full_path = ns + [language.filter_short_reference_name(t)]
    return "::".join(full_path)


@template_language_filter(__name__)
def filter_full_macro_name(language: Language, t: pydsdl.CompositeType) -> str:
    """
    Provides a string usable as part of a macro name that is the full namespace, typename, major, and minor version
    for a given composite type.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_full_macro_name
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
        template = '{{ my_obj | full_macro_name }}'

        # then, with stropping enabled
        rendered = 'any__int__2Foo_1_2'

    .. invisible-code-block: python

        my_obj.short_name = my_obj.full_name.split('.')[-1]
        my_obj.full_namespace = '.'.join(my_obj.full_name.split('.')[:-1])

        jinja_filter_tester(filter_full_macro_name, template, rendered, 'cpp', my_obj=my_obj)

    :param pydsdl.CompositeType t: The DSDL type to get the fully-resolved reference name for.
    """
    ns_parts = t.full_namespace.split(".")
    if language.enable_stropping:
        ns = list(map(functools.partial(filter_id, language), ns_parts))
    else:
        ns = ns_parts

    full_path = ns + [language.filter_short_reference_name(t)]
    return "_".join(full_path)


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
        my_type.has_parent_service = False

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
        my_type.has_parent_service = False

    .. code-block:: python

        # Given a type with legal C++ characters
        my_type.short_name = 'Struct_'
        my_type.version.major = 0
        my_type.version.minor = 1

        # and
        template = '{{ my_type | short_reference_name }}'

        # then, with stropping enabled
        rendered = 'Struct__0_1'

    .. invisible-code-block: python

        jinja_filter_tester(filter_short_reference_name, template, rendered, 'cpp', my_type=my_type)

    .. invisible-code-block: python
        my_service_type = MagicMock(spec=pydsdl.ServiceType)
        my_service_type.version = MagicMock()
        my_service_type.parent_service = None
        my_service_type.has_parent_service = False
        my_service_type.request_type = MagicMock(spec=pydsdl.StructureType)
        my_service_type.request_type.has_parent_service = True
        my_service_type.request_type.short_name = "Request"
        my_service_type.request_type.version = my_service_type.version
        my_service_type.request_type.parent_service = my_service_type
        my_service_type.response_type = MagicMock(spec=pydsdl.StructureType)
        my_service_type.response_type.has_parent_service = True
        my_service_type.response_type.short_name = "Response"
        my_service_type.response_type.version = my_service_type.version
        my_service_type.response_type.parent_service = my_service_type

    .. code-block:: python

        # Given a service type
        my_service_type.short_name = 'Struct_'
        my_service_type.version.major = 0
        my_service_type.version.minor = 1

        # and
        template = '''
        {{ my_service_type | short_reference_name }}
        {{ my_service_type.request_type | short_reference_name }}
        {{ my_service_type.response_type | short_reference_name }}
        '''

        # then, with stropping enabled
        rendered = '''
        Struct_
        Request_0_1
        Response_0_1
        '''

    .. invisible-code-block: python
        jinja_filter_tester(filter_short_reference_name, template, rendered, 'cpp', my_service_type=my_service_type)

    :param pydsdl.CompositeType t: The DSDL type to get the reference name for.
    """
    if isinstance(t, pydsdl.ServiceType):
        if YesNoDefault.test_truth(YesNoDefault.DEFAULT, language.enable_stropping):
            return language.filter_id(t.short_name)
        else:
            return str(t.short_name)
    return language.filter_short_reference_name(t)


@template_language_list_filter(__name__)
@template_environment_list_filter
def filter_includes(
    language: Language, env: Environment, t: pydsdl.CompositeType, sort: bool = True
) -> typing.List[str]:
    """
    Returns a list of all include paths for a given type.

    :param pydsdl.CompositeType t: The type to scan for dependencies.
    :param bool sort: If true the returned list will be sorted.
    :return: a list of include headers needed for a given type.


    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_includes
        from unittest.mock import MagicMock
        import pydsdl

        my_type = MagicMock(spec=pydsdl.UnionType)
        my_type.version = MagicMock()
        my_type.parent_service = None

    .. code-block:: python

        # Listing the includes for a union with only integer types:
        template = "{% for include in my_type | includes -%}{{include}}{%- endfor %}"

        # cstdint will normally be generated. limits is always generated.
        rendered = "<cstdint><limits>"

    .. invisible-code-block: python

        jinja_filter_tester(filter_includes, template, rendered, "cpp", my_type=my_type)

    .. code-block:: python

        # You can suppress std includes by setting use_standard_types to False under
        # nunavut.lang.cpp
        rendered = "<limits>"

    .. invisible-code-block: python

        lctx = (
            LanguageContextBuilder(include_experimental_languages=True)
                .set_target_language("cpp")
                .set_target_language_configuration_override("use_standard_types", False)
                .create()
        )
        jinja_filter_tester(filter_includes, template, rendered, lctx, my_type=my_type)
    """
    try:
        omit_serialization_support = env.globals["nunavut"].support["omit"]
    except KeyError:
        omit_serialization_support = False
    return IncludeGenerator(language, t, omit_serialization_support).generate_include_filepart_list(
        language.extension, sort
    )


@template_language_filter(__name__)
def filter_destructor_name(language: Language, instance: pydsdl.Any) -> str:
    """
    Returns a token that is the local destructor name. For example:

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_destructor_name
        from unittest.mock import MagicMock
        import pydsdl

        my_type = MagicMock(spec=pydsdl.FixedLengthArrayType)
        my_type.element_type = MagicMock(spec=pydsdl.UnsignedIntegerType)
        my_type.element_type.bit_length = 8
        my_type.element_type.cast_mode = pydsdl.PrimitiveType.CastMode.SATURATED


    .. code-block:: python

        # Given a pydsdl.FixedLengthArrayType "my_type":
        my_type.short_name = 'Foo'
        my_type.capacity = 2

        # and
        template = 'ptr->{{ my_type | destructor_name }}'

        # then
        rendered = 'ptr->~array<std::uint8_t,2>'

    .. invisible-code-block: python

        jinja_filter_tester(filter_destructor_name, template, rendered, 'cpp', my_type=my_type)


    :param pydsdl.CompositeType t: The type to generate a destructor template for.
    :return: A destructor name token.
    """
    declaration = filter_declaration(language, instance)
    declaration_parts = declaration.split("<")
    declaration_parts[0] = declaration_parts[0].split("::")[-1]
    return "~" + "<".join(declaration_parts)


@template_language_filter(__name__)
def filter_explicit_decorator(language: Language, instance: pydsdl.Any, special_method: SpecialMethod) -> str:
    """
    Emit the constructor name, decorated with "explicit" if it has only one argument
    """
    name: str = language.filter_short_reference_name(instance)
    arg_count: int = len(instance.fields_except_padding) + (
        0 if language.get_option("allocator_is_default_constructible") else 1
    )
    if special_method == SpecialMethod.InitializingConstructorWithAllocator and arg_count == 1:
        return f"explicit {name}"
    else:
        return f"{name}"


@template_language_filter(__name__)
def filter_default_value_initializer(language: Language, instance: pydsdl.Any) -> str:
    """
    Emit a default initialization expression for the given instance if primitive, array,
    or composite.
    """
    if (
        isinstance(instance, pydsdl.PrimitiveType)
        or isinstance(instance, pydsdl.ArrayType)
        or isinstance(instance, pydsdl.CompositeType)
    ):
        return "{}"
    return ""


def needs_initializing_value(special_method: SpecialMethod) -> bool:
    """Helper method used by filter_value_initializer()"""
    return special_method == SpecialMethod.InitializingConstructorWithAllocator or needs_rhs(special_method)


def needs_rhs(special_method: SpecialMethod) -> bool:
    """Helper method used by filter_value_initializer()"""
    return special_method in (
        SpecialMethod.CopyConstructorWithAllocator,
        SpecialMethod.MoveConstructorWithAllocator,
    )


def needs_allocator(instance: pydsdl.Any) -> bool:
    """Helper method used by filter_value_initializer()"""
    return isinstance(instance.data_type, pydsdl.VariableLengthArrayType) or isinstance(
        instance.data_type, pydsdl.CompositeType
    )


def needs_vla_init_args(instance: pydsdl.Any, special_method: SpecialMethod) -> bool:
    """Helper method used by filter_value_initializer()"""
    return special_method == SpecialMethod.AllocatorConstructor and isinstance(
        instance.data_type, pydsdl.VariableLengthArrayType
    )


def needs_move(special_method: SpecialMethod) -> bool:
    """Helper method used by filter_value_initializer()"""
    return special_method == SpecialMethod.MoveConstructorWithAllocator


def requires_initialization(instance: pydsdl.Any) -> bool:
    """Helper method used by filter_value_initializer()"""
    return (
        isinstance(instance.data_type, pydsdl.PrimitiveType)
        or isinstance(instance.data_type, pydsdl.ArrayType)
        or isinstance(instance.data_type, pydsdl.CompositeType)
    )


def assemble_initializer_expression(
    wrap: str, rhs: str, leading_args: typing.List[str], trailing_args: typing.List[str]
) -> str:
    """Helper method used by filter_value_initializer()"""
    if wrap:
        rhs = "{}({})".format(wrap, rhs)
    args = []
    if rhs:
        args.append(rhs)
    args = leading_args + args + trailing_args
    return "{" + ", ".join(args) + "}"


@template_language_filter(__name__)
def filter_value_initializer(language: Language, instance: pydsdl.Any, special_method: SpecialMethod) -> str:
    """
    Emit an initialization expression for a C++ special method.
    """

    value_initializer: str = ""
    if requires_initialization(instance):
        wrap: str = ""
        rhs: str = ""
        leading_args: typing.List[str] = []
        trailing_args: typing.List[str] = []

        if needs_initializing_value(special_method):
            if needs_rhs(special_method):
                rhs = "rhs."
            rhs += language.filter_id(instance)

        if needs_vla_init_args(instance, special_method):
            constructor_args = language.get_option("variable_array_type_constructor_args")
            if isinstance(constructor_args, str) and len(constructor_args) > 0:
                trailing_args.append(constructor_args.format(MAX_SIZE=instance.data_type.capacity))

        if needs_allocator(instance):
            if language.get_option("ctor_convention") == ConstructorConvention.UsesLeadingAllocator.value:
                leading_args.extend(["std::allocator_arg", "allocator"])
            else:
                trailing_args.append("allocator")

        if needs_move(special_method):
            wrap = "std::move"

        value_initializer = assemble_initializer_expression(wrap, rhs, leading_args, trailing_args)

    return value_initializer


@template_language_filter(__name__)
def filter_default_construction(language: Language, instance: pydsdl.Any, reference: str) -> str:
    if (
        isinstance(instance, pydsdl.CompositeType)
        and language.get_option("ctor_convention") != ConstructorConvention.Default.value
    ):
        return f"{reference}.get_allocator()"
    else:
        return ""


@template_language_filter(__name__)
def filter_declaration(language: Language, instance: pydsdl.Any) -> str:
    """
    Emit a declaration statement for the given instance.
    """
    if isinstance(instance, pydsdl.PrimitiveType) or isinstance(instance, pydsdl.VoidType):
        return filter_type_from_primitive(language, instance)
    elif isinstance(instance, pydsdl.VariableLengthArrayType):
        return language.create_vla_decl(filter_declaration(language, instance.element_type), instance.capacity)
    elif isinstance(instance, pydsdl.ArrayType):
        if isinstance(instance.element_type, pydsdl.BooleanType):
            return language.create_bitset_decl(filter_declaration(language, instance.element_type), instance.capacity)
        else:
            return language.create_array_decl(filter_declaration(language, instance.element_type), instance.capacity)
    else:
        return filter_full_reference_name(language, instance)


@template_language_filter(__name__)
def filter_type_from_primitive(language: Language, value: pydsdl.PrimitiveType) -> str:
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

        lctx = (
            LanguageContextBuilder(include_experimental_languages=True)
                .set_target_language("cpp")
                .set_target_language_configuration_override("use_standard_types", False)
                .create()
        )
        jinja_filter_tester(filter_type_from_primitive,
                            template,
                            rendered,
                            lctx,
                            unsigned_int_32_type=test_type)

    :param str value: The dsdl primitive to transform.

    :return: A valid C++ type name.

    :raises TemplateRuntimeError: If the primitive cannot be represented as a standard C++ type.
    """
    return _CFit.get_best_fit(value.bit_length).to_c_type(value, language, "std::")


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
        return ""
    else:
        return "::".join(namespace_list) + "::"


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
        from nunavut.lang._common import UniqueNameGenerator

    .. code-block:: python

        # Given
        template  = '{{ "foo" | to_template_unique_name }},{{ "Foo" | to_template_unique_name }},'
        template += '{{ "fOO" | to_template_unique_name }}'

        # then
        rendered = '_foo0_,_foo1_,_fOO0_'

    .. invisible-code-block: python

        UniqueNameGenerator.reset()
        jinja_filter_tester(filter_to_template_unique_name, template, rendered, 'cpp')

    .. code-block:: python

        # Given
        template = '{{ "i like coffee" | to_template_unique_name }}'

        # then
        rendered = '_i like coffee0_'

    .. invisible-code-block: python

        UniqueNameGenerator.reset()
        jinja_filter_tester(filter_to_template_unique_name, template, rendered, 'cpp')


    :param str base_token: A token to include in the base name.
    :return: A name that is likely to be valid C++ identifier and is likely to
        be unique within the file generated by the current template.
    """
    if len(base_token) > 0:
        adj_base_token = base_token[0:1].lower() + base_token[1:]
    else:
        adj_base_token = base_token

    return UniqueNameGenerator.get_instance()("cpp", adj_base_token, "_", "_")


def filter_as_boolean_value(value: bool) -> str:
    """
    Filter a boolean expression to produce a valid C++ "true" or "false" token.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_as_boolean_value

    .. code-block:: python

        assert "true" == filter_as_boolean_value(True)
        assert "false" == filter_as_boolean_value(False)

    """
    return "true" if value else "false"


@template_language_filter(__name__)
def filter_indent_if_not(language: Language, text: str, depth: int = 1) -> str:
    r"""
    Emit indent characters as configured for the language but only as needed. This
    is different from the built-in indent filter in that it may add or remove spaces based on the
    existing indent.

    .. invisible-code-block: python

        from nunavut.lang.cpp import filter_indent_if_not

    .. code-block:: python

        # Given a string with an existing indent of 4 spaces...
        template  = '{{ "    int a = 1;" | indent_if_not }}'

        # then if cpp.indent == 4 we expect no change.
        rendered = '    int a = 1;'

    .. invisible-code-block: python

        assert_language_config_value('cpp', 'indent', '4', 'this test expected an indent of 4')
        jinja_filter_tester(filter_indent_if_not, template, rendered, 'cpp')

    .. code-block:: python

        # If the indent is only 3 spaces...
        template  = '{{ "   int a = 1;" | indent_if_not }}'

        # then if cpp.indent == 4 we expect 4 spaces (i.e. not 7 spaces)
        rendered = '    int a = 1;'

    .. invisible-code-block: python

        jinja_filter_tester(filter_indent_if_not, template, rendered, 'cpp')

    .. code-block:: python

        # We can also specify multiple indents...
        template  = '{{ "int a = 1;" | indent_if_not(2) }}'

        rendered = '        int a = 1;'

    .. invisible-code-block: python

        jinja_filter_tester(filter_indent_if_not, template, rendered, 'cpp')

    .. code-block:: python

        # ...or no indent
        template  = '{{ "    int a = 1;" | indent_if_not(0) }}'

        rendered = 'int a = 1;'

    .. invisible-code-block: python

        jinja_filter_tester(filter_indent_if_not, template, rendered, 'cpp')

    .. code-block:: python

        # Finally, note that blank lines are not indented.
        template  = '''
            {%- set block_text -%}
                int a = 1;
                {# empty line #}
                int b = 2;
            {%- endset -%}{{ block_text | indent_if_not(1) }}'''

        rendered  = '    int a = 1;'
        rendered += '\n'
        rendered += '\n'  # Nothing but spaces so this is stripped
        rendered += '    int b = 2;'

    .. invisible-code-block: python

        jinja_filter_tester(filter_indent_if_not, template, rendered, 'cpp')

    :param text: The text to indent.
    :param depth: The number of indents. For example, if depth is 2 and the indent for this language is
        4 spaces then the text will be indented by 8 spaces.

    """
    configured_indent = int(language.get_config_value("indent"))
    lines = text.splitlines(keepends=True)
    result = ""
    for i in range(0, len(lines)):
        line = lines[i].lstrip()
        if len(line) == 0:
            # don't indent blank lines
            result += "\n"
        else:
            result += (" " * (depth * configured_indent)) + line

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

    :return: The minimum, required bits needed to store some values of the given type.
    """
    return typing.cast(int, min(t.bit_length_set))


@functools.lru_cache(3)
def _make_textwrap(width: int, initial_indent: str, subseqent_indent: str) -> textwrap.TextWrapper:
    return textwrap.TextWrapper(
        width=width,
        initial_indent=initial_indent,
        subsequent_indent=subseqent_indent,
        break_on_hyphens=True,
        break_long_words=False,
        replace_whitespace=False,
    )


def _make_block_comment(text: str, prefix: str, comment: str, suffix: str, indent: int, line_length: int) -> str:
    doc_lines = text.splitlines()  # type: typing.List[str]
    indented_comment = "{}{}".format(" " * indent, comment)

    commented_doc_lines = []  # type: typing.List[str]

    if len(doc_lines) > 0:
        if len(prefix) > 0:
            commented_doc_lines.append(prefix)
        else:
            commented_doc_lines.extend(
                _make_textwrap(width=line_length, initial_indent=comment, subseqent_indent=indented_comment).wrap(
                    doc_lines.pop(0)
                )
            )

    tw = _make_textwrap(width=line_length, initial_indent=indented_comment, subseqent_indent=indented_comment)

    for docline in doc_lines:
        # The docs for textwrap.TextWrapper.wrap say:
        # "If the wrapped output has no content, the returned list is empty."
        # This behavior cannot be altered so we need to work around it manually.
        commented_doc_lines.extend(tw.wrap(docline) if docline.strip() else [indented_comment])

    if len(suffix) > 0 and len(commented_doc_lines) > 0:
        commented_doc_lines.append("{}{}".format(" " * indent, suffix))

    return "\n".join(commented_doc_lines)


@template_language_filter(__name__)
def filter_block_comment(language: Language, text: str, style: str, indent: int = 0, line_length: int = 100) -> str:
    """
    Reformats text as a block comment using Python's :meth:`textwrap.TextWrapper.wrap` function.

    :param text: The text to emit as a block comment.
    :param style: Dictates the style of comments (see return documentation for valid style names).
    :param indent: The number of spaces to indent the comments by (tab indent is not supported. Sorry).
    :param line_length: The soft maximum width to wrap text at. Some violations may occur where long words are used.

    :returns str: A comment block. Comment styles supported are:

        .. invisible-code-block: python

            from nunavut.lang.cpp import filter_block_comment

            # Initial, private, verification:
            text = '''This is a list:
             1. one
             2. two
             3. three'''

            template = '''
                {{ text | block_comment('cpp-doxygen', 4, 50) }}
                void some_method();
            '''

            rendered = '''
                ///
                /// This is a list:
                ///  1. one
                ///  2. two
                ///  3. three
                ///
                void some_method();
            '''

            jinja_filter_tester(filter_block_comment, template, rendered, 'cpp', text=text)

            # handle empty case
            text = ''

            template = '''
                {{ text | block_comment('cpp-doxygen', 4, 50) }}
                void some_method();
            '''

            rendered = '''
                {}
                void some_method();
            '''.format('')

            jinja_filter_tester(filter_block_comment, template, rendered, 'cpp', text=text)

            template = '''
                {{ text | block_comment('c', 4, 50) }}
                void some_method();
            '''

            jinja_filter_tester(filter_block_comment, template, rendered, 'cpp', text=text)

            # Cover ValueError clause
            template = "{{ text | block_comment('not a style', 4, 24) }}"

            try:
                jinja_filter_tester(filter_block_comment, template, rendered, 'cpp', text=text)
                assert False
            except ValueError:
                pass

        **javadoc**

        .. code-block:: python

            # Given a type with the following docstring
            text = 'This is a bunch of documentation.'

            # and
            template = '''
                {{ text | block_comment('javadoc', 4, 24) }}
                void some_method();
            '''

            # the output will be
            rendered = '''
                /**
                 * This is a bunch
                 * of documentation.
                 */
                void some_method();
            '''

        .. invisible-code-block: python

            jinja_filter_tester(filter_block_comment, template, rendered, 'cpp', text=text)

        **cpp-doxygen**

        .. code-block:: python

            # that same template using the cpp style of doxygen...
            template = '''
                {{ text | block_comment('cpp-doxygen', 4, 24) }}
                void some_method();
            '''

            # ...will be
            rendered = '''
                ///
                /// This is a bunch
                /// of
                /// documentation.
                ///
                void some_method();
            '''

        .. invisible-code-block: python

            jinja_filter_tester(filter_block_comment, template, rendered, 'cpp', text=text)

        **cpp**

        .. code-block:: python

            # also supported is cpp style...
            template = '''
                {{ text | block_comment('cpp', 4, 24) }}
                void some_method();
            '''

            rendered = '''
                // This is a bunch of
                // documentation.
                void some_method();
            '''

        .. invisible-code-block: python

            jinja_filter_tester(filter_block_comment, template, rendered, 'cpp', text=text)

        **c**

        .. code-block:: python

            # c style...
            template = '''
                {{ text | block_comment('c', 4, 24) }}
                void some_method();
            '''

            rendered = '''
                /*
                 * This is a bunch
                 * of documentation.
                 */
                void some_method();
            '''

        .. invisible-code-block: python

            jinja_filter_tester(filter_block_comment, template, rendered, 'cpp', text=text)

        **qt**

        .. code-block:: python

            # and Qt style...
            template = '''
                {{ text | block_comment('qt', 4, 24) }}
                void some_method();
            '''

            rendered = '''
                /*!
                 * This is a bunch
                 * of documentation.
                 */
                void some_method();
            '''

        .. invisible-code-block: python

            jinja_filter_tester(filter_block_comment, template, rendered, 'cpp', text=text)

            from nunavut.lang import LanguageContextBuilder

            comment_configs = (
                LanguageContextBuilder(include_experimental_languages=True)
                    .set_target_language('cpp')
                    .create()
                    .get_target_language()
                    .get_config_value_as_dict('comment_styles')
            )
            if len(comment_configs) != 5:
                raise RuntimeError('A comment style was added but not documented here. Please document it/them.')

    """

    config_styles = language.get_config_value_as_dict(
        "comment_styles"
    )  # type: typing.Mapping[str, typing.Mapping[str, str]]

    try:
        config_style = config_styles[style.lower()]
    except KeyError:
        raise ValueError(
            "{} is not a supported comment style. Supported is c, cpp, cpp-doxygen, and javadoc".format(style)
        )

    return _make_block_comment(
        text=text,
        prefix=config_style["prefix"],
        comment=config_style["comment"],
        suffix=config_style["suffix"],
        indent=indent,
        line_length=line_length,
    )
