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
import importlib
import inspect
import logging
import pathlib
import typing

from ._config import LanguageConfig

logger = logging.getLogger(__name__)


class Language:
    """
    Facilities for generating source code for a specific language.

    :param str language_name:                The name of the language used by the :mod:`nunavut.lang` module.
    :param LanguageConfig config:            The parser to load language properties into.
    :param bool omit_serialization_support:  The value to set for the :func:`omit_serialization_support` property
                                             for this language.
    :param typing.Optional[typing.Mapping[str, typing.Any]] language_options: Opaque arguments passed through to the
                target :class:`nunavut.lang.Language` object.
    """

    def _find_callable_for_language(self, callable_name_prefix: str) -> \
            typing.Mapping[str, typing.Callable]:
        callable_map = dict()  # type: typing.Dict[str, typing.Callable]
        lang_module = self._language_module
        callables = inspect.getmembers(lang_module, inspect.isfunction)
        callable_name_prefix_len = len(callable_name_prefix)
        for function_tuple in callables:
            function_name = function_tuple[0]
            if len(function_name) > callable_name_prefix_len and \
                    function_name[0:callable_name_prefix_len] == callable_name_prefix:
                callable_map[function_name[callable_name_prefix_len:]] = function_tuple[1]
                logging.debug("Found callable {} for language {}".format(function_name[callable_name_prefix_len:],
                                                                         self._language_name))
        return callable_map

    def _find_filters_for_language(self) -> typing.Mapping[str, typing.Callable]:
        return self._find_callable_for_language('filter_')

    def _find_tests_for_language(self) -> typing.Mapping[str, typing.Callable]:
        return self._find_callable_for_language('is_')

    @classmethod
    def get_language_config_parser(cls) -> LanguageConfig:
        """
        Create a :class:`LanguageConfig` instance configured for reading
        language properties.yaml.
        """
        return LanguageConfig()

    def __init__(self,
                 language_name: str,
                 config: LanguageConfig,
                 omit_serialization_support: bool,
                 language_options: typing.Optional[typing.Mapping[str, typing.Any]] = None):
        self._globals = None  # type: typing.Optional[typing.Mapping[str, typing.Any]]
        self._language_name = language_name
        self._section = 'nunavut.lang.{}'.format(language_name)
        self._language_module = importlib.import_module(self._section)
        self._config_getter_cache = {}  # type: typing.Mapping[str, functools.partial[typing.Any]]
        self._filters = self._find_filters_for_language()
        self._tests = self._find_tests_for_language()
        self._config = config
        self._omit_serialization_support = omit_serialization_support
        self._language_options = config.get_config_value_as_dict(self._section, 'options', dict())

        if language_options is not None:
            self._language_options.update(language_options)

    def __getattr__(self, name: str) -> typing.Any:
        """
        Any attribute access to a Language object will return the regular properties and
        any globals defined for the language. Because of this do not extend properties
        on this object in a way that will clash with the globals it defines (e.g. typename_
        or valuetoken_ should not be used as the start of attribute names).
        """
        try:
            return self.get_globals()[name]
        except KeyError as e:
            raise AttributeError(e)

    def get_config_value(self,
                         key: str,
                         default_value: typing.Optional[str] = None) -> str:
        """
        Get an optional language property from the language configuration.

        :param str key: The config value to retrieve.
        :param default_value: The value to return if the key was not in the configuration. If provided
                this method will not raise.
        :type default_value: typing.Optional[str]
        :return: Either the value from the config or the default_value if provided.
        :rtype: str
        :raises: KeyError if the section or the key in the section does not exist and a default_value was not provided.
        """
        return self._config.get_config_value(self._section, key, default_value)

    def get_config_value_as_bool(self, key: str, default_value: bool = False) -> bool:
        """
        Get an optional language property from the language configuration returning a boolean.

        :param str key: The config value to retrieve.
        :param bool default_value: The value to use if no value existed.
        :return: The config value as either True or False.
        :rtype: bool
        """
        return self._config.get_config_value_as_bool(self._section, key, default_value)

    def get_config_value_as_dict(self, key: str, default_value: typing.Optional[typing.Dict] = None) -> \
            typing.Dict[str, typing.Any]:
        """
        Get a language property parsing it as a map with string keys.

        .. invisible-code-block: python

            from nunavut.lang import LanguageConfig, Language

            config = LanguageConfig()
            config.add_section('nunavut.lang.c')
            config.set('nunavut.lang.c', 'foo', {'one': 1})

            lang_c = Language('c', config, True)

            assert lang_c.get_config_value_as_dict('foo')['one'] == 1

            assert lang_c.get_config_value_as_dict('bar', {'one': 2})['one'] == 2

        :param str key:           The config value to retrieve.
        :param default_value:     The value to return if the key was not in the configuration. If provided this method
            will not raise a KeyError nor a TypeError.
        :type default_value: typing.Optional[typing.Mapping[str, typing.Any]]
        :return:                  Either the value from the config or the default_value if provided.
        :rtype: typing.Mapping[str, typing.Any]
        :raises: KeyError if the key does not exist and a default_value was not provided.
        :raises: TypeError if the value exists but is not a dict and a default_value was not provided.

        """
        return self._config.get_config_value_as_dict(self._section, key, default_value)

    def get_config_value_as_list(self, key: str, default_value: typing.Optional[typing.List] = None)\
            -> typing.List[typing.Any]:
        """
        Get a language property parsing it as a map with string keys.

        :param str key:           The config value to retrieve.
        :param default_value:     The value to return if the key was not in the configuration. If provided this method
            will not raise a KeyError nor a TypeError.
        :type default_value:      typing.Optional[typing.List[typing.Any]]
        :return:                  Either the value from the config or the default_value if provided.
        :rtype:                   typing.List[typing.Any]
        :raises:                  KeyError if the key does not exist and a default_value was not provided.
        :raises:                  TypeError if the value exists but is not a dict and a default_value was not provided.

        """
        return self._config.get_config_value_as_list(self._section, key, default_value)

    @property
    def extension(self) -> str:
        """
        The extension to use for files generated in this language.
        """
        return self._config.get_config_value(self._section, 'extension', 'get')

    @property
    def namespace_output_stem(self) -> typing.Optional[str]:
        """
        The name of a namespace file for this language.
        """
        try:
            return self._config.get_config_value(self._section, 'namespace_file_stem')
        except KeyError:
            return None

    @property
    def name(self) -> str:
        """
        The name of the language used by the :mod:`nunavut.lang` module.
        """
        return self._language_name

    @property
    def support_namespace(self) -> typing.List[str]:
        """
        The hierarchical namespace used by the support software. The property
        is a dot separated string when specified in configuration. This
        property returns that value split into namespace components with the
        first identifier being the first index in the array, etc.

        .. invisible-code-block: python

            from nunavut.lang import Language

            config = Language.get_language_config_parser()
            config.add_section('nunavut.lang.cpp')

            lang_cpp = Language('cpp', config, True)

        .. code-block:: python

            config.set('nunavut.lang.cpp', 'support_namespace', 'foo.bar')
            assert len(lang_cpp.support_namespace) == 2
            assert lang_cpp.support_namespace[0] == 'foo'
            assert lang_cpp.support_namespace[1] == 'bar'

        """
        namespace_str = self._config.get_config_value(self._section, 'support_namespace', default_value='')
        return namespace_str.split('.')

    @property
    def enable_stropping(self) -> bool:
        """
        Whether or not to strop identifiers for this language.
        """
        return self._config.get_config_value_as_bool(self._section, 'enable_stropping')

    @property
    def has_standard_namespace_files(self) -> bool:
        """
        Whether or not the language defines special namespace files as part of
        its core standard (e.g. python's __init__).
        """
        return self._config.get_config_value_as_bool(self._section, 'has_standard_namespace_files')

    @property
    def stable_support(self) -> bool:
        """
        Whether support for this language is designated 'stable', and not experimental.
        """
        return self._config.get_config_value_as_bool(self._section, 'stable_support')

    @property
    def omit_serialization_support(self) -> bool:
        """
        If True then generators should not include serialization routines, types,
        or support libraries for this language.
        """
        return self._omit_serialization_support

    @property
    def support_files(self) -> typing.Generator[pathlib.Path, None, None]:
        """
        Iterates over non-templated supporting files embedded within the Nunavut distribution.

        .. invisible-code-block: python

            from nunavut.lang import Language
            from unittest.mock import MagicMock

            mock_config = MagicMock()

            my_lang = Language('c', mock_config, True)
            my_lang._section = "nunavut.lang.not_a_language_really_not_a_language"
            for support_file in my_lang.support_files:
                # if the module doesn't exist it shouldn't have any support files.
                assert False

        """
        try:
            module = importlib.import_module('{}.support'.format(self._section))

            # All language support modules must provide a list_support_files method
            # to allow the copy generator access to the packaged support files.
            list_support_files = getattr(module, 'list_support_files')  \
                # type: typing.Callable[[], typing.Generator[pathlib.Path, None, None]]
            return list_support_files()
        except ImportError:
            # No serialization support for this language
            logger.info("No serialization support for selected target. Skipping serialization support generation.")

            def list_support_files() -> typing.Generator[pathlib.Path, None, None]:
                # This makes both MyPy and sonarqube happy.
                return typing.cast(typing.Generator[pathlib.Path, None, None], iter(()))

            return list_support_files()

    def get_option(self,
                   option_key: str,
                   default_value: typing.Union[typing.Mapping[str, typing.Any], str, None] = None)\
            -> typing.Union[typing.Mapping[str, typing.Any], str, None]:
        """
        Get a language option for this language.

        .. invisible-code-block: python

            from nunavut.lang import Language

            config = Language.get_language_config_parser()
            config.add_section('nunavut.lang.cpp')
            config.set('nunavut.lang.cpp', 'options', {'target_endianness': 'little'})

            lang_cpp = Language('cpp', config, True)

        .. code-block:: python

            # Values can come from defaults...
            assert lang_cpp.get_option('target_endianness') == 'little'

            # ... or can be provided to a language instance.
            my_lang = Language('cpp', config, True, language_options={'target_endianness': 'any'})
            assert my_lang.get_option('target_endianness') == 'any'

            # Also, this method can provide a sane default.
            assert lang_cpp.get_option('foobar', 'sane_default') == 'sane_default'

        :return: Either the value provided to the :class:`Language` instance, the value from properties.yaml,
            or the :code:`default_value`.

        """
        try:
            return self._language_options[option_key]  # type: ignore
        except KeyError:
            return default_value

    def get_templates_package_name(self) -> str:
        """
        The name of the nunavut python package containing filters, types, and configuration
        for this language.
        """
        return self._section

    def get_named_types(self) -> typing.Mapping[str, str]:
        """
        Get a map of named types to the type name to emit for this language.
        """
        return self._config.get_config_value_as_dict(self._section, 'named_types', default_value={})

    def get_named_values(self) -> typing.Mapping[str, str]:
        """
        Get a map of named values to the token to emit for this language.
        """
        return self._config.get_config_value_as_dict(self._section, 'named_values', default_value={})

    def get_filters(self) -> typing.Mapping[str, typing.Callable]:
        """
        Inspect the language module for functions with a name starting with "filter\\_" and return
        a map of filter names to the filter callable.

        :returns: A mapping of filter names to filter functions.
        """
        return self._filters

    def get_tests(self) -> typing.Mapping[str, typing.Callable]:
        """
        Inspect the language module for functions with a name starting with "is\\_" and return
        a map of test names to the test callable.

        :returns: A mapping of test names to test functions.
        """
        return self._tests

    def get_globals(self) -> typing.Mapping[str, typing.Any]:
        """
        Get all values for this language that should be available in a global context.

        :returns: A mapping of global names to global values.
        """
        if self._globals is None:
            globals_map = dict()  # type: typing.Dict[str, typing.Any]

            for key, value in self.get_named_types().items():
                globals_map['typename_{}'.format(key)] = value
            for key, value in self.get_named_values().items():
                globals_map['valuetoken_{}'.format(key)] = value

            self._globals = globals_map
        return self._globals

    def get_options(self) -> typing.Mapping[str, typing.Any]:
        """
        Get all language options for this Language.

        :returns: A mapping of option names to option values.
        """
        return self._language_options


class LanguageContext:
    """
    Context object containing the current target language (if any) and used to access
    :class:`Language` objects.

    :param str target_language: If provided a :class:`Language` object will be created to hold
                                the target language set for this context. If None then there is
                                no target language.
    :param str extension: The extension to use for generated file types or None to use a default
                          based on the target_language.
    :param str namespace_output_stem: The filename stem to give to Namespace output files if
                                      emitted or None to use a default based on a target_language.
    :param additional_config_files: A list of paths to additional ini files to load as configuration.
        These will override any values found in the :file:`nunavut.lang.properties.yaml` file and files
        appearing later in this list will override value found in earlier entries.
    :type additional_config_files: typing.List[pathlib.Path]
    :param bool omit_serialization_support_for_target: If True then generators should not include
        serialization routines, types, or support libraries for the target language.
    :param typing.Optional[typing.Mapping[str, typing.Any]] language_options: Opaque arguments passed through to the
                target :class:`nunavut.lang.Language` object.
    :param bool include_experimental_languages: If True, expose languages with experimental (non-stable) support.
    :raises ValueError: If extension is None and no target language was provided.
    :raises KeyError: If the target language is not known.
    """

    @classmethod
    def _load_config(cls, *additional_config_files: pathlib.Path) -> LanguageConfig:
        import pkg_resources
        parser = Language.get_language_config_parser()
        resources = [r for r in pkg_resources.resource_listdir(__name__, '.') if r.endswith('.yaml')]
        for resource in resources:
            with pkg_resources.resource_stream(__name__, resource) as resource_stream:
                ini_string = resource_stream.read().decode(encoding='utf-8', errors='replace')
                parser.read_string(ini_string, resource)
        for additional_path in additional_config_files:
            with open(str(additional_path), 'r') as additional_file:
                parser.read_file(additional_file)
        return parser

    def __init__(self,
                 target_language: typing.Optional[str] = None,
                 extension: typing.Optional[str] = None,
                 namespace_output_stem: typing.Optional[str] = None,
                 additional_config_files: typing.List[pathlib.Path] = [],
                 omit_serialization_support_for_target: bool = True,
                 language_options: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                 include_experimental_languages: bool = True):
        self._extension = extension
        self._namespace_output_stem = namespace_output_stem
        self._config = self._load_config(*additional_config_files)
        self._languages = dict()  # type: typing.Dict[str, Language]

        # create target language, if there is one.
        self._target_language = None
        if target_language is not None:
            try:
                self._target_language = Language(target_language, self._config,
                                                 omit_serialization_support_for_target,
                                                 language_options=language_options)
            except ImportError:
                raise KeyError('{} is not a supported language'.format(target_language))
            if not (self._target_language.stable_support or include_experimental_languages):
                raise ValueError(
                    '{} support is only experimental, but experimental language support is not enabled'
                    .format(target_language)
                )
            if namespace_output_stem is None:
                self._namespace_output_stem = self._target_language.namespace_output_stem

            target_language_section_name = 'nunavut.lang.{}'.format(target_language)
            if self._namespace_output_stem is not None:
                self._config.set(target_language_section_name,
                                 'namespace_file_stem',
                                 self._namespace_output_stem)
            if extension is not None:
                self._config.set(target_language_section_name,
                                 'extension',
                                 extension)
            self._languages[target_language] = self._target_language

        # create remaining languages
        remaining_languages = set(self.get_supported_language_names()) - set((target_language,))
        self._populate_languages(remaining_languages, include_experimental_languages)

    def _populate_languages(self, language_names: typing.Iterable[str],
                            include_experimental: bool) -> None:
        for language_name in language_names:
            try:
                lang = Language(language_name, self._config, False)
                if lang.stable_support or include_experimental:
                    self._languages[language_name] = lang
            except ImportError:
                raise KeyError('{} is not a supported language'.format(language_name))

    def get_language(self, key_or_module_name: str) -> Language:
        """
        Get a :class:`Language` object for a given language identifier.

        :param str key_or_module_name: Either one of the Nunavut mnemonics for a supported language or
            the ``__name__`` of one of the ``nunavut.lang.[language]`` python modules.
        :returns: A :class:`Language` object cached by this context.
        :rtype: Language
        """
        if key_or_module_name is None or len(key_or_module_name) == 0:
            raise ValueError('key argument is required.')
        key = (key_or_module_name[13:] if key_or_module_name.startswith('nunavut.lang.') else key_or_module_name)
        return self.get_supported_languages()[key]

    def get_supported_language_names(self) -> typing.Iterable[str]:
        """Get a list of target languages supported by Nunavut.

        :returns: An iterable of strings which are languages with special
            support within Nunavut templates.
        """
        return [s[13:] for s in self._config.sections() if s.startswith('nunavut.lang.')]

    def get_output_extension(self) -> str:
        """
        Gets the output extension to use regardless of a target language being available or not.

        :returns: A file extension name with a leading dot.
        """
        if self._extension is not None:
            return self._extension
        elif self._target_language is not None:
            return self._target_language.extension
        else:
            raise RuntimeError('No extension was provided and no target language was set.'
                               'Cannot determine the extension to use.')

    def get_default_namespace_output_stem(self) -> typing.Optional[str]:
        """
        The filename stem to give to Namespace output files if emitted or None if there was none
        specified and there is no target language.

        :returns: A file name stem or None
        """
        return self._namespace_output_stem

    def get_target_language(self) -> typing.Optional[Language]:
        """
        Returns the target language configured on this object or None
        if no target language was specified.
        """
        return self._target_language

    def get_target_id_filter(self) -> typing.Callable[[str, str], str]:
        """
        A filter that will transform a given string into a valid identifier
        in the target language. The string is pass through unmodified if no
        target language was set.
        """
        if self._target_language is not None:
            filters = self._target_language.get_filters()
            for name, filter in filters.items():
                if name == 'id':
                    id_filter = typing.cast(typing.Callable[[Language, str, str], str], filter)
                    return functools.partial(id_filter, self._target_language)

        def no_filter(unfiltered: str, _: str = '') -> str:
            return unfiltered

        return no_filter

    def get_supported_languages(self) -> typing.Dict[str, Language]:
        """
        Returns a collection of available language support objects.
        """
        return self._languages

    @property
    def config(self) -> LanguageConfig:
        return self._config
