# Copyright (c) 2019 OpenCyphal
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@opencyphal.org>

from __future__ import annotations
import os
import sys
import pickle
from typing import Sequence, Iterable
import shutil
import logging
import importlib
import dataclasses
from pathlib import Path
import subprocess
import pytest
import pydsdl


# Please maintain these carefully if you're changing the project's directory structure.
SELF_DIR = Path(__file__).resolve().parent
VERIFICATION_DIR = SELF_DIR.parent
ROOT_DIR = VERIFICATION_DIR.parent
PUBLIC_REGULATED_DATA_TYPES_DIR = ROOT_DIR / "submodules" / "public_regulated_data_types"
TEST_TYPES_DIR = VERIFICATION_DIR / "nunavut_test_types"
DESTINATION_DIR = Path.cwd().resolve() / ".generated.python"

_CACHE_FILE_NAME = "pydsdl_cache.pickle.tmp"


@dataclasses.dataclass(frozen=True)
class GeneratedPackageInfo:
    models: Sequence[pydsdl.CompositeType]
    """
    List of PyDSDL objects describing the source DSDL definitions.
    This can be used for arbitrarily complex introspection and reflection.
    """


@pytest.fixture(scope="session")
def compiled() -> list[GeneratedPackageInfo]:
    """
    Runs the DSDL package generator against the standard and test namespaces, emits a list of GeneratedPackageInfo.
    Automatically adds the path to the generated packages to sys path to make them importable.
    The output is cached permanently on disk in a file in the output directory.
    To force regeneration, remove the generated package directories.
    """
    if str(DESTINATION_DIR) not in sys.path:  # pragma: no cover
        sys.path.insert(0, str(DESTINATION_DIR))
    importlib.invalidate_caches()
    cache_file = DESTINATION_DIR / _CACHE_FILE_NAME

    if DESTINATION_DIR.exists():  # pragma: no cover
        if cache_file.exists():
            with open(cache_file, "rb") as f:
                out = pickle.load(f)
            assert out and isinstance(out, list)
            assert all(map(lambda x: isinstance(x, GeneratedPackageInfo), out))
            return out

        shutil.rmtree(DESTINATION_DIR, ignore_errors=True)
    DESTINATION_DIR.mkdir(parents=True, exist_ok=True)

    pydsdl_logger = logging.getLogger("pydsdl")
    pydsdl_logging_level = pydsdl_logger.level
    try:
        pydsdl_logger.setLevel(logging.INFO)
        out = _compile_all(
            [
                PUBLIC_REGULATED_DATA_TYPES_DIR / "uavcan",
                TEST_TYPES_DIR / "if",
                TEST_TYPES_DIR / "numpy",
                TEST_TYPES_DIR / "test0",
            ],
        )
    finally:
        pydsdl_logger.setLevel(pydsdl_logging_level)

    with open(cache_file, "wb") as f:
        pickle.dump(out, f)

    assert out and isinstance(out, list)
    assert all(map(lambda x: isinstance(x, GeneratedPackageInfo), out))
    return out


def _compile(
    root_namespace_directory: Path | str, lookup_directories: list[Path | str] | None = None
) -> GeneratedPackageInfo | None:
    root_namespace_directory = Path(root_namespace_directory).resolve()
    composite_types = pydsdl.read_namespace(
        root_namespace_directory=str(root_namespace_directory),
        lookup_directories=list(map(str, lookup_directories or [])),
    )
    if not composite_types:
        return None
    args = ["nnvg", str(root_namespace_directory), "--target-language=py", "--outdir", str(DESTINATION_DIR)]
    subprocess.check_call(
        args,
        env={
            "DSDL_INCLUDE_PATH": os.pathsep.join(map(str, lookup_directories or [])),
        },
    )
    return GeneratedPackageInfo(models=composite_types)


def _compile_all(root_namespace_directories: Iterable[Path | str]) -> list[GeneratedPackageInfo]:
    out: list[GeneratedPackageInfo] = []
    root_namespace_directories = list(root_namespace_directories)
    for nsd in root_namespace_directories:
        gpi = _compile(nsd, root_namespace_directories)
        if gpi is not None:
            out.append(gpi)
    return out
