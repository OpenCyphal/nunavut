#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# This software is distributed under the terms of the MIT License.
#
"""
Enable pytest integration of doctests in source and/or in documentation.
"""
import functools
import typing
from doctest import ELLIPSIS
from fnmatch import fnmatch
from unittest.mock import MagicMock

import pytest
from sybil import Sybil
from sybil.integration.pytest import SybilFile
from sybil.parsers.codeblock import CodeBlockParser
from sybil.parsers.doctest import DocTestParser

from nunavut.jinja.jinja2 import DictLoader, Environment
from nunavut.lang import LanguageContext
from nunavut.templates import (ContextFilterAttributeName,
                               EnvironmentFilterAttributeName,
                               LanguageFilterAttributeName)


@pytest.fixture
def jinja_filter_tester(request):  # type: ignore
    """
    Use to create fluent but testable documentation for Jinja filters.

    Example::

        .. invisible-code-block: python

            from nunavut.templates import templateEnvironmentFilter

            @templateEnvironmentFilter
            def filter_dummy(env, input):
                return input

        .. code-block:: python

            # Given
            I = 'foo'

            # and
            template = '{{ I | dummy }}'

            # then
            rendered = I


        .. invisible-code-block: python

            jinja_filter_tester(filter_dummy, template, rendered, 'c', I=I)

    """
    def _make_filter_test_template(filter: typing.Callable,
                                   body: str,
                                   expected: str,
                                   target_language: typing.Union[typing.Optional[str], LanguageContext],
                                   **globals: typing.Optional[typing.Dict[str, typing.Any]]) -> str:
        e = Environment(loader=DictLoader({'test': body}))
        filter_name = filter.__name__[7:]
        if hasattr(filter, EnvironmentFilterAttributeName) and getattr(filter, EnvironmentFilterAttributeName):
            e.filters[filter_name] = functools.partial(filter, e)
        else:
            e.filters[filter_name] = filter

        if hasattr(filter, ContextFilterAttributeName) and getattr(filter, ContextFilterAttributeName):
            context = MagicMock()
            e.filters[filter_name] = functools.partial(filter, context)
        else:
            e.filters[filter_name] = filter

        if globals is not None:
            e.globals.update(globals)

        if isinstance(target_language, LanguageContext):
            lctx = target_language
        else:
            lctx = LanguageContext(target_language)

        if hasattr(filter, LanguageFilterAttributeName):
            language_name = getattr(filter, LanguageFilterAttributeName)
            e.filters[filter_name] = functools.partial(filter, lctx.get_language(language_name))
        else:
            e.filters[filter_name] = filter

        rendered = str(e.get_template('test').render())
        if expected != rendered:
            msg = 'Unexpected template output\n\texpected : {}\n\twas      : {}'.format(expected, rendered)
            raise AssertionError(msg)
        return rendered

    return _make_filter_test_template


def _pytest_integration_that_actually_works() -> typing.Callable:
    """
    Sybil matching is pretty broken. We'll have to help it out here. The problem is that
    exclude patterns passed into the Sybil object are matched against file name stems such that
    files cannot be excluded by path.
    """

    _excludes = [
        '**/markupsafe/*',
        '**/jinja2/*',
    ]

    _sy = Sybil(
        parsers=[
            DocTestParser(optionflags=ELLIPSIS),
            CodeBlockParser(),
        ],
        fixtures=['jinja_filter_tester']
    )

    def pytest_collect_file(parent: typing.Any, path: typing.Any) -> typing.Optional[SybilFile]:
        if fnmatch(str(path), '**/nunavut/**/*.py') and not any(fnmatch(str(path), pattern) for pattern in _excludes):
            return SybilFile(path, parent, _sy)
        else:
            return None

    return pytest_collect_file


pytest_collect_file = _pytest_integration_that_actually_works()
