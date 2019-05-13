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
import nunavut.postprocessors


class AbstractGenerator(metaclass=abc.ABCMeta):
    """
        Abstract base class for classes that generate source file output
        from a given pydsdl parser result.

        :param nunavut.Namespace namespace:  The top-level namespace to
            generates types at and from.
        :param bool generate_namespace_types:  Set to true to emit files
            for namespaces. False will only generate files for datatypes.
    """

    def __init__(self,
                 namespace: nunavut.Namespace,
                 generate_namespace_types: bool):
        self._namespace = namespace
        self._generate_namespace_types = generate_namespace_types

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
                     allow_overwrite: bool = True,
                     post_processors: typing.Optional[typing.List['nunavut.postprocessors.PostProcessor']] = None) -> int:
        """
        Generates all output for a given :class:`nunavut.Namespace` and using
        the templates found by this object.

        :param bool is_dryrun: If True then no output files will actually be
                               written but all other operations will be performed.
        :param bool allow_overwrite: If True then the generator will attempt to overwrite any existing files
                                it encounters. If False then the generator will raise an error if the
                                output file exists and the generation is not a dry-run.
        :param post_processors: A list of :class:`nunavut.postprocessors.PostProcessor`
        """
        raise NotImplementedError()
