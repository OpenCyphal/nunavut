# Copyright (c) 2023 OpenCyphal
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@opencyphal.org>
# type: ignore

import os
import sys
import shutil
from pathlib import Path
import nox


PYTHONS = ["3.11", "3.12", "3.13", "3.14", "3.15"]
FUZZ_PYTHONS = ["3.12", "3.13"]  # Atheris ships wheels for CPython 3.12+ on x86_64 Linux only.

nox.options.error_on_external_run = True
nox.options.sessions = ["clean", "test", "black"]  # The fuzz session is for long local runs only.

# Please keep these updated if the project directory is changed.
SUITE_DIR = Path(__file__).resolve().parent
SUITE_SRC_DIR = SUITE_DIR / "suite"
VERIFICATION_DIR = SUITE_DIR.parent
NUNAVUT_DIR = VERIFICATION_DIR.parent

PUBLIC_REGULATED_DATA_TYPES_DIR = NUNAVUT_DIR / "submodules" / "public_regulated_data_types"
TEST_TYPES_DIR = VERIFICATION_DIR / "nunavut_test_types"
FUZZ_DIR = SUITE_DIR / "fuzz-out"  # Not a valid identifier, so setuptools does not mistake it for a package.


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
    ]:  # Not .hypothesis or FUZZ_DIR: they keep failing examples and the fuzz corpus across runs.
        for f in Path.cwd().glob(w):
            session.log(f"Removing: {f}")
            if f.is_dir():
                shutil.rmtree(f, ignore_errors=True)
            else:
                f.unlink(missing_ok=True)


@nox.session(python=PYTHONS)
def test(session):
    # Log the Python version
    session.run("python", "--version")
    session.install("-e", str(NUNAVUT_DIR))
    session.install("-e", ".")
    session.install("-r", "generated_code_requirements.txt")
    session.install(
        "pytest     ~= 8.1",
        "coverage   ~= 7.4",
        "mypy       ~= 1.9",
        "pylint     ~= 3.1",
        "hypothesis ~= 6.100",
    )

    generated_dir, root_namespace_dirs = _generate(session)

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
        *session.posargs,  # E.g., -k to select tests.
        env={
            "NUNAVUT_VERIFICATION_DSDL_PATH": os.pathsep.join(map(str, root_namespace_dirs)),
            "PYTHONPATH": str(generated_dir),
        },
    )
    if not session.posargs:  # A filtered run does not cover everything.
        session.run("coverage", "report", "--fail-under=95")
    if session.interactive:
        session.run("coverage", "html")
        report_file = Path.cwd().resolve() / "htmlcov" / "index.html"
        session.log(f"OPEN IN WEB BROWSER: file://{report_file}")

    # The static analysis is run in the same session because it relies on the generated code.
    session.run(
        "mypy",
        "--strict",
        f"--config-file={NUNAVUT_DIR / 'pyproject.toml'}",  # Inherit the settings from the outer project.
        f"--python-version={session.python}",  # The outer project targets an older version than NumPy 2 stubs need.
        # Check by package name: the generated root contains an __init__.py, so checking by path would make mypy
        # see the same files under two module names.
        "-p",
        SUITE_SRC_DIR.name,
        *[a for x in generated_dir.iterdir() if x.is_dir() and x.name[0] not in "._" for a in ("-p", x.name)],
        env={
            "MYPYPATH": os.pathsep.join([str(generated_dir), str(SUITE_DIR)]),
        },
    )
    session.run(
        "pylint",
        str(SUITE_SRC_DIR),
        env={
            "PYTHONPATH": str(generated_dir),
        },
    )


@nox.session(python=FUZZ_PYTHONS)
def fuzz(session):
    """
    Coverage-guided fuzzing of the generated deserialization code with Atheris. Not run by default.
    Positional arguments are passed to libFuzzer, e.g.: nox -s fuzz-3.13 -- -max_total_time=3600 -jobs=8 -workers=8
    The corpus is kept in FUZZ_DIR/corpus across runs; crash reproducers are written to FUZZ_DIR.
    If any positional argument is a file (e.g., a crash reproducer), only the given files are run.
    """
    session.install("-e", str(NUNAVUT_DIR))
    session.install("-e", ".")
    session.install("-r", "generated_code_requirements.txt")
    session.install("pytest ~= 8.1", "atheris >= 2.3")
    generated_dir, root_namespace_dirs = _generate(session)
    # Not under the session's tmp dir: Nox deletes the whole session environment when it recreates it.
    seeds_dir, corpus_dir = FUZZ_DIR / "seeds", FUZZ_DIR / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    env = {
        "NUNAVUT_VERIFICATION_DSDL_PATH": os.pathsep.join(map(str, root_namespace_dirs)),
        "PYTHONPATH": str(generated_dir),
    }
    harness = str(SUITE_DIR / "tools" / "fuzz_deserialize.py")
    session.run("python", harness, "--write-seeds", str(seeds_dir), env=env)
    args = session.posargs or ["-max_total_time=60"]
    inputs = [] if any(not a.startswith("-") for a in args) else [str(corpus_dir), str(seeds_dir)]
    # The harness is run as an executable (its shebang finds the session's python first on the PATH) because
    # libFuzzer re-executes argv[0] for -jobs, -workers, and -fork.
    session.run(
        harness,
        f"-artifact_prefix={FUZZ_DIR}/",
        "-max_len=16384",
        *args,
        *inputs,
        env=env,
        external=True,
    )


def _generate(session):
    """
    Generates the Python packages from all root namespaces into the session's tmp dir in a single nnvg invocation.
    Invoking nnvg once per namespace does not work because generating a namespace that depends on another one
    rewrites the dependency's package __init__.py with only the types that were needed.
    Returns the output directory and the list of root namespace directories.
    """
    # The tmp dir will contain the DSDL-generated packages. We do not want to contaminate the source tree.
    # Invoke Nunavut manually prior to running the tests because the generated packages must already be available.
    # Invoking Nunavut from within PyTest is not possible because it will not be able to find the generated packages.
    root_namespace_dirs = [
        PUBLIC_REGULATED_DATA_TYPES_DIR / "uavcan",
        TEST_TYPES_DIR / "test0" / "regulated",
        TEST_TYPES_DIR / "test0" / "if",
    ]
    generated_dir = Path(session.create_tmp()).resolve()
    session.run(
        "nnvg",
        *[str(Path(nsd).resolve()) for nsd in root_namespace_dirs],
        "--target-language=py",
        "--outdir",
        str(generated_dir),
    )
    session.log("Compilation finished")
    return generated_dir, root_namespace_dirs


@nox.session(reuse_venv=True)
def black(session):
    session.install("black ~= 23.3")
    session.run("black", "--check", "suite", "tools", "noxfile.py")
