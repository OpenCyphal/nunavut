# Copyright (c) 2019 OpenCyphal
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@opencyphal.org>

from __future__ import annotations
import logging
import pydsdl
from .util import expand_service_types, make_random_object
from .conftest import GeneratedPackageInfo


_MAX_EXTENT_BYTES = 99 * 1024 ** 2
"""
Do not test data types whose extent exceeds this limit.
"""

_logger = logging.getLogger(__name__)


def test_textual(compiled: list[GeneratedPackageInfo]) -> None:
    from nunavut_support import get_attribute

    def validate(obj: object, s: str) -> None:
        for f in model.fields_except_padding:  # pylint: disable=undefined-loop-variable
            field_present = (f"{f.name}=" in s) or (f"{f.name}_=" in s)
            if isinstance(model.inner_type, pydsdl.UnionType):  # pylint: disable=undefined-loop-variable
                # In unions only the active field is printed.
                # The active field may contain nested fields which  may be named similarly to other fields
                # in the current union, so we can't easily ensure lack of non-active fields in the output.
                field_active = get_attribute(obj, f.name) is not None
                if field_active:
                    assert field_present, f"{f.name}: {s}"
            else:
                # In structures all fields are printed always.
                assert field_present, f"{f.name}: {s}"

    for info in compiled:
        for model in expand_service_types(info.models):
            if model.extent > 8 * _MAX_EXTENT_BYTES:
                _logger.info("Skipping %s due to excessive size", model)
                continue
            _logger.debug("Testing textual representation of %s...", model)
            for fn in [str, repr]:
                assert callable(fn)
                for _ in range(10):
                    ob = make_random_object(model)
                    validate(ob, fn(ob))
