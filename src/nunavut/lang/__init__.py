#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2020  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""Language-specific support in nunavut.

This package contains modules that provide specific support for generating
source for various languages using templates.
"""
import abc
import functools
import importlib
import logging
import pathlib
import types
import typing

import pydsdl

from ..dependencies import Dependencies, DependencyBuilder
from .._utilities import YesNoDefault, iter_package_resources
from ._config import LanguageConfig, VersionReader

logger = logging.getLogger(__name__)


class LanguageLoader:
    """
    Factory class that loads language meta-data and concrete :class:`nunavut.lang.Language` objects.

    :param additional_config_files: A list of paths to additional configuration files to load as configuration.
        These will override any values found in the :file:`nunavut.lang.properties.yaml` file and files
        appearing later in this list will override value found in earlier entries.

        .. invisible-code-block: python

            from nunavut.lang import LanguageLoader

            subject = LanguageLoader()

            c_reserved_identifiers = subject.config.get_config_value('nunavut.lang.c','reserved_identifiers')
            assert len(c_reserved_identifiers) > 0
    """

    @classmethod
    def load_language_module(cls, language_name: str) -> "types.ModuleType":
        module_name = "nunavut.lang.{}".format(language_name)
        return importlib.import_module(module_name)

    @classmethod
    def _load_config(cls, *additional_config_files: pathlib.Path) -> LanguageConfig:
        parser = LanguageConfig()
        for resource in iter_package_resources(__name__, ".yaml"):
            ini_string = resource.read_text()
            parser.read_string(ini_string)
        for additional_path in additional_config_files:
            with open(str(additional_path), "r") as additional_file:
                parser.read_file(additional_file)
        return parser

    def __init__(self, *additional_config_files: pathlib.Path):
        self._config = None  # type: typing.Optional[LanguageConfig]
        self._additional_config_files = additional_config_files

    @property
    def config(self) -> LanguageConfig:
        """
        Meta-data about all languages merged from the Nunavut internal defaults and any additional
        configuration files provided to this class's constructor.
        """
        if self._config is None:
            self._config = self._load_config(*self._additional_config_files)
        return self._config

    def load_language(
        self,
        language_name: str,
        omit_serialization_support: bool,
        language_options: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ) -> "Language":
        """
        :param str language_name:                The name of the language used by the :mod:`nunavut.lang` module.
        :param LanguageConfig config:            The parser to load language properties into.
        :param bool omit_serialization_support:  The value to set for the :func:`omit_serialization_support` property
                                                for this language.
        :param typing.Optional[typing.Mapping[str, typing.Any]] language_options: Opaque arguments passed through to the
                    target :class:`nunavut.lang.Language` object.

        :return: A new object that extends :class:`nunavut.lang.Language`.
        :rtype: nunavut.lang.Language

        .. invisible-code-block: python

            from nunavut.lang import LanguageLoader

        .. code-block:: python

            lang_c = LanguageLoader().load_language('c', True)
            assert lang_c.name == 'c'

        .. invisible-code-block: python

            # let's go ahead and load the rest of our known, internally supported languages just to raise
            # test failures right here at the wellspring.

            lang_cpp = LanguageLoader().load_language('py', True)
            assert lang_cpp.name == 'py'

            lang_js = LanguageLoader().load_language('js', True)
            assert lang_js.name == 'js'

        """
        ln_module = self.load_language_module(language_name)

        try:
            language_type = typing.cast(typing.Type["Language"], getattr(ln_module, "Language"))
        except AttributeError:
            logging.debug(
                "Unable to find a Language object in nunavut.lang.{}. Using a Generic language object".format(
                    language_name
                )
            )
            language_type = _GenericLanguage

        if language_type == Language:
            # the language module just imported the base class so let's go ahead and use _GenericLanguage
            language_type = _GenericLanguage

        return language_type(ln_module, self.config, omit_serialization_support, language_options)


class Language(metaclass=abc.ABCMeta):
    """
    Facilities for generating source code for a specific language. Concrete Language classes must be implemented
    by the language support package below lang and should be instantiated using
    :class:`nunavut.lang.LanguageLoader`.

    :param str language_name:                The name of the language used by the :mod:`nunavut.lang` module.
    :param LanguageConfig config:            The parser to load language properties into.
    :param bool omit_serialization_support:  The value to set for the :func:`omit_serialization_support` property
                                             for this language.
    :param typing.Optional[typing.Mapping[str, typing.Any]] language_options: Opaque arguments passed through to the
                target :class:`nunavut.lang.Language` object.

        .. invisible-code-block: python

            from nunavut.lang import Language, _GenericLanguage
            from unittest.mock import MagicMock

            mock_config = MagicMock()
            mock_module = MagicMock()

            mock_module.__name__ = 'foo'
            try:
                my_lang = _GenericLanguage(mock_module, mock_config, True)
                # module must be within 'nunavut'
                assert False
            except RuntimeError:
                pass

            mock_module.__name__ = 'nunavut.foo'
            try:
                my_lang = _GenericLanguage(mock_module, mock_config, True)
                # module must be within 'nunavut.lang'
                assert False
            except RuntimeError:
                pass

            mock_module.__name__ = 'not.nunavut.foo'
            try:
                my_lang = _GenericLanguage(mock_module, mock_config, True)
                # module must be within 'nunavut.lang'
                assert False
            except RuntimeError:
                pass

            mock_module.__name__ = 'nunavut.lang.foo'
            my_lang = _GenericLanguage(mock_module, mock_config, True)
            assert my_lang.name == 'foo'
    """

    @classmethod
    def default_filter_id_for_target(cls, instance: typing.Any) -> str:
        """
        The default transformation of any object into a string.

        :param any instance:        Any object or data that either has a name property or can be converted to a string.
        :return: Either ``str(instance.name)`` if the instance has a name property or just ``str(instance)``
        """
        if hasattr(instance, "name"):
            return str(instance.name)
        else:
            return str(instance)

    def __init__(
        self,
        language_module: "types.ModuleType",
        config: LanguageConfig,
        omit_serialization_support: bool,
        language_options: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ):
        self._globals = None  # type: typing.Optional[typing.Mapping[str, typing.Any]]
        self._section = language_module.__name__
        name_parts = self._section.split(".")
        if len(name_parts) != 3 or name_parts[0] != "nunavut" or name_parts[1] != "lang":
            raise RuntimeError("unknown module provided to Language class.")
        self._language_name = name_parts[2]
        self._config = config
        self._omit_serialization_support = omit_serialization_support
        self._language_options = config.get_config_value_as_dict(self._section, "options", dict())

        if language_options is not None:
            self._language_options.update(language_options)

        self._filters = dict()  # type: typing.Dict[str, typing.Callable]
        self._tests = dict()  # type: typing.Dict[str, typing.Callable]
        self._uses = dict()  # type: typing.Dict[str, typing.Callable]

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

    def get_support_module(self) -> typing.Tuple[str, typing.Tuple[int, int, int], typing.Optional["types.ModuleType"]]:
        """
        Returns the module object for the language support files.
        :return: A tuple of module name, x.y.z module version, and the module object itself.

        .. invisible-code-block: python

            from nunavut.lang import Language, _GenericLanguage
            from unittest.mock import MagicMock

            mock_config = MagicMock()
            mock_module = MagicMock()
            mock_module.__name__ = 'nunavut.lang.cpp'

            my_lang = _GenericLanguage(mock_module, mock_config, True)
            my_lang._section = "nunavut.lang.cpp"
            module_name, support_version, _ = my_lang.get_support_module()

            assert module_name == "nunavut.lang.cpp.support"
            assert support_version[0] == 1

        """
        module_name = "{}.support".format(self._section)

        try:
            module = importlib.import_module(module_name)
            version_tuple = VersionReader.read_version(module)
            return (module_name, version_tuple, module)
        except (ImportError, ValueError):
            # No serialization support for this language
            logger.info("No serialization support for selected target. Cannot retrieve module.")

            return (module_name, (0, 0, 0), None)

    @functools.lru_cache()
    def get_dependency_builder(self, for_type: pydsdl.Any) -> DependencyBuilder:
        return DependencyBuilder(for_type)

    @abc.abstractmethod
    def get_includes(self, dep_types: Dependencies) -> typing.List[str]:
        """
        Get a list of include paths that are specific to this language and the options set for it.
        :param Dependencies dep_types: A description of the dependencies includes are needed for.
        :return: A list of include file paths. The list may be empty if no includes were needed.
        """
        pass

    def filter_id(self, instance: typing.Any, id_type: str = "any") -> str:
        """
        Produces a valid identifier in the language for a given object. The encoding may not be reversible.

        :param any instance:        Any object or data that either has a name property or can be converted
                                    to a string.
        :param str id_type:         A type of identifier. This is different for each language. For example, for C this
                                    value can be 'typedef', 'macro', 'function', or 'enum'.
                                    Use 'any' to apply stropping rules for all identifier types to the instance.
        :return: A token that is a valid identifier in the language, is not a reserved keyword, and is transformed
                in a deterministic manner based on the provided instance.
        """
        return self.default_filter_id_for_target(instance)

    def filter_short_reference_name(
        self, t: pydsdl.CompositeType, stropping: YesNoDefault = YesNoDefault.DEFAULT, id_type: str = "any"
    ) -> str:
        """
        Provides a string that is a shorted version of the full reference name omitting any namespace parts of the type.

        :param pydsdl.CompositeType t: The DSDL type to get the reference name for.
        :param YesNoDefault stropping: If DEFAULT then the stropping value configured for the target language is used
                                       else this overrides that value.
        :param str id_type:         A type of identifier. This is different for each language. For example, for C this
                                    value can be 'typedef', 'macro', 'function', or 'enum'.
                                    Use 'any' to apply stropping rules for all identifier types to the instance.
        """
        short_name = "{short}_{major}_{minor}".format(short=t.short_name, major=t.version.major, minor=t.version.minor)
        if YesNoDefault.test_truth(stropping, self.enable_stropping):
            return self.filter_id(short_name, id_type)
        else:
            return short_name

    def get_config_value(self, key: str, default_value: typing.Optional[str] = None) -> str:
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

    def get_config_value_as_dict(
        self, key: str, default_value: typing.Optional[typing.Dict] = None
    ) -> typing.Dict[str, typing.Any]:
        """
        Get a language property parsing it as a map with string keys.

        .. invisible-code-block: python

            from nunavut.lang import LanguageConfig, LanguageLoader, Language, _GenericLanguage

            config = LanguageConfig()
            config.add_section('nunavut.lang.c')
            config.set('nunavut.lang.c', 'foo', {'one': 1})

            lang_c = _GenericLanguage(LanguageLoader.load_language_module('c'), config, True)

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

    def get_config_value_as_list(
        self, key: str, default_value: typing.Optional[typing.List] = None
    ) -> typing.List[typing.Any]:
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
        return self._config.get_config_value(self._section, "extension", "get")

    @property
    def namespace_output_stem(self) -> typing.Optional[str]:
        """
        The name of a namespace file for this language.
        """
        try:
            return self._config.get_config_value(self._section, "namespace_file_stem")
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

            config = {
                'nunavut.lang.cpp':
                {
                    'support_namespace': 'foo.bar'
                }
            }
            lctx = configurable_language_context_factory(config, 'cpp')
            lang_cpp = lctx.get_target_language()

            assert len(lang_cpp.support_namespace) == 2
            assert lang_cpp.support_namespace[0] == 'foo'
            assert lang_cpp.support_namespace[1] == 'bar'

        """
        namespace_str = self._config.get_config_value(self._section, "support_namespace", default_value="")
        return namespace_str.split(".")

    @property
    def enable_stropping(self) -> bool:
        """
        Whether or not to strop identifiers for this language.
        """
        return self._config.get_config_value_as_bool(self._section, "enable_stropping")

    @property
    def has_standard_namespace_files(self) -> bool:
        """
        Whether or not the language defines special namespace files as part of
        its core standard (e.g. python's __init__).
        """
        return self._config.get_config_value_as_bool(self._section, "has_standard_namespace_files")

    @property
    def stable_support(self) -> bool:
        """
        Whether support for this language is designated 'stable', and not experimental.
        """
        return self._config.get_config_value_as_bool(self._section, "stable_support")

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

            from nunavut.lang import Language, _GenericLanguage
            from unittest.mock import MagicMock

            mock_config = MagicMock()
            mock_module = MagicMock()
            mock_module.__name__ = 'nunavut.lang.foo'

            my_lang = _GenericLanguage(mock_module, mock_config, True)
            my_lang._section = "nunavut.lang.not_a_language_really_not_a_language"
            for support_file in my_lang.support_files:
                # if the module doesn't exist it shouldn't have any support files.
                assert False

        """
        _, _, module = self.get_support_module()

        if module is not None:
            # All language support modules must provide a list_support_files method
            # to allow the copy generator access to the packaged support files.
            list_support_files = getattr(
                module, "list_support_files"
            )  # type: typing.Callable[[], typing.Generator[pathlib.Path, None, None]]
            return list_support_files()
        else:
            # No serialization support for this language
            def list_support_files() -> typing.Generator[pathlib.Path, None, None]:
                # This makes both MyPy and sonarqube happy.
                return typing.cast(typing.Generator[pathlib.Path, None, None], iter(()))

            return list_support_files()

    def get_option(
        self, option_key: str, default_value: typing.Union[typing.Mapping[str, typing.Any], str, None] = None
    ) -> typing.Union[typing.Mapping[str, typing.Any], str, None]:
        """
        Get a language option for this language.

        .. invisible-code-block: python

            config = {
                'nunavut.lang.cpp':
                {
                    'options': {'target_endianness': 'little'}
                }
            }
            lctx = configurable_language_context_factory(config, 'cpp')
            lang_cpp = lctx.get_target_language()

        .. code-block:: python

            # Values can come from defaults...
            assert lang_cpp.get_option('target_endianness') == 'little'

            # ... or can come from a sane default.
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
        return self._config.get_config_value_as_dict(self._section, "named_types", default_value={})

    def get_named_values(self) -> typing.Mapping[str, str]:
        """
        Get a map of named values to the token to emit for this language.
        """
        return self._config.get_config_value_as_dict(self._section, "named_values", default_value={})

    def get_globals(self) -> typing.Mapping[str, typing.Any]:
        """
        Get all values for this language that should be available in a global context.

        :return: A mapping of global names to global values.
        """
        if self._globals is None:
            globals_map = dict()  # type: typing.Dict[str, typing.Any]

            for key, value in self.get_named_types().items():
                globals_map["typename_{}".format(key)] = value
            for key, value in self.get_named_values().items():
                globals_map["valuetoken_{}".format(key)] = value

            self._globals = globals_map
        return self._globals

    def get_options(self) -> typing.Mapping[str, typing.Any]:
        """
        Get all language options for this Language.

        :return: A mapping of option names to option values.
        """
        return self._language_options


class _GenericLanguage(Language):
    """
    Language type used when the language support within Nunavut does not define a language-specific
    subclass.

    Do not use this. Use :class:`nunavut.lang.LanguageLoader` which will create the proper object type
    based on inspection of the Nunavut internals.
    """

    def get_includes(self, dep_types: Dependencies) -> typing.List[str]:
        return []


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
    :param additional_config_files: A list of paths to additional files to load as configuration.
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

    def __init__(
        self,
        target_language: typing.Optional[str] = None,
        extension: typing.Optional[str] = None,
        namespace_output_stem: typing.Optional[str] = None,
        additional_config_files: typing.List[pathlib.Path] = [],
        omit_serialization_support_for_target: bool = True,
        language_options: typing.Optional[typing.Mapping[str, typing.Any]] = None,
        include_experimental_languages: bool = True,
    ):
        self._extension = extension
        self._namespace_output_stem = namespace_output_stem
        self._ln_loader = LanguageLoader(*additional_config_files)
        self._config = self._ln_loader.config
        self._languages = dict()  # type: typing.Dict[str, Language]

        # create target language, if there is one.
        self._target_language = None
        if target_language is not None:
            try:
                self._target_language = self._ln_loader.load_language(
                    target_language, omit_serialization_support_for_target, language_options=language_options
                )
            except ImportError:
                raise KeyError("{} is not a supported language".format(target_language))
            if not (self._target_language.stable_support or include_experimental_languages):
                raise ValueError(
                    "{} support is only experimental, but experimental language support is not enabled".format(
                        target_language
                    )
                )
            if namespace_output_stem is None:
                self._namespace_output_stem = self._target_language.namespace_output_stem

            target_language_section_name = "nunavut.lang.{}".format(target_language)
            if self._namespace_output_stem is not None:
                self._config.set(target_language_section_name, "namespace_file_stem", self._namespace_output_stem)
            if extension is not None:
                self._config.set(target_language_section_name, "extension", extension)
            self._languages[target_language] = self._target_language

        # create remaining languages
        remaining_languages = set(self.get_supported_language_names()) - set((target_language,))
        self._populate_languages(remaining_languages, include_experimental_languages)

    def _populate_languages(self, language_names: typing.Iterable[str], include_experimental: bool) -> None:
        for language_name in language_names:
            try:
                lang = self._ln_loader.load_language(language_name, False)
                if lang.stable_support or include_experimental:
                    self._languages[language_name] = lang
            except ImportError:
                raise KeyError("{} is not a supported language".format(language_name))

    def get_language(self, key_or_module_name: str) -> Language:
        """
        Get a :class:`Language` object for a given language identifier.

        :param str key_or_module_name: Either one of the Nunavut mnemonics for a supported language or
            the ``__name__`` of one of the ``nunavut.lang.[language]`` python modules.
        :return: A :class:`Language` object cached by this context.
        :rtype: Language
        """
        if key_or_module_name is None or len(key_or_module_name) == 0:
            raise ValueError("key argument is required.")
        key = key_or_module_name[13:] if key_or_module_name.startswith("nunavut.lang.") else key_or_module_name
        return self.get_supported_languages()[key]

    def get_supported_language_names(self) -> typing.Iterable[str]:
        """Get a list of target languages supported by Nunavut.

        :return: An iterable of strings which are languages with special
            support within Nunavut templates.
        """
        return [s[13:] for s in self._config.sections() if s.startswith("nunavut.lang.")]

    def get_output_extension(self) -> str:
        """
        Gets the output extension to use regardless of a target language being available or not.

        :return: A file extension name with a leading dot.
        """
        if self._extension is not None:
            return self._extension
        elif self._target_language is not None:
            return self._target_language.extension
        else:
            raise RuntimeError(
                "No extension was provided and no target language was set. Cannot determine the extension to use."
            )

    def get_default_namespace_output_stem(self) -> typing.Optional[str]:
        """
        The filename stem to give to Namespace output files if emitted or None if there was none
        specified and there is no target language.

        :return: A file name stem or None
        """
        return self._namespace_output_stem

    def get_target_language(self) -> typing.Optional[Language]:
        """
        Returns the target language configured on this object or None
        if no target language was specified.
        """
        return self._target_language

    def filter_id_for_target(self, instance: typing.Any, id_type: str = "any") -> str:
        """
        A filter that will transform a given string or pydsdl identifier into a valid identifier in the target language.
        A default transformation is applied if no target language is set.

        :param any instance:        Any object or data that either has a name property or can be converted to a string.
        :param str id_type:         A type of identifier. This is different for each language.
                                    Use 'any' to apply stropping rules for all identifier types to the instance.
        :return: A token that is a valid identifier in the target language, is not a reserved keyword, and is
                 transformed in a deterministic manner based on the provided instance.
        """
        if self._target_language is not None:
            return self._target_language.filter_id(instance, id_type)
        else:
            return Language.default_filter_id_for_target(instance)

    def get_supported_languages(self) -> typing.Dict[str, Language]:
        """
        Returns a collection of available language support objects.
        """
        return self._languages

    @property
    def config(self) -> LanguageConfig:
        return self._config
