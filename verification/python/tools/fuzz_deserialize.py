#!/usr/bin/env python3
# Copyright (c) 2026 OpenCyphal
# This software is distributed under the terms of the MIT License.
# type: ignore

"""
Coverage-guided fuzzing of the DSDL-generated Python deserialization code with Atheris (libFuzzer for Python).

This is meant for long local runs; CI runs the Hypothesis tests in ``suite/test_fuzz.py`` instead, which apply the same
oracle (``suite/fuzzing.py``). Run it through Nox, which generates the code, writes the seed corpus, and passes any
extra arguments to libFuzzer::

    nox -s fuzz-3.13 -- -max_total_time=3600 -jobs=8 -workers=8

Input layout: the first two bytes (big endian) select the type from the list returned by
:func:`suite.fuzzing.fuzzable_models` (modulo its length), the third byte selects the number of fragments the rest is
split into, and the rest is the serialized representation.

Extra option (consumed before libFuzzer sees the arguments): ``--write-seeds DIR`` writes valid serialized samples
of every type into DIR and exits.
"""

import os
import sys
import random
import hashlib
import numpy
import atheris

with atheris.instrument_imports(include=["nunavut_support", "uavcan", "regulated", "if_"]):
    import nunavut_support

from suite.fuzzing import fuzzable_models, check_deserialize
from suite.util import make_random_object


_SEEDS_PER_TYPE = 4

_MODELS = fuzzable_models()

with atheris.instrument_imports(include=["nunavut_support", "uavcan", "regulated", "if_"]):
    _CLASSES = [nunavut_support.get_class(m) for m in _MODELS]  # Imports (and instruments) the generated modules.


def _cuts(length: int, num_fragments: int) -> list[int]:
    return [length * i // num_fragments for i in range(1, num_fragments)]


def test_one_input(data: bytes) -> None:
    if len(data) < 3:
        return
    dtype = _CLASSES[int.from_bytes(data[:2], "big") % len(_CLASSES)]
    payload = data[3:]
    check_deserialize(dtype, payload, _cuts(len(payload), data[2] % 8 + 1))


def _write_seeds(directory: str) -> None:
    os.makedirs(directory, exist_ok=True)
    random.seed(0)
    numpy.random.seed(0)
    for index, (model, dtype) in enumerate(zip(_MODELS, _CLASSES)):
        samples = [dtype()] + [make_random_object(model) for _ in range(_SEEDS_PER_TYPE - 1)]
        for obj in samples:
            seed = index.to_bytes(2, "big") + b"\x00" + b"".join(nunavut_support.serialize(obj))
            if len(seed) > 64 * 1024:
                continue  # libFuzzer ignores large inputs anyway (see -max_len).
            check_deserialize(dtype, seed[3:])
            with open(os.path.join(directory, hashlib.sha1(seed).hexdigest()), "wb") as f:
                f.write(seed)
    print(f"Wrote seeds for {len(_MODELS)} types into {directory}")


def main() -> None:
    if len(sys.argv) >= 3 and sys.argv[1] == "--write-seeds":
        _write_seeds(sys.argv[2])
        return
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
