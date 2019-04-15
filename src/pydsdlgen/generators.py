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
from typing import Dict, KeysView

from pydsdl import CompositeType


class AbstractGenerator(metaclass=ABCMeta):
    """
        Abstract base class for classes that generate source file output
        from a given pydsdl parser result.

        :param dict type_map:   A map of pydsdl types to the path the type will be generated at.
    """

    def __init__(self,
                 type_map: Dict[CompositeType, Path]):
        self._type_map = type_map

    @property
    def input_types(self) -> KeysView[CompositeType]:
        return self._type_map.keys()

    @property
    def type_map(self) -> Dict[CompositeType, Path]:
        return self._type_map

    @abstractmethod
    def generate_all(self, is_dryrun: bool = False) -> int:
        """
        Generates all output for a given set of dsdl inputs and using
        the templates found by this object.

        :param bool is_dryrun: If True then no output files will actually be
                               written but all other operations will be performed.
        """
        raise NotImplementedError()
