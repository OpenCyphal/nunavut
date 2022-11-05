#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# This software is distributed under the terms of the MIT License.
#
"""
Fixtures for our tests.
"""

import logging
import os
import pathlib
import re
import subprocess
import tempfile
import textwrap
import typing
import urllib
from doctest import ELLIPSIS

import pydsdl
import pytest
from sybil import Sybil

try:
    from sybil.parsers.codeblock import PythonCodeBlockParser
except ImportError:
    from sybil.parsers.codeblock import CodeBlockParser as PythonCodeBlockParser

from sybil.parsers.doctest import DocTestParser

from nunavut import Namespace


# +-------------------------------------------------------------------------------------------------------------------+
# | PYTEST HOOKS
# +-------------------------------------------------------------------------------------------------------------------+


def pytest_configure(config: typing.Any) -> None:
    """
    See https://docs.pytest.org/en/6.2.x/reference.html#initialization-hooks
    """
    # pydsdl._dsdl_definition is reeeeeeealy verbose at the INFO level and below. Turn this down to reduce
    # scroll-blindness.
    logging.getLogger("pydsdl._dsdl_definition").setLevel(logging.WARNING)
    # A lot of DEBUG noise in the other loggers so we'll tune this down to INFO and higher.
    logging.getLogger("pydsdl._namespace").setLevel(logging.INFO)
    logging.getLogger("pydsdl._data_type_builder").setLevel(logging.INFO)


def pytest_addoption(parser):  # type: ignore
    """
    See https://docs.pytest.org/en/6.2.x/reference.html#initialization-hooks
    """
    parser.addoption(
        "--keep-generated",
        action="store_true",
        help=textwrap.dedent(
            """
        If set then the temporary directory used to generate files for each test will be left after
        the test has completed. Normally this directory is temporary and therefore cleaned up automatically.

        :: WARNING ::
        This will leave orphaned files on disk. They won't be big but there will be a lot of them.

        :: WARNING ::
        Do not run tests in parallel when using this option.
    """
        ),
    )


# +-------------------------------------------------------------------------------------------------------------------+
# | TEST FIXTURES
# +-------------------------------------------------------------------------------------------------------------------+


@pytest.fixture
def run_nnvg(request):  # type: ignore
    """
    Test helper for invoking the nnvg commandline script as part of a unit test.
    """

    def _run_nnvg(
        gen_paths: typing.Any,
        args: typing.List[str],
        check_result: bool = True,
        env: typing.Optional[typing.Dict[str, str]] = None,
        raise_called_process_error: bool = False,
    ) -> subprocess.CompletedProcess:
        """
        Helper to invoke nnvg for unit testing within the proper python coverage wrapper.
        """
        coverage_args = ["coverage", "run", "--parallel-mode", "-m", "nunavut"]
        this_env = os.environ.copy()
        if env is not None:
            this_env.update(env)
        try:
            return subprocess.run(
                coverage_args + args, check=check_result, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=this_env
            )
        except subprocess.CalledProcessError as e:
            if raise_called_process_error:
                raise e
            else:
                raise AssertionError(e.stderr.decode("utf-8"))

    return _run_nnvg


class GenTestPaths:
    """Helper to generate common paths used in our unit tests."""

    def __init__(self, test_file: str, keep_temporaries: bool, node_name: str):
        test_file_path = pathlib.Path(test_file)
        self.test_name = "{}_{}".format(test_file_path.parent.stem, node_name)
        self.test_dir = test_file_path.parent
        search_dir = self.test_dir.resolve()
        while search_dir.is_dir() and not (search_dir / pathlib.Path("src")).is_dir():
            search_dir = search_dir.parent
        self.root_dir = search_dir
        self.templates_dir = self.test_dir / pathlib.Path("templates")
        self.dsdl_dir = self.test_dir / pathlib.Path("dsdl")

        self._keep_temp = keep_temporaries
        self._out_dir = None  # type: typing.Optional[pathlib.Path]
        self._build_dir = None  # type: typing.Optional[pathlib.Path]
        self._dsdl_dir = None  # type: typing.Optional[pathlib.Path]
        self._temp_dirs = []  # type: typing.List[tempfile.TemporaryDirectory]
        print('Paths for test "{}" under dir {}'.format(self.test_name, self.test_dir))
        print("(root directory: {})".format(self.root_dir))

    def test_path_finalizer(self) -> None:
        for temporary_dir in self._temp_dirs:
            temporary_dir.cleanup()
        self._temp_dirs.clear()

    def create_new_temp_dir(self, dir_key: str) -> pathlib.Path:
        if self._keep_temp:
            result = self._ensure_dir(self.build_dir / pathlib.Path(dir_key))
        else:
            temporary_dir = tempfile.TemporaryDirectory(dir=str(self.build_dir))
            result = pathlib.Path(temporary_dir.name)
            self._temp_dirs.append(temporary_dir)
        return result

    @property
    def out_dir(self) -> pathlib.Path:
        """
        The directory to place test output under for this test case.
        """
        if self._out_dir is None:
            self._out_dir = self.create_new_temp_dir(urllib.parse.quote_plus(self.test_name))
        return self._out_dir

    @property
    def build_dir(self) -> pathlib.Path:
        if self._build_dir is None:
            self._build_dir = self._ensure_dir(self.root_dir / pathlib.Path("build"))
        return self._build_dir

    @staticmethod
    def find_outfile_in_namespace(
        typename: str, namespace: Namespace, type_version: pydsdl.Version = None
    ) -> typing.Optional[str]:
        found_outfile = None  # type: typing.Optional[str]
        for dsdl_type, outfile in namespace.get_all_types():
            if dsdl_type.full_name == typename:
                if type_version is not None:
                    if isinstance(dsdl_type, pydsdl.CompositeType) and type_version == dsdl_type.version:
                        found_outfile = str(outfile)
                        break
                    # else ignore this since it's either a namespace or it's not the version
                    # of the type we're looking for.
                elif found_outfile is not None:
                    raise RuntimeError(
                        "Type {} had more than one version for this test but no type version argument"
                        " was provided.".format(typename)
                    )
                else:
                    found_outfile = str(outfile)

        return found_outfile

    @staticmethod
    def _ensure_dir(path_dir: pathlib.Path) -> pathlib.Path:
        try:
            path_dir.mkdir()
        except FileExistsError:
            pass
        if not path_dir.exists() or not path_dir.is_dir():
            raise RuntimeWarning('Test directory "{}" was not setup properly. Tests may fail.'.format(path_dir))
        return path_dir


@pytest.fixture(scope="function")
def gen_paths(request):  # type: ignore
    """
    Used by the "gentest" unittests in Nunavut to standardize output paths for generated code created as part of
    the tests. Use the --keep-generated argument to disable the auto-clean behaviour this fixture provides by default.
    """
    g = GenTestPaths(str(request.fspath), request.config.option.keep_generated, request.node.name)
    request.addfinalizer(g.test_path_finalizer)
    return g


class _UniqueNameEvaluator:
    def __init__(self) -> None:
        self._found_names = set()  # type: typing.Set[str]

    def __call__(self, expected_pattern: str, actual_value: str) -> None:
        assert re.match(expected_pattern, actual_value) is not None
        assert actual_value not in self._found_names
        self._found_names.add(actual_value)


@pytest.fixture(scope="function")
def unique_name_evaluator(request):  # type: ignore
    """
    Class that defined ``assert_is_expected_and_unique`` allowing assertion that a set of values
    in a single test adhere to a provided pattern and are unique values (compared to other values
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
    from nunavut.lang import LanguageContext, LanguageContextBuilder

    def _assert_language_config_value(
        target_language: typing.Union[str, LanguageContext],
        key: str,
        expected_value: typing.Any,
        message: typing.Optional[str],
    ) -> None:
        if isinstance(target_language, LanguageContext):
            lctx = target_language
        else:
            lctx = (
                LanguageContextBuilder(include_experimental_languages=True)
                .set_target_language(target_language)
                .create()
            )

        language = lctx.get_target_language()
        if language is None:
            raise AssertionError("Unable to determine target language from provided arguments.")
        if expected_value != language.get_config_value(key):
            raise AssertionError(message)

    return _assert_language_config_value


@pytest.fixture
def jinja_filter_tester(request):  # type: ignore
    """
    Use to create fluent but testable documentation for Jinja filters and tests

    Example:

        .. code-block: python

            from nunavut._templates import template_environment_filter

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

            from nunavut.lang import LanguageContextBuilder, Language
            lctx = (
                LanguageContextBuilder()
                    .set_target_language("c")
                    .set_target_language_configuration_override(Language.WKCV_ENABLE_STROPPING, False)
                    .create()
            )

            jinja_filter_tester(filter_dummy, template, rendered, lctx, I=I)
    """
    from nunavut.jinja.jinja2 import DictLoader
    from nunavut.lang import LanguageContext, LanguageContextBuilder

    def _make_filter_test_template(
        filter_or_list_of_filters: typing.Union[None, typing.Callable, typing.List[typing.Callable]],
        body: str,
        expected: str,
        target_language_or_language_context: typing.Union[str, LanguageContext],
        **globals: typing.Optional[typing.Dict[str, typing.Any]]
    ) -> str:
        from nunavut.jinja import CodeGenEnvironment

        if isinstance(target_language_or_language_context, LanguageContext):
            lctx = target_language_or_language_context
        else:
            lctx = (
                LanguageContextBuilder(include_experimental_languages=True)
                .set_target_language(target_language_or_language_context)
                .create()
            )

        if filter_or_list_of_filters is None:
            additional_filters = dict()  # type: typing.Optional[typing.Dict[str, typing.Callable]]
        elif isinstance(filter_or_list_of_filters, list):
            additional_filters = dict()
            for filter in filter_or_list_of_filters:
                additional_filters[filter.__name__] = filter
        else:
            additional_filters = {filter_or_list_of_filters.__name__: filter_or_list_of_filters}

        e = CodeGenEnvironment(
            lctx=lctx,
            loader=DictLoader({"test": body}),
            allow_filter_test_or_use_query_overwrite=True,
            additional_filters=additional_filters,
            additional_globals=globals,
        )
        e.update_nunavut_globals(
            *lctx.get_target_language().get_support_module(), is_dryrun=True, omit_serialization_support=True
        )

        rendered = str(e.get_template("test").render())
        if expected != rendered:
            msg = "Unexpected template output\n\texpected : {}\n\twas      : {}".format(
                expected.replace("\n", "\\n"), rendered.replace("\n", "\\n")
            )
            raise AssertionError(msg)
        return rendered

    return _make_filter_test_template


@pytest.fixture
def mock_environment(request):  # type: ignore
    """
    A MagicMock that can be used where a jinja environment is needed.
    """
    from unittest.mock import MagicMock

    mock_environment = MagicMock()
    support_mock = MagicMock()
    mock_environment.globals = {"nunavut": support_mock}
    support_mock.support = {"omit": True}

    return mock_environment


# +-------------------------------------------------------------------------------------------------------------------+
# | SYBIL
# +-------------------------------------------------------------------------------------------------------------------+


_sy = Sybil(
    parsers=[
        DocTestParser(optionflags=ELLIPSIS),
        PythonCodeBlockParser(),
    ],
    pattern="**/*",
    excludes=[
        "**/markupsafe/*",
        "**/jinja2/*",
        "**/static/*",
        "**/.*/*",
        "**/.*",
        "**/CONTRIBUTING.rst",
        "**/verification/*",
        "**/prof/*",
        "*.png",
    ],
    fixtures=[
        "jinja_filter_tester",
        "gen_paths",
        "assert_language_config_value",
    ],
)


pytest_collect_file = _sy.pytest()
