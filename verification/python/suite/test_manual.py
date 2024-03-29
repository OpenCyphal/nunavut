# Copyright (c) 2019 OpenCyphal
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@opencyphal.org>

from __future__ import annotations
import logging
import numpy
import pytest
from .conftest import GeneratedPackageInfo


_logger = logging.getLogger(__name__)


def test_manual_assignment(compiled: list[GeneratedPackageInfo]) -> None:
    from uavcan.primitive import Unstructured_1_0 as Un, String_1_0 as St

    del compiled

    ob1 = Un(memoryview(b"Hello world"))
    assert ob1.value.tobytes().decode() == "Hello world"

    ob2 = St(memoryview(b"Hello world"))
    assert ob2.value.tobytes().decode() == "Hello world"


def test_manual_del(compiled: list[GeneratedPackageInfo]) -> None:
    from nunavut_support import deserialize, get_attribute, set_attribute
    import if_

    del compiled

    # Implicit zero extension
    ize = deserialize(if_.del_1_0, [memoryview(b"")])
    assert ize is not None
    assert repr(ize) == repr(if_.del_1_0())

    obj = deserialize(
        if_.del_1_0,
        _compile_serialized_representation(
            # void8
            "00000000"
            # B union, second field C.1.0[<=2] y
            "00000001"
            "00000010"  # length 2 elements
            # First element C.1.0
            "00000001"  # second field selected uint1 y
            "00000111"  # y = 7
            # Second element C.1.0
            "00000000"  # first field selected uint1 x
            "00000101"  # x = 5
            # B union, first field C.1.0[2] x
            "00000000"
            # First element C.1.0
            "00000000"  # first field selected uint1 x
            "00001000"  # x = 8
            # Second element C.1.0
            "00000001"  # second field selected uint1 y
            "00001101"  # y = 13
            # empty B.1.0[<=2] y
            "00000000"
        ),
    )
    assert obj is not None
    assert obj.else_[0].x is None
    assert obj.else_[0].y is not None
    assert len(obj.else_[0].y) == 2
    assert obj.else_[0].y[0].x is None
    assert obj.else_[0].y[0].y == 7
    assert obj.else_[0].y[1].x == 5
    assert obj.else_[0].y[1].y is None
    assert obj.else_[1].x is not None
    assert obj.else_[1].y is None
    assert obj.else_[1].x[0].x == 8
    assert obj.else_[1].x[0].y is None
    assert obj.else_[1].x[1].x is None
    assert obj.else_[1].x[1].y == 13
    assert len(obj.raise_) == 0

    with pytest.raises(AttributeError, match="nonexistent"):
        get_attribute(obj, "nonexistent")

    with pytest.raises(AttributeError, match="nonexistent"):
        set_attribute(obj, "nonexistent", 123)


def test_manual_heartbeat(compiled: list[GeneratedPackageInfo]) -> None:
    from nunavut_support import deserialize, get_attribute, set_attribute
    import uavcan.node

    del compiled

    # Implicit zero extension
    ize = deserialize(uavcan.node.Heartbeat_1_0, [memoryview(b"")])
    assert ize is not None
    assert repr(ize) == repr(uavcan.node.Heartbeat_1_0())
    assert ize.uptime == 0
    assert ize.vendor_specific_status_code == 0

    obj = deserialize(
        uavcan.node.Heartbeat_1_0,
        _compile_serialized_representation(
            _bin(0xEFBE_ADDE, 32),  # uptime dead beef in little-endian byte order
            "00000010",  # health caution
            "00000001",  # mode initialization
            "10101111",  # vendor-specific
        ),
    )
    assert obj is not None
    assert obj.uptime == 0xDEADBEEF
    assert obj.health.value == uavcan.node.Health_1_0.CAUTION
    assert obj.mode.value == uavcan.node.Mode_1_0.INITIALIZATION
    assert obj.vendor_specific_status_code == 0b10101111

    with pytest.raises(AttributeError, match="nonexistent"):
        get_attribute(obj, "nonexistent")

    with pytest.raises(AttributeError, match="nonexistent"):
        set_attribute(obj, "nonexistent", 123)


def test_minor_alias(compiled: list[GeneratedPackageInfo]) -> None:
    from regulated.delimited import BDelimited_1, BDelimited_1_1, BDelimited_1_0

    del compiled
    assert BDelimited_1 is not BDelimited_1_0  # type: ignore
    assert BDelimited_1 is BDelimited_1_1


def test_delimited(compiled: list[GeneratedPackageInfo]) -> None:
    from nunavut_support import serialize, deserialize
    from regulated.delimited import A_1_0, A_1_1, BDelimited_1_0, BDelimited_1_1
    from regulated.delimited import CFixed_1_0, CFixed_1_1, CVariable_1_0, CVariable_1_1

    del compiled

    def u8(x: int) -> bytes:
        return int(x).to_bytes(1, "little")

    def u32(x: int) -> bytes:
        return int(x).to_bytes(4, "little")

    # Serialize first and check against the reference.
    o = A_1_0(
        del_=BDelimited_1_0(
            var=[CVariable_1_0([1, 2]), CVariable_1_0([3], 4)],
            fix=[CFixed_1_0([5, 6])],
        ),
    )
    print("object below:\n", o)
    sr = b"".join(serialize(o))
    del o
    # fmt: off
    ref = (
        u8(1)               # | Union tag of del
        + u32(23)           # |     Delimiter header of BDelimited.1.0 del
        + u8(2)             # |         Array var contains two elements
        + u32(4)            # |             Delimiter header of the first array element
        + u8(2)             # |                 Array a contains 2 elements
        + u8(1) + u8(2)     # |                     This is the array a
        + u8(0)             # |                 Field b left uninitialized
        + u32(3)            # |             Delimiter header of the second array element
        + u8(1)             # |                 Array a contains 1 element
        + u8(3)             # |                     This is the array a
        + u8(4)             # |                     Field b
        + u8(1)             # |         Array fix contains one element
        + u32(2)            # |             Delimiter header of the only array element
        + u8(5) + u8(6)     # |                 This is the array a
    )
    # fmt: on
    print(" ".join(f"{b:02x}" for b in sr))
    assert sr == ref

    # Deserialize using a DIFFERENT MINOR VERSION which requires the implicit zero extension/truncation rules to work.
    q = deserialize(A_1_1, [memoryview(sr)])
    assert q
    assert q.del_ is not None
    assert len(q.del_.var) == 2
    assert len(q.del_.fix) == 1
    assert list(q.del_.var[0].a) == [1, 2]
    assert list(q.del_.var[1].a) == [3]  # b is implicitly truncated
    assert list(q.del_.fix[0].a) == [5, 6, 0]  # 3rd is implicitly zero-extended
    assert q.del_.fix[0].b == 0  # b is implicitly zero-extended

    # Reverse version switch.
    q = A_1_1(
        del_=BDelimited_1_1(
            var=[CVariable_1_1([11, 22])],
            fix=[CFixed_1_1([5, 6, 7], 8), CFixed_1_1([100, 200, 123], 99)],
        ),
    )
    sr = b"".join(serialize(q))
    del q
    print(" ".join(f"{b:02x}" for b in sr))
    p = deserialize(A_1_0, [memoryview(sr)])
    assert p
    assert p.del_ is not None
    assert len(p.del_.var) == 1
    assert len(p.del_.fix) == 2
    assert list(p.del_.var[0].a) == [11, 22]
    assert p.del_.var[0].b == 0  # b is implicitly zero-extended
    assert list(p.del_.fix[0].a) == [5, 6]  # 3rd is implicitly truncated, b is implicitly truncated
    assert list(p.del_.fix[1].a) == [100, 200]  # 3rd is implicitly truncated, b is implicitly truncated

    # Delimiter header too large.
    assert None is deserialize(A_1_1, [memoryview(b"\x01" + b"\xFF" * 4)])


def _compile_serialized_representation(*binary_chunks: str) -> list[memoryview]:
    s = "".join(binary_chunks)
    s = s.ljust(len(s) + 8 - len(s) % 8, "0")
    assert len(s) % 8 == 0
    byte_sized_chunks = [s[i : i + 8] for i in range(0, len(s), 8)]
    byte_list = list(map(lambda x: int(x, 2), byte_sized_chunks))
    out = numpy.array(byte_list, dtype=numpy.uint8)
    _logger.debug("Constructed serialized representation: %r --> %s", binary_chunks, out)
    return [out.data]


def _bin(value: int, width: int) -> str:
    out = bin(value)[2:].zfill(width)
    assert len(out) == width, f"Value is too wide: {bin(value)} is more than {width} bits wide"
    return out
