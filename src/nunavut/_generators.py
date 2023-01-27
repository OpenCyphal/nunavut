#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
"""
Module containing types and utilities for building generator objects.
Generators abstract the code generation technology used to transform
pydsdl AST into source code.
"""

import abc
import pathlib
import typing

from pydsdl import read_namespace as read_dsdl_namespace

from nunavut._namespace import Namespace, build_namespace_tree
from nunavut._utilities import YesNoDefault
from nunavut.lang import LanguageContextBuilder
from nunavut.lang._language import Language


class AbstractGenerator(metaclass=abc.ABCMeta):
    """
    Abstract base class for classes that generate source file output
    from a given pydsdl parser result.

    :param nunavut.Namespace namespace:  The top-level namespace to
        generates types at and from.
    :param YesNoDefault generate_namespace_types:  Set to YES
        to force generation files for namespaces and NO to suppress.
        DEFAULT will generate namespace files based on the language
        preference.
    """

    def __init__(
        self,
        namespace: Namespace,
        generate_namespace_types: YesNoDefault = YesNoDefault.DEFAULT,
    ):
        self._namespace = namespace
        if generate_namespace_types == YesNoDefault.YES:
            self._generate_namespace_types = True
        elif generate_namespace_types == YesNoDefault.NO:
            self._generate_namespace_types = False
        else:
            target_language = self._namespace.get_language_context().get_target_language()
            if target_language.has_standard_namespace_files:
                self._generate_namespace_types = True
            else:
                self._generate_namespace_types = False

    @property
    def namespace(self) -> Namespace:
        """
        The root :class:`nunavut.Namespace` for this generator.
        """
        return self._namespace

    @property
    def generate_namespace_types(self) -> bool:
        """
        If true then the generator is set to emit files for :class:`nunavut.Namespace`
        in addition to the pydsdl datatypes. If false then only files for pydsdl datatypes
        will be generated.
        """
        return self._generate_namespace_types

    @abc.abstractmethod
    def get_templates(self, omit_serialization_support: bool = False) -> typing.Iterable[pathlib.Path]:
        """
        Enumerate all templates found in the templates path.
        :param bool omit_serialization_support: If True then templates needed only for serialization will be omitted.
        :return: A list of paths to all templates found by this Generator object.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def generate_all(
        self, is_dryrun: bool = False, allow_overwrite: bool = True, omit_serialization_support: bool = False
    ) -> typing.Iterable[pathlib.Path]:
        """
        Generates all output for a given :class:`nunavut.Namespace` and using
        the templates found by this object.

        :param bool is_dryrun: If True then no output files will actually be
                               written but all other operations will be performed.
        :param bool allow_overwrite: If True then the generator will attempt to overwrite any existing files
                                it encounters. If False then the generator will raise an error if the
                                output file exists and the generation is not a dry-run.
        :param bool omit_serialization_support: If True then the generator will emit only types without additional
                                serialization and deserialization support and logic.
        :return: 0 for success. Non-zero for errors.
        :raises: PermissionError if :attr:`allow_overwrite` is False and the file exists.
        """
        raise NotImplementedError()


def create_default_generators(
    namespace: Namespace, **kwargs: typing.Any
) -> typing.Tuple["AbstractGenerator", "AbstractGenerator"]:
    """
    Create the two generators used by Nunavut; a code-generator and a support-library generator.

    :param nunavut.Namespace namespace: The namespace to generate code within.
    :param kwargs: A list of arguments that are forwarded to the generator constructors.
    :return: Tuple with the first item being the code-generator and the second the support-library
        generator.
    """
    from nunavut.jinja import DSDLCodeGenerator, SupportGenerator

    return (DSDLCodeGenerator(namespace, **kwargs), SupportGenerator(namespace, **kwargs))


# +---------------------------------------------------------------------------+
# | GENERATION HELPERS
# +---------------------------------------------------------------------------+


def generate_types(
    language_key: str,
    root_namespace_dir: pathlib.Path,
    out_dir: pathlib.Path,
    omit_serialization_support: bool = True,
    is_dryrun: bool = False,
    allow_overwrite: bool = True,
    lookup_directories: typing.Optional[typing.Iterable[str]] = None,
    allow_unregulated_fixed_port_id: bool = False,
    language_options: typing.Mapping[str, typing.Any] = {},
    include_experimental_languages: bool = False,
) -> None:
    """
    Helper method that uses default settings and built-in templates to generate types for a given
    language. This method is the most direct way to generate code using Nunavut.

    :param str language_key: The name of the language to generate source for.
                See the :doc:`../../docs/templates` for details on available language support.
    :param pathlib.Path root_namespace_dir: The path to the root of the DSDL types to generate
                code for.
    :param pathlib.Path out_dir: The path to generate code at and under.
    :param bool omit_serialization_support: If True then logic used to serialize and deserialize data is omitted.
    :param bool is_dryrun: If True then nothing is generated but all other activity is performed and any errors
                that would have occurred are reported.
    :param bool allow_overwrite: If True then generated files are allowed to overwrite existing files under the
                `out_dir` path.
    :param typing.Optional[typing.Iterable[str]] lookup_directories: Additional directories to search for dependent
                types referenced by the types provided under the `root_namespace_dir`. Types will not be generated
                for these unless they are used by a type in the root namespace.
    :param bool allow_unregulated_fixed_port_id: If True then errors will become warning when using fixed port
                identifiers for unregulated datatypes.
    :param typing.Optional[typing.Mapping[str, typing.Any]] language_options: Opaque arguments passed through to the
                language objects. The supported arguments and valid values are different depending on the language
                specified by the `language_key` parameter.
    :param bool include_experimental_languages: If true then experimental languages will also be available.
    """

    language_context = (
        LanguageContextBuilder(include_experimental_languages=include_experimental_languages)
        .set_target_language(language_key)
        .set_target_language_configuration_override(Language.WKCV_LANGUAGE_OPTIONS, language_options)
        .create()
    )

    if lookup_directories is None:
        lookup_directories = []

    type_map = read_dsdl_namespace(
        str(root_namespace_dir), lookup_directories, allow_unregulated_fixed_port_id=allow_unregulated_fixed_port_id
    )

    namespace = build_namespace_tree(type_map, str(root_namespace_dir), str(out_dir), language_context)

    generator, support_generator = create_default_generators(namespace)
    support_generator.generate_all(is_dryrun, allow_overwrite, omit_serialization_support)
    generator.generate_all(is_dryrun, allow_overwrite, omit_serialization_support)
