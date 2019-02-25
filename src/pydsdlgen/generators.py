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

from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Dict
from typing import ItemsView, KeysView

from pydsdl.data_type import CompoundType


class AbstractGenerator(metaclass=ABCMeta):
    """
        Abstract base class for classes that generate source file output
        from a given pydsdl parser result.

        :param Path output_basedir: The directory under which all output will be placed.
        :param dict parser_result: The output from pydsdl's parser.
    """

    def __init__(self, output_basedir: Path, parser_result: Dict[CompoundType, Path]):
        self._output_basedir = output_basedir
        self._parser_result = parser_result

    @property
    def input_types(self) -> KeysView[CompoundType]:
        return self._parser_result.keys()

    @property
    def parser_results(self) -> ItemsView[CompoundType, Path]:
        return self._parser_result.items()

    @abstractmethod
    def generate_all(self, is_dryrun: bool = False) -> int:
        """
        Generates all output for a given set of dsdl inputs and using
        the templates found by this object.

        :param bool is_dryrun: If True then no output files will actually be
                               written but all other operations will be performed.
        """
        raise NotImplementedError()
