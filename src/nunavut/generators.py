#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
Module containing types and utilities for building generator objects.
Generators abstract the code generation technology used to transform
pydsdl AST into source code.
"""

import abc
import typing

import nunavut


class AbstractGenerator(metaclass=abc.ABCMeta):
    """
        Abstract base class for classes that generate source file output
        from a given pydsdl parser result.

        :param nunavut.Namespace namespace:  The top-level namespace to
            generates types at and from.
        :param nunavut.YesNoDefault generate_namespace_types:  Set to YES
            to force generation files for namespaces and NO to suppress.
            DEFAULT will generate namespace files based on the language
            preference.
    """

    def __init__(self,
                 namespace: nunavut.Namespace,
                 generate_namespace_types: nunavut.YesNoDefault = nunavut.YesNoDefault.DEFAULT):
        self._namespace = namespace
        if generate_namespace_types == nunavut.YesNoDefault.YES:
            self._generate_namespace_types = True
        elif generate_namespace_types == nunavut.YesNoDefault.NO:
            self._generate_namespace_types = False
        else:
            target_language = self._namespace.get_language_context().get_target_language()
            if target_language is not None and target_language.has_standard_namespace_files:
                self._generate_namespace_types = True
            else:
                self._generate_namespace_types = False

    @property
    def namespace(self) -> nunavut.Namespace:
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
    def generate_all(self,
                     is_dryrun: bool = False,
                     allow_overwrite: bool = True) \
            -> int:
        """
        Generates all output for a given :class:`nunavut.Namespace` and using
        the templates found by this object.

        :param bool is_dryrun: If True then no output files will actually be
                               written but all other operations will be performed.
        :param bool allow_overwrite: If True then the generator will attempt to overwrite any existing files
                                it encounters. If False then the generator will raise an error if the
                                output file exists and the generation is not a dry-run.
        :return: 0 for success. Non-zero for errors.
        :raises: PermissionError if :attr:`allow_overwrite` is False and the file exists.
        """
        raise NotImplementedError()


def create_builtin_source_generator(namespace: nunavut.Namespace) -> 'AbstractGenerator':
    """
    Create a new :class:`Generator <nunavut.generators.AbstractGenerator>` that uses internal templates
    and configuration to generate source code for DSDL messages.
    """
    from nunavut.jinja import Generator

    return Generator(namespace)


def create_support_generator(namespace: nunavut.Namespace) -> 'AbstractGenerator':
    """
    Create a new :class:`Generator <nunavut.generators.AbstractGenerator>` that uses embedded support
    headers, libraries, and other types needed to use generated serialization code for the
    :func:`target language <nunavut.lang.LanguageContext.get_target_language>`. If no target language
    is set or if serialization support has been turned off a no-op generator will be returned instead.
    """
    class _NoOpSupportGenerator(AbstractGenerator):
        def generate_all(self,
                         is_dryrun: bool = False,
                         allow_overwrite: bool = True) \
                -> int:
            return 0

    target_language = namespace.get_language_context().get_target_language()
    if target_language is None or target_language.omit_serialization_support:
        return _NoOpSupportGenerator(namespace, nunavut.YesNoDefault.DEFAULT)
    else:
        SupportGenerator = getattr(target_language.module, 'SupportGenerator', _NoOpSupportGenerator)  \
            # type: typing.Type[AbstractGenerator]
        return SupportGenerator(namespace)
