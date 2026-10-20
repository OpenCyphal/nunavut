#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Runtime tests for generating into the same output directory in several nnvg runs
(https://github.com/OpenCyphal/nunavut/issues/403). Test IDs V1 and V2 refer to the approved test plan:
https://github.com/OpenCyphal/nunavut/issues/403#issuecomment-6297320522

Each test generates into a temporary directory in separate runs, then imports the result in a fresh Python process so
that the merged packages are loaded from disk rather than from modules already imported by this process.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import nunavut


def _root_namespace_dir(name: str) -> Path:
    for entry in os.environ["NUNAVUT_VERIFICATION_DSDL_PATH"].split(os.pathsep):
        if Path(entry).name == name:
            return Path(entry)
    raise LookupError(f"Root namespace {name} is not in NUNAVUT_VERIFICATION_DSDL_PATH")


def _generate(outdir: Path, targets: list[Path], roots: list[Path]) -> None:
    nunavut.generate_all("py", targets, roots, outdir, jobs=1)


def _run_python(outdir: Path, code: str) -> None:
    env = dict(os.environ, PYTHONPATH=str(outdir))
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


_IMPORT_ALL_AND_GET_CLASS = """
import importlib
import os
from pathlib import Path
import nunavut_support

root = Path(os.environ["PYTHONPATH"])
checked = 0
for module_file in sorted(root.rglob("*_[0-9]*_[0-9]*.py")):
    module_name = ".".join(module_file.relative_to(root).with_suffix("").parts)
    module = importlib.import_module(module_name)
    cls = getattr(module, module_file.stem)
    assert nunavut_support.get_class(nunavut_support.get_model(cls)) is cls, module_name
    checked += 1
assert checked > 0
print(checked)
"""


def test_v1_types_from_every_run_are_reachable(tmp_path: Path) -> None:
    """
    The #403 reproduction at runtime: generate uavcan, then the regulated test types (which depend on uavcan), into
    the same directory. Every generated type from both runs must import and be found by get_class().
    """
    uavcan = _root_namespace_dir("uavcan")
    regulated = _root_namespace_dir("regulated")
    _generate(tmp_path, sorted(uavcan.rglob("*.dsdl")), [uavcan])
    _generate(tmp_path, sorted(regulated.rglob("*.dsdl")), [regulated, uavcan])
    _run_python(tmp_path, _IMPORT_ALL_AND_GET_CLASS)


def test_v2_newer_minor_moves_the_alias_and_keeps_the_older_binding(tmp_path: Path) -> None:
    uavcan = _root_namespace_dir("uavcan")
    node = uavcan / "node"
    _generate(tmp_path, [node / "435.ExecuteCommand.1.2.dsdl"], [uavcan])
    _generate(tmp_path, [node / "435.ExecuteCommand.1.3.dsdl"], [uavcan])
    _run_python(
        tmp_path,
        "import uavcan.node as n\n"
        "assert n.ExecuteCommand_1 is n.ExecuteCommand_1_3\n"
        "assert n.ExecuteCommand_1_2.__name__ == 'ExecuteCommand_1_2'\n",
    )
