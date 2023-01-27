#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2020  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
"""Language-specific support in nunavut.

This package contains modules that provide specific support for generating
source for various languages using templates.
"""
import functools
import logging
import pathlib
import typing

from ._config import LanguageConfig as LanguageConfig
from ._language import Language as Language
from ._language import LanguageClassLoader as LanguageClassLoader

logger = logging.getLogger(__name__)


class UnsupportedLanguageError(ValueError):
    """
    Error type raised if an unsupported language type is used.
    """

    pass


class LanguageContextBuilder:
    """
    Used to instatiate new :class:`LanguageContext` objects.

    The simplest invocation will always work by using the :data:`LanguageContextBuilder.DEFAULT_TARGET_LANGUAGE`
    constant:

    .. code-block:: python

        from nunavut.lang import LanguageContextBuilder

        default_language_context = LanguageContextBuilder().create()

        assert LanguageContextBuilder.DEFAULT_TARGET_LANGUAGE == default_language_context.get_target_language().name

    Typically a target language is specified at minimum. Also see constants on :class:`nunavut.lang.Language` for
    well-known options that the builder can override:

    .. code-block:: python

        from nunavut.lang import LanguageContextBuilder

        customized_language_context = (
            LanguageContextBuilder()
                .set_target_language("c")
                .set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".h")
                .create()
        )

        assert customized_language_context.get_target_language().extension == ".h"

    :param include_experimental_languages: If set then languages that are not fully supported will be allowed otherwise
        any experimental languages will be missing and errors will be raised as if the language specified was unknown.

    """

    DEFAULT_TARGET_LANGUAGE = "c"  #: The target language used for new contexts if none is specified.

    def __init__(self, include_experimental_languages: bool = False):
        self._target_language_name: typing.Optional[str] = None
        self._target_language_config: typing.Dict[str, str] = {}
        self._ln_loader = LanguageClassLoader()
        self._include_experimental_languages = include_experimental_languages

    def get_supported_language_names(self) -> typing.Iterable[str]:
        """
        Get a list of target languages supported by Nunavut.

        :return: An iterable of strings which are languages with special
            support within Nunavut templates.
        """
        return [LanguageClassLoader.to_language_name(s) for s in self._ln_loader.config.sections()]

    @property
    def config(self) -> LanguageConfig:
        return self._ln_loader.config

    # +-----------------------------------------------------------------------+
    # | BUILDER SYNTAX
    # +-----------------------------------------------------------------------+

    def set_target_language_configuration_override(self, key: str, value: typing.Any) -> "LanguageContextBuilder":
        """
        Stores a key and value to override in the configuration for a language target when a LanguageContext is crated.
        These overrides are always set under the language section of the target langauge.

        .. invisible-code-block: python

            from nunavut.lang import LanguageContextBuilder, Language, LanguageClassLoader

        .. code-block:: python

            builder = LanguageContextBuilder().set_target_language("c")

            default_c_file_extension = builder.config.get_config_value(
                                            LanguageClassLoader.to_language_module_name("c"),
                                            Language.WKCV_DEFINITION_FILE_EXTENSION)

            assert default_c_file_extension == ".h"

        We can now try to override the file extension for a future "C" target language object:

        .. code-block:: python

            builder.set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".foo")

        ...but that value will not be overriden until you create the target language:

        .. code-block:: python

            default_c_file_extension = builder.config.get_config_value(
                                            LanguageClassLoader.to_language_module_name("c"),
                                            Language.WKCV_DEFINITION_FILE_EXTENSION)

            assert default_c_file_extension == ".h"

            _ = builder.create()

            overridden_c_file_extension = builder.config.get_config_value(
                                            LanguageClassLoader.to_language_module_name("c"),
                                            Language.WKCV_DEFINITION_FILE_EXTENSION)

            assert overridden_c_file_extension == ".foo"

        Note that the config is scoped by the builder but is then inherited by the langauge objects created by the
        builder:

        .. code-block:: python

            one = (
                LanguageContextBuilder()
                    .set_target_language("c")
                    .set_target_language_configuration_override("foo", 1)
                )
            two = (
                LanguageContextBuilder()
                    .set_target_language("c")
                    .set_target_language_configuration_override("foo", 2)
                )

            # Here we see that the second override of "foo" does not affect the first because they
            # are in different builders.

            assert (
                    one.create().get_target_language().get_config_value("foo")
                    !=
                    two.create().get_target_language().get_config_value("foo")
                )

        """
        if value is not None:
            self._target_language_config[key] = value
        return self

    def set_target_language_extension(
        self, target_language_extension: typing.Optional[str]
    ) -> "LanguageContextBuilder":
        """
        Helper method for setting the target language file extension (since this is a common override).

        Calling this method is the same as doing:

        .. invisible-code-block: python

            from nunavut.lang import LanguageContextBuilder, Language, LanguageClassLoader

        .. code-block:: python

            LanguageContextBuilder().set_target_language_configuration_override(
                Language.WKCV_DEFINITION_FILE_EXTENSION,
                ".h")

        """
        return self.set_target_language_configuration_override(
            Language.WKCV_DEFINITION_FILE_EXTENSION, target_language_extension
        )

    def set_target_language(self, target_language: typing.Optional[str]) -> "LanguageContextBuilder":
        """
        Set the language name to target. This can be either the name of the language, as defined by Nunavut, or
        it can be the language package name.

        .. invisible-code-block: python

            from nunavut.lang import LanguageContextBuilder, LanguageClassLoader

        .. code-block:: python

            assert LanguageContextBuilder().set_target_language("c").create().get_target_language().name == "c"

            assert (
                LanguageContextBuilder()
                    .set_target_language(LanguageClassLoader.to_language_module_name("c"))
                    .create()
                    .get_target_language().name == "c"
            )

        Also note that, if the language name is None, the default name will be assigned internally:

        .. code-block:: python

            target_language = LanguageContextBuilder().set_target_language(None).create().get_target_language()

            assert target_language.name == LanguageContextBuilder.DEFAULT_TARGET_LANGUAGE

        """
        if target_language is None:
            self._target_language_name = self.DEFAULT_TARGET_LANGUAGE
        else:
            self._target_language_name = LanguageClassLoader.to_language_name(target_language)
        return self

    def set_additional_config_files(
        self, additional_config_files: typing.List[pathlib.Path]
    ) -> "LanguageContextBuilder":
        """
        A list of paths to additional yaml files to load as configuration.
        These will override any values found in the :file:`nunavut.lang.properties.yaml` file and files
        appearing later in this list will override value found in earlier entries.

        .. invisible-code-block: python

            import pathlib
            import yaml
            import textwrap
            from nunavut.lang import LanguageContextBuilder, Language, LanguageClassLoader

            overrides_file = gen_paths.out_dir / pathlib.Path("overrides1.yaml")

            overrides_data = {LanguageClassLoader.to_language_module_name("c"):
                {Language.WKCV_DEFINITION_FILE_EXTENSION: ".foo"}
            }

            with open(overrides_file, "w") as overrides_handle:
                yaml.dump(overrides_data, overrides_handle)

        .. code-block:: python

            target_language_w_overrides = (
                LanguageContextBuilder()
                    .set_target_language("c")
                    .set_additional_config_files([overrides_file])
                    .create()
                    .get_target_language()
            )

            target_language_no_overrides = (
                LanguageContextBuilder()
                    .set_target_language("c")
                    .create()
                    .get_target_language()
            )

            assert target_language_w_overrides.extension == ".foo"
            assert target_language_no_overrides.extension == ".h"

        Overrides are applies as unions. For example, given this override data:

        .. code-block:: python

            overrides_data = '''
                nunavut.lang.c:
                    extension: .foo
                    non-standard: bar
            '''

        ...the standard "extension" property will be overridden and the "non-standard" property will be added.

        .. invisible-code-block: python

            second_overrides_file = gen_paths.out_dir / pathlib.Path("overrides2.yaml")
            with open(second_overrides_file, "w") as overrides_handle:
                overrides_handle.write(textwrap.dedent(overrides_data))

        .. code-block:: python

            target_language_w_overrides = (
                LanguageContextBuilder()
                    .set_target_language("c")
                    .set_additional_config_files([second_overrides_file])
                    .create()
                    .get_target_language()
            )

            assert ".foo" == target_language_w_overrides.extension
            assert "bar" == target_language_w_overrides.get_config_value("non-standard")

        """
        for additional_path in additional_config_files:
            with open(str(additional_path), "r") as additional_file:
                self._ln_loader.config.update_from_file(additional_file)

        return self

    def create(self) -> "LanguageContext":
        """
        Applies all pending configuration overrides to the internal :class:`LanguageConfig` object and instatiates
        a :class:`LanguageContext` object.
        """
        # First find the target language to use...
        target_language_name = self._resolve_target_language(self._target_language_name)

        # Now update the configuration for the target language with everything we stored in this
        # builder instance...
        self.config.update_section(
            LanguageClassLoader.to_language_module_name(target_language_name), self._target_language_config
        )

        # Create the target language instance...
        target_language = self._new_language_w_experimental_handling(target_language_name)

        # and finally, build the LanguageContext.
        return LanguageContext(
            self._ln_loader.config, target_language, functools.partial(self._new_language_map, target_language)
        )

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _new_language_w_experimental_handling(self, language_name: str) -> Language:
        try:
            language = self._ln_loader.new_language(language_name)
        except ImportError as e:
            logger.debug("Import Error {} when trying to load language {}".format(str(e), language_name))
            raise KeyError("language {} is not a supported language".format(language_name))
        if not (language.stable_support or self._include_experimental_languages):
            raise UnsupportedLanguageError(
                "{} support is only experimental, but experimental language support is not enabled".format(
                    language_name
                )
            )
        return language

    def _new_language_map(self, target_language: Language) -> typing.Dict[str, Language]:
        """
        Build a map of all supported languages.
        :param target_language: The target language is included in the returned map but must be build
            by another method.
        """
        languages: typing.Dict[str, Language] = {target_language.name: target_language}
        for language_name in set(self.get_supported_language_names()) - set((target_language.name,)):
            try:
                languages[language_name] = self._new_language_w_experimental_handling(language_name)
            except UnsupportedLanguageError:
                pass
        return languages

    def _resolve_target_language(self, explicit_value: typing.Optional[str]) -> str:

        if explicit_value is not None:
            return explicit_value

        inferred_target_language_name: typing.Optional[str] = None

        target_extension = self._target_language_config.get(Language.WKCV_DEFINITION_FILE_EXTENSION, None)
        if target_extension is not None:
            for language_config_section_name, language_config_section in self.config.sections().items():
                if language_config_section.get("extension", None) == target_extension:
                    inferred_target_language_name = LanguageClassLoader.to_language_name(language_config_section_name)
                    break

        if inferred_target_language_name is None:
            inferred_target_language_name = self.DEFAULT_TARGET_LANGUAGE
            logger.info(
                "No target language specified and none could be inferred. Using default language, {}".format(
                    self.DEFAULT_TARGET_LANGUAGE
                )
            )
        else:
            logging.info(
                'Inferring target language %s based on extension "%s".',
                inferred_target_language_name,
                target_extension,
            )
        return inferred_target_language_name


class LanguageContext:
    """
    Context object containing the current target language and all supported :class:`nunavut.lang.Language` objects.

    :param language_configuration: The configuration for all languages as defined by the properties.yaml schema.
    :param target_language: The target language.
    :param supported_language_builder: factory closure that will create :class:`nunavut.lang.Language` objects for
                                       all supported languages when :func:`LanguageContext.get_target_languages`
                                       is first called.
    """

    def __init__(
        self,
        language_configuration: LanguageConfig,
        target_language: Language,
        supported_language_builder: typing.Callable[[], typing.Dict[str, Language]],
    ):
        self._config = language_configuration
        self._target_language = target_language
        self._all_supported_languages: typing.Optional[typing.Dict[str, Language]] = None
        self._all_supported_languages_builder = supported_language_builder

    def get_language(self, key_or_module_name: str) -> Language:
        """
        Get a :class:`nunavut.lang.Language` object for a given language identifier.

        :param str key_or_module_name: Either one of the Nunavut mnemonics for a supported language or
            the ``__name__`` of one of the ``nunavut.lang.[language]`` python modules.
        :return: A :class:`nunavut.lang.Language` object cached by this context.
        :rtype: nunavut.lang.Language
        """
        if key_or_module_name is None or len(key_or_module_name) == 0:
            raise ValueError("key argument is required.")
        key = LanguageClassLoader.to_language_name(key_or_module_name)
        return self.get_supported_languages()[key]

    def get_target_language(self) -> Language:
        """
        Returns the target language for code generation.
        """
        return self._target_language

    def filter_id_for_target(self, instance: typing.Any, id_type: str = "any") -> str:
        """
        A filter that will transform a given string or pydsdl identifier into a valid identifier in the target language.

        :param any instance:        Any object or data that either has a name property or can be converted to a string.
        :param str id_type:         A type of identifier. This is different for each language.
                                    Use 'any' to apply stropping rules for all identifier types to the instance.
        :return: A token that is a valid identifier in the target language, is not a reserved keyword, and is
                 transformed in a deterministic manner based on the provided instance.
        """
        return self._target_language.filter_id(instance, id_type)

    def get_supported_languages(self) -> typing.Dict[str, Language]:
        """
        Returns a collection of available language support objects.

         .. invisible-code-block: python

            from nunavut.lang import LanguageContextBuilder

            lctx = LanguageContextBuilder().create()

            default_language = None

            for language_name, language in lctx.get_supported_languages().items():
                if language_name == LanguageContextBuilder.DEFAULT_TARGET_LANGUAGE:
                    default_language = language
                    break

            assert default_language is not None
            assert default_language.name == LanguageContextBuilder.DEFAULT_TARGET_LANGUAGE
            assert len(lctx.get_supported_languages()) > 1

        """
        if self._all_supported_languages is None:
            self._all_supported_languages = self._all_supported_languages_builder()
        return self._all_supported_languages

    @property
    def config(self) -> LanguageConfig:
        return self._config
