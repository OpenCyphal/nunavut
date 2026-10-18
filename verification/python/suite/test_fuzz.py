# Copyright (c) 2026 OpenCyphal
# This software is distributed under the terms of the MIT License.

"""
Property-based fuzzing of the generated (de)serialization code using Hypothesis.

Unlike ``test_rand.py``, which feeds uniformly random bytes that rarely get past a length prefix, a union tag, or a
delimiter header, the inputs here are mostly valid serialized representations generated from the DSDL model and then
mutated (bit flips, interesting byte values, truncation, extension, insertion, deletion), so the decoders are exercised
past their first few checks. Every input is also split into fragments at arbitrary offsets.

The number of examples per type and per test is small by default to keep CI fast. For a longer local run, set the
environment variable ``NUNAVUT_PYTHON_FUZZ_EXAMPLES`` (and optionally select types with ``-k``)::

    NUNAVUT_PYTHON_FUZZ_EXAMPLES=20000 nox -s test-3.13 -- -k "test_fuzz and Heartbeat"

Failing examples are saved in the Hypothesis database (``.hypothesis/``) and replayed first on the next run.
"""

from __future__ import annotations
import os
import struct
import functools
import dataclasses
from typing import Any
import pydsdl
import pytest
from hypothesis import given, settings, HealthCheck, strategies as st
from .fuzzing import fuzzable_models, max_serialized_bytes, check_deserialize, check_roundtrip


_NUM_EXAMPLES = int(os.environ.get("NUNAVUT_PYTHON_FUZZ_EXAMPLES", 20))
"""
Number of Hypothesis examples per type and per test. Raise this for a deeper exploration.
"""

_MAX_LIST_LENGTH = 32
"""
Arrays longer than this are generated as a short random prefix followed by a repeated element,
which keeps the generation fast while still reaching the capacity limits.
"""

_MAX_RAW_BYTES = 4096
"""
The upper size limit of the unstructured byte inputs.
"""

_SETTINGS = settings(
    max_examples=_NUM_EXAMPLES,
    deadline=None,  # The CI machines are too noisy for the per-example deadline to be useful.
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large, HealthCheck.large_base_example],
)


@dataclasses.dataclass(frozen=True)
class FuzzInput:
    """A serialized representation and the offsets at which it is to be fragmented."""

    data: bytes
    cuts: tuple[int, ...] = ()


def pytest_generate_tests(metafunc: Any) -> None:
    if "model" in metafunc.fixturenames:
        models = fuzzable_models()
        metafunc.parametrize("model", models, ids=list(map(str, models)))


@_SETTINGS
@given(data=st.data())
def test_fuzz_roundtrip(model: pydsdl.CompositeType, data: st.DataObject) -> None:
    """
    Forward test: a valid object must serialize, and deserialize back into an equal object, however the
    serialized representation is fragmented.
    """
    obj = data.draw(objects(model), label="object")
    sr_length = max_serialized_bytes(model)
    cuts = data.draw(st.lists(st.integers(0, sr_length), max_size=8), label="cuts")
    check_roundtrip(obj, cuts)


@_SETTINGS
@given(data=st.data())
def test_fuzz_deserialize(model: pydsdl.CompositeType, data: st.DataObject) -> None:
    """
    Reverse test: an arbitrary (mostly almost-valid) input must either be rejected with None
    or deserialize into an object that round-trips.
    """
    from nunavut_support import get_class

    check_deserialize(get_class(model), *dataclasses.astuple(data.draw(inputs(model), label="input")))


def test_fuzz_deserialize_edge_cases(model: pydsdl.CompositeType) -> None:
    """
    Deterministic inputs that the random generation is unlikely to produce together:
    every truncation of the default object, and runs of all-zero and all-one bytes around the maximum length.
    """
    from nunavut_support import get_class, serialize

    dtype = get_class(model)
    default_sr = b"".join(serialize(dtype()))
    for n in range(len(default_sr) + 1):
        check_deserialize(dtype, default_sr[:n])
    max_bytes = max_serialized_bytes(model)
    for length in {0, 1, 2, 8, max_bytes - 1, max_bytes, max_bytes + 1}:
        for fill in (b"\x00", b"\xff", b"\x55", b"\xaa"):
            if length >= 0:
                check_deserialize(dtype, fill * length, (length // 2,))


def test_nested_delimited_longer_than_extent() -> None:
    """
    Regression test for a defect found by fuzzing: a delimiter header may specify more bytes than the extent of the
    nested type, and the excess is skipped (implicit truncation), so the outer object may consume more than the
    maximum of its bit length set. The generated code used to fail an assertion on that instead of returning
    the object.
    """
    from regulated.delimited import BSealed_1_0
    from nunavut_support import deserialize, get_model

    nested = bytes([2, 0x11, 0x22, 0xFE]) + b"\xaa" * 36  # CVariable.1.0 with 36 trailing bytes; its extent is 4.
    sr = bytes([1]) + len(nested).to_bytes(4, "little") + nested + bytes([0])
    assert len(sr) * 8 > get_model(BSealed_1_0).bit_length_set.max
    obj = deserialize(BSealed_1_0, [memoryview(bytearray(sr))])
    assert obj is not None
    assert len(obj.var) == 1 and list(obj.var[0].a) == [0x11, 0x22] and obj.var[0].b == -2
    assert len(obj.fix) == 0
    assert check_deserialize(BSealed_1_0, sr) is not None
    assert check_roundtrip(obj) == bytes([1, 4, 0, 0, 0, 2, 0x11, 0x22, 0xFE, 0])


def test_serialize_numpy_integer_scalars() -> None:
    """
    Regression test for a defect found by fuzzing with NumPy 2: elements of arrays of non-standard-width signed
    integers are NumPy scalars, and under the NEP 50 promotion rules the bit manipulation in the support library
    overflowed on them.
    """
    from regulated.basics import PrimitiveArrayFixed_0_1

    obj = PrimitiveArrayFixed_0_1()
    obj.a_i7 = [-64, 63]
    obj.n_i7 = [0, -1]
    check_roundtrip(obj)


def test_fuzz_oracle() -> None:
    """
    Make sure the oracle can actually detect a contract violation.
    """
    from nunavut_support import get_class
    from .fuzzing import fragment

    assert [bytes(x) for x in fragment(b"abcdef", (4, 2, 2, 99))] == [b"ab", b"", b"cd", b"ef", b""]

    class _Broken(get_class(fuzzable_models()[0])):  # type: ignore
        @staticmethod
        def _deserialize_(_: Any) -> None:
            raise IndexError("out of range")

    with pytest.raises(IndexError):
        check_deserialize(_Broken, b"")


# ----------------------------------------  STRATEGIES  ----------------------------------------


def inputs(model: pydsdl.CompositeType) -> st.SearchStrategy[FuzzInput]:
    """
    Serialized representations of the model: mostly valid ones with a few mutations applied,
    sometimes plain random bytes, fragmented at random offsets.
    """
    valid = objects(model).map(check_roundtrip)
    max_bytes = max_serialized_bytes(model)
    raw = st.binary(max_size=min(max_bytes + 8, _MAX_RAW_BYTES))
    data = st.one_of(_mutated(valid), valid, raw)
    return data.flatmap(
        lambda d: st.builds(FuzzInput, st.just(d), st.lists(st.integers(0, len(d)), max_size=8).map(tuple))
    )


_INTERESTING_BYTES = [0x00, 0x01, 0x7F, 0x80, 0xFE, 0xFF]


@st.composite
def _mutated(draw: st.DrawFn, base: st.SearchStrategy[bytes]) -> bytes:
    data = bytearray(draw(base))
    for _ in range(draw(st.integers(1, 4))):
        op = draw(st.sampled_from(["flip", "set", "length", "truncate", "extend", "insert", "delete"]))
        index = draw(st.integers(0, len(data)))
        if op == "flip" and data:
            data[index % len(data)] ^= 1 << draw(st.integers(0, 7))
        elif op == "set" and data:
            data[index % len(data)] = draw(st.sampled_from(_INTERESTING_BYTES) | st.integers(0, 255))
        elif op == "length":  # Overwrite what may be a length prefix or a delimiter header and back it up with data.
            width = draw(st.sampled_from([1, 2, 4]))
            candidates = [  # Places that hold a small little-endian number are likely length fields.
                i for i in range(len(data) - width + 1) if int.from_bytes(data[i : i + width], "little") <= len(data)
            ]
            if candidates:
                index = draw(st.sampled_from(candidates))
            length = draw(st.integers(0, min(2 ** (8 * width) - 1, 256)))
            data[index : index + width] = length.to_bytes(width, "little")
            data += bytes(length)
        elif op == "truncate":
            del data[index:]
        elif op == "extend":
            data += draw(st.binary(min_size=1, max_size=16))
        elif op == "insert":
            data[index:index] = draw(st.binary(min_size=1, max_size=4))
        elif op == "delete":
            del data[index : index + draw(st.integers(1, 4))]
    return bytes(data)


@functools.cache
def objects(model: pydsdl.CompositeType) -> st.SearchStrategy[Any]:
    """
    Instances of the DSDL-generated class of the composite type populated with arbitrary valid values.
    """
    from nunavut_support import get_class, set_attribute

    dtype = get_class(model)

    def construct(field_values: dict[str, Any]) -> Any:
        obj = dtype()
        for name, value in field_values.items():
            set_attribute(obj, name, value)
        return obj

    if isinstance(model, pydsdl.UnionType):  # Select one field, then populate it.
        variants = [st.fixed_dictionaries({f.name: _values(f.data_type)}).map(construct) for f in model.fields]
        return st.one_of(variants)
    if isinstance(model, pydsdl.DelimitedType):
        return objects(model.inner_type)
    return st.fixed_dictionaries({f.name: _values(f.data_type) for f in model.fields_except_padding}).map(construct)


def _values(ty: pydsdl.SerializableType) -> st.SearchStrategy[Any]:
    if isinstance(ty, pydsdl.CompositeType):
        return objects(ty)
    if isinstance(ty, pydsdl.BooleanType):
        return st.booleans()
    if isinstance(ty, pydsdl.IntegerType):
        rng = ty.inclusive_value_range
        return st.integers(int(rng.min), int(rng.max))
    if isinstance(ty, pydsdl.FloatType):  # Arbitrary bit patterns including all NaN payloads, infinities, subnormals.
        fmt = {16: ("<H", "<e"), 32: ("<I", "<f"), 64: ("<Q", "<d")}[ty.bit_length]
        return st.integers(0, 2**ty.bit_length - 1).map(lambda x: struct.unpack(fmt[1], struct.pack(fmt[0], x))[0])
    if isinstance(ty, pydsdl.ArrayType):
        et = ty.element_type
        if isinstance(ty, pydsdl.FixedLengthArrayType):
            min_length, max_length = ty.capacity, ty.capacity
        else:
            min_length, max_length = 0, ty.capacity
        if isinstance(et, pydsdl.UnsignedIntegerType) and et.bit_length == 8:
            out: st.SearchStrategy[Any] = st.binary(min_size=min_length, max_size=max_length)
            if ty.string_like:
                out = out | st.text(max_size=max_length // 4)
            return out
        return _lists(_values(et), min_length, max_length)
    raise TypeError(f"Unsupported type: {ty}")  # pragma: no cover


def _lists(elements: st.SearchStrategy[Any], min_length: int, max_length: int) -> st.SearchStrategy[list[Any]]:
    if max_length <= _MAX_LIST_LENGTH:
        return st.lists(elements, min_size=min_length, max_size=max_length)

    def pad(prefix: list[Any], filler: Any, length: int) -> list[Any]:
        return (prefix + [filler] * length)[:length]

    long = st.builds(
        pad,
        st.lists(elements, max_size=_MAX_LIST_LENGTH),
        elements,
        st.sampled_from([min_length, max_length]) | st.integers(min_length, max_length),
    )
    if min_length > _MAX_LIST_LENGTH:
        return long
    return st.lists(elements, min_size=min_length, max_size=_MAX_LIST_LENGTH) | long
