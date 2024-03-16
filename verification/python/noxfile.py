# Copyright (c) 2023 OpenCyphal
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@opencyphal.org>
# type: ignore

import os
import shutil
from pathlib import Path
import nox


PYTHONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]

nox.options.error_on_external_run = True

# Please keep these updated if the project directory is changed.
SUITE_DIR = Path(__file__).resolve().parent
SUITE_SRC_DIR = SUITE_DIR / "suite"
VERIFICATION_DIR = SUITE_DIR.parent
NUNAVUT_DIR = VERIFICATION_DIR.parent

PUBLIC_REGULATED_DATA_TYPES_DIR = NUNAVUT_DIR / "submodules" / "public_regulated_data_types"
TEST_TYPES_DIR = VERIFICATION_DIR / "nunavut_test_types"


@nox.session(python=False)
def clean(session):
    for w in [
        "*.egg-info",
        "nunavut_out",
        ".coverage*",
        "html*",
        ".*cache",
        ".*compiled",
        "*.log",
        "*.tmp",
        ".nox",
    ]:
        for f in Path.cwd().glob(w):
            session.log(f"Removing: {f}")
            if f.is_dir():
                shutil.rmtree(f, ignore_errors=True)
            else:
                f.unlink(missing_ok=True)


@nox.session(python=PYTHONS)
def test(session):
    session.install("-e", str(NUNAVUT_DIR))
    session.install("-e", ".")
    session.install("-r", "generated_code_requirements.txt")
    session.install(
        "pytest     ~= 7.3",
        "coverage   ~= 7.2",
        "mypy       ~= 1.2",
        "pylint     ~= 2.17",
    )

    # The tmp dir will contain the DSDL-generated packages. We do not want to contaminate the source tree.
    # Invoke Nunavut manually prior to running the tests because the generated packages must already be available.
    # Invoking Nunavut from within PyTest is not possible because it will not be able to find the generated packages.
    root_namespace_dirs = [
        PUBLIC_REGULATED_DATA_TYPES_DIR / "uavcan",
        TEST_TYPES_DIR / "test0" / "regulated",
        TEST_TYPES_DIR / "test0" / "if",
    ]
    generated_dir = Path(session.create_tmp()).resolve()
    for nsd in root_namespace_dirs:
        session.run(
            "nnvg",
            str(Path(nsd).resolve()),
            "--target-language=py",
            "--outdir",
            str(generated_dir),
            env={
                "DSDL_INCLUDE_PATH": os.pathsep.join(map(str, root_namespace_dirs)),
            },
        )
    session.log(f"Compilation finished")

    # Run PyTest against the verification suite and the generated code at the same time.
    # If there are any doctests or unit tests within the generated code, they will be executed as well.
    test_paths = [
        SUITE_SRC_DIR,
        generated_dir,
    ]
    session.run(
        "coverage",
        "run",
        "-m",
        "pytest",
        *map(str, test_paths),
        env={
            "NUNAVUT_VERIFICATION_DSDL_PATH": os.pathsep.join(map(str, root_namespace_dirs)),
            "PYTHONPATH": str(generated_dir),
        },
    )
    session.run("coverage", "report", "--fail-under=95")
    if session.interactive:
        session.run("coverage", "html")
        report_file = Path.cwd().resolve() / "htmlcov" / "index.html"
        session.log(f"OPEN IN WEB BROWSER: file://{report_file}")

    # The static analysis is run in the same session because it relies on the generated code.
    session.run(
        "mypy",
        "--strict",
        f"--config-file={NUNAVUT_DIR / 'tox.ini'}",  # Inherit the settings from the outer project. Not sure about it.
        str(SUITE_SRC_DIR),
        *[str(x) for x in generated_dir.iterdir() if x.is_dir() and x.name[0] not in "._"],
    )
    session.run(
        "pylint",
        str(SUITE_SRC_DIR),
        env={
            "PYTHONPATH": str(generated_dir),
        },
    )


@nox.session(reuse_venv=True)
def black(session):
    session.install("black ~= 23.3")
    session.run("black", "--check", "suite", "noxfile.py")
