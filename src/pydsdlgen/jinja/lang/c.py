#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    jinja-based filters for generating C. All filters in this
    module will be available in the template's global namespace as ``c``.
"""

from enum import Enum, unique
from typing import TypeVar, Type

from pydsdlgen.jinja.jinja2 import TemplateRuntimeError
from pydsdl.data_type import (PrimitiveType, SignedIntegerType,
                              UnsignedIntegerType, FloatType, BooleanType)


def filter_macrofy(value: str) -> str:
    """
        Filter to transform an input into a valid C preprocessor identifier token.

        The following example assumes a string "my full name" as ``full_name``.

        Example::

            #ifndef {{T.full_name | c.macrofy}}

        Result Example::

            #ifndef MY_FULL_NAME

        :param str value: The value to transform.

        :returns: A valid C preprocessor identifier token.
    """
    return value.replace(' ', '_').replace('.', '_').upper()


_CFit_T = TypeVar('_CFit_T', bound='_CFit')


@unique
class _CFit(Enum):
    IN_8 = 8
    IN_16 = 16
    IN_32 = 32
    IN_64 = 64

    def to_std_int(self, is_signed: bool) -> str:
        return "{}int{}_t".format(('' if is_signed else 'u'), self.value)

    def to_c_int(self, is_signed: bool) -> str:
        if self.value == 8:
            intname = 'char'
        elif self.value == 16:
            intname = 'int'
        elif self.value == 32:
            intname = 'long'
        else:
            intname = 'long long'

        if not is_signed:
            intname = 'unsigned' + intname

        return intname

    def to_c_float(self) -> str:
        if self.value == 8 or self.value == 16 or self.value == 32:
            return 'float'
        else:
            return 'double'

    def to_c_type(self, value: PrimitiveType, use_standard_types: bool = True) -> str:
        if isinstance(value, UnsignedIntegerType):
            return (self.to_c_int(False) if not use_standard_types else self.to_std_int(False))
        elif isinstance(value, SignedIntegerType):
            return (self.to_c_int(True) if not use_standard_types else self.to_std_int(True))
        elif isinstance(value, FloatType):
            return self.to_c_float()
        elif isinstance(value, BooleanType):
            return ('BOOL' if not use_standard_types else 'bool')
        else:
            raise TemplateRuntimeError("{} is not a known PrimitiveType".format(type(value).__name__))

    @classmethod
    def get_best_fit(cls: Type[_CFit_T], bit_length: int) -> _CFit_T:
        if bit_length <= 8:
            bestfit = _CFit.IN_8
        elif bit_length <= 16:
            bestfit = _CFit.IN_16
        elif bit_length <= 32:
            bestfit = _CFit.IN_32
        elif bit_length <= 64:
            bestfit = _CFit.IN_64
        else:
            raise TemplateRuntimeError(
                "Cannot emit a standard type for a primitive that is larger than 64 bits ({}).".format(
                        bit_length
                    )
                )
        return cls(bestfit)


def filter_type_from_primitive(value: PrimitiveType, use_standard_types: bool = True) -> str:
    """
        Filter to transform a pydsdl :class:`~pydsdl.data_type.PrimitiveType` into
        a valid C type.

        The following example assumes that data_type is of :class:`~.pydsdl.data_type.UnsignedIntegerType`
        and has a 32 bit length.

        Example::

            {{ field.data_type | c.type_from_primitive(use_standard_types=True) }} std_{{ field.name }};
            {{ field.data_type | c.type_from_primitive(use_standard_types=False) }} c_{{ field.name }};

        Result Example::

            uint32_t std_foo;
            unsigned long c_foo;

        :param str value: The dsdl primitive to transform.

        :returns: A valid C99 type name.

        :raises TemplateRuntimeError: If the primitive cannot be represented as a standard C type.
    """
    return _CFit.get_best_fit(value.bit_length).to_c_type(value, use_standard_types)
