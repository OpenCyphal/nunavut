# Copyright (c) 2023 OpenCyphal
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@opencyphal.org>
# type: ignore

import shutil
from pathlib import Path
import nox


PYTHONS = ["3.8", "3.9", "3.10", "3.11"]

nox.options.error_on_external_run = True

SUITE_ROOT_DIR = Path(__file__).resolve().parent
SUITE_SRC_DIR = SUITE_ROOT_DIR / "suite"
NUNAVUT_ROOT_DIR = SUITE_ROOT_DIR.parent.parent
GENERATED_DIR = SUITE_ROOT_DIR / "nunavut_out"


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
    session.install("-e", str(NUNAVUT_ROOT_DIR))
    session.install("-e", ".")
    session.install("-r", "generated_code_requirements.txt")
    session.install(
        "pytest     ~= 7.3",
        "coverage   ~= 7.2",
        "mypy       ~= 1.2",
        "pylint     ~= 2.17",
    )
    session.run("coverage", "run", "-m", "pytest")
    session.run("coverage", "report", "--fail-under=95")
    if session.interactive:
        session.run("coverage", "html")
        report_file = Path.cwd().resolve() / "htmlcov" / "index.html"
        session.log(f"OPEN IN WEB BROWSER: file://{report_file}")

    # The static analysis is run in the same session because it relies on the generated code.
    session.run(
        "mypy",
        "--strict",
        f"--config-file={NUNAVUT_ROOT_DIR / 'tox.ini'}",  # Inherit the settings from the outer project.
        str(SUITE_SRC_DIR),
        *[str(x) for x in GENERATED_DIR.iterdir() if x.is_dir() and x.name[0] not in "._"],
    )
    session.run(
        "pylint",
        str(SUITE_SRC_DIR),
        env={
            "PYTHONPATH": str(GENERATED_DIR),
        },
    )


@nox.session(reuse_venv=True)
def black(session):
    session.install("black ~= 23.3")
    session.run("black", "--check", "suite", "noxfile.py")
