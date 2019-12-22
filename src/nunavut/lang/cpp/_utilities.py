#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    Additional, internal logic supporting C++ code generators.
"""

import pathlib
import typing

import pydsdl

import nunavut

from .. import Language


class IncludeGenerator(nunavut.DependencyBuilder):

    def __init__(self,
                 language: Language,
                 t: pydsdl.CompositeType,
                 id_filter: typing.Callable[[Language, str], str],
                 short_reference_name_filter: typing.Callable[..., str]):
        super().__init__(t)
        self._language = language
        self._use_standard_types = bool(self._language.get_config_value_as_bool('use_standard_types', True))
        self._id = id_filter
        self._short_reference_name_filter = short_reference_name_filter

    def generate_include_filepart_list(self,
                                       output_extension: str,
                                       sort: bool) -> typing.List[str]:
        dep_types = self.direct()

        path_list = [self._make_path(dt, output_extension) for dt in dep_types.composite_types]

        if not self._language.omit_serialization_support:
            from .support import list_support_headers
            path_list += [str(p) for p in list_support_headers(self._language.support_namespace)]

        prefer_system_includes = bool(self._language.get_config_value_as_bool('prefer_system_includes', False))
        if prefer_system_includes:
            path_list_with_punctuation = ['<{}>'.format(p) for p in path_list]
        else:
            path_list_with_punctuation = ['"{}"'.format(p) for p in path_list]

        if sort:
            return self._get_std_includes(dep_types) + sorted(path_list_with_punctuation)
        else:
            return self._get_std_includes(dep_types) + path_list_with_punctuation

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _get_std_includes(self, dep_types: nunavut.Dependencies) -> typing.List[str]:
        std_includes = []  # type: typing.List[str]
        if self._use_standard_types:
            if dep_types.uses_integer:
                std_includes.append('cstdint')
            if dep_types.uses_array:
                std_includes.append('array')
            if dep_types.uses_variable_length_array:
                std_includes.append('vector')
        return ['<{}>'.format(include) for include in sorted(std_includes)]

    def _make_path(self, dt: pydsdl.CompositeType, output_extension: str) -> str:
        short_name = self._short_reference_name_filter(self._language, dt)
        ns_path = pathlib.Path(*self._make_ns_list(dt)) / pathlib.Path(short_name).with_suffix(output_extension)
        return str(ns_path)

    def _make_ns_list(self, dt: pydsdl.SerializableType) -> typing.List[str]:
        if self._language.enable_stropping:
            return [self._id(self._language, x) for x in dt.full_namespace.split('.')]
        else:
            return typing.cast(typing.List[str], dt.full_namespace.split('.'))
