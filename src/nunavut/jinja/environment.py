#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2021  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
import datetime
import inspect
import logging
import types
import typing

import nunavut.lang

from ..templates import LanguageEnvironment
from .extensions import JinjaAssert, UseQuery
from .jinja2 import BaseLoader, Environment, StrictUndefined, select_autoescape
from .jinja2.ext import Extension
from .jinja2.ext import do as jinja_do
from .jinja2.ext import loopcontrols as loopcontrols
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

    def __init__(self, **kwargs: typing.Any):
        for name in kwargs:
            setattr(self, name, kwargs[name])

    def __repr__(self) -> str:
        type_name = type(self).__name__
        arg_strings = []
        star_args = {}
        for name, value in self._get_kwargs():
            if name.isidentifier():
                arg_strings.append("%s=%r" % (name, value))
            else:
                star_args[name] = value
        if star_args:
            arg_strings.append("**%s" % repr(star_args))
        return "%s(%s)" % (type_name, ", ".join(arg_strings))

    def _get_kwargs(self) -> typing.List[typing.Any]:
        return list(self.__dict__.items())

    def __eq__(self, other: typing.Any) -> bool:
        if not isinstance(other, LanguageTemplateNamespace):
            return NotImplemented
        return vars(self) == vars(other)

    def __contains__(self, key: str) -> bool:
        return key in self.__dict__

    def update(self, update_from: typing.Mapping[str, typing.Any]) -> None:
        for key, value in update_from.items():
            setattr(self, key, value)

    def items(self) -> typing.ItemsView[str, typing.Any]:
        return self.__dict__.items()

    def values(self) -> typing.ValuesView[typing.Any]:
        return self.__dict__.values()


# +---------------------------------------------------------------------------+
# | JINJA : CodeGenEnvironment
# +---------------------------------------------------------------------------+


class CodeGenEnvironment(Environment):
    """
    Jinja Environment optimized for compile-time generation of source code
    (i.e. as opposed to dynamically generating webpages).

    .. invisible-code-block: python

        from nunavut.lang import LanguageContext, Language
        from nunavut.jinja import CodeGenEnvironment
        from nunavut.jinja.jinja2 import DictLoader

    .. code-block:: python

        template = 'Hello World'

        e = CodeGenEnvironment(loader=DictLoader({'test': template}))
        assert 'Hello World' ==  e.get_template('test').render()

    .. warning::
        The :attr:`RESERVED_GLOBAL_NAMESPACES` and :attr:`RESERVED_GLOBAL_NAMES` collections
        contain names in the global namespace reserved by this environment. Attempting to override one
        of these reserved names will cause the constructor to raise an error.

    .. code-block:: python

        try:
            CodeGenEnvironment(loader=DictLoader({'test': template}), additional_globals={'ln': 'bad_ln'})
            assert False
        except RuntimeError:
            pass

    Other safe-guards include checks that Jinja built-ins aren't accidentally overridden...

    .. code-block:: python

        try:
            CodeGenEnvironment(loader=DictLoader({'test': template}),
                                                 additional_filters={'indent': lambda x: x})
            assert False
        except RuntimeError:
            pass

        # You can allow overwrite of built-ins using the ``allow_filter_test_or_use_query_overwrite``
        # argument.
        e = CodeGenEnvironment(loader=DictLoader({'test': template}),
                                                 additional_filters={'indent': lambda x: x},
                                                 allow_filter_test_or_use_query_overwrite=True)
        assert 'foo' == e.filters['indent']('foo')

    ...or that user-defined filters or redefined.

    .. code-block:: python

        class MyFilters:

            @staticmethod
            def filter_misnamed(name: str) -> str:
                return name

        e = CodeGenEnvironment(loader=DictLoader({'test': template}),
                               additional_filters={'filter_misnamed': lambda x: x})

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

    NUNAVUT_NAMESPACE_PREFIX = "nunavut.lang."

    def __init__(
        self,
        loader: BaseLoader,
        lctx: typing.Optional[nunavut.lang.LanguageContext] = None,
        trim_blocks: bool = False,
        lstrip_blocks: bool = False,
        additional_filters: typing.Optional[typing.Dict[str, typing.Callable]] = None,
        additional_tests: typing.Optional[typing.Dict[str, typing.Callable]] = None,
        additional_globals: typing.Optional[typing.Dict[str, typing.Any]] = None,
        extensions: typing.List[Extension] = [jinja_do, loopcontrols, JinjaAssert, UseQuery],
        allow_filter_test_or_use_query_overwrite: bool = False,
    ):
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
                    raise RuntimeError('Additional global "{}" uses a reserved global name'.format(global_name))
                self.globals[global_name] = global_value

        self._allow_replacements = allow_filter_test_or_use_query_overwrite

        for global_namespace in self.RESERVED_GLOBAL_NAMESPACES:
            self.globals[global_namespace] = LanguageTemplateNamespace()

        self.globals["now_utc"] = datetime.datetime(datetime.MINYEAR, 1, 1)
        self._target_language = None  # type: typing.Optional[nunavut.lang.Language]

        # --------------------------------------------------
        # After this point we do that most heinous act so common in dynamic languages;
        # we expose the state of this partially constructed object so we can complete
        # configuring it.

        if lctx is not None:
            self._update_language_support(lctx)

            supported_languages = (
                lctx.get_supported_languages().values()
            )  # type: typing.Optional[typing.ValuesView[nunavut.lang.Language]]
        else:
            supported_languages = None

        self._update_nunavut_globals(lctx)

        self.add_conventional_methods_to_environment(self)

        if additional_filters is not None:
            self._add_each_to_environment(
                additional_filters.items(), self.filters, supported_languages=supported_languages
            )
        if additional_tests is not None:
            self._add_each_to_environment(additional_tests.items(), self.tests, supported_languages=supported_languages)

    def add_conventional_methods_to_environment(self, obj: typing.Any) -> None:
        for name, method in inspect.getmembers(obj, inspect.isroutine):
            try:
                self._add_conventional_method_to_environment(method, name, supported_languages=self.supported_languages)
            except TypeError:
                pass

    @property
    def supported_languages(self) -> typing.ValuesView[nunavut.lang.Language]:
        ln_globals = self.globals["ln"]  # type: LanguageTemplateNamespace
        return ln_globals.values()

    @property
    def nunavut_global(self) -> LanguageTemplateNamespace:
        return typing.cast(LanguageTemplateNamespace, self.globals["nunavut"])

    @property
    def target_language_uses_queries(self) -> LanguageTemplateNamespace:
        return typing.cast(LanguageTemplateNamespace, self.globals["uses_queries"])

    @property
    def language_options(self) -> LanguageTemplateNamespace:
        return typing.cast(LanguageTemplateNamespace, self.globals["options"])

    @property
    def language_support(self) -> LanguageTemplateNamespace:
        return typing.cast(LanguageTemplateNamespace, self.globals["ln"])

    @property
    def target_language(self) -> typing.Optional[nunavut.lang.Language]:
        return self._target_language

    @property
    def now_utc(self) -> datetime.datetime:
        return typing.cast(datetime.datetime, self.globals["now_utc"])

    @now_utc.setter
    def now_utc(self, utc_time: datetime.datetime) -> None:
        self.globals["now_utc"] = utc_time

    def add_test(self, test_name: str, test_callable: typing.Callable) -> None:
        self._add_to_environment(test_name, test_callable, self.tests)

    # +----------------------------------------------------------------------------------------------------------------+
    # | Private
    # +----------------------------------------------------------------------------------------------------------------+
    def _resolve_collection(
        self,
        conventional_method_prefix: typing.Optional[str],
        method_name: str,
        collection_maybe: typing.Optional[typing.Union[LanguageTemplateNamespace, typing.Dict[str, typing.Any]]],
    ) -> typing.Union[LanguageTemplateNamespace, typing.Dict[str, typing.Any]]:
        if collection_maybe is not None:
            return collection_maybe

        if LanguageEnvironment.is_test_name(conventional_method_prefix):
            return typing.cast(typing.Dict[str, typing.Any], self.tests)
        elif LanguageEnvironment.is_filter_name(conventional_method_prefix):
            return typing.cast(typing.Dict[str, typing.Any], self.filters)
        elif LanguageEnvironment.is_uses_query_name(conventional_method_prefix):
            uses_queries = self.globals["uses_queries"]
            return typing.cast(LanguageTemplateNamespace, uses_queries)
        else:
            raise TypeError(
                "Tried to add an item {} to the template environment but we don't know what the item is.".format(
                    method_name
                )
            )

    def _add_to_environment(
        self,
        item_name: str,
        item: typing.Any,
        collection: typing.Union[LanguageTemplateNamespace, typing.Dict[str, typing.Any]],
    ) -> None:
        if item_name in collection:
            if not self._allow_replacements:
                raise RuntimeError("{} was already defined.".format(item_name))
            elif item_name in JINJA2_FILTERS:
                logger.info("Replacing Jinja built-in {}".format(item_name))
            else:
                logger.info('Replacing "{}" which was already defined for this environment.'.format(item_name))
        else:
            logger.debug("Adding {} to environment".format(item_name))
        if isinstance(collection, LanguageTemplateNamespace):
            setattr(collection, item_name, item)
        else:
            collection[item_name] = item

    def _add_conventional_method_to_environment(
        self,
        method: typing.Callable[..., bool],
        method_name: str,
        collection_maybe: typing.Optional[typing.Union[LanguageTemplateNamespace, typing.Dict[str, typing.Any]]] = None,
        supported_languages: typing.Optional[typing.ValuesView[nunavut.lang.Language]] = None,
        method_language: typing.Optional[nunavut.lang.Language] = None,
        is_target: bool = False,
    ) -> None:
        """

        :param str callable_name: The name of the callable to use in a template.
        :param typing.Callable[..., bool] callable: The named callable.
        :param typing.Optional[str] callable_namespace: If provided the namespace to prefix to the callable name.
        :return: tuple of name and the callable which might be prepared as a partial function based on decorators.
        :raises: RuntimeWarning if the callable requested resources that were not available in this environment.

            .. invisible-code-block: python

                from nunavut.jinja import CodeGenEnvironment
                from nunavut.jinja.jinja2 import DictLoader
                from nunavut.templates import template_language_test
                from unittest.mock import MagicMock

                lctx = MagicMock(spec=LanguageContext)
                poop_lang = MagicMock(spec=Language)
                poop_lang.name = 'poop'
                poop_lang.get_templates_package_name = MagicMock(return_value='nunavut.lang.poop')
                lctx.get_target_language = MagicMock(return_value=None)
                lctx.get_supported_languages = MagicMock(return_value = {'poop': poop_lang})

                @template_language_test('nunavut.lang.poop')
                def test_test(language):
                    return True

                e = CodeGenEnvironment(
                    loader=DictLoader({'test': 'hello world'}),
                    additional_tests={'foo': test_test},
                    lctx=lctx
                )
                assert test_test == e.tests['foo'].func
                assert e.tests['foo']()
        """

        result = LanguageEnvironment.handle_conventional_methods(method, method_name, supported_languages)
        collection = self._resolve_collection(result[0], method_name, collection_maybe)

        if method_language is not None:
            self._add_to_environment("ln.{}.{}".format(method_language.name, result[1]), result[2], collection)
        else:
            self._add_to_environment(result[1], result[2], collection)
        if is_target:
            self._add_to_environment(result[1], result[2], collection)

    def _add_each_to_environment(
        self,
        items: typing.AbstractSet[typing.Tuple[str, typing.Callable]],
        collection: typing.Optional[
            typing.Union[
                LanguageTemplateNamespace,
                typing.Dict[str, typing.Any],
            ]
        ] = None,
        supported_languages: typing.Optional[typing.ValuesView[nunavut.lang.Language]] = None,
        language: typing.Optional[nunavut.lang.Language] = None,
        is_target: bool = False,
    ) -> None:
        for method_name, method in items:
            self._add_conventional_method_to_environment(
                method, method_name, collection, supported_languages, language, is_target
            )

    @classmethod
    def _create_platform_version(cls) -> typing.Dict[str, typing.Any]:
        import platform
        import sys

        platform_version = {}  # type: typing.Dict[str, typing.Any]

        platform_version["python_implementation"] = platform.python_implementation()
        platform_version["python_version"] = platform.python_version()
        platform_version["python_release_level"] = sys.version_info[3]
        platform_version["python_build"] = platform.python_build()
        platform_version["python_compiler"] = platform.python_compiler()
        platform_version["python_revision"] = platform.python_revision()

        try:
            platform_version["python_xoptions"] = sys._xoptions
        except AttributeError:  # pragma: no cover
            platform_version["python_xoptions"] = {}

        platform_version["runtime_platform"] = platform.platform()

        return platform_version

    def _add_support_from_language_module_to_environment(
        self,
        lctx: nunavut.lang.LanguageContext,
        language: nunavut.lang.Language,
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

    def _update_language_support(self, lctx: nunavut.lang.LanguageContext) -> None:

        supported_languages = lctx.get_supported_languages()
        target_language = lctx.get_target_language()
        ln_globals = self.globals["ln"]
        if target_language is not None:
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
            is_target = target_language is not None and supported_language == target_language
            try:
                self._add_support_from_language_module_to_environment(
                    lctx,
                    supported_language,
                    nunavut.lang.LanguageLoader.load_language_module(supported_language.name),
                    is_target,
                )
            except ModuleNotFoundError:
                pass

    def _update_nunavut_globals(self, lctx: typing.Optional[nunavut.lang.LanguageContext] = None) -> None:

        # Helper global so we don't have to futz around with the "omit_serialization_support"
        # logic in the templates. The omit_serialization_support property of the Language
        # object is read-only so this boolean will remain consistent for the Environment.
        target_language = None if lctx is None else lctx.get_target_language()
        if target_language is not None:
            omit_serialization_support = target_language.omit_serialization_support
            support_namespace, support_version, _ = target_language.get_support_module()
        else:
            logger.debug("There is no target language so we cannot generate serialization support")
            omit_serialization_support = True
            support_namespace = ""
            support_version = (0, 0, 0)

        nunavut_namespace = self.nunavut_global

        setattr(
            nunavut_namespace,
            "support",
            {"omit": omit_serialization_support, "namespace": support_namespace, "version": support_version},
        )

        if "version" not in nunavut_namespace:
            import nunavut.version
            from nunavut.jinja.loaders import DSDLTemplateLoader

            setattr(nunavut_namespace, "version", nunavut.version.__version__)
            setattr(nunavut_namespace, "platform_version", self._create_platform_version())

            if isinstance(self.loader, DSDLTemplateLoader):
                setattr(nunavut_namespace, "template_sets", self.loader.get_template_sets())
