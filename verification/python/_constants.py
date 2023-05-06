# Copyright (c) 2019 OpenCyphal
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@opencyphal.org>

from __future__ import annotations
import pydsdl
import pytest
import nunavut_support
from ._util import expand_service_types
from .conftest import GeneratedPackageInfo


def test_constants(compiled: list[GeneratedPackageInfo]) -> None:
    for info in compiled:
        for model in expand_service_types(info.models, keep_services=True):
            dtype = nunavut_support.get_class(model)
            for c in model.constants:
                if isinstance(c.data_type, pydsdl.PrimitiveType):  # pragma: no branch
                    reference = c.value
                    generated = nunavut_support.get_attribute(dtype, c.name)
                    assert isinstance(reference, pydsdl.Primitive)
                    assert reference.native_value == pytest.approx(
                        generated
                    ), "The generated constant does not compare equal against the DSDL source"
            fpid_obj = nunavut_support.get_fixed_port_id(dtype)
            fpid_mod = nunavut_support.get_model(dtype).fixed_port_id
            assert (fpid_obj == fpid_mod) or (fpid_obj is None) or (fpid_mod is None)
