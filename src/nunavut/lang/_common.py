#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2020  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""Language-specific support in nunavut.

This package contains modules that provide specific support for generating
source for various languages using templates.
"""
import functools
import pathlib
import re
import typing

import pydsdl

from . import Language


class IncludeGenerator:
    def __init__(self, language: Language, t: pydsdl.CompositeType):
        self._type = t
        self._language = language

    def generate_include_filepart_list(self, output_extension: str, sort: bool) -> typing.List[str]:
        dep_types = self._language.get_dependency_builder(self._type).direct()

        path_list = [str(self.make_path(dt, self._language, output_extension)) for dt in dep_types.composite_types]

        if not self._language.omit_serialization_support:
            namespace_path = pathlib.Path("")
            for namespace_part in self._language.support_namespace:
                namespace_path = namespace_path / pathlib.Path(namespace_part)
            path_list += [
                (namespace_path / pathlib.Path(p.name).with_suffix(output_extension)).as_posix()
                for p in self._language.support_files
            ]

        prefer_system_includes = self._language.get_config_value_as_bool("prefer_system_includes", False)
        if prefer_system_includes:
            path_list_with_punctuation = ["<{}>".format(p) for p in path_list]
        else:
            path_list_with_punctuation = ['"{}"'.format(p) for p in path_list]

        if sort:
            return sorted(path_list_with_punctuation) + self._language.get_includes(dep_types)
        else:
            return path_list_with_punctuation + self._language.get_includes(dep_types)

    @classmethod
    def make_path(
        cls,
        dt: pydsdl.CompositeType,
        language: typing.Optional[Language] = None,
        output_extension: typing.Optional[str] = None,
    ) -> pathlib.Path:
        """
        Common method for createing a relative path to a datatype source file.

        .. invisible-code-block: python

            import pydsdl
            from nunavut.lang._common import IncludeGenerator
            from nunavut.lang import Language
            from unittest.mock import MagicMock

            config = {
                        'nunavut.lang.c':
                        {
                            'enable_stropping': True
                        }
                    }

            lctx = configurable_language_context_factory(config, 'c')
            lang_c = lctx.get_target_language()

            test_type = MagicMock(spec=pydsdl.CompositeType)
            test_type.parent_service = False
            test_type.attributes = []
            test_type.full_namespace = 'name.space'
            test_type.short_name = 'typename'
            test_type.version = MagicMock()
            test_type.version.major = 1
            test_type.version.minor = 0

        .. code-block:: python

            assert 'name/space/typename_1_0.h' == IncludeGenerator.make_path(test_type, lang_c, '.h').as_posix()
            assert 'name/space/typename_1_0.h' == IncludeGenerator.make_path(test_type, lang_c).as_posix()
            assert 'name/space/typename_1_0' == IncludeGenerator.make_path(test_type).as_posix()

        """
        if language is None:
            short_name = "{short}_{major}_{minor}".format(
                short=dt.short_name, major=dt.version.major, minor=dt.version.minor
            )
        else:
            short_name = language.filter_short_reference_name(dt, id_type="path")

        if output_extension is None:
            output_extension = "" if language is None else language.extension

        ns_path = pathlib.Path(*cls._make_ns_list(language, dt)) / pathlib.Path(short_name).with_suffix(
            output_extension
        )
        return ns_path

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+

    @classmethod
    def _make_ns_list(cls, language: typing.Optional[Language], dt: pydsdl.SerializableType) -> typing.List[str]:
        if language is not None and language.enable_stropping:
            return [language.filter_id(x, id_type="path") for x in dt.full_namespace.split(".")]
        else:
            return typing.cast(typing.List[str], dt.full_namespace.split("."))


class UniqueNameGenerator:
    """
    Functor used by template filters to obtain a unique name within a given template.
    This should be made available as a private global within each template.
    """

    _singleton = None  # type: typing.Optional['UniqueNameGenerator']

    def __init__(self) -> None:
        self._index_map = {}  # type: typing.Dict[str, typing.Dict[str, int]]

    @classmethod
    def reset(cls) -> None:
        cls._singleton = cls()

    @classmethod
    def get_instance(cls) -> "UniqueNameGenerator":
        if cls._singleton is None:
            raise RuntimeError("No UniqueNameGenerator has been created. Please use reset to create.")
        return cls._singleton

    def __call__(self, key: str, base_token: str, prefix: str, suffix: str) -> str:
        """
        Uses a global index to generate a number unique to a given base_token within a template
        for a given domain (key).
        """
        try:
            keymap = self._index_map[key]
        except KeyError:
            keymap = {}
            self._index_map[key] = keymap

        try:
            next_index = keymap[base_token]
            keymap[base_token] = next_index + 1
        except KeyError:
            next_index = 0
            keymap[base_token] = 1

        return "{prefix}{base_token}{index}{suffix}".format(
            prefix=prefix, base_token=base_token, index=next_index, suffix=suffix
        )


class TokenEncoder:
    """
    One-way transforms from strings of unicode characters into valid identifiers for a given language.

    The behavior of the encoder is entirely driven by language configuration. In the examples below the
    following configuration is used:

    .. code-block:: python
            stropping_prefix = '_pre_'
            stropping_suffix = '_post_'
            encoding_prefix = '_code_'
            reserved_token_patterns_by_type = {
                'var':
                    [
                        '^reserved[A-Za-z]',
                        '^[A-Z]+',
                        '^(__)|(^(_)[A-Z])'
                    ]
            }
            reserved_identifiers = [
                'this_is_reserved',
                '_pre_reservedToken_post_'
            ]
            token_encoding_rules_by_identifier_type = {
                'all':
                    [
                        '(^\\d{1})|([^a-zA-Z0-9_]+)'
                    ]
            }
            whitespace_encoding_char = '_'

    .. invisible-code-block: python

        from nunavut.lang._common import TokenEncoder
        from nunavut.lang import Language

        config = {
                    'nunavut.lang.c':
                    {
                        'stropping_prefix': stropping_prefix,
                        'stropping_suffix': stropping_suffix,
                        'encoding_prefix': encoding_prefix,
                        'reserved_token_patterns_by_type': reserved_token_patterns_by_type,
                        'reserved_identifiers': reserved_identifiers,
                        'token_encoding_rules_by_identifier_type': token_encoding_rules_by_identifier_type,
                        'whitespace_encoding_char': whitespace_encoding_char
                     }
                }

        lctx = configurable_language_context_factory(config, 'c')
        lang_c = lctx.get_target_language()

    .. code-block:: python

        encoder = TokenEncoder(lang_c)
        assert '_code_0061' == encoder.encode_character('a')
        assert 'this_is_not_reserved' == encoder.strop('this_is_not_reserved')
        assert '_pre_this_is_reserved_post_' == encoder.strop('this_is_reserved', 'var')
        assert '_pre_reservedVariableName_post_' == encoder.strop('reservedVariableName', 'var')
        assert '_code_0031CantStartWithNumber' == encoder.strop('1CantStartWithNumber')

        # this shows that encoding happens first then stropping
        assert '_pre_Mem_set_post_' == encoder.strop('Mem set')

        try:
            encoder.strop('reservedToken')
            assert False
        except RuntimeError as e:
            # strop raises RuntimeError if the stropping results in an illegal identifier
            pass

    Languages can also provide additional reserved identifiers in the constructor:

    .. code-block:: python

        encoder = TokenEncoder(lang_c, ['this_is_not_reserved'])

        assert '_pre_this_is_not_reserved_post_' == encoder.strop('this_is_not_reserved')

    .. invisible-code-block: python

        stropping_prefix = '_CODE_'
        encoding_prefix = '_XX_'
        token_encoding_rules_by_identifier_type = {
            'all':
                [
                    '(^\\d{1})|([^a-zA-Z0-9_]+)',
                    '^(__)|(^(_)[A-Z])'
                ]
        }
        config['nunavut.lang.c']['stropping_prefix'] = stropping_prefix
        config['nunavut.lang.c']['encoding_prefix'] = encoding_prefix
        config['nunavut.lang.c']['token_encoding_rules_by_identifier_type'] = token_encoding_rules_by_identifier_type

        lctx = configurable_language_context_factory(config, 'c')
        lang_c = lctx.get_target_language()

        encoder = TokenEncoder(lang_c)

        try:
            encoder.strop('1CantStartWithNumber')
            assert False
        except RuntimeError:
            # strop raises a RuntimeError if the final result is itself reserved.
            pass

    Languages may also provide a handler to be invoked if the automatic stropping fails.

    .. code-block:: python

        def stroppingErrorHandler(encoder: TokenEncoder,
                                 failed_stop: str,
                                 token_type: str,
                                 pending_error: RuntimeError) -> str:
            return 'well_crap'

        encoder = TokenEncoder(lang_c, stropping_failure_handler=stroppingErrorHandler)

        assert 'well_crap' == encoder.strop('reservedToken')

    .. note::
        The token type 'any' is invalid. Any is used to specify patterns that apply to all other token types.
        To strop a token such that it obeys all rules for all token types use the type 'all' instead.

        .. code-block:: python

            encoder = TokenEncoder(lang_c)

            try:
                encoder.strop('foobar', 'all')
                assert False
            except ValueError:
                pass

    """

    def __init__(
        self,
        language: Language,
        additional_reserved_identifiers: typing.Optional[typing.List[str]] = None,
        stropping_failure_handler: typing.Optional[
            typing.Callable[["TokenEncoder", str, str, RuntimeError], str]
        ] = None,
        encoding_failure_handler: typing.Optional[
            typing.Callable[["TokenEncoder", str, str, RuntimeError], str]
        ] = None,
    ) -> None:
        self._reserved_token_patterns_by_type = self._get_map_of_type_to_lists_of_patterns(
            language, "reserved_token_patterns_by_type"
        )
        self._stropping_failure_handler = stropping_failure_handler
        self._encoding_failure_handler = encoding_failure_handler
        self._token_encoding_rules_by_identifier_type = self._get_map_of_type_to_lists_of_patterns(
            language, "token_encoding_rules_by_identifier_type"
        )
        self._reserved_identifiers = language.get_config_value_as_list("reserved_identifiers", default_value=[])
        if additional_reserved_identifiers is not None:
            self._reserved_identifiers = self._reserved_identifiers + additional_reserved_identifiers
        self._stropping_prefix = language.get_config_value("stropping_prefix", "")
        self._stropping_suffix = language.get_config_value("stropping_suffix", "")
        self._encoding_prefix = language.get_config_value("encoding_prefix", "")
        try:
            self._whitespace_encoding_char = language.get_config_value(
                "whitespace_encoding_char"
            )  # type: typing.Optional[str]
        except KeyError:
            self._whitespace_encoding_char = None
        self._collapse_whitespace_when_encoding = language.get_config_value_as_bool("collapse_whitespace_when_encoding")

    def _encoding_filter(self, m: typing.Match) -> str:
        """
        This will encode any illegal characters in an identifier using Python's re.sub function.
        """
        matched_span = m.string[m.start() : m.end()]
        if self._collapse_whitespace_when_encoding and matched_span.isspace():
            if self._whitespace_encoding_char is not None:
                return self._whitespace_encoding_char
            else:
                return self.encode_character(" ")
        else:
            return "".join(map(self.encode_character, matched_span))

    def _matches(
        self, input_string: str, patterns: typing.Union[typing.List[typing.Pattern], typing.List[str]]
    ) -> bool:
        for string_or_pattern in patterns:
            if isinstance(string_or_pattern, str):
                if string_or_pattern == input_string:
                    return True
            elif string_or_pattern.match(input_string):
                return True
        return False

    def _encode(self, token: str, token_type: str, dry_run: bool) -> str:
        encoded = token
        try:
            encoding_rules = self._token_encoding_rules_by_identifier_type[token_type]

            for token_pattern in encoding_rules:
                if not dry_run:
                    encoded = token_pattern.sub(self._encoding_filter, encoded)
                elif token_pattern.match(encoded):
                    raise RuntimeError(
                        'Unstable encoding: using prefix "{}" partially encoded token: "{}"'.format(
                            self._encoding_prefix, encoded
                        )
                    )
        except KeyError:
            pass
        return encoded

    def _strop_by_keyword(self, token: str, token_type: str, dry_run: bool) -> str:
        stropped = token

        if self._matches(stropped, self._reserved_identifiers):
            if not dry_run:
                stropped = self._stropping_prefix + stropped + self._stropping_suffix
            else:
                raise RuntimeError(
                    'input token "{}" of type "{}" yielded an illegal token after '
                    "stropping: {}".format(stropped, token_type, stropped)
                )

        return stropped

    def _strop_by_pattern(self, token: str, token_type: str, dry_run: bool) -> str:

        stropped = token

        reserved_pattern_rules = self._reserved_token_patterns_by_type[token_type]

        if self._matches(stropped, reserved_pattern_rules):
            if not dry_run:
                stropped = self._stropping_prefix + stropped + self._stropping_suffix
            else:
                raise RuntimeError(
                    'input token "{}" of type "{}" yielded an illegal token after '
                    "stropping: {}".format(stropped, token_type, stropped)
                )

        return stropped

    def _do_for_type_and_all(
        self, transform: typing.Callable[[str, str, bool], str], token: str, token_type: str, dry_run: bool
    ) -> str:
        transformed = token

        try:
            transformed = transform(transformed, "all", dry_run)
        except KeyError:
            pass

        if token_type != "all":
            try:
                transformed = transform(transformed, token_type, dry_run)
            except KeyError:
                pass

        return transformed

    # +------------------------------------------------------------------------------------------------------------+
    # | PUBLIC API
    # +------------------------------------------------------------------------------------------------------------+

    def encode_character(self, c: str) -> str:
        if self._whitespace_encoding_char is not None and c.isspace():
            return self._whitespace_encoding_char
        else:
            return "{}{:04X}".format(self._encoding_prefix, ord(c))

    @functools.lru_cache(maxsize=1024)
    def strop(self, token: str, token_type: str = "any") -> str:  # noqa: C901

        token_type_lower = token_type.lower()
        if token_type_lower == "all":
            raise ValueError(
                """Token type 'all' is reserved for patterns that apply to all other types. A single token
                can't be all token types at once but it can be compatible with any type; perhaps you meant 'any'?
            """
            )

        # we encode first.
        encoded = self._do_for_type_and_all(self._encode, token, token_type_lower, False)

        # next we strop the encoded result if it matches a known keyword in the language
        stropped = self._do_for_type_and_all(self._strop_by_keyword, encoded, token_type_lower, False)

        # we then strop if a reserved pattern matches the token
        stropped = self._do_for_type_and_all(self._strop_by_pattern, stropped, token_type_lower, False)

        # and check that the stropping yielded a viable token
        try:
            self._do_for_type_and_all(self._strop_by_pattern, stropped, token_type_lower, True)
        except RuntimeError as pending_error:
            if self._stropping_failure_handler is None:
                raise pending_error
            else:
                stropped = self._stropping_failure_handler(self, stropped, token_type, pending_error)

        # and check that the stropping didn't result in a keyword
        try:
            self._do_for_type_and_all(self._strop_by_keyword, stropped, token_type_lower, True)
        except RuntimeError as pending_error:
            if self._stropping_failure_handler is None:
                raise pending_error
            else:
                stropped = self._stropping_failure_handler(self, stropped, token_type, pending_error)

        # finally, we make sure stropping didn't result in encoding violations
        try:
            self._do_for_type_and_all(self._encode, stropped, token_type_lower, True)
        except RuntimeError as pending_error:
            if self._encoding_failure_handler is None:
                raise pending_error
            else:
                stropped = self._encoding_failure_handler(self, stropped, token_type, pending_error)

        return stropped

    # +----------------------------------------------------------------------------------------------------------------+
    # | Language CONFIGURATION HELPERS
    # +----------------------------------------------------------------------------------------------------------------+
    @classmethod
    def _get_map_of_type_to_lists_of_patterns(
        cls, language: Language, key: str
    ) -> typing.Mapping[str, typing.List[typing.Pattern]]:
        """
        Parses a dictionary value retrieved from Language configuration as a map (with string keys) with each
        value being a list containing pre-compiled, regular expressions.

        Configuration Example:

        .. code-block:: python

            # given this configuration...
            reserved_token_patterns_by_type = {
                    'function':
                        [
                            '^(is|to|str|mem|wcs)[a-z]'
                        ],
                    'typedef':
                        [
                            '^u?int[a-zA-Z_0-9]*_t',
                            '^(atomic_|memory_)[a-z]',
                            '^(cnd_|mtx_|thrd_|tss_)[a-z]'
                        ]
                }

        .. invisible-code-block: python

            from nunavut.lang import Language
            from nunavut.lang._common import TokenEncoder

            config = {
                        'nunavut.lang.cpp':
                        {
                            'reserved_token_patterns_by_type': reserved_token_patterns_by_type
                        }
                    }

            lctx = configurable_language_context_factory(config, 'cpp')
            lang_cpp = lctx.get_target_language()

        .. code-block:: python

            # ... an example use would look like this:
            pattern_map = TokenEncoder._get_map_of_type_to_lists_of_patterns(lang_cpp,
                                                                             'reserved_token_patterns_by_type')
            assert len(pattern_map['function']) == 1
            assert list(pattern_map['function'])[0].match('memset')

        .. invisible-code-block: python

            assert not list(pattern_map['function'])[0].match('foobar')
            assert len(pattern_map['typedef']) == 3

        Note that identifiers are always forced to lower-case:

        .. code-block:: python

            # 'MyIdentiFierTYpE' will be converted to 'myidentifiertype' by this object.
            reserved_token_patterns_by_type = {
                    'MyIdentiFierTYpE':
                        [
                            'foobar'
                        ]
                }

        .. invisible-code-block: python

            config = {
                        'nunavut.lang.cpp':
                        {
                            'reserved_token_patterns_by_type': reserved_token_patterns_by_type
                        }
                    }

            lctx = configurable_language_context_factory(config, 'cpp')
            lang_cpp = lctx.get_target_language()

        .. code-block:: python

            pattern_map = TokenEncoder._get_map_of_type_to_lists_of_patterns(lang_cpp,
                                                                             'reserved_token_patterns_by_type')
            assert len(pattern_map['myidentifiertype']) == 1
            assert list(pattern_map['myidentifiertype'])[0].match('foobar')

        The 'any' key is generated as a union of all keys. If an existing 'any' key is found an exception is raised.
        Any applies to requests to encode or strop a token such that it could be any kind of identifier in a given
        target language. This is different from the special 'all' key which contains patterns that apply to all tokens
        for a target language even if the requested operation is for a specific type.

        .. code-block:: python

            reserved_token_patterns_by_type = {
                    'all':
                        [
                            'all'
                        ],
                    'foo':
                        [
                            'two',
                            'three'
                        ],
                    'bar':
                        [
                            'four',
                            'five'
                        ]
                }

        .. invisible-code-block: python

            config = {
                        'nunavut.lang.cpp':
                        {
                            'reserved_token_patterns_by_type': reserved_token_patterns_by_type
                        }
                    }

            lctx = configurable_language_context_factory(config, 'cpp')
            lang_cpp = lctx.get_target_language()

        .. code-block:: python

            pattern_map = TokenEncoder._get_map_of_type_to_lists_of_patterns(lang_cpp,
                                                                             'reserved_token_patterns_by_type')
            assert len(pattern_map['all']) == 1
            assert len(pattern_map['foo']) == 2
            assert len(pattern_map['bar']) == 2

        .. invisible-code-block: python

            reserved_token_patterns_by_type = {
                    'any':
                        [
                            'foo'
                        ],
                    'all':
                        [
                            'all'
                        ],
                    'foo':
                        [
                            'two',
                            'three'
                        ]
                }
            config['nunavut.lang.cpp']['reserved_token_patterns_by_type'] = reserved_token_patterns_by_type
            lctx = configurable_language_context_factory(config, 'cpp')
            lang_cpp = lctx.get_target_language()

            try:
                TokenEncoder._get_map_of_type_to_lists_of_patterns(lang_cpp,
                                                                   'reserved_token_patterns_by_type')
                assert False
            except RuntimeError:
                pass

        """
        map_of_list_of_patterns = dict()  # type: typing.Dict[str, typing.List[typing.Pattern]]
        map_of_list_of_strings = language.get_config_value_as_dict(key, default_value={})

        any_patterns = []  # type: typing.List[typing.Pattern]
        for mixed_case_type, patterns_for_type in map_of_list_of_strings.items():
            identifier_type = mixed_case_type.lower()
            pattern_list = [re.compile(p) for p in patterns_for_type]
            map_of_list_of_patterns[identifier_type] = pattern_list
            if identifier_type == "any":
                raise RuntimeError(
                    "{}:{} - 'any' key is reserved and cannot be used in configuration.".format(language.name, key)
                )
            any_patterns = any_patterns + pattern_list

        map_of_list_of_patterns["any"] = any_patterns

        return map_of_list_of_patterns
