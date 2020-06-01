#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2020  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""Language-specific support in nunavut.

This package contains modules that provide specific support for generating
source for various languages using templates.
"""
import configparser
import functools
import importlib
import inspect
import logging
import pathlib
import typing

logger = logging.getLogger(__name__)


class Language:
    """
    Facilities for generating source code for a specific language.

    :param str language_name:                The name of the language used by the :mod:`nunavut.lang` module.
    :param configparser.ConfigParser config: The parser to load language properties from.
    :param bool omit_serialization_support:  The value to set for the :func:`omit_serialization_support` property
                                             for this language.
    """

    @classmethod
    def _find_filters_for_language(cls, language_name: str) -> typing.Mapping[str, typing.Callable]:
        filter_map = dict()  # type: typing.Dict[str, typing.Callable]
        lang_module = importlib.import_module('nunavut.lang.{}'.format(language_name))
        filters = inspect.getmembers(lang_module, inspect.isfunction)
        for function_tuple in filters:
            function_name = function_tuple[0]
            if len(function_name) > 7 and function_name[0:7] == "filter_":
                filter_map[function_name[7:]] = function_tuple[1]
                logging.debug("Adding filter {} for language {}".format(function_name[7:],
                                                                        language_name))
        return filter_map

    def __init__(self,
                 language_name: str,
                 config: configparser.ConfigParser,
                 omit_serialization_support: bool):
        self._globals = None  # type: typing.Optional[typing.Mapping[str, typing.Any]]
        self._language_name = language_name
        self._section = 'nunavut.lang.{}'.format(language_name)
        self._filters = self._find_filters_for_language(language_name)
        self._config = config
        self._omit_serialization_support = omit_serialization_support

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

    @property
    def extension(self) -> str:
        """
        The extension to use for files generated in this language.
        """
        return self._config.get(self._section, 'extension')

    @property
    def namespace_output_stem(self) -> typing.Optional[str]:
        """
        The name of a namespace file for this language.
        """
        return self._config.get(self._section, 'namespace_file_stem')

    @property
    def name(self) -> str:
        """
        The name of the language used by the :mod:`nunavut.lang` module.
        """
        return self._language_name

    @property
    def stropping_prefix(self) -> str:
        """
        The string to prepend to an identifier when stropping.
        """
        return self._config.get(self._section, 'stropping_prefix')

    @property
    def stropping_suffix(self) -> str:
        """
        The string to add to the end of an identifier when stropping.
        """
        return self._config.get(self._section, 'stropping_suffix')

    @property
    def support_namespace(self) -> typing.List[str]:
        """
        The hierarchial namespace used by the support software. The property
        is a dot separated string when specified in configuration. This
        property returns that value split into namespace components with the
        first identifier being the first index in the array, etc.

        .. invisible-code-block: python

            from nunavut.lang import Language
            import configparser

            config = configparser.ConfigParser()
            config.add_section('nunavut.lang.cpp')


            lang_cpp = Language('cpp', config, True)

        .. code-block:: python

            config.set('nunavut.lang.cpp', 'support_namespace', 'foo.bar')
            assert len(lang_cpp.support_namespace) == 2
            assert lang_cpp.support_namespace[0] == 'foo'
            assert lang_cpp.support_namespace[1] == 'bar'

        """
        namespace_str = self._config.get(self._section, 'support_namespace', fallback='')
        return namespace_str.split('.')

    @property
    def encoding_prefix(self) -> str:
        """
        The string to prepend to an encoding hex value.
        """
        return self._config.get(self._section, 'encoding_prefix')

    @property
    def enable_stropping(self) -> bool:
        """
        Whether or not to strop identifiers for this language.
        """
        return self._config.getboolean(self._section, 'enable_stropping')

    @property
    def has_standard_namespace_files(self) -> bool:
        """
        Whether or not the language defines special namespace files as part of
        its core standard (e.g. python's __init__).
        """
        return self._config.getboolean(self._section, 'has_standard_namespace_files')

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
        """
        module = importlib.import_module('nunavut.lang.{}.support'.format(self._language_name))

        # All language support modules must provide a list_support_files method
        # to allow the copy generator access to the packaged support files.
        list_support_files = getattr(module, 'list_support_files')  \
            # type: typing.Callable[[], typing.Generator[pathlib.Path, None, None]]
        return list_support_files()

    def get_config_value(self,
                         key: str,
                         default_value: typing.Union[typing.Mapping[str, typing.Any], str, None] = None)\
            -> typing.Union[typing.Mapping[str, typing.Any], str, None]:
        """
        Get an optional language property from the language configuration.

        :param str key: The config value to retrieve.
        :param default_value: The value to return if the key was not in the configuration. If provided
            this method will not raise.
        :type default_value: typing.Union[typing.Mapping[str, typing.Any], str, None]
        :return: Either the value from the config or the default_value if provided.
        :rtype: typing.Union[typing.Mapping[str, typing.Any], str, None]
        :raises: KeyError if the key does not exist and a default_value was not provied.
        """
        return self._config.get(self._section, key, fallback=default_value)

    def get_config_value_as_bool(self, key: str, default_value: bool = False) -> bool:
        """
        Get an optional language property from the language configuration returning a boolean. The rules
        for boolean conversion are as follows:

        .. invisible-code-block: python

            from nunavut.lang import Language
            import configparser

            config = configparser.ConfigParser()
            config.add_section('nunavut.lang.cpp')

            lang_cpp = Language('cpp', config, True)

        .. code-block:: python

            # "Any string" = True
            config.set('nunavut.lang.cpp', 'v', 'Any string')
            assert lang_cpp.get_config_value_as_bool('v')

            # "true" = True
            config.set('nunavut.lang.cpp', 'v', 'true')
            assert lang_cpp.get_config_value_as_bool('v')

            # "TrUe" = True
            config.set('nunavut.lang.cpp', 'v', 'TrUe')
            assert lang_cpp.get_config_value_as_bool('v')

            # "1" = True
            config.set('nunavut.lang.cpp', 'v', '1')
            assert lang_cpp.get_config_value_as_bool('v')

            # "false" = False
            config.set('nunavut.lang.cpp', 'v', 'false')
            assert not lang_cpp.get_config_value_as_bool('v')

            # "FaLse" = False
            config.set('nunavut.lang.cpp', 'v', 'FaLse')
            assert not lang_cpp.get_config_value_as_bool('v')

            # "0" = False
            config.set('nunavut.lang.cpp', 'v', '0')
            assert not lang_cpp.get_config_value_as_bool('v')

            # "" = False
            config.set('nunavut.lang.cpp', 'v', '')
            assert not lang_cpp.get_config_value_as_bool('v')

            # False if not defined
            assert not lang_cpp.get_config_value_as_bool('not_a_key')

            # True if not defined but default_value is True
            assert lang_cpp.get_config_value_as_bool('not_a_key', True)

        :param str key: The config value to retrieve.
        :param bool default_value: The value to use if no value existed.
        :return: The config value as either True or False.
        :rtype: bool
        """
        result = self._config.get(self._section, key, fallback='' if not default_value else '1')
        if result.lower() == 'false' or result == '0':
            return False
        else:
            return bool(result)

    def get_templates_package_name(self) -> str:
        """
        The name of the nunavut python package containing filters, types, and configuration
        for this language.
        """
        return 'nunavut.lang.{}'.format(self.name)

    def get_named_types(self) -> typing.Mapping[str, str]:
        """
        Get a map of named types to the type name to emit for this language.
        """
        return self._config.getdict(self._section, 'named_types', fallback={})  # type: ignore

    def get_named_values(self) -> typing.Mapping[str, str]:
        """
        Get a map of named values to the token to emit for this language.
        """
        return self._config.getdict(self._section, 'named_values', fallback={})  # type: ignore

    def get_reserved_identifiers(self) -> typing.List[str]:
        """
        Get a list of identifiers that are reserved keywords for this language.
        """
        return self._config.getlist(self._section, 'reserved_identifiers', fallback=[])  # type: ignore

    def get_filters(self) -> typing.Mapping[str, typing.Callable]:
        """
        Inspect the language module for functions with a name starting with "filter\\_" and return
        a map of filter names to the filter callable.

        :returns: A mapping of filter names to filter functions.
        """
        return self._filters

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
        These will override any values found in the :file:`nunavut.lang.properties.ini` file and files
        appearing later in this list will override value found in earlier entries.
    :type additional_config_files: typing.List[pathlib.Path]
    :param bool omit_serialization_support_for_target: If True then generators should not include
        serialization routines, types, or support libraries for the target language.
    :raises ValueError: If extension is None and no target language was provided.
    :raises KeyError: If the target language is not known.
    """

    @classmethod
    def _as_dict(cls, value: str) -> typing.Dict[str, typing.Any]:
        value_as_dict = dict()
        value_pairs = value.strip().split('\n')
        for pair in value_pairs:
            kv = pair.strip().split('=')
            value_as_dict[kv[0].strip()] = kv[1].strip()
        return value_as_dict

    @classmethod
    def _as_list(cls, value: str) -> typing.List[str]:
        return [r.strip() for r in value.split('\n')]

    @classmethod
    def _load_config(cls, *additional_config_files: pathlib.Path) -> configparser.ConfigParser:
        import pkg_resources
        parser = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation(),
                                           converters={'dict': cls._as_dict,
                                                       'list': cls._as_list})
        resources = [r for r in pkg_resources.resource_listdir(__name__, '.') if r.endswith('.ini')]
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
                 omit_serialization_support_for_target: bool = True):
        self._extension = extension
        self._namespace_output_stem = namespace_output_stem
        self._config = self._load_config(*additional_config_files)

        # create target language, if there is one.
        if target_language is None:
            self._target_language = None
        else:
            try:
                self._target_language = Language(target_language, self._config,
                                                 omit_serialization_support_for_target)
            except ImportError:
                raise KeyError('{} is not a supported language'.format(target_language))
            if namespace_output_stem is not None:
                self._config.set('nunavut.lang.{}'.format(target_language),
                                 'namespace_file_stem',
                                 namespace_output_stem)
            if extension is not None:
                self._config.set('nunavut.lang.{}'.format(target_language),
                                 'extension',
                                 extension)

        # create remaining languages
        self._languages = dict()  # type: typing.Dict[str, Language]
        for language_name in self.get_supported_language_names():
            if self._target_language is not None and self._target_language.name == language_name:
                self._languages[language_name] = self._target_language
            else:
                try:
                    self._languages[language_name] = Language(language_name, self._config, False)
                except ImportError:
                    raise KeyError('{} is not a supported language'.format(language_name))

    def get_language(self, key_or_modulename: str) -> Language:
        """
        Get a :class:`Language` object for a given language identifier.

        :param str key_or_modulename: Either one of the Nunavut mnemonics for a supported language or
            the ``__name__`` of one of the ``nunavut.lang.[language]`` python modules.
        :returns: A :class:`Language` object cached by this context.
        :rtype: Language
        """
        if key_or_modulename is None or len(key_or_modulename) == 0:
            raise ValueError('key argument is required.')
        key = (key_or_modulename[13:] if key_or_modulename.startswith('nunavut.lang.') else key_or_modulename)
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

    def get_target_id_filter(self) -> typing.Callable[[str], str]:
        """
        A filter that will transform a given string into a valid identifier
        in the target language. The string is pass through unmodified if no
        target language was set.
        """
        if self._target_language is not None:
            filters = self._target_language.get_filters()
            for name, filter in filters.items():
                if name == 'id':
                    id_filter = typing.cast(typing.Callable[[Language, str], str], filter)
                    return functools.partial(id_filter, self._target_language)

        return lambda unfiltered: unfiltered

    def get_supported_languages(self) -> typing.Dict[str, Language]:
        """
        Returns a collection of available language support objects.
        """
        return self._languages

    @property
    def config(self) -> configparser.ConfigParser:
        return self._config


class _UniqueNameGenerator:
    """
    Functor used by template filters to obtain a unique name within a given template.
    This should be made available as a private global within each template.
    """
    _singleton = None  # type: typing.Optional['_UniqueNameGenerator']

    def __init__(self) -> None:
        self._index_map = {}  # type: typing.Dict[str, typing.Dict[str, int]]

    @classmethod
    def reset(cls) -> None:
        cls._singleton = cls()

    @classmethod
    def get_instance(cls) -> '_UniqueNameGenerator':
        if cls._singleton is None:
            raise RuntimeError('No _UniqueNameGenerator has been created. Please use reset to create.')
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
            prefix=prefix,
            base_token=base_token,
            index=next_index,
            suffix=suffix)
