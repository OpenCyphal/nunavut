#
# Copyright 2024 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2024  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
"""
Filters for generating python. All filters in this
module will be available in the template's global namespace as ``lua``.
"""
from __future__ import annotations
import builtins
import functools
import keyword
import base64
import gzip
import pickle
import itertools
import re
import typing
from typing import Any, Iterable

import pydsdl
from jinja2 import Environment

from nunavut._dependencies import Dependencies
from nunavut._templates import (
    SupportsTemplateContext,
    template_context_filter,
    template_language_filter,
    template_language_int_filter,
    template_language_list_filter,
    template_environment_list_filter,
)
from nunavut.lang import Language as BaseLanguage
from nunavut.lang._common import RequireGenerator, TokenEncoder, UniqueNameGenerator


class Language(BaseLanguage):
    """
    Concrete, Lua-specific :class:`nunavut.lang.Language` object.
    """

    @staticmethod
    def _handle_stropping_failure(
        encoder: TokenEncoder, stropped: str, token_type: str, pending_error: RuntimeError
    ) -> str:
        """
        If the generic stropping results in either `^_[A-Z]` or `^__` we handle the failure
        with lua-specific logic.
        """
        m = re.match(r"^_+([A-Z]?)", stropped)
        if m:
            # Resolve the conflict between Lua's global identifier rules and our desire to use
            # '_' as a stropping prefix:
            return "_{}{}".format(m.group(1).lower(), stropped[m.end() :])

        # we couldn't help after all. raise the pending error.
        raise pending_error

    @functools.lru_cache(maxsize=None)
    def _get_token_encoder(self) -> TokenEncoder:
        """
        Caching getter to ensure we don't have to recompile TokenEncoders for each filter invocation.
        """
        return TokenEncoder(self, stropping_failure_handler=self._handle_stropping_failure)

    def get_includes(self, dep_types: Dependencies) -> list[str]:
        # imports aren't requires?
        return []

    def filter_id(self, instance: Any, id_type: str = "any") -> str:
        raw_name = self.default_filter_id_for_target(instance)
        return self._get_token_encoder().strop(raw_name, id_type)

    def get_support_globals(self, namespace: typing.Any) -> typing.Dict[str, typing.Any]:
        """
        Provide additional globals for support template rendering.
        Collects all messages and services from the namespace tree.

        :param namespace: The root namespace being generated
        :return: Dictionary of additional globals to inject into support templates
        """
        all_messages = []
        all_services = []
        fixed_port_messages = []
        fixed_port_services = []

        def collect_from_namespace(ns: typing.Any) -> None:
            """Recursively collect all types from namespace tree."""
            for data_type, _ in ns.get_nested_types():
                if isinstance(data_type, pydsdl.ServiceType):
                    all_services.append(data_type)
                    if hasattr(data_type, "fixed_port_id") and data_type.fixed_port_id is not None:
                        fixed_port_services.append(data_type)
                else:
                    all_messages.append(data_type)
                    if hasattr(data_type, "fixed_port_id") and data_type.fixed_port_id is not None:
                        fixed_port_messages.append(data_type)

            # Recurse into nested namespaces
            for child_ns in ns.get_nested_namespaces():
                collect_from_namespace(child_ns)

        if namespace is not None:
            collect_from_namespace(namespace)

        return {
            "all_messages": all_messages,
            "all_services": all_services,
            "fixed_port_messages": fixed_port_messages,
            "fixed_port_services": fixed_port_services,
        }


@template_language_filter(__name__)
def filter_id(language: Language, instance: typing.Any, id_type: str = "any") -> str:
    """
    Filter that produces a valid C identifier for a given object. The encoding may not
    be reversible.
    :param any instance:        Any object or data that either has a name property or can be converted
                                to a string.
    :param str id_type:         A type of identifier. For lua this value can be 'local' or 'function'.
                                use 'any' to apply stropping rules for all identifier types to the instance.
    :return: A token that is a valid identifier for Lua, is not a reserved keyword, and is transformed
              in a deterministic manner based on the provided instance.
    """
    print(">>LUA ", instance, " is ", instance.__class__, " with id ", id_type)
    return language.filter_id(instance, id_type)


@template_language_filter(__name__)
def filter_string_reference_name(language: Language, t: pydsdl.CompositeType) -> str:
    """
    Provides a string that is the full namespace, typename, major, and minor version for a given composite type.
    :param pydsdl.CompositeType t: The DSDL type to get the fully-resolved reference name for.
    """
    ns_parts = t.full_name.split(".")
    if len(ns_parts) > 1:
        if language.enable_stropping:
            ns = list(map(functools.partial(filter_id, language), ns_parts[:-1]))
        else:
            ns = ns_parts[:-1]
        return ".".join(ns + [language.filter_short_reference_name(t)])
    else:
        return language.filter_short_reference_name(t)


@template_language_filter(__name__)
def filter_full_reference_name(language: Language, t: pydsdl.CompositeType) -> str:
    """
    Provides a string that is the full namespace, typename, major, and minor version for a given composite type.
    :param pydsdl.CompositeType t: The DSDL type to get the fully-resolved reference name for.
    """
    ns_parts = t.full_name.split(".")
    if len(ns_parts) > 1:
        if language.enable_stropping:
            ns = list(map(functools.partial(filter_id, language), ns_parts[:-1]))
        else:
            ns = ns_parts[:-1]
        return "_".join(ns + [language.filter_short_reference_name(t)])
    else:
        return language.filter_short_reference_name(t)


@template_language_filter(__name__)
def filter_short_reference_name(language: Language, t: pydsdl.CompositeType) -> str:
    """
    Provides a string that is a shorted version of the full reference name. This type is unique only within its
    namespace.
    :param pydsdl.CompositeType t: The DSDL type to get the reference name for.
    """
    return language.filter_short_reference_name(t)


@template_language_filter(__name__)
def filter_to_protofield_type(language: Language, value: pydsdl.PrimitiveType) -> str:
    """
    Converts a primitive type to a wireshark protofield subtype
    """
    if isinstance(value, pydsdl.UnsignedIntegerType):

        if value.bit_length <= 8:
            return "uint8"
        elif value.bit_length <= 16:
            return "uint16"
        elif value.bit_length <= 24:
            return "uint24"
        elif value.bit_length <= 32:
            return "uint32"
        elif value.bit_length <= 40:
            return "uint40"
        elif value.bit_length <= 48:
            return "uint48"
        elif value.bit_length <= 56:
            return "uint56"
        elif value.bit_length <= 64:
            return "uint64"
        else:
            raise RuntimeError("Bit depth above 64 bit is not supported!")
    elif isinstance(value, pydsdl.SignedIntegerType):
        if value.bit_length <= 8:
            return "int8"
        elif value.bit_length <= 16:
            return "int16"
        elif value.bit_length <= 24:
            return "int24"
        elif value.bit_length <= 32:
            return "int32"
        elif value.bit_length <= 40:
            return "int40"
        elif value.bit_length <= 48:
            return "int48"
        elif value.bit_length <= 56:
            return "int56"
        elif value.bit_length <= 64:
            return "int64"
        else:
            raise RuntimeError("Bit depth above 64 bit is not supported!")
    elif isinstance(value, pydsdl.FloatType):
        if value.bit_length <= 32:
            return "float"
        elif value.bit_length <= 64:
            return "double"
        else:
            raise RuntimeError("Bit depth above 64 bit is not supported!")
    elif isinstance(value, pydsdl.BooleanType):
        return "bool"
    elif isinstance(value, pydsdl.VoidType):
        return "none"
    else:
        raise RuntimeError("{} is not a known PrimitiveType".format(type(value).__name__))


@template_language_filter(__name__)
def filter_to_field_type(language: Language, value: pydsdl.PrimitiveType) -> str:
    """
    Converts a primitive type to a protofield subtype
    """
    if isinstance(value, pydsdl.UnsignedIntegerType):
        if value.bit_length <= 8:
            return "ftypes.UINT8"
        elif value.bit_length <= 16:
            return "ftypes.UINT16"
        elif value.bit_length <= 24:
            return "ftypes.UINT24"
        elif value.bit_length <= 32:
            return "ftypes.UINT32"
        elif value.bit_length <= 64:
            return "ftypes.UINT64"
        else:
            raise RuntimeError("Bit depth above 64 bit is not supported!")
    elif isinstance(value, pydsdl.SignedIntegerType):
        if value.bit_length <= 8:
            return "ftypes.INT8"
        elif value.bit_length <= 16:
            return "ftypes.INT16"
        elif value.bit_length <= 24:
            return "ftypes.INT24"
        elif value.bit_length <= 32:
            return "ftypes.INT32"
        elif value.bit_length <= 64:
            return "ftypes.INT64"
        else:
            raise RuntimeError("Bit depth above 64 bit is not supported!")
    elif isinstance(value, pydsdl.FloatType):
        if value.bit_length <= 32:
            return "ftypes.FLOAT"
        elif value.bit_length <= 64:
            return "ftypes.DOUBLE"
        else:
            raise RuntimeError("Bit depth above 64 bit is not supported!")
    elif isinstance(value, pydsdl.BooleanType):
        return "ftypes.BOOLEAN"
    elif isinstance(value, pydsdl.VoidType):
        return "ftypes.NONE"
    else:
        raise RuntimeError("{} is not a known PrimitiveType".format(type(value).__name__))


@template_language_filter(__name__)
def filter_to_base_type(language: Language, value: pydsdl.PrimitiveType) -> str:
    """
    Converts a primitive type to a protofield subtype
    """
    if isinstance(value, pydsdl.UnsignedIntegerType):
        return "base.DEC"
    elif isinstance(value, pydsdl.SignedIntegerType):
        return "base.DEC"
    elif isinstance(value, pydsdl.FloatType):
        return ""
    elif isinstance(value, pydsdl.BooleanType):
        return ""
    elif isinstance(value, pydsdl.VoidType):
        return "base.NONE"
    else:
        raise RuntimeError("{} is not a known PrimitiveType".format(type(value).__name__))


@template_language_int_filter(__name__)
def filter_to_serialized_length(language: Language, value: pydsdl.PrimitiveType) -> int:
    """
    Returns the number of serialized bytes to use for each Primitive bit depth
    """
    if value.bit_length <= 8:
        return 1
    elif value.bit_length <= 16:
        return 2
    elif value.bit_length <= 24:
        return 3
    elif value.bit_length <= 32:
        return 4
    elif value.bit_length <= 40:
        return 5
    elif value.bit_length <= 48:
        return 6
    elif value.bit_length <= 56:
        return 7
    elif value.bit_length <= 64:
        return 8
    else:
        raise RuntimeError("Bit depth above 64 bit is not supported!")


@template_language_filter(__name__)
def filter_to_wireshark_type(language: Language, value: pydsdl.PrimitiveType) -> str:
    """
    Converts a primitive type to a wireshark protofield subtype
    """
    if isinstance(value, pydsdl.UnsignedIntegerType):
        if value.bit_length <= 8:
            return "uint"
        elif value.bit_length <= 16:
            return "uint"
        elif value.bit_length <= 24:
            return "uint"
        elif value.bit_length <= 32:
            return "uint"
        elif value.bit_length <= 40:
            return "uint64"
        elif value.bit_length <= 48:
            return "uint64"
        elif value.bit_length <= 56:
            return "uint64"
        elif value.bit_length <= 64:
            return "uint64"
        else:
            raise RuntimeError("Bit depth above 64 bit is not supported!")
    elif isinstance(value, pydsdl.SignedIntegerType):
        if value.bit_length <= 8:
            return "int"
        elif value.bit_length <= 16:
            return "int"
        elif value.bit_length <= 24:
            return "int"
        elif value.bit_length <= 32:
            return "int"
        elif value.bit_length <= 40:
            return "int64"
        elif value.bit_length <= 48:
            return "int64"
        elif value.bit_length <= 56:
            return "int64"
        elif value.bit_length <= 64:
            return "int64"
        else:
            raise RuntimeError("Bit depth above 64 bit is not supported!")
    elif isinstance(value, pydsdl.FloatType):
        if value.bit_length <= 32:
            return "float"
        elif value.bit_length <= 64:
            return "double"
        else:
            raise RuntimeError("Bit depth above 64 bit is not supported!")
    elif isinstance(value, pydsdl.BooleanType):
        return "bool"
    else:
        raise RuntimeError("{} is not a known PrimitiveType".format(type(value).__name__))


@template_language_list_filter(__name__)
def filter_requires(
    language: Language, t: pydsdl.CompositeType, sort: bool = True
) -> typing.List[pydsdl.CompositeType]:
    return RequireGenerator(language, t).generate_require_list(sort)
