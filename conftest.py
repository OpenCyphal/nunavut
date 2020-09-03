#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# This software is distributed under the terms of the MIT License.
#
"""
Fixtures for our tests.
"""

import functools
import os
import pathlib
import re
import subprocess
import tempfile
import textwrap
import typing
from doctest import ELLIPSIS
from unittest.mock import MagicMock

import pytest
from sybil import Sybil
from sybil.integration.pytest import SybilFile
from sybil.parsers.codeblock import CodeBlockParser
from sybil.parsers.doctest import DocTestParser

from nunavut import Namespace
from nunavut.jinja.jinja2 import DictLoader
from nunavut.lang import LanguageContext
from nunavut.templates import (CONTEXT_FILTER_ATTRIBUTE_NAME,
                               ENVIRONMENT_FILTER_ATTRIBUTE_NAME,
                               LANGUAGE_FILTER_ATTRIBUTE_NAME)


@pytest.fixture
def run_nnvg(request):  # type: ignore
    def _run_nnvg(gen_paths: typing.Any,
                  args: typing.List[str],
                  check_result: bool = True,
                  env: typing.Optional[typing.Dict[str, str]] = None) -> subprocess.CompletedProcess:
        """
        Helper to invoke nnvg for unit testing within the proper python coverage wrapper.
        """
        coverage_args = ['coverage', 'run', '--parallel-mode', '-m', 'nunavut']
        this_env = os.environ.copy()
        if env is not None:
            this_env.update(env)
        return subprocess.run(coverage_args + args,
                              check=check_result,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              env=this_env)
    return _run_nnvg


class GenTestPaths:
    """Helper to generate common paths used in our unit tests."""

    def __init__(self, test_file: str, keep_temporaries: bool, node_name: str):
        test_file_path = pathlib.Path(test_file)
        self.test_name = '{}_{}'.format(test_file_path.parent.stem, node_name)
        self.test_dir = test_file_path.parent
        search_dir = self.test_dir.resolve()
        while search_dir.is_dir() and not (search_dir / pathlib.Path('src')).is_dir():
            search_dir = search_dir.parent
        self.root_dir = search_dir
        self.templates_dir = self.test_dir / pathlib.Path('templates')
        self.dsdl_dir = self.test_dir / pathlib.Path('dsdl')

        self._keep_temp = keep_temporaries
        self._out_dir = None  # type: typing.Optional[typing.Any]
        self._build_dir = None  # type: typing.Optional[pathlib.Path]
        self._dsdl_dir = None  # type: typing.Optional[pathlib.Path]
        print('Paths for test "{}" under dir {}'.format(self.test_name, self.test_dir))
        print('(root directory: {})'.format(self.root_dir))

    @property
    def out_dir(self) -> pathlib.Path:
        """
        The directory to place test output under for this test case.
        """
        if self._out_dir is None:
            if self._keep_temp:
                self._out_dir = lambda: None
                test_output_dir = self._ensure_dir(self.build_dir / pathlib.Path(self.test_name))
                setattr(self._out_dir, 'name', str(test_output_dir))
            else:
                self._out_dir = tempfile.TemporaryDirectory(dir=str(self.build_dir))
        return pathlib.Path(self._out_dir.name)

    @property
    def build_dir(self) -> pathlib.Path:
        if self._build_dir is None:
            self._build_dir = self._ensure_dir(self.root_dir / pathlib.Path('build'))
        return self._build_dir

    @staticmethod
    def find_outfile_in_namespace(typename: str, namespace: Namespace) -> typing.Optional[str]:
        for dsdl_type, outfile in namespace.get_all_types():
            if dsdl_type.full_name == typename:
                return str(outfile)
        return None

    @staticmethod
    def _ensure_dir(path_dir: pathlib.Path) -> pathlib.Path:
        try:
            path_dir.mkdir()
        except FileExistsError:
            pass
        if not path_dir.exists() or not path_dir.is_dir():
            raise RuntimeWarning('Test directory "{}" was not setup properly. Tests may fail.'.format(path_dir))
        return path_dir


@pytest.fixture(scope='function')
def gen_paths(request):  # type: ignore
    return GenTestPaths(str(request.fspath), request.config.option.keep_generated, request.node.name)


def pytest_addoption(parser):  # type: ignore
    parser.addoption("--keep-generated", action="store_true", help=textwrap.dedent('''
        If set then the temporary directory used to generate files for each test will be left after
        the test has completed. Normally this directory is temporary and therefore cleaned up automatically.

        :: WARNING ::
        This will leave orphaned files on disk. They won't be big but there will be a lot of them.

        :: WARNING ::
        Do not run tests in parallel when using this option.
    '''))


class _UniqueNameEvaluator:

    def __init__(self) -> None:
        self._found_names = set()  # type: typing.Set[str]

    def __call__(self, expected_pattern: str, actual_value: str) -> None:
        assert re.match(expected_pattern, actual_value) is not None
        assert actual_value not in self._found_names
        self._found_names.add(actual_value)


@pytest.fixture(scope='function')
def unique_name_evaluator(request):  # type: ignore
    """
    Class that defined ``assert_is_expected_and_unique`` allowing assertion that a set of values
    in a single test adhere to a provided pattern and are unique values (comparted to other values
    provided to this method).

    .. code-block:: python

        def test_is_unique(unique_name_evaluator) -> None:
            value0 = '_foo0_'
            value1 = '_foo1_'
            unique_name_evaluator(r'_foo\\d_', value0)
            unique_name_evaluator(r'_foo\\d_', value1)

            # This next line should fail because value 0 was already evaluated so it
            # is not unique
            unique_name_evaluator(r'_foo\\d_', value0)

    """
    return _UniqueNameEvaluator()


@pytest.fixture
def assert_language_config_value(request):  # type: ignore
    """
    Assert that a given configuration value is set for the target language.
    """
    def _assert_language_config_value(target_language: typing.Union[typing.Optional[str], LanguageContext],
                                      key: str,
                                      expected_value: typing.Any,
                                      message: typing.Optional[str]) -> None:
        if isinstance(target_language, LanguageContext):
            lctx = target_language
        else:
            lctx = LanguageContext(target_language)

        language = lctx.get_target_language()
        if language is None:
            raise AssertionError('Unable to determine target language from provided arguments.')
        if expected_value != language.get_config_value(key):
            raise AssertionError(message)
    return _assert_language_config_value


@pytest.fixture
def configurable_language_context_factory(request):  # type: ignore
    """
    Use to create a LanguageContext that the test can write configuration overrides for.

    Example:

        .. code-block:: python

            def test_my_test(configurable_language_context_factory):
                lctx = configurable_language_context_factory({'nunavut.lang.c': {'foo': 'bar'}},
                                                             'c')
                assert lctx.get_target_language().get_config_value('foo') == 'bar'

        .. invisible-code-block: python

            test_my_test(configurable_language_context_factory)

    """
    def _make_configurable_language_context(config_overrides: typing.Mapping[str, typing.Mapping[str, typing.Any]],
                                            target_language: typing.Optional[str] = None,
                                            extension: typing.Optional[str] = None,
                                            namespace_output_stem: typing.Optional[str] = None,
                                            omit_serialization_support_for_target: bool = True) \
            -> LanguageContext:
        from tempfile import NamedTemporaryFile
        config_bytes = []  # type: typing.List[bytearray]

        def _config_gen(indent: int,
                        key: str,
                        value: typing.Union[typing.Dict, typing.Any],
                        out_config_bytes: typing.List[bytearray]) \
                -> None:
            line = bytearray('{}{} = '.format('    ' * indent, key), 'utf8')
            if isinstance(value, dict):
                line += bytearray('\n', 'utf8')
                out_config_bytes.append(line)
                for subkey, subvalue in value.items():
                    _config_gen(indent + 1, subkey, subvalue, out_config_bytes)
            else:
                line += bytearray('{}\n'.format(str(value)), 'utf8')
                out_config_bytes.append(line)

        for section, config in config_overrides.items():
            config_bytes.append(bytearray('[{}]\n'.format(section), 'utf8'))
            for key, value in config.items():
                _config_gen(0, key, value, config_bytes)

        with NamedTemporaryFile() as config_override_file:
            config_override_file.writelines(config_bytes)
            config_override_file.flush()
            return LanguageContext(target_language, extension,
                                   additional_config_files=[pathlib.Path(config_override_file.name)])
    return _make_configurable_language_context


@pytest.fixture
def jinja_filter_tester(request):  # type: ignore
    """
    Use to create fluent but testable documentation for Jinja filters.

    Example:

        .. code-block: python

            from nunavut.templates import template_environment_filter

            @template_environment_filter
            def filter_dummy(env, input):
                return input


            # Given
            I = 'foo'

            # and
            template = '{{ I | dummy }}'

            # then
            rendered = I

            jinja_filter_tester(filter_dummy, template, rendered, 'c', I=I)

    You can also control the language context:

        .. code-block: python
            lctx = configurable_language_context_factory({'nunavut.lang.c': {'enable_stropping': False}}, 'c')

            jinja_filter_tester(filter_dummy, template, rendered, lctx, I=I)
    """
    def _make_filter_test_template(filter_or_list: typing.Union[typing.Callable, typing.List[typing.Callable]],
                                   body: str,
                                   expected: str,
                                   target_language_or_language_context: typing.Union[typing.Optional[str], LanguageContext],
                                   **globals: typing.Optional[typing.Dict[str, typing.Any]]) -> str:
        from nunavut.jinja import CodeGenEnvironment
        e = CodeGenEnvironment(loader=DictLoader({'test': body}))

        if globals is not None:
            e.globals.update(globals)

        if isinstance(target_language_or_language_context, LanguageContext):
            lctx = target_language_or_language_context
        else:
            lctx = LanguageContext(target_language_or_language_context)

        filters = (filter_or_list if isinstance(filter_or_list, list) else [filter_or_list])
        for filter in filters:
            filter_name = filter.__name__[7:]
            if hasattr(filter, ENVIRONMENT_FILTER_ATTRIBUTE_NAME) and \
                    getattr(filter, ENVIRONMENT_FILTER_ATTRIBUTE_NAME):
                e.filters[filter_name] = functools.partial(filter, e)
            else:
                e.filters[filter_name] = filter

            if hasattr(filter, CONTEXT_FILTER_ATTRIBUTE_NAME) and getattr(filter, CONTEXT_FILTER_ATTRIBUTE_NAME):
                context = MagicMock()
                e.filters[filter_name] = functools.partial(filter, context)
            else:
                e.filters[filter_name] = filter

            if hasattr(filter, LANGUAGE_FILTER_ATTRIBUTE_NAME):
                language_name = getattr(filter, LANGUAGE_FILTER_ATTRIBUTE_NAME)
                e.filters[filter_name] = functools.partial(filter, lctx.get_language(language_name))
            else:
                e.filters[filter_name] = filter

        target_language_resolved = lctx.get_target_language()
        if target_language_resolved is not None:
            e.globals.update(target_language_resolved.get_globals())

        rendered = str(e.get_template('test').render())
        if expected != rendered:
            msg = 'Unexpected template output\n\texpected : {}\n\twas      : {}'.format(
                expected.replace('\n', '\\n'), rendered.replace('\n', '\\n'))
            raise AssertionError(msg)
        return rendered

    return _make_filter_test_template


_sy = Sybil(
    parsers=[
        DocTestParser(optionflags=ELLIPSIS),
        CodeBlockParser(),
    ],
    pattern='**/*',
    excludes=[
        '**/markupsafe/*',
        '**/jinja2/*',
        '**/static/*',
        '**/.*/*',
        '**/.*',
        '**/CONTRIBUTING.rst'
    ],
    fixtures=['jinja_filter_tester',
              'gen_paths',
              'assert_language_config_value',
              'configurable_language_context_factory']
)


pytest_collect_file = _sy.pytest()
