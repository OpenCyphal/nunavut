#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Checks the CMake package in a built Nunavut wheel (#422). Installs the wheel into a new virtual environment, then
configures and builds the project in this folder with ``Nunavut_DIR=$(python -m nunavut --cmake-dir)``::

    python3 test/cmake_installed/check_installed_package.py <nunavut wheel> <empty work folder>

"""

import argparse
import json
import os
import subprocess
import sys
import venv
from pathlib import Path
from typing import Any, List

PROJECT_DIR = Path(__file__).resolve().parent


def _run(args: List[Any], check: bool = True, **kwargs: Any) -> "subprocess.CompletedProcess[str]":
    args = [str(arg) for arg in args]
    print("$ " + " ".join(args), flush=True)
    # An installed Nunavut must work without PYTHONPATH.
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    return subprocess.run(args, check=check, text=True, env=env, **kwargs)


def _new_venv_python(env_dir: Path, with_pip: bool) -> Path:
    venv.create(env_dir, with_pip=with_pip)
    return env_dir / "bin" / "python"


def _fail(message: str) -> None:
    sys.exit(f"FAILED: {message}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("work_dir", type=Path)
    args = parser.parse_args()
    work_dir = args.work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    if any(work_dir.iterdir()):
        _fail(f"{work_dir} is not empty")

    python = _new_venv_python(work_dir / "venv-nunavut", with_pip=True)
    _run([python, "-m", "pip", "install", "--quiet", args.wheel.resolve()])
    cmake_dir = _run([python, "-m", "nunavut", "--cmake-dir"], capture_output=True).stdout.strip()
    nunavut_dir = f"-DNunavut_DIR={cmake_dir}"

    # Generate and build with the Python that Nunavut is installed in.
    build_dir = work_dir / "build"
    _run(["cmake", "-S", PROJECT_DIR, "-B", build_dir, nunavut_dir, f"-DPython3_EXECUTABLE={python}"])
    _run(["cmake", "--build", build_dir])
    _run([build_dir / "smoke"])

    # The manifests record the nunavut that ran at configure and build time; both must be the installed one.
    configure_args = json.loads((build_dir / "generate_commands.json").read_text("utf-8"))["cmdline"]
    generate_manifest = build_dir / "cyphal-types-and-support-smoke-generate.json"
    build_args = json.loads(generate_manifest.read_text("utf-8"))["cmdline"]
    installed_main = Path(cmake_dir).parent / "__main__.py"
    for step, step_args in (("configure", configure_args), ("build", build_args)):
        if not Path(step_args[0]).samefile(installed_main):
            _fail(f"{step} ran {step_args[0]}, expected {installed_main}")

    # An installed Nunavut adds no lookup folder of its own (the public regulated types aren't in the wheel).
    lookup_dirs = [configure_args[i + 1] for i, arg in enumerate(configure_args) if arg == "--lookup-dir"]
    if lookup_dirs != [str(PROJECT_DIR / "dsdl" / "smoke")]:
        _fail(f"expected only the project's lookup folder, got {lookup_dirs}")

    # A Python that doesn't have this Nunavut installed is refused.
    bare_python = _new_venv_python(work_dir / "venv-bare", with_pip=False)
    refused = _run(
        ["cmake", "-S", PROJECT_DIR, "-B", work_dir / "build-bare", nunavut_dir, f"-DPython3_EXECUTABLE={bare_python}"],
        check=False,
        capture_output=True,
    )
    # CMake word-wraps error messages, so compare with the whitespace collapsed.
    if refused.returncode == 0 or "does not import the Nunavut package" not in " ".join(refused.stderr.split()):
        _fail(f"expected configure to refuse {bare_python}:\n{refused.stdout}\n{refused.stderr}")

    print("PASSED")


if __name__ == "__main__":
    main()
