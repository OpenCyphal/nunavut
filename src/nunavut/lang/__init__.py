#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""Language-specific support in nunavut.

This package contains modules that provide specific support for generating
source for various languages using templates.
"""
import inspect
import typing
import logging
import importlib

logger = logging.getLogger(__name__)


class Language:
    """
    Facilities for generating source code for a specific language.

    :param str language_name:   The name of the language used by the :mod:`nunavut.lang` module.
    :param str extension: The extension to use for generated file types. All paths and filenames
            are built using pathlib. See pathlib documentation for platform differences
            when forming paths, filenames, and extensions.
    :param str namespace_output_stem: The filename stem to give to Namespace output files if
                                      emitted.
    """

    def __init__(self, language_name: str, extension: str, namespace_output_stem: typing.Optional[str] = None):
        self._language_name = language_name
        self._extension = extension
        self._namespace_output_stem = namespace_output_stem
        self._module = None  # type: typing.Optional[typing.Any]

    @property
    def extension(self) -> str:
        return self._extension

    @property
    def namespace_output_stem(self) -> typing.Optional[str]:
        return self._namespace_output_stem

    @property
    def name(self) -> str:
        """
        The name of the language used by the :mod:`nunavut.lang` module.
        """
        return self._language_name

    def get_module(self) -> typing.Any:
        """
        Return the python module that contains the language-specific resources.
        """
        if self._module is None:
            self._module = importlib.import_module('nunavut.lang.{}'.format(self._language_name))
        return self._module

    def get_templates_package_name(self) -> str:
        return 'nunavut.lang.{}'.format(self.name)


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
    :raises ValueError: If extension is None and no target language was provided.
    :raises KeyError: If the target language is not known.
    """

    _language_defaults = {
        'c': ('.h', '_namespace_'),
        'cpp': ('.hpp', '_namespace_'),
        'js': ('.js', '_namespace_'),
        'py': ('.py', '__init__')
    }

    def __init__(self,
                 target_language: typing.Optional[str] = None,
                 extension: typing.Optional[str] = None,
                 namespace_output_stem: typing.Optional[str] = None):
        if extension is None:
            if target_language is None:
                raise ValueError('You must provide a target language if extension is not specified.')
            extension = self._language_defaults[target_language][0]
        self._extension = extension
        if target_language is None:
            self._namespace_output_stem = namespace_output_stem
        else:
            self._namespace_output_stem = (namespace_output_stem
                                           if namespace_output_stem is not None
                                           else self._language_defaults[target_language][1])
        self._target_language = (Language(target_language, extension, namespace_output_stem)
                                 if target_language is not None else None)
        self._language_modules = None  # type: typing.Optional[typing.Dict]

    def get_supported_language_names(self) -> typing.Iterable[str]:
        """Get a list of target languages supported by Nunavut.

        :returns: An iterable of strings which are languages with special
            support within Nunavut templates.
        """
        return self._language_defaults.keys()

    def get_output_extension(self) -> str:
        """
        Gets the output extension to use regardless of a target language being available or not.

        :returns: A file extension name with a leading dot.
        """
        return self._extension

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

    def get_id_filter(self) -> typing.Callable[[str], str]:
        """
        A filter that will transform a given string into a valid identifier
        in the target language. The string is pass through unmodified if no
        target language was set.
        """
        lang_module = self.get_target_language()
        if lang_module is not None:
            module_functions = inspect.getmembers(lang_module.get_module(), inspect.isfunction)
            for function_tuple in module_functions:
                if function_tuple[0] == 'filter_id':
                    return typing.cast(typing.Callable[[str], str], function_tuple[1])

        return lambda unfiltered: unfiltered

    def get_supported_languages(self) -> typing.Dict[str, Language]:
        """
        Returns a collection of available language support objects.
        """
        if self._language_modules is None:
            self._language_modules = dict()
            for language_name in self.get_supported_language_names():
                defaults_tuple = self._language_defaults[language_name]
                self._language_modules[language_name] = Language(language_name, defaults_tuple[0], defaults_tuple[1])
        return self._language_modules
