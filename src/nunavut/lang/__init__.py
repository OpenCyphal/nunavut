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
    """
    def __init__(self, language_name: str):
        self._language_name = language_name
        self._module = None  # type: typing.Optional[typing.Any]

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


class LanguageContext:
    """
    Context object containing the current target language (if any) and used to access
    :class:`Language` objects.
    """

    _default_output_extensions = {
        'c': '.h',
        'cpp': '.hpp',
        'js': '.js',
        'py': '.py'
    }

    def __init__(self, target_language: typing.Optional[str] = None):
        self._target_language = (Language(target_language) if target_language is not None else None)
        self._language_modules = None  # type: typing.Optional[typing.Dict]

    def get_supported_language_names(self) -> typing.Iterable[str]:
        """Get a list of target languages supported by Nunavut.

        :returns: An iterable of strings which are languages with special
            support within Nunavut templates.
        """
        return self._default_output_extensions.keys()

    @classmethod
    def get_default_output_extension(cls, language_name: str) -> str:
        """
        For a given supported language get the default file extension to use when generating source
        code for the language.

        :param str language_name: One of the languages listed in the values returned by :func:`get_supported_language_names()`.
        :returns: A file extension name with a leading dot.
        :raises KeyError: If the language name is not known by this version of nunavut.
        """
        return cls._default_output_extensions[language_name]

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
                self._language_modules[language_name] = Language(language_name)
        return self._language_modules
