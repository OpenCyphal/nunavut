#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Nox session definitions for nunavut.

The standard version to develop against is 3.11. Minimum supported version is 3.10.
"""

import glob
import os
from pathlib import Path

import nox

# +---------------------------------------------------------------------------+
# | CONFIGURATION
# +---------------------------------------------------------------------------+

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13"]
DEFAULT_PYTHON = "3.11"

BASE_DEPS = [
    "Sybil",
    "pytest",
    "pytest-timeout",
    "pytest-cov",
    "pytest-profiling",
    "coverage",
    "types-PyYAML",
    "pyyaml",
]

DEV_DEPS = [
    *BASE_DEPS,
    "autopep8",
    "rope",
    "isort",
    "nox",
    "jsonschema",
]

LINT_DEPS = [
    *DEV_DEPS,
    "black",
    "pylint",
    "doc8",
    "Pygments",
    "mypy",
    "lxml",
    "types-setuptools",
    "types-PyYAML",
]

nox.options.sessions = [
    "lint",
    f"nnvg-{DEFAULT_PYTHON}",
    f"doctest-{DEFAULT_PYTHON}",
    f"rstdoctest-{DEFAULT_PYTHON}",
    f"test-{DEFAULT_PYTHON}",
    "report",
]


# +---------------------------------------------------------------------------+
# | HELPERS
# +---------------------------------------------------------------------------+


def _project_root() -> Path:
    """Return the absolute path to the project root."""
    return Path(__file__).parent.resolve()


def _forward_github_env(session: nox.Session) -> None:
    """Forward GITHUB_* environment variables into the session."""
    for key, value in os.environ.items():
        if key == "GITHUB" or key.startswith("GITHUB_"):
            session.env[key] = value


# +---------------------------------------------------------------------------+
# | SESSIONS
# +---------------------------------------------------------------------------+


@nox.session(python=PYTHON_VERSIONS)
def test(session: nox.Session) -> None:
    """Run the test suite with coverage."""
    session.install("-e", ".")
    session.install(*BASE_DEPS)
    session.env["PYTHONDONTWRITEBYTECODE"] = "1"
    _forward_github_env(session)
    tmpdir = session.create_tmp()
    session.run(
        "coverage",
        "run",
        "-m",
        "pytest",
        *session.posargs,
        f"--basetemp={tmpdir}",
        "-p",
        "no:cacheprovider",
        f"--junit-xml={tmpdir}/xunit-result.xml",
        f"--rootdir={_project_root()}",
        str(_project_root() / "test"),
    )
    session.run("coverage", "combine", "--append")


@nox.session(python=PYTHON_VERSIONS)
def nnvg(session: nox.Session) -> None:
    """Run nnvg code generation with coverage."""
    session.install("-e", ".")
    session.install(*BASE_DEPS)
    session.env["PYTHONDONTWRITEBYTECODE"] = "1"
    _forward_github_env(session)
    tmpdir = session.create_tmp()
    session.run(
        "coverage",
        "run",
        "-m",
        "nunavut",
        "-O",
        tmpdir,
        "--target-language",
        "cpp",
        "--experimental-languages",
        "--language-standard",
        "c++17-pmr",
        "-v",
        str(_project_root() / "submodules" / "public_regulated_data_types" / "uavcan"),
    )
    session.run("coverage", "combine", "--append")


@nox.session(python=PYTHON_VERSIONS)
def doctest(session: nox.Session) -> None:
    """Run doctests in source code with coverage."""
    session.install("-e", ".")
    session.install(*BASE_DEPS)
    session.env["PYTHONDONTWRITEBYTECODE"] = "1"
    _forward_github_env(session)
    tmpdir = session.create_tmp()
    session.run(
        "coverage",
        "run",
        "-m",
        "pytest",
        *session.posargs,
        f"--basetemp={tmpdir}",
        "-p",
        "no:cacheprovider",
        "--ignore-glob=*.bak",
        f"--rootdir={_project_root()}",
        str(_project_root() / "src"),
    )
    session.run("coverage", "combine", "--append")


@nox.session(python=PYTHON_VERSIONS)
def rstdoctest(session: nox.Session) -> None:
    """Run doctests in RST documentation."""
    session.install("-e", ".")
    session.install(*BASE_DEPS)
    session.env["PYTHONDONTWRITEBYTECODE"] = "1"
    _forward_github_env(session)
    tmpdir = session.create_tmp()
    session.run(
        "pytest",
        *session.posargs,
        f"--basetemp={tmpdir}",
        "-p",
        "no:cacheprovider",
        f"--rootdir={_project_root()}",
        str(_project_root() / "docs"),
    )


@nox.session(python=DEFAULT_PYTHON)
def lint(session: nox.Session) -> None:
    """Run linters (pylint, black, doc8, mypy)."""
    session.install("-e", ".")
    session.install(*LINT_DEPS)
    tmpdir = session.create_tmp()
    root = _project_root()
    session.run(
        "pylint",
        "--reports=y",
        f"--rcfile={root / '.pylintrc'}",
        f"--output={tmpdir}/pylint.txt",
        "--output-format=json2",
        "--clear-cache-post-run=y",
        "--confidence=HIGH",
        str(root / "src" / "nunavut"),
    )
    session.run(
        "black",
        "--check",
        "--line-length",
        "120",
        "--force-exclude",
        r"(/jinja2/|/markupsafe/)",
        str(root / "src"),
    )
    session.run(
        "doc8",
        "--ignore-path",
        str(root / "docs" / "cmake" / "build"),
        "--ignore-path",
        str(root / "docs" / "cmake" / "external"),
        str(root / "docs"),
    )
    session.run(
        "mypy",
        "-p",
        "nunavut",
        f"--cache-dir={tmpdir}",
        f"--txt-report={tmpdir}/mypy-report-lib",
        f"--config-file={root / 'setup.cfg'}",
    )


@nox.session(python=DEFAULT_PYTHON)
def docs(session: nox.Session) -> None:
    """Build Sphinx documentation."""
    session.install("-e", ".")
    session.install("-r", "requirements.txt")
    session.install("sphinx")
    tmpdir = session.create_tmp()
    session.run("sphinx-build", "-W", "-b", "html", str(_project_root()), tmpdir)


@nox.session(python=DEFAULT_PYTHON)
def report(session: nox.Session) -> None:
    """Generate coverage reports (HTML and XML)."""
    session.install("coverage")
    tmpdir = session.create_tmp()
    session.run("coverage", "combine", "--append", success_codes=[0, 1])
    session.run("coverage", "html", "-d", tmpdir)
    session.run("coverage", "xml", "-o", f"{tmpdir}/coverage.xml")


@nox.session(python=DEFAULT_PYTHON)
def package(session: nox.Session) -> None:
    """Build and check the distribution package."""
    session.install("build", "twine", "setuptools")
    session.install("-e", ".")
    tmpdir = session.create_tmp()
    dist_dir = str(Path(tmpdir) / "dist")
    session.run("python", "version_check_pydsdl.py", "-vv")
    session.run(
        "python",
        "-m",
        "build",
        "-o",
        dist_dir,
        "--sdist",
        "--wheel",
        f"--config-setting=--build-number={os.environ.get('GITHUB_RUN_ID', '0')}",
    )
    dist_files = glob.glob(f"{dist_dir}/*")
    session.run("twine", "check", *dist_files)


@nox.session(python=DEFAULT_PYTHON)
def format(session: nox.Session) -> None:
    """Run code formatters (isort, black)."""
    session.install("-e", ".")
    session.install(*DEV_DEPS, "black")
    root = _project_root()
    session.run(
        "isort",
        "--skip-glob",
        "*/jinja2/*",
        "--skip-glob",
        "*/markupsafe/*",
        str(root / "src" / "nunavut"),
    )
    session.run(
        "black",
        "--line-length",
        "120",
        "--force-exclude",
        r"(/jinja2/|/markupsafe/)",
        str(root / "src"),
    )


@nox.session(python=DEFAULT_PYTHON)
def local(session: nox.Session) -> None:
    """Set up a local development environment with all dependencies."""
    session.install("-e", ".")
    session.install(*LINT_DEPS)
    session.install("-r", "requirements.txt")
    session.install("sphinx")
    session.run("python", "--version")
