#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
# cSpell: words loopcontrols
#
"""
Jinja environment for Nunavut code generation.
"""

import datetime
import inspect
import logging
import platform
import sys
import types
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    ItemsView,
    KeysView,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
    ValuesView,
    cast,
)

from nunavut._templates import LanguageEnvironment
from nunavut.lang import Language, LanguageClassLoader, LanguageContext

from .extensions import JinjaAssert, UseQuery
from .jinja2 import BaseLoader, Environment, StrictUndefined, select_autoescape
from .jinja2.ext import Extension
from .jinja2.ext import do as jinja_do
from .jinja2.ext import loopcontrols
from .jinja2.filters import FILTERS as JINJA2_FILTERS

logger = logging.getLogger(__name__)

# +---------------------------------------------------------------------------+
# | JINJA : LanguageTemplateNamespace
# +---------------------------------------------------------------------------+


class LanguageTemplateNamespace:
    """
    Generic namespace object used to create reserved namespaces in the global environment.

    .. invisible-code-block: python

        from nunavut.jinja.environment import LanguageTemplateNamespace

    .. code-block:: python

        ns = LanguageTemplateNamespace()

        # any property can be set at any time.
        ns.foo = 'foo'
        assert ns.foo == 'foo'

        # repr of the ns enables cloning using exec
        exec('ns2={}'.format(repr(ns)))
        assert ns2.foo == 'foo'

        # clones will be equal
        assert ns2 == ns

        # but not the same object
        assert ns2 is not ns

    In addition to the namespace behavior this object exposed some dictionary-like methods:

    .. code-block:: python

        ns = LanguageTemplateNamespace()
        ns.update({'foo':'bar'})

        assert ns.foo == 'bar'

    .. invisible-code-block: python

        ns = LanguageTemplateNamespace(one='one', two='two')
        assert 'one' == ns.one
        assert 'two' == ns.two

    """

    def __init__(self, **kwargs: Any):
        for name, value in kwargs.items():
            setattr(self, name, value)

    def __repr__(self) -> str:
        type_name = type(self).__name__
        arg_strings = []
        star_args = {}
        for name, value in self._get_kwargs():
            if name.isidentifier():
                arg_strings.append(f"{name}={repr(value)}")
            else:
                star_args[name] = value
        if star_args:
            arg_strings.append(f"**{repr(star_args)}")
        return f"{type_name}({','.join(arg_strings)})"

    def _get_kwargs(self) -> List[Any]:
        return list(self.__dict__.items())

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LanguageTemplateNamespace):
            return NotImplemented
        return vars(self) == vars(other)

    def __contains__(self, key: str) -> bool:
        return key in self.__dict__

    def update(self, update_from: Mapping[str, Any]) -> None:
        """
        update the namespace with the given values.
        """
        for key, value in update_from.items():
            setattr(self, key, value)

    def items(self) -> ItemsView[str, Any]:
        """
        The items in the namespace.
        """
        return self.__dict__.items()

    def keys(self) -> KeysView[Any]:
        """
        The values in the namespace.
        """
        return self.__dict__.keys()

    def values(self) -> ValuesView[Any]:
        """
        The values in the namespace.
        """
        return self.__dict__.values()


# +---------------------------------------------------------------------------+
# | JINJA : CodeGenEnvironment
# +---------------------------------------------------------------------------+
class CodeGenEnvironmentBuilder:
    """
    Builder class for creating a CodeGenEnvironment object for code generation.

    :param BaseLoader loader: The loader used to load templates.
    :param LanguageContext lctx: The language context used for code generation.
    """

    DEFAULT_JINJA_EXTENSIONS = [jinja_do, loopcontrols, JinjaAssert, UseQuery]

    def __init__(self, loader: BaseLoader) -> None:
        self._loader = loader
        self._trim_blocks = False
        self._lstrip_blocks = False
        self._additional_filters: Optional[Dict[str, Callable]] = None
        self._additional_tests: Optional[Dict[str, Callable]] = None
        self._additional_globals: Optional[Dict[str, Any]] = None
        self._extensions = self.DEFAULT_JINJA_EXTENSIONS[:]
        self._allow_filter_test_or_use_query_overwrite = False
        self._embed_auditing_info = False

    @property
    def loader(self) -> BaseLoader:
        """
        The loader.

        :return: The loader.
        :rtype: BaseLoader
        """
        return self._loader

    def set_trim_blocks(self, trim_blocks: bool) -> "CodeGenEnvironmentBuilder":
        """
        Set the trim blocks flag.

        :param bool trim_blocks: The trim blocks flag.
        :return: The CodeGenEnvironmentBuilder object.
        :rtype: CodeGenEnvironmentBuilder
        """
        self._trim_blocks = trim_blocks
        return self

    def set_lstrip_blocks(self, lstrip_blocks: bool) -> "CodeGenEnvironmentBuilder":
        """
        Set the lstrip blocks flag.

        :param bool lstrip_blocks: The lstrip blocks flag.
        :return: The CodeGenEnvironmentBuilder object.
        :rtype: CodeGenEnvironmentBuilder
        """
        self._lstrip_blocks = lstrip_blocks
        return self

    def add_filters(self, **additional_filters: Callable) -> "CodeGenEnvironmentBuilder":
        """
        Add filters to the created environment.

        :param Dict[str, Callable] additional_filters: The additional filters.
        :return: The CodeGenEnvironmentBuilder object.
        :rtype: CodeGenEnvironmentBuilder
        """
        if self._additional_filters is None:
            self._additional_filters = additional_filters
        else:
            self._additional_filters.update(additional_filters)
        return self

    def add_tests(self, **additional_tests: Callable) -> "CodeGenEnvironmentBuilder":
        """
        Add tests to the created environment.

        :param Dict[str, Callable] additional_tests: The additional tests.
        :return: The CodeGenEnvironmentBuilder object.
        :rtype: CodeGenEnvironmentBuilder
        """
        if self._additional_tests is None:
            self._additional_tests = additional_tests
        else:
            self._additional_tests.update(additional_tests)
        return self

    def add_globals(self, **additional_globals: Any) -> "CodeGenEnvironmentBuilder":
        """
        Add globals so the created environment.

        :param Dict[str, Any] additional_globals: The additional globals.
        :return: The CodeGenEnvironmentBuilder object.
        :rtype: CodeGenEnvironmentBuilder
        """
        if self._additional_globals is None:
            self._additional_globals = additional_globals
        else:
            self._additional_globals.update(additional_globals)
        return self

    def set_extensions(self, *extensions: Extension) -> "CodeGenEnvironmentBuilder":
        """
        Set the extensions.

        :param List[Extension] extensions: The extensions.
        :return: The CodeGenEnvironmentBuilder object.
        :rtype: CodeGenEnvironmentBuilder
        """
        self._extensions = list(extensions)
        return self

    def set_allow_filter_test_or_use_query_overwrite(
        self, allow_filter_test_or_use_query_overwrite: bool
    ) -> "CodeGenEnvironmentBuilder":
        """
        Allow overwriting of built-in filters, tests, or use queries.

        :param bool allow_filter_test_or_use_query_overwrite: Allow overwrite of built-ins.
        :return: The CodeGenEnvironmentBuilder object.
        :rtype: CodeGenEnvironmentBuilder
        """
        self._allow_filter_test_or_use_query_overwrite = allow_filter_test_or_use_query_overwrite
        return self

    def set_embed_auditing_info(self, embed_auditing_info: bool) -> "CodeGenEnvironmentBuilder":
        """
        Set whether to embed auditing information in generated files.

        :param bool embed_auditing_info: Whether to embed auditing information.
        :return: The CodeGenEnvironmentBuilder object.
        :rtype: CodeGenEnvironmentBuilder
        """
        self._embed_auditing_info = embed_auditing_info
        return self

    def create(self, lctx: LanguageContext) -> "CodeGenEnvironment":
        """
        Create a CodeGenEnvironment object.

        :return: A CodeGenEnvironment object.
        :rtype: CodeGenEnvironment
        """
        env = CodeGenEnvironment(
            self.loader,
            trim_blocks=self._trim_blocks,
            lstrip_blocks=self._lstrip_blocks,
            additional_filters=self._additional_filters,
            additional_tests=self._additional_tests,
            additional_globals=self._additional_globals,
            extensions=self._extensions,
            allow_filter_test_or_use_query_overwrite=self._allow_filter_test_or_use_query_overwrite,
            embed_auditing_info=self._embed_auditing_info,
        )
        env.set_language_context(lctx)
        return env


# +---------------------------------------------------------------------------+


class CodeGenEnvironment(Environment):
    """
    Jinja Environment optimized for compile-time generation of source code
    (i.e. as opposed to dynamically generating webpages).

    Do not instanceate directly. Use the :class:`CodeGenEnvironmentBuilder` to create an instance.

    .. invisible-code-block: python

        from nunavut.lang import LanguageContext, LanguageContextBuilder
        from nunavut.lang._language import Language
        from nunavut.jinja import CodeGenEnvironmentBuilder
        from nunavut.jinja.jinja2 import DictLoader

        lctx = LanguageContextBuilder().create()

    .. code-block:: python

        template = 'Hello World'

        e = CodeGenEnvironmentBuilder(DictLoader({'test': template})).create(lctx)
        assert 'Hello World' ==  e.get_template('test').render()

    .. warning::
        The :attr:`RESERVED_GLOBAL_NAMESPACES` and :attr:`RESERVED_GLOBAL_NAMES` collections
        contain names in the global namespace reserved by this environment. Attempting to override one
        of these reserved names will cause the constructor to raise an error.

    .. code-block:: python

        try:
            (
                CodeGenEnvironmentBuilder(DictLoader({'test': template}))
                .add_globals(ln='bad_ln')
                .create(lctx)
            )
            assert False
        except RuntimeError:
            pass

    Other safe-guards include checks that Jinja built-ins aren't accidentally overridden...

    .. code-block:: python

        try:
            (
                CodeGenEnvironmentBuilder(DictLoader({'test': template}))
                .add_filters(indent=lambda x: x)
                .create(lctx)
            )
            assert False
        except RuntimeError:
            pass

        # You can allow overwrite of built-ins using the ``allow_filter_test_or_use_query_overwrite``
        # argument.
        e = (
                CodeGenEnvironmentBuilder(DictLoader({'test': template}))
                .add_filters(indent=lambda x: x)
                .set_allow_filter_test_or_use_query_overwrite(True)
                .create(lctx)
            )
        assert 'foo' == e.filters['indent']('foo')

    ...or that user-defined filters or redefined.

    .. code-block:: python

        class MyFilters:

            @staticmethod
            def filter_misnamed(name: str) -> str:
                return name

        e = (
                CodeGenEnvironmentBuilder(DictLoader({'test': template}))
                .add_filters(filter_misnamed=lambda x: x)
                .create(lctx)
            )

        try:
            e.add_conventional_methods_to_environment(MyFilters())
            assert False
        except RuntimeError:
            pass

    .. note:: Maintainer's Note
        This class should remain DSDL agnostic. It is, theoretically, applicable using Jinja with any compiler front-end
        input although, in practice, it will only ever be used with pydsdl AST.
        Pydsdl-specific logic should live in the CodeGenerator (:class:`nunavut.jinja.DSDLCodeGenerator`).

    """

    RESERVED_GLOBAL_NAMESPACES = {"ln", "options", "uses_queries", "nunavut"}

    RESERVED_GLOBAL_NAMES = {"now_utc"}

    def __init__(
        self,
        loader: BaseLoader,
        trim_blocks: bool,
        lstrip_blocks: bool,
        additional_filters: Optional[Dict[str, Callable]],
        additional_tests: Optional[Dict[str, Callable]],
        additional_globals: Optional[Dict[str, Any]],
        extensions: Optional[List[Extension]],
        allow_filter_test_or_use_query_overwrite: bool,
        embed_auditing_info: bool = False,
    ):  # pylint: disable=too-many-arguments
        super().__init__(
            loader=loader,  # nosec
            extensions=extensions,
            autoescape=select_autoescape(
                enabled_extensions=("htm", "html", "xml", "json"), default_for_string=False, default=False
            ),
            undefined=StrictUndefined,
            keep_trailing_newline=True,
            lstrip_blocks=lstrip_blocks,
            trim_blocks=trim_blocks,
            auto_reload=False,
            cache_size=400,
        )
        if additional_globals is not None:
            for global_name, global_value in additional_globals.items():
                if global_name in self.RESERVED_GLOBAL_NAMESPACES or global_name in self.RESERVED_GLOBAL_NAMES:
                    raise RuntimeError(f'Additional global "{global_name}" uses a reserved global name')
                self.globals[global_name] = global_value

        self._allow_replacements = allow_filter_test_or_use_query_overwrite
        self._embed_auditing_info = embed_auditing_info

        for global_namespace in self.RESERVED_GLOBAL_NAMESPACES:
            self.globals[global_namespace] = LanguageTemplateNamespace()

        self.globals["now_utc"] = datetime.datetime(datetime.MINYEAR, 1, 1)

        self._additional_filters = additional_filters
        self._additional_tests = additional_tests
        self._target_language: Optional[Language] = None

    def set_language_context(self, lctx: LanguageContext) -> None:
        """
        Set the language context and update the environment with the supported languages.
        This also takes the target language from the context and updates the environment with the target language's
        globals, options, filters, and tests.
        """
        self._target_language = lctx.get_target_language()

        self._update_language_support(lctx)

        supported_languages = lctx.get_supported_languages().values()  # type: Optional[ValuesView[Language]]

        nunavut_namespace = self.nunavut_global
        setattr(nunavut_namespace, "embed_auditing_info", self._embed_auditing_info)
        setattr(nunavut_namespace, "platform_version", self._create_platform_version(self._embed_auditing_info))

        if self._target_language is None:
            omit_serialization = False
            support_version = (0, 0, 0)
            support_namespace = []
            target_language_name = "(no target language)"
            experimental = False
        else:
            omit_serialization = self._target_language.get_config_value_as_bool("omit_serialization_support", False)
            support_version = self._target_language.get_support_module()[1]
            support_namespace = self._target_language.support_namespace
            target_language_name = self._target_language.name
            experimental = not self._target_language.stable_support

        setattr(
            nunavut_namespace,
            "support",
            {
                "omit": omit_serialization,  # deprecated. Use "options.omit_serialization_support".
                "namespace": ".".join(support_namespace),
                "version": (support_version[0], support_version[1], support_version[2]),
            },
        )

        setattr(
            nunavut_namespace,
            "target_language",
            {"name": target_language_name, "experimental": experimental},
        )

        if "version" not in nunavut_namespace:
            # pylint: disable=import-outside-toplevel
            from nunavut import __version__ as nunavut_version

            setattr(nunavut_namespace, "version", nunavut_version)

        self.add_conventional_methods_to_environment(self)

        if self._additional_filters is not None:
            self._add_each_to_environment(
                self._additional_filters.items(), self.filters, supported_languages=supported_languages
            )
        if self._additional_tests is not None:
            self._add_each_to_environment(
                self._additional_tests.items(), self.tests, supported_languages=supported_languages
            )

    def add_conventional_methods_to_environment(self, obj: Any) -> None:
        """
        Adds methods using specific naming conventions to the Jinja environment. For example, methods named `filter_*`
        are added to the Jinja environment as filters.

        This method iterates over the methods of the given object and adds them to the Jinja environment.
        Only methods that are supported by the specified languages are added.

        :param Any obj: The object to add the methods from.

        """
        for name, method in inspect.getmembers(obj, inspect.isroutine):
            try:
                self._add_conventional_method_to_environment(method, name, supported_languages=self.supported_languages)
            except TypeError:
                pass

    @property
    def supported_languages(self) -> ValuesView[Language]:
        """
        The supported languages in the environment.

        :return: A view of the supported languages.
        :rtype: ValuesView[Language]
        """
        ln_globals = self.globals["ln"]  # type: LanguageTemplateNamespace
        return ln_globals.values()

    @property
    def nunavut_global(self) -> LanguageTemplateNamespace:
        """
        The `nunavut` global namespace.

        :return: The `nunavut` global namespace.
        :rtype: LanguageTemplateNamespace
        """
        return cast(LanguageTemplateNamespace, self.globals["nunavut"])

    @property
    def target_language_uses_queries(self) -> LanguageTemplateNamespace:
        """
        All `uses_queries` for the target language.

        :return: The uses queries for the target language.
        :rtype: LanguageTemplateNamespace
        """
        return cast(LanguageTemplateNamespace, self.globals["uses_queries"])

    @property
    def language_options(self) -> LanguageTemplateNamespace:
        """
        The language options.

        :return: The language options.
        :rtype: LanguageTemplateNamespace
        """
        return cast(LanguageTemplateNamespace, self.globals["options"])

    @property
    def language_support(self) -> LanguageTemplateNamespace:
        """
        The language support.

        :return: The language support.
        :rtype: LanguageTemplateNamespace
        """
        return cast(LanguageTemplateNamespace, self.globals["ln"])

    @property
    def target_language(self) -> Language:
        """
        The target language.

        :return: The target language.
        :rtype: Language
        """
        if self._target_language is None:
            raise RuntimeError("No target language has been set.")
        return self._target_language

    @property
    def now_utc(self) -> datetime.datetime:
        """
        Get or set the current UTC time.

        :return: The current UTC time.
        :rtype: datetime.datetime
        """
        return cast(datetime.datetime, self.globals["now_utc"])

    @now_utc.setter
    def now_utc(self, utc_time: datetime.datetime) -> None:
        self.globals["now_utc"] = utc_time

    @property
    def embed_auditing_info(self) -> bool:
        """
        Whether to embed auditing information in generated files.

        :return: Whether to embed auditing information.
        :rtype: bool
        """
        return self._embed_auditing_info

    def add_test(self, test_name: str, test_callable: Callable) -> None:
        """
        Add a test to the environment.

        :param str test_name: The name of the test.
        :param Callable test_callable: The test.
        :return: None
        """
        self._add_to_environment(test_name, test_callable, self.tests)

    # +----------------------------------------------------------------------------------------------------------------+
    # | Private
    # +----------------------------------------------------------------------------------------------------------------+
    def _resolve_collection(
        self,
        conventional_method_prefix: Optional[str],
        method_name: str,
        collection_maybe: Optional[Union[LanguageTemplateNamespace, Dict[str, Any]]],
    ) -> Union[LanguageTemplateNamespace, Dict[str, Any]]:
        """
        Resolve the collection to add the item to. If collection_maybe is not None then it is returned otherwise the
        collection is resolved based on the method name.
        """
        if collection_maybe is not None:
            return collection_maybe

        if LanguageEnvironment.is_test_name(conventional_method_prefix):
            return cast(Dict[str, Any], self.tests)
        if LanguageEnvironment.is_filter_name(conventional_method_prefix):
            return cast(Dict[str, Any], self.filters)
        if LanguageEnvironment.is_uses_query_name(conventional_method_prefix):
            uses_queries = self.globals["uses_queries"]
            return cast(LanguageTemplateNamespace, uses_queries)
        raise TypeError(
            f"Tried to add an item {method_name} to the template environment but we don't know what the item is."
        )

    def _add_to_environment(
        self,
        item_name: str,
        item: Any,
        collection: Union[LanguageTemplateNamespace, Dict[str, Any]],
    ) -> None:
        if item_name in collection:
            if not self._allow_replacements:
                raise RuntimeError(f"{item_name} was already defined.")
            if item_name in JINJA2_FILTERS:
                logger.info("Replacing Jinja built-in %s", item_name)
            else:
                logger.info('Replacing "%s" which was already defined for this environment.', item_name)
        else:
            logger.debug("Adding %s to environment", item_name)
        if isinstance(collection, LanguageTemplateNamespace):
            setattr(collection, item_name, item)
        else:
            collection[item_name] = item

    def _add_conventional_method_to_environment(
        self,
        method: Callable[..., bool],
        method_name: str,
        collection_maybe: Optional[Union[LanguageTemplateNamespace, Dict[str, Any]]] = None,
        supported_languages: Optional[ValuesView[Language]] = None,
        method_language: Optional[Language] = None,
        is_target: bool = False,
    ) -> None:
        """
        Add a method using specific naming conventions to the Jinja environment. For example, methods named `filter_*`
        are added to the Jinja environment as filters.

        :param Callable[..., bool] method: The named method.
        :param str method_name: The name of the callable to use in a template.
        :param Optional[Union[LanguageTemplateNamespace, Dict[str, Any]]] collection_maybe:
            The collection to add the method to. If None then the collection is resolved based on the method name.
        :param Optional[ValuesView[Language]] supported_languages: The supported languages.
        :param Optional[Language] method_language: The language of the method.
        :param bool is_target: Whether the method is for the target language.

            .. invisible-code-block: python

                from nunavut.jinja import CodeGenEnvironmentBuilder
                from nunavut.jinja.jinja2 import DictLoader
                from nunavut._templates import template_language_test
                from unittest.mock import MagicMock

                lctx = MagicMock(spec=LanguageContext)
                poop_lang = MagicMock(spec=Language)
                poop_lang.name = 'poop'
                poop_lang.get_templates_package_name = MagicMock(return_value='nunavut.lang.poop')
                lctx.get_target_language = poop_lang
                lctx.get_supported_languages = MagicMock(return_value = {'poop': poop_lang})

                @template_language_test('nunavut.lang.poop')
                def test_test(language):
                    return True

                e = (
                    CodeGenEnvironmentBuilder(DictLoader({'test': 'hello world'}))
                    .add_tests(foo=test_test)
                    .create(lctx)
                )
                assert test_test == e.tests['foo'].func
                assert e.tests['foo']()
        """

        result = LanguageEnvironment.handle_conventional_methods(method, method_name, supported_languages)
        collection = self._resolve_collection(result[0], method_name, collection_maybe)

        if method_language is not None:
            self._add_to_environment(f"ln.{method_language.name}.{result[1]}", result[2], collection)
        else:
            self._add_to_environment(result[1], result[2], collection)
        if is_target:
            self._add_to_environment(result[1], result[2], collection)

    def _add_each_to_environment(
        self,
        items: AbstractSet[Tuple[str, Callable]],
        collection: Optional[
            Union[
                LanguageTemplateNamespace,
                Dict[str, Any],
            ]
        ] = None,
        supported_languages: Optional[ValuesView[Language]] = None,
        language: Optional[Language] = None,
        is_target: bool = False,
    ) -> None:
        for method_name, method in items:
            self._add_conventional_method_to_environment(
                method, method_name, collection, supported_languages, language, is_target
            )

    @classmethod
    def _create_platform_version(cls, embed_auditing_info: bool) -> Dict[str, Any]:

        platform_version = {}  # type: Dict[str, Any]

        platform_version["python_version"] = platform.python_version()
        if embed_auditing_info:
            platform_version["python_implementation"] = platform.python_implementation()
            platform_version["python_release_level"] = sys.version_info[3]
            platform_version["python_build"] = platform.python_build()
            platform_version["python_compiler"] = platform.python_compiler()
            platform_version["python_revision"] = platform.python_revision()

            try:
                # pylint: disable=protected-access
                platform_version["python_xoptions"] = sys._xoptions
            except AttributeError:  # pragma: no cover
                platform_version["python_xoptions"] = {}

            platform_version["runtime_platform"] = platform.platform()

        return platform_version

    def _add_support_from_language_module_to_environment(
        self,
        lctx: LanguageContext,
        language: Language,
        ln_module: "types.ModuleType",
        is_target: bool = False,
    ) -> None:
        supported_languages = lctx.get_supported_languages()
        ln_env = LanguageEnvironment.find_all_conventional_methods_in_language_module(
            language, supported_languages.values(), ln_module
        )
        self._add_each_to_environment(
            ln_env.filters.items(), self.filters, supported_languages.values(), language=language, is_target=is_target
        )
        self._add_each_to_environment(
            ln_env.tests.items(), self.tests, supported_languages.values(), language=language, is_target=is_target
        )
        if is_target:
            self._target_language = language
            self._add_each_to_environment(
                ln_env.uses_queries.items(),
                self.globals["uses_queries"],
                supported_languages.values(),
                language=language,
                is_target=is_target,
            )

    def _update_language_support(self, lctx: LanguageContext) -> None:
        supported_languages = lctx.get_supported_languages()
        target_language = lctx.get_target_language()
        ln_globals = self.globals["ln"]
        self.globals.update(target_language.get_globals())
        globals_options_ns = self.globals["options"]
        globals_options_ns.update(target_language.get_options())
        for supported_language in supported_languages.values():
            if supported_language.name not in ln_globals:
                setattr(
                    ln_globals, supported_language.name, LanguageTemplateNamespace(options=LanguageTemplateNamespace())
                )
            ln_globals_ns = getattr(ln_globals, supported_language.name)
            ln_globals_ns.update(supported_language.get_globals())
            ln_globals_options_ns = getattr(ln_globals_ns, "options")
            ln_globals_options_ns.update(supported_language.get_options())

        # then load everything into the environment from this list.
        # note that we don't unload anything here so this method is not idempotent
        for supported_language in supported_languages.values():
            try:
                self._add_support_from_language_module_to_environment(
                    lctx,
                    supported_language,
                    LanguageClassLoader.load_language_module(supported_language.name),
                    (supported_language == target_language),
                )
            except ModuleNotFoundError:
                pass
