# Copyright (c) 2026 OpenCyphal
# This software is distributed under the terms of the MIT License.

"""
The fuzzing oracle shared by the Hypothesis property tests (``test_fuzz.py``) and the optional Atheris harness
(``verification/python/tools/fuzz_deserialize.py``).

The oracle follows the documented contract of :func:`nunavut_support.deserialize`: for an invalid serialized
representation it returns None and never raises. Any exception it raises (including a failed assertion inside the
generated code) is a defect in the generated code or in the support library. If it returns an object, that object
has to survive a serialize/deserialize round trip unchanged.
"""

from __future__ import annotations
from typing import Any, Sequence
import pydsdl
from .util import expand_service_types, are_close
from .conftest import read_generated_packages


MAX_FUZZ_SERIALIZED_BYTES = 1024**2
"""
Types whose serialized representation can be larger than this are not fuzzed because every deserialization of them
allocates the whole object (fixed-length arrays are zero-extended), which makes each fuzz iteration far too slow.
"""


def fuzzable_models() -> list[pydsdl.CompositeType]:
    """
    All non-service composite types from the namespaces listed in ``NUNAVUT_VERIFICATION_DSDL_PATH``
    (service types are expanded into their request and response types), in a stable order.
    """
    out: list[pydsdl.CompositeType] = []
    for info in read_generated_packages():
        for model in expand_service_types(info.models):
            if max_serialized_bytes(model) <= MAX_FUZZ_SERIALIZED_BYTES:
                out.append(model)
    return sorted(out, key=str)


def max_serialized_bytes(model: pydsdl.CompositeType) -> int:
    return int(model.bit_length_set.max + 7) // 8


def fragment(data: bytes, cuts: Sequence[int]) -> list[memoryview]:
    """
    Splits the data into writeable memoryview fragments at the given offsets (clamped into the valid range,
    duplicates allowed, which yields empty fragments).
    """
    buf = memoryview(bytearray(data))
    bounds = [0, *sorted(min(max(c, 0), len(data)) for c in cuts), len(data)]
    return [buf[a:b] for a, b in zip(bounds, bounds[1:])]


def check_deserialize(dtype: type, data: bytes, cuts: Sequence[int] = ()) -> Any:
    """
    Runs the deserialization oracle on one input. Raises on any contract violation; returns the deserialized object
    or None if the input was rejected.
    """
    from nunavut_support import deserialize, get_model

    model = get_model(dtype)
    obj = deserialize(dtype, fragment(data, cuts))  # Must not raise, no matter the input.
    if cuts:  # Fragmentation must not affect the outcome.
        whole = deserialize(dtype, fragment(data, ()))
        assert (obj is None) == (whole is None), f"fragmentation changed the outcome: {obj!r} vs {whole!r}"
        assert obj is None or are_close(model, obj, whole), f"fragmentation changed the result: {obj!r} vs {whole!r}"
    if obj is None:
        return None
    assert type(obj) is dtype, f"{type(obj)} is not {dtype}"  # pylint: disable=unidiomatic-typecheck
    check_roundtrip(obj)
    return obj


def check_roundtrip(obj: Any, cuts: Sequence[int] = ()) -> bytes:
    """
    Serializes the object, checks the length against the type's bit length set, deserializes it back (optionally
    fragmented), and checks that the result equals the original and that it serializes into the same bytes.
    Returns the serialized representation.
    """
    from nunavut_support import serialize, deserialize, get_model

    model = get_model(obj)
    sr = b"".join(serialize(obj))
    assert len(sr) <= max_serialized_bytes(model), f"{len(sr)} bytes exceeds the maximum of {model}"
    back = deserialize(type(obj), fragment(sr, cuts))
    assert back is not None, f"{obj!r} serialized into {sr.hex()} that does not deserialize"
    assert are_close(model, obj, back), f"{obj!r} != {back!r}; sr: {sr.hex()}"
    sr_back = b"".join(serialize(back))
    assert sr_back == sr, f"serialization is not stable for {obj!r}: {sr.hex()} != {sr_back.hex()}"
    return sr
