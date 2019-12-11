#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
Abstractions around template engine internals.
"""
import typing

ENVIRONMENT_FILTER_ATTRIBUTE_NAME = 'environmentfilter'
"""
For now this is set to a value that is internally compatible with the
embedded version of jinja2 we use in Nunavut. If you use this variable
instead of its current value you will be insulated from this.
"""

CONTEXT_FILTER_ATTRIBUTE_NAME = 'contextfilter'
"""
For now this is set to a value that is internally compatible with the
embedded version of jinja2 we use in Nunavut. If you use this variable
instead of its current value you will be insulated from this.
"""

LANGUAGE_FILTER_ATTRIBUTE_NAME = 'nv_languagefilter'
"""
Nunavut-specific attribute for filters that take their :class:`nunavut.lang.Language`
as the first argument.
"""


class SupportsTemplateEnv:
    """
    Provided as a pseudo
    `protocol <https://mypy.readthedocs.io/en/latest/protocols.html#simple-user-defined-protocols/>`_.
    (in anticipation of that becoming part of the core Python typing someday).

    :var Dict globals: A dictionary mapping global names (str) to variables (Any) that are available in
                       each template's global environment.
    :var Dict filters: A dictionary mapping filter names (str) to filters (Callable). Filters are simply
                       global functions available to templates but are most often used to transform a
                       given input to output emitted by the template.
    """

    globals = dict()  # type: typing.Dict[str, typing.Any]
    filters = dict()  # type: typing.Dict[str, typing.Callable]
    tests = dict()  # type: typing.Dict[str, typing.Callable[[typing.Any], bool]]


class SupportsTemplateContext:
    """
    Provided as a pseudo
    `protocol <https://mypy.readthedocs.io/en/latest/protocols.html#simple-user-defined-protocols/>`_.
    (in anticipation of that becoming part of the core Python typing someday).
    """


def template_environment_filter(filter_func: typing.Callable) -> typing.Callable[..., str]:
    """
    Decorator for marking environment dependent filters.
    An object supporting the :class:`SupportsTemplateEnv` protocol
    will be passed to the filter as the first argument.
    """
    setattr(filter_func, ENVIRONMENT_FILTER_ATTRIBUTE_NAME, True)
    return filter_func


def template_context_filter(filter_func: typing.Callable) -> typing.Callable[..., str]:
    """
    Decorator for marking context dependent filters.
    An object supporting the :class:`SupportsTemplateContext` protocol
    will be passed to the filter as the first argument.
    """
    setattr(filter_func, CONTEXT_FILTER_ATTRIBUTE_NAME, True)
    return filter_func


LanguageFilterReturnType = typing.TypeVar('LanguageFilterReturnType')


class GenericTemplateLanguageFilter(typing.Generic[LanguageFilterReturnType]):
    """
    Decorator for marking template filters that take a :class:`nunavut.lang.Language` object
    as the first argument with a generic return type.
    """

    def __init__(self, language_name_or_module: str):
        self._language_name_or_module = language_name_or_module

    def __call__(self, filter_func: typing.Callable[..., LanguageFilterReturnType]) \
            -> typing.Callable[..., LanguageFilterReturnType]:
        self._annotate_function(filter_func)
        return filter_func

    def _annotate_function(self, filter_func: typing.Callable[..., typing.Any]) -> None:
        setattr(filter_func, LANGUAGE_FILTER_ATTRIBUTE_NAME, self._language_name_or_module)


class template_language_filter(GenericTemplateLanguageFilter[str]):
    """
    Decorator for marking template filters that take a :class:`nunavut.lang.Language` object
    as the first argument.
    """
    pass


class template_language_list_filter(GenericTemplateLanguageFilter[typing.List[str]]):
    """
    Decorator for marking template filters that take a :class:`nunavut.lang.Language` object
    as the first argument and return a list of strings.
    """
    pass


class template_language_int_filter(GenericTemplateLanguageFilter[int]):
    """
    Decorator for marking template filters that take a :class:`nunavut.lang.Language` object
    as the first argument and return an integer.
    """
    pass
