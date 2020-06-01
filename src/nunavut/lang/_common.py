#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2020  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""Language-specific support in nunavut.

This package contains modules that provide specific support for generating
source for various languages using templates.
"""
import pathlib
import pydsdl
import typing

from . import Language
from nunavut import (DependencyBuilder, Dependencies)


class IncludeGenerator(DependencyBuilder):

    def __init__(self,
                 language: Language,
                 t: pydsdl.CompositeType,
                 id_filter: typing.Callable[[Language, str], str],
                 short_reference_name_filter: typing.Callable[..., str]):
        super().__init__(t)
        self._language = language
        self._id = id_filter
        self._short_reference_name_filter = short_reference_name_filter

    def generate_include_filepart_list(self,
                                       output_extension: str,
                                       sort: bool) -> typing.List[str]:
        dep_types = self.direct()

        path_list = [self._make_path(dt, output_extension) for dt in dep_types.composite_types]

        if not self._language.omit_serialization_support:
            namespace_path = pathlib.Path('')
            for namespace_part in self._language.support_namespace:
                namespace_path = namespace_path / pathlib.Path(namespace_part)
            path_list += [str(namespace_path / pathlib.Path(p.name)) for p in self._language.support_files]

        prefer_system_includes = bool(self._language.get_config_value_as_bool('prefer_system_includes', False))
        if prefer_system_includes:
            path_list_with_punctuation = ['<{}>'.format(p) for p in path_list]
        else:
            path_list_with_punctuation = ['"{}"'.format(p) for p in path_list]

        if sort:
            return sorted(path_list_with_punctuation) + self._get_language_includes(dep_types)
        else:
            return path_list_with_punctuation + self._get_language_includes(dep_types)

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+

    def _get_language_includes(self, dep_types: Dependencies) -> typing.List[str]:
        """
        Retrieve well-known includes for well-known languages. If this list grows beyond
        C and C++ then utilize the language properties.ini to drive this from configuration.
        """
        if self._language.name == 'c':
            return self._get_std_includes_for_c(dep_types)
        elif self._language.name == 'cpp':
            return self._get_std_includes_for_cpp(dep_types)
        else:
            return []

    def _get_std_includes_for_cpp(self, dep_types: Dependencies) -> typing.List[str]:
        std_includes = []  # type: typing.List[str]
        if self._language.get_config_value_as_bool('use_standard_types'):
            if dep_types.uses_integer:
                std_includes.append('cstdint')
            if dep_types.uses_array:
                std_includes.append('array')
            if dep_types.uses_variable_length_array:
                std_includes.append('vector')
        return ['<{}>'.format(include) for include in sorted(std_includes)]

    def _get_std_includes_for_c(self, dep_types: Dependencies) -> typing.List[str]:
        std_includes = []  # type: typing.List[str]
        if self._language.get_config_value_as_bool('use_standard_types'):
            std_includes.append('stdlib.h')
            # we always include stdlib if standard types are in use since initializers
            # require the use of NULL
            if dep_types.uses_integer:
                std_includes.append('stdint.h')
            if dep_types.uses_bool:
                std_includes.append('stdbool.h')
            if dep_types.uses_primitive_static_array:
                # We include this for memset.
                std_includes.append('string.h')
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
