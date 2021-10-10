#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
Abstractions around template engine internals.
"""
import functools
import inspect
import types
import typing

import nunavut.lang

ENVIRONMENT_FILTER_ATTRIBUTE_NAME = "environmentfilter"
"""
For now this is set to a value that is internally compatible with the
embedded version of jinja2 we use in Nunavut. If you use this variable
instead of its current value you will be insulated from this.
"""

CONTEXT_FILTER_ATTRIBUTE_NAME = "contextfilter"
"""
For now this is set to a value that is internally compatible with the
embedded version of jinja2 we use in Nunavut. If you use this variable
instead of its current value you will be insulated from this.
"""

LANGUAGE_FILTER_ATTRIBUTE_NAME = "nv_languagefilter"
"""
Nunavut-specific attribute for filters or tests that take their :class:`nunavut.lang.Language`
as the first argument.
"""


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

    Note that any template that uses such a filter will make the jinja "frame"
    the filter appears within volatile and therefore unable to be optimized.
    """
    setattr(filter_func, CONTEXT_FILTER_ATTRIBUTE_NAME, True)
    return filter_func


def template_volatile_filter(filter_func: typing.Callable) -> typing.Callable[..., str]:
    """
    Decorator for marking a filter as volatile therefore disabling optimizations for the
    frame it appears within.
    An opaque object will be passed to the filter as the first argument.
    """
    setattr(filter_func, CONTEXT_FILTER_ATTRIBUTE_NAME, True)
    return filter_func


LanguageFilterReturnType = typing.TypeVar("LanguageFilterReturnType")


class GenericTemplateLanguageFilter(typing.Generic[LanguageFilterReturnType]):
    """
    Decorator for marking template filters that take a :class:`nunavut.lang.Language` object
    as the first argument with a generic return type.
    """

    def __init__(self, language_name_or_module: str):
        self._language_name_or_module = language_name_or_module

    def __call__(
        self, filter_func: typing.Callable[..., LanguageFilterReturnType]
    ) -> typing.Callable[..., LanguageFilterReturnType]:
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


class template_language_test(GenericTemplateLanguageFilter[bool]):
    """
    Decorator for marking template tests that take a :class:`nunavut.lang.Language` object
    as the first argument.
    """

    pass


# +-------------------------------------------------------------------------------------------------------------------+
# | LanguageEnvironment
# +-------------------------------------------------------------------------------------------------------------------+


class LanguageEnvironment:
    """
    Data structure defining stuff contributed to a template environment for a given :class:`Language`.
    """

    TEST_NAME_PREFIX = "is_"
    FILTER_NAME_PREFIX = "filter_"
    USES_QUERY_PREFIX = "uses_"

    @classmethod
    def is_test_name(cls, callable_name: typing.Optional[str]) -> bool:
        return (
            callable_name is not None
            and len(callable_name) >= len(cls.TEST_NAME_PREFIX)
            and callable_name.startswith(cls.TEST_NAME_PREFIX)
        )

    @classmethod
    def is_filter_name(cls, callable_name: typing.Optional[str]) -> bool:
        return (
            callable_name is not None
            and len(callable_name) >= len(cls.FILTER_NAME_PREFIX)
            and callable_name.startswith(cls.FILTER_NAME_PREFIX)
        )

    @classmethod
    def is_uses_query_name(cls, callable_name: typing.Optional[str]) -> bool:
        return (
            callable_name is not None
            and len(callable_name) >= len(cls.USES_QUERY_PREFIX)
            and callable_name.startswith(cls.USES_QUERY_PREFIX)
        )

    LanguageListT = typing.TypeVar(
        "LanguageListT", typing.AbstractSet[nunavut.lang.Language], typing.ValuesView[nunavut.lang.Language]
    )

    def __init__(self, language_name: str) -> None:
        self._language_name = language_name
        self._tests = dict()  # type: typing.Dict[str, typing.Callable]
        self._filters = dict()  # type: typing.Dict[str, typing.Callable]
        self._uses_queries = dict()  # type: typing.Dict[str, typing.Callable]

    @property
    def language_name(self) -> str:
        return self._language_name

    @property
    def tests(self) -> typing.Mapping[str, typing.Callable]:
        return self._tests

    @property
    def filters(self) -> typing.Mapping[str, typing.Callable]:
        return self._filters

    @property
    def uses_queries(self) -> typing.Mapping[str, typing.Callable]:
        return self._uses_queries

    @classmethod
    def _parse_callable_name(
        cls, callable: typing.Callable, callable_name: typing.Optional[str] = None
    ) -> typing.Tuple[typing.Optional[str], str]:
        if callable_name is None:
            if isinstance(callable, functools.partial):
                callable_name = callable.func.__name__
            else:
                callable_name = callable.__name__

        if cls.is_test_name(callable_name):
            prefix = cls.TEST_NAME_PREFIX  # type: typing.Optional[str]
            method_name = callable_name[len(cls.TEST_NAME_PREFIX) :]
        elif cls.is_filter_name(callable_name):
            prefix = cls.FILTER_NAME_PREFIX
            method_name = callable_name[len(cls.FILTER_NAME_PREFIX) :]
        elif cls.is_uses_query_name(callable_name):
            prefix = cls.USES_QUERY_PREFIX
            method_name = callable_name[len(cls.USES_QUERY_PREFIX) :]
        else:
            prefix = None
            method_name = callable_name

        return (prefix, method_name)

    @classmethod
    def handle_conventional_methods(
        cls,
        callable: typing.Callable,
        callable_name: typing.Optional[str] = None,
        supported_languages: typing.Optional[LanguageListT] = None,
    ) -> typing.Tuple[typing.Optional[str], str, typing.Callable]:
        """
        Processes method objects that utilize the nunavut convention of ``is_``, ``filter_``, or ``uses_`` prefixes.
        Also wraps the method in a partial if it requested the language as the first argument.

        :param str callable_name: If provided this is the name used to process the callable otherwise
                                the ``__name__`` property is used from the callable itself.
        :return: A 3-tuple with the prefix, method name without prefix, and the method or partial. If the first
                                element is ``None`` then the callable was not a conventional method.
        """

        prefix, method_name = cls._parse_callable_name(callable, callable_name)

        resolved_callable = None  # type: typing.Optional[typing.Callable]
        if hasattr(callable, LANGUAGE_FILTER_ATTRIBUTE_NAME):
            callable_language_name = getattr(callable, LANGUAGE_FILTER_ATTRIBUTE_NAME)

            if supported_languages is not None:
                for language in supported_languages:
                    if language.get_templates_package_name() == callable_language_name:
                        resolved_callable = functools.partial(callable, language)
                        break
            if resolved_callable is None:
                raise RuntimeWarning(
                    'Language callable "{}", required an unsupported language({})'.format(
                        method_name, callable_language_name
                    )
                )
        else:
            resolved_callable = callable

        return (prefix, method_name, resolved_callable)

    # +---------------------------------------------------------------------------------------------------------------+
    # | DATA MODEL
    # +---------------------------------------------------------------------------------------------------------------+
    def __getitem__(self, key: str) -> typing.Dict[str, typing.Callable]:
        key_case_insensitive = key.lower()
        if key_case_insensitive.startswith("is"):
            return self._tests
        elif key_case_insensitive.startswith("filter"):
            return self._filters
        elif key_case_insensitive.startswith("uses"):
            return self._uses_queries
        else:
            raise KeyError("Key {} was not supported by this object.".format(key))

    # +---------------------------------------------------------------------------------------------------------------+
    # | FACTORY
    # +---------------------------------------------------------------------------------------------------------------+
    @classmethod
    def find_all_conventional_methods_in_language_module(
        cls, language: nunavut.lang.Language, all_languages: LanguageListT, language_module: "types.ModuleType"
    ) -> "LanguageEnvironment":
        results = LanguageEnvironment(language.name)

        callables = inspect.getmembers(language_module, inspect.isfunction)
        for function_tuple in callables:
            result = cls.handle_conventional_methods(function_tuple[1], supported_languages=all_languages)
            if result[0] is not None:
                results[result[0]][result[1]] = result[2]

        return results
