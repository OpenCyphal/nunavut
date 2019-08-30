#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""Language-specific support in jinja templates.

This package contains modules that provide specific support for generating
source for various languages using jinja templates.
"""
import inspect
import typing
import logging

from nunavut.jinja.jinja2 import Environment

from . import c, cpp, js, py

__language_modules__ = {
    'c': c,
    'cpp': cpp,
    'js': js,
    'py': py
}

logger = logging.getLogger(__name__)


def get_supported_languages() -> typing.Iterable[str]:
    """Get a list of languages this module supports.

    :returns: An iterable of strings which are language names accepted by the
        :func:`~add_language_support` function.
    """
    return __language_modules__.keys()


def add_language_support(language_name: str, environment: Environment, make_implicit: bool = False) -> None:
    """
    Inspects a given language support module and adds all functions
    found whose name starts with "filter\\_" to the provided environment
    as "[language_name].[function name minus 'filter\\_']".

    For example, if a language module foo.py has a filter function
    "filter_bar" and this method is called with a prefix of "foo"
    then the environment will have a filter name "foo.bar" added to
    it.

    :param str language_name: The language to add support for.
    :param Environment environment: The jinja2 environment to inject
        language support into.
    :param bool make_implicit: Populate the environment globals directly with
        the given language features.

    :raises KeyError: If language_name is not a supported language.
    :raises RuntimeError: If called on an environment that already had implicit
                      language support installed.
    """
    if make_implicit:
        try:
            if environment.globals['_nv_implicit_language'] != language_name:
                raise RuntimeError('Implicit language support for {} was already installed.'.format(environment.globals['_nv_implicit_language']))
            else:
                logger.warning('Implicit language support for {} added twice.'.format(language_name))
            return
        except KeyError:
            environment.globals['_nv_implicit_language'] = language_name

    lang_module = __language_modules__[language_name]
    filters = inspect.getmembers(lang_module, inspect.isfunction)
    for function_tuple in filters:
        function_name = function_tuple[0]
        if len(function_name) > 7 and function_name[0:7] == "filter_":
            if make_implicit:
                environment.filters[function_name[7:]] = function_tuple[1]
                logging.debug("Adding implicit filter {} for language {}".format(function_name[7:], language_name))
            else:
                environment.filters["{}.{}".format(
                    language_name, function_name[7:])] = function_tuple[1]
