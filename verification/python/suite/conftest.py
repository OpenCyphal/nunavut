# Copyright (c) 2019 OpenCyphal
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@opencyphal.org>

from __future__ import annotations
import os
import sys
from typing import Sequence, Any
import dataclasses
from pathlib import Path
import logging
import pytest
import pydsdl


# Please maintain these carefully if you're changing the project's directory structure.
SELF_DIR = Path(__file__).resolve().parent
VERIFICATION_DIR = SELF_DIR.parent.parent
ROOT_DIR = VERIFICATION_DIR.parent
PUBLIC_REGULATED_DATA_TYPES_DIR = ROOT_DIR / "submodules" / "public_regulated_data_types"
TEST_TYPES_DIR = VERIFICATION_DIR / "nunavut_test_types"
COMPILE_OUTPUT_DIR = (Path.cwd() / "nunavut_out").resolve()


@dataclasses.dataclass(frozen=True)
class GeneratedPackageInfo:
    models: Sequence[pydsdl.CompositeType]
    """
    List of PyDSDL objects describing the source DSDL definitions.
    This can be used for arbitrarily complex introspection and reflection.
    """


@pytest.fixture(scope="session", autouse=True)  # Enable autouse to ensure that generated DSDL are usable in doctests.
def compiled() -> list[GeneratedPackageInfo]:
    """
    Runs the DSDL package generator against the standard and test namespaces and emits a GeneratedPackageInfo
    per namespace.
    Automatically adds the path to the generated packages to sys path to make them importable.
    """
    if str(COMPILE_OUTPUT_DIR) not in sys.path:
        sys.path.insert(0, str(COMPILE_OUTPUT_DIR))
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
        args = [str(nsd), "--target-language=py", "--outdir", str(COMPILE_OUTPUT_DIR)]
        _run_nnvg(
            args,
            env={
                "DSDL_INCLUDE_PATH": os.pathsep.join(map(str, root_namespace_directories)),
            },
        )
        out.append(GeneratedPackageInfo(models=composite_types))
    return out


def pytest_configure(config: Any) -> None:
    """
    See https://docs.pytest.org/en/6.2.x/reference.html#initialization-hooks
    """
    del config
    logging.getLogger("pydsdl").setLevel(logging.INFO)


def _run_nnvg(args: list[str], env: dict[str, str] | None = None) -> None:
    """Helper to invoke nnvg for unit testing within the proper python coverage wrapper."""
    import subprocess

    coverage_args = ["coverage", "run", "--parallel-mode", "-m", "nunavut"]
    this_env = os.environ.copy()
    if env is not None:
        this_env.update(env)
    subprocess.check_call(coverage_args + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=this_env)
