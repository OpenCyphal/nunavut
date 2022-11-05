#
# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2022  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
"""
Language-specific support in nunavut.

This module contains the Language object and supporting types.
"""
import abc
import functools
import importlib
import logging
import pathlib
import types
import typing

import pydsdl

from nunavut._dependencies import Dependencies, DependencyBuilder
from nunavut._utilities import ResourceType, YesNoDefault, empty_list_support_files, iter_package_resources

from ._config import LanguageConfig, VersionReader

logger = logging.getLogger(__name__)


# +---------------------------------------------------------------------------+
# | ABSTRACT LANGUAGE
# +---------------------------------------------------------------------------+


class Language(metaclass=abc.ABCMeta):
    """
    Facilities for generating source code for a specific language. Concrete Language classes must be implemented
    by the language support package below lang and should be instantiated using
    :class:`nunavut.lang.LanguageClassLoader`.

    :param str module_name:                  The name of the :mod:`nunavut.lang` module that contains the concrete
                                             language type and its resources.
    :param LanguageConfig config:            All configuration as defined by the properties.yaml schema.
    :param kwargs:                           Opaque arguments passed through to the target
                                             :class:`nunavut.lang.Language` object. See all "WKLA" constants
                                             on this class for well-known keyword arguments.

        .. invisible-code-block: python

            from nunavut.lang._language import Language
            from nunavut.lang._language import _GenericLanguage
            from unittest.mock import MagicMock

            mock_config = MagicMock()

            try:
                my_lang = _GenericLanguage("foo", mock_config)
                # module must be within 'nunavut'
                assert False
            except RuntimeError:
                pass

            try:
                my_lang = _GenericLanguage("nunavut.foo", mock_config)
                # module must be within 'nunavut.lang'
                assert False
            except RuntimeError:
                pass

            try:
                my_lang = _GenericLanguage("not.nunavut.foo", mock_config)
                # module must be within 'nunavut.lang'
                assert False
            except RuntimeError:
                pass

            my_lang = _GenericLanguage("nunavut.lang.foo", mock_config)
            assert my_lang.name == 'foo'
    """

    # Well-Known Configuration Values (WKCV)
    # These are language configuration values the base Language class will look for.
    WKCV_DEFINITION_FILE_EXTENSION = "extension"
    WKCV_NAMESPACE_FILE_STEM = "namespace_file_stem"
    WKCV_SUPPORT_NAMESPACE = "support_namespace"
    WKCV_ENABLE_STROPPING = "enable_stropping"
    WKCV_HAS_STANDARD_NAMESPACE_FILES = "has_standard_namespace_files"
    WKCV_STABLE_SUPPORT = "stable_support"
    WKCV_NAMED_TYPES = "named_types"
    WKCV_NAMED_VALUES = "named_values"
    WKCV_LANGUAGE_OPTIONS = "options"

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

    # +-----------------------------------------------------------------------+
    # | LIFECYCLE AND DATA MODEL
    # +-----------------------------------------------------------------------+

    def __init__(self, language_module_name: str, config: LanguageConfig, **kwargs: typing.Any):
        self._globals = None  # type: typing.Optional[typing.Mapping[str, typing.Any]]
        self._section = language_module_name
        if not self._section.startswith(LanguageClassLoader.MODULE_PREFIX):
            raise RuntimeError("Unknown module name for language: {}".format(self._section))
        self._language_name = LanguageClassLoader.to_language_name(self._section)
        self._config = config
        self._language_options = config.get_config_value_as_dict(self._section, self.WKCV_LANGUAGE_OPTIONS, dict())
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

    # +-----------------------------------------------------------------------+
    # | PROPERTIES
    # +-----------------------------------------------------------------------+
    @property
    def extension(self) -> str:
        """
        The extension to use for files generated in this language.
        """
        return self._config.get_config_value(self._section, self.WKCV_DEFINITION_FILE_EXTENSION)

    @property
    def namespace_output_stem(self) -> typing.Optional[str]:
        """
        The name of a namespace file for this language.
        """
        return self._config.get_config_value(self._section, self.WKCV_NAMESPACE_FILE_STEM, None)

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

            from nunavut.lang import Language, LanguageContextBuilder

            lang_cpp = (
                LanguageContextBuilder(include_experimental_languages=True)
                    .set_target_language("cpp")
                    .set_target_language_configuration_override(Language.WKCV_SUPPORT_NAMESPACE, "foo.bar")
                    .create()
                    .get_target_language()
            )

            assert len(lang_cpp.support_namespace) == 2
            assert lang_cpp.support_namespace[0] == 'foo'
            assert lang_cpp.support_namespace[1] == 'bar'

        """
        namespace_str = self._config.get_config_value(self._section, self.WKCV_SUPPORT_NAMESPACE, default_value="")
        return namespace_str.split(".")

    @property
    def enable_stropping(self) -> bool:
        """
        Whether or not to strop identifiers for this language.
        """
        return self._config.get_config_value_as_bool(self._section, self.WKCV_ENABLE_STROPPING)

    @property
    def has_standard_namespace_files(self) -> bool:
        """
        Whether or not the language defines special namespace files as part of
        its core standard (e.g. python's __init__).
        """
        return self._config.get_config_value_as_bool(self._section, self.WKCV_HAS_STANDARD_NAMESPACE_FILES)

    @property
    def stable_support(self) -> bool:
        """
        Whether support for this language is designated 'stable', and not experimental.
        """
        return self._config.get_config_value_as_bool(self._section, self.WKCV_STABLE_SUPPORT)

    @property
    def named_types(self) -> typing.Mapping[str, str]:
        """
        Get a map of named types to the type name to emit for this language.
        """
        return self._config.get_config_value_as_dict(self._section, self.WKCV_NAMED_TYPES, default_value={})

    @property
    def named_values(self) -> typing.Mapping[str, str]:
        """
        Get a map of named values to the token to emit for this language.
        """
        return self._config.get_config_value_as_dict(self._section, self.WKCV_NAMED_VALUES, default_value={})

    # +-----------------------------------------------------------------------+
    # | METHODS
    # +-----------------------------------------------------------------------+

    def get_support_module(self) -> typing.Tuple[str, typing.Tuple[int, int, int], typing.Optional["types.ModuleType"]]:
        """
        Returns the module object for the language support files.
        :return: A tuple of module name, x.y.z module version, and the module object itself.

        .. invisible-code-block: python

            from nunavut.lang._language import Language, _GenericLanguage, LanguageConfig
            from unittest.mock import MagicMock

            mock_config = MagicMock()
            mock_module_name= LanguageClassLoader.to_language_module_name("cpp")

            my_lang = _GenericLanguage(mock_module_name, mock_config)
            my_lang._section = LanguageClassLoader.to_language_module_name("cpp")
            module_name, support_version, _ = my_lang.get_support_module()

            assert module_name == LanguageClassLoader.to_language_module_name("cpp") + ".support"
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

            from nunavut.lang._language import LanguageConfig, LanguageClassLoader, Language, _GenericLanguage

            config = LanguageConfig()
            config.add_section('nunavut.lang.c')
            config.set('nunavut.lang.c', 'foo', {'one': 1})

            lang_c = _GenericLanguage(LanguageClassLoader.to_language_module_name('c'), config)

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

    def get_support_files(
        self, resource_type: ResourceType = ResourceType.ANY
    ) -> typing.Generator[pathlib.Path, None, None]:
        """
        Iterates over supporting files embedded within the Nunavut distribution.

        :param resource_type: The type of support resources to enumerate.

        .. invisible-code-block: python

            from nunavut.lang._language import Language, _GenericLanguage, LanguageClassLoader
            from unittest.mock import MagicMock

            mock_config = MagicMock()
            mock_module_name_ = LanguageClassLoader.to_language_module_name("foo")

            my_lang = _GenericLanguage(mock_module_name_, mock_config)
            my_lang._section =  LanguageClassLoader.to_language_module_name("not_a_language_really_not_a_language")
            for support_file in my_lang.get_support_files():
                # if the module doesn't exist it shouldn't have any support files.
                assert False

        """
        _, _, module = self.get_support_module()

        if module is not None:
            # All language support modules must provide a list_support_files method
            # to allow the copy generator access to the packaged support files.
            list_support_files = getattr(
                module, "list_support_files"
            )  # type: typing.Callable[[ResourceType], typing.Generator[pathlib.Path, None, None]]
            return list_support_files(resource_type)
        else:
            return empty_list_support_files()

    def get_option(
        self, option_key: str, default_value: typing.Union[typing.Mapping[str, typing.Any], str, None] = None
    ) -> typing.Union[typing.Mapping[str, typing.Any], str, None]:
        """
        Get a language option for this language.

        .. invisible-code-block: python

            from nunavut.lang import Language, LanguageContextBuilder

            options = {'target_endianness': 'little'}

            lang_cpp = (
                LanguageContextBuilder(include_experimental_languages=True)
                    .set_target_language("cpp")
                    .set_target_language_configuration_override(Language.WKCV_LANGUAGE_OPTIONS, options)
                    .create()
                    .get_target_language()
            )

        .. code-block:: python

            # Values can come from defaults...
            assert lang_cpp.get_option('target_endianness') == 'little'

            # ... or can come from a sane default.
            assert lang_cpp.get_option('foobar', 'sane_default') == 'sane_default'

        :return: Either the value provided to the :class:`nunavut.lang.Language` instance, the value from
            properties.yaml or the :code:`default_value`.

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

    def get_globals(self) -> typing.Mapping[str, typing.Any]:
        """
        Get all values for this language that should be available in a global context.

        :return: A mapping of global names to global values.
        """
        if self._globals is None:
            globals_map = dict()  # type: typing.Dict[str, typing.Any]

            for key, value in self.named_types.items():
                globals_map["typename_{}".format(key)] = value
            for key, value in self.named_values.items():
                globals_map["valuetoken_{}".format(key)] = value

            self._globals = globals_map
        return self._globals

    def get_options(self) -> typing.Mapping[str, typing.Any]:
        """
        Get all language options for this Language.

        :return: A mapping of option names to option values.
        """
        return self._language_options


# +---------------------------------------------------------------------------+
# | UNDEFINED LANGUAGE TYPE (concrete)
# +---------------------------------------------------------------------------+


class _GenericLanguage(Language):
    """
    Language type used when the language support within Nunavut does not define a language-specific
    subclass.

    Do not use this. Use :class:`nunavut.lang.LanguageClassLoader` which will create the proper object type
    based on inspection of the Nunavut internals.
    """

    def get_includes(self, dep_types: Dependencies) -> typing.List[str]:
        return []


# +---------------------------------------------------------------------------+
# | LANGUAGE CLASSLOADER
# +---------------------------------------------------------------------------+


class LanguageClassLoader:
    """
    Class loader to resolve concrete :class:`nunavut.lang.Language` types.

    :param additional_config_files: A list of paths to additional configuration files to load as configuration.
        These will override any values found in the :file:`nunavut.lang.properties.yaml` file and files
        appearing later in this list will override value found in earlier entries.

        .. invisible-code-block: python

            from nunavut.lang import LanguageClassLoader, LanguageConfig

            subject = LanguageClassLoader()

            c_reserved_identifiers = subject.config.get_config_value(
                LanguageClassLoader.to_language_module_name("c"), "reserved_identifiers")
            assert len(c_reserved_identifiers) > 0
    """

    MODULE_NAME = "nunavut.lang"
    MODULE_PREFIX = MODULE_NAME + "."
    MODULE_FORMAT = MODULE_PREFIX + "{}"

    @classmethod
    def to_language_name(cls, unknown_string: str) -> str:
        """
        Helper method to take a string that is either a language name or a language module name
        and always return a langauge name.

        .. invisible-code-block: python
            from nunavut.lang import LanguageClassLoader

        .. code-block: python

            assert "c" == LanguageClassLoader.to_language_name("c")
            assert "c" == LanguageClassLoader.to_language_name("nunavut.lang.c")

        """
        return (
            unknown_string[len(cls.MODULE_PREFIX) :] if unknown_string.startswith(cls.MODULE_PREFIX) else unknown_string
        )

    @classmethod
    def to_language_module_name(cls, unknown_string: str) -> str:
        """
        Helper method to take a string that is either a language name or a language module name
        and always return a langauge module name.

        .. invisible-code-block: python
            from nunavut.lang import LanguageClassLoader

        .. code-block: python

            assert "nunavut.lang.c" == LanguageClassLoader.to_language_module_name("c")
            assert "nunavut.lang.c" == LanguageClassLoader.to_language_module_name("nunavut.lang.c")

        """
        return (
            cls.MODULE_FORMAT.format(unknown_string)
            if not unknown_string.startswith(cls.MODULE_PREFIX)
            else unknown_string
        )

    @classmethod
    def _load_config(cls) -> LanguageConfig:
        parser = LanguageConfig()
        for resource in iter_package_resources(cls.MODULE_NAME, ".yaml"):
            ini_string = resource.read_text()
            parser.update_from_string(ini_string)
        return parser

    def __init__(self) -> None:
        self._config = None  # type: typing.Optional[LanguageConfig]

    @classmethod
    def load_language_module(cls, language_name: str) -> "types.ModuleType":
        module_name = cls.to_language_module_name(language_name)
        return importlib.import_module(module_name)

    @property
    def config(self) -> LanguageConfig:
        """
        Meta-data about all languages merged from the Nunavut internal defaults and any additional
        configuration files provided to this class's constructor.
        """
        if self._config is None:
            self._config = self._load_config()
        return self._config

    @functools.lru_cache()
    def load_language_class(self, language_name: str) -> typing.Tuple[types.ModuleType, typing.Type[Language]]:
        """
        :param str language_name:                The name of the language used by the :mod:`nunavut.lang` module.

        :return: A concrete :class:`nunavut.lang.Language`.

        .. invisible-code-block: python

            from nunavut.lang import LanguageClassLoader, Language

            lang_c_mod, lang_c_cls = LanguageClassLoader().load_language_class('c')
            assert lang_c_mod.__name__ == 'nunavut.lang.c'
            assert issubclass(lang_c_cls, Language)

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

        return (ln_module, language_type)

    def new_language(self, language_name: str, **kwargs: typing.Any) -> Language:
        """
        Instantiate a new language class. This is a helper that reuses the internally held
        module and :class:`LanguageConfig` to invoke the required :class:`nunavut.lang.Language` constructor.

        :param str language_name:                The name of the language used by the :mod:`nunavut.lang` module.
        :param kwargs:                           Opaque arguments passed to the :class:`nunavut.lang.Language`
                                                 constructor.

        :return: A new :class:`nunavut.lang.Language` instance.

        .. invisible-code-block: python

            from nunavut.lang import LanguageClassLoader

        .. code-block:: python

            # Using this helper method:

            lang_c = LanguageClassLoader().new_language('c')

            assert lang_c.name == 'c'


            # Without the helper:

            loader = LanguageClassLoader()
            lang_c_module, lang_c_class = loader.load_language_class('c')
            lang_c = lang_c_class(lang_c_module.__name__, loader.config)

            assert lang_c.name == 'c'

        .. invisible-code-block: python

            # let's go ahead and load the rest of our known, internally supported languages just to raise
            # test failures right here at the wellspring.

            lang_py = LanguageClassLoader().new_language('py')
            assert lang_py.name == 'py'

            lang_js = LanguageClassLoader().new_language('js')
            assert lang_js.name == 'js'

        """
        ln_module, ln_class = self.load_language_class(language_name)
        return ln_class(ln_module.__name__, config=self.config, **kwargs)
