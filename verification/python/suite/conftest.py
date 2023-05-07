# Copyright (c) 2019 OpenCyphal
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@opencyphal.org>

from __future__ import annotations
import os
import sys
from typing import Sequence, Callable, Any
import dataclasses
from pathlib import Path
import pytest
import pydsdl


# Please maintain these carefully if you're changing the project's directory structure.
SELF_DIR = Path(__file__).resolve().parent
VERIFICATION_DIR = SELF_DIR.parent.parent
ROOT_DIR = VERIFICATION_DIR.parent
PUBLIC_REGULATED_DATA_TYPES_DIR = ROOT_DIR / "submodules" / "public_regulated_data_types"
TEST_TYPES_DIR = VERIFICATION_DIR / "nunavut_test_types"


@dataclasses.dataclass(frozen=True)
class GeneratedPackageInfo:
    models: Sequence[pydsdl.CompositeType]
    """
    List of PyDSDL objects describing the source DSDL definitions.
    This can be used for arbitrarily complex introspection and reflection.
    """


@pytest.fixture()
def compiled(run_nnvg: Callable[..., Any], gen_paths: Any) -> list[GeneratedPackageInfo]:
    """
    Runs the DSDL package generator against the standard and test namespaces and emits a GeneratedPackageInfo
    per namespace.
    Automatically adds the path to the generated packages to sys path to make them importable.
    """
    print("DSDL GENERATION OUTPUT:", gen_paths.out_dir)
    if str(gen_paths.out_dir) not in sys.path:  # pragma: no cover
        sys.path.insert(0, str(gen_paths.out_dir))

    out: list[GeneratedPackageInfo] = []
    root_namespace_directories = [
        PUBLIC_REGULATED_DATA_TYPES_DIR / "uavcan",
        TEST_TYPES_DIR / "test0" / "regulated",
        TEST_TYPES_DIR / "test0" / "if",
    ]
    for nsd in root_namespace_directories:
        nsd = Path(nsd).resolve()
        composite_types = pydsdl.read_namespace(
            root_namespace_directory=str(nsd),
            lookup_directories=list(map(str, root_namespace_directories)),
        )
        if not composite_types:
            continue
        args = [str(nsd), "--target-language=py", "--outdir", str(gen_paths.out_dir)]
        run_nnvg(
            gen_paths,
            args,
            env={
                "DSDL_INCLUDE_PATH": os.pathsep.join(map(str, root_namespace_directories)),
            },
        )
        out.append(GeneratedPackageInfo(models=composite_types))
    return out
