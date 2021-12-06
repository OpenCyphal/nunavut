#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2021  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
Objects and utilities for handling DSDL dependencies when generating code for a given type.
"""

import typing

import pydsdl


class Dependencies:
    """
    Data structure that contains a set of composite types and annotations (bool flags)
    which constitute a set of dependencies for a set of DSDL objects.
    """

    def __init__(self) -> None:
        self.composite_types = set()  # type: typing.Set[pydsdl.CompositeType]
        self.uses_integer = False
        self.uses_float = False
        self.uses_variable_length_array = False
        self.uses_array = False
        self.uses_bool = False
        self.uses_primitive_static_array = False
        self.uses_union = False


class DependencyBuilder:
    """
    Given a list of DSDL types this object builds a set of types that the given types use.

    .. invisible-code-block: python

        import pydsdl
        from unittest.mock import MagicMock
        from nunavut.dependencies import DependencyBuilder

        my_dependant_type_l2 = MagicMock(spec=pydsdl.CompositeType)
        my_dependant_type_l2.parent_service = False
        my_dependant_type_l2.attributes = []

        my_dependant_type_l1 = MagicMock(spec=pydsdl.CompositeType)
        my_dependant_type_l1.parent_service = False
        my_dependant_type_l1.attributes = [MagicMock(data_type=my_dependant_type_l2)]

        my_top_level_type = MagicMock(spec=pydsdl.UnionType)
        my_top_level_type.parent_service = False
        my_top_level_type.attributes = [MagicMock(data_type=my_dependant_type_l1)]

        direct_dependencies = DependencyBuilder(my_top_level_type).direct()

        assert len(direct_dependencies.composite_types) == 1
        assert my_dependant_type_l1 in direct_dependencies.composite_types

        transitive_dependencies = DependencyBuilder(my_top_level_type).transitive()

        assert len(transitive_dependencies.composite_types) == 2
        assert my_dependant_type_l1 in transitive_dependencies.composite_types
        assert my_dependant_type_l2 in transitive_dependencies.composite_types
        assert direct_dependencies.uses_integer
        assert direct_dependencies.uses_union

    :param dependant_types: A list of types to build dependencies for.
    :type dependant_types: typing.Iterable[pydsdl.Any]
    """

    def __init__(self, *dependant_types: pydsdl.Any):
        self._dependent_types = dependant_types

    def transitive(self) -> Dependencies:
        """
        Build a set of all transitive dependencies for the dependent types
        set for this builder.
        """
        return self._build_dependency_list(self._dependent_types, True)

    def direct(self) -> Dependencies:
        """
        Build a set of all first-order dependencies for the dependent types
        set for this builder.
        """
        return self._build_dependency_list(self._dependent_types, False)

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+

    @classmethod
    def _build_dependency_list(
        cls, dependant_types: typing.Iterable[pydsdl.CompositeType], transitive: bool
    ) -> Dependencies:
        results = Dependencies()
        for dependant in dependant_types:
            if isinstance(dependant, pydsdl.UnionType):
                # Unions always require integer for the tag field.
                results.uses_integer = True
                results.uses_union = True
            cls._extract_dependent_types(cls._extract_data_types(dependant), transitive, results)
        return results

    @classmethod
    def _extract_data_types(cls, t: pydsdl.CompositeType) -> typing.List[pydsdl.SerializableType]:
        # Make a list of all attributes defined by this type
        if isinstance(t, pydsdl.ServiceType):
            return [attr.data_type for attr in t.request_type.attributes] + [
                attr.data_type for attr in t.response_type.attributes
            ]
        else:
            return [attr.data_type for attr in t.attributes]

    @classmethod
    def _extract_dependent_types_handle_array_type(
        cls, dependant_type: pydsdl.ArrayType, transitive: bool, inout_dependencies: Dependencies
    ) -> None:
        if isinstance(dependant_type, pydsdl.VariableLengthArrayType):
            inout_dependencies.uses_variable_length_array = True
        else:
            inout_dependencies.uses_array = True
            if isinstance(dependant_type.element_type, pydsdl.PrimitiveType):
                inout_dependencies.uses_primitive_static_array = True

    @classmethod
    def _extract_dependent_types(
        cls, dependant_types: typing.Iterable[pydsdl.Any], transitive: bool, inout_dependencies: Dependencies
    ) -> None:
        for dt in dependant_types:
            if isinstance(dt, pydsdl.CompositeType):
                if dt not in inout_dependencies.composite_types:
                    inout_dependencies.composite_types.add(dt)
                    if transitive:
                        cls._extract_dependent_types(cls._extract_data_types(dt), transitive, inout_dependencies)
            elif isinstance(dt, pydsdl.ArrayType):
                cls._extract_dependent_types_handle_array_type(dt, transitive, inout_dependencies)
                cls._extract_dependent_types([dt.element_type], transitive, inout_dependencies)
            elif isinstance(dt, pydsdl.IntegerType):
                inout_dependencies.uses_integer = True
            elif isinstance(dt, pydsdl.FloatType):
                inout_dependencies.uses_float = True
            elif isinstance(dt, pydsdl.BooleanType):
                inout_dependencies.uses_bool = True
