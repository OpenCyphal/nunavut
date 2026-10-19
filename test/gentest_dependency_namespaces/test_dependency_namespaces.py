#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Tests for how dependency namespaces are generated (https://github.com/OpenCyphal/nunavut/issues/403).

The fixture has a ``dep.ns`` namespace (``A.1.0``, ``A.1.1``, ``B.1.0``, ``C.1.0``, and a nested ``dep.ns.inner``)
and two root namespaces that each depend on a different part of it: ``user1.X`` uses ``dep.ns.A.1.0`` and
``user2.Y`` uses ``dep.ns.B.1.0``.
"""

import typing
from pathlib import Path

from nunavut import generate_all

_ALL_DEP_NS_TYPES = ["A_1_0", "A_1_1", "B_1_0", "C_1_0"]


def _targets(gen_paths: typing.Any, root_namespace: str) -> typing.List[Path]:
    return sorted((gen_paths.dsdl_dir / root_namespace).rglob("*.dsdl"))


def _roots(gen_paths: typing.Any) -> typing.List[Path]:
    return [gen_paths.dsdl_dir / name for name in ("dep", "user1", "user2")]


def _generate(gen_paths: typing.Any, language: str, root_namespace: str, outdir: Path, **kwargs: typing.Any) -> None:
    generate_all(
        language,
        _targets(gen_paths, root_namespace),
        _roots(gen_paths),
        outdir,
        include_experimental_languages=True,
        **kwargs,
    )


def _imported_names(init_file: Path) -> typing.List[str]:
    """The names a generated Python namespace file imports, in the order it imports them."""
    lines = init_file.read_text(encoding="utf-8").splitlines()
    return [line.split(" as ")[-1] for line in lines if line.startswith("from ")]


def _without_timestamp(generated_file: Path) -> str:
    lines = generated_file.read_text(encoding="utf-8").splitlines()
    return "\n".join(line for line in lines if "Generated at" not in line)


def test_py_dependency_namespace_is_complete(gen_paths: typing.Any) -> None:
    """
    A namespace that is generated only because a target depends on one of its types gets all of its types, so its
    __init__.py lists the whole namespace. Nested namespaces are not pulled in.
    """
    _generate(gen_paths, "py", "user1", gen_paths.out_dir)

    dep_ns = gen_paths.out_dir / "dep" / "ns"
    assert _imported_names(dep_ns / "__init__.py") == _ALL_DEP_NS_TYPES
    for name in _ALL_DEP_NS_TYPES:
        assert (dep_ns / f"{name}.py").exists()
    assert not (dep_ns / "inner").exists()


def test_py_sequential_generation_keeps_dependency_namespace_complete(gen_paths: typing.Any) -> None:
    """
    Generating two root namespaces one after the other into the same directory leaves a shared dependency namespace's
    __init__.py complete and identical to the one made by generating that namespace directly. Before the fix, the
    second run rewrote dep/ns/__init__.py to list only B_1_0, so dep.ns.A_1_0 stopped resolving.
    """
    sequential = gen_paths.out_dir / "sequential"
    _generate(gen_paths, "py", "user1", sequential)
    _generate(gen_paths, "py", "user2", sequential)

    direct = gen_paths.out_dir / "direct"
    _generate(gen_paths, "py", "dep", direct)

    init_file = Path("dep", "ns", "__init__.py")
    assert _imported_names(sequential / init_file) == _ALL_DEP_NS_TYPES
    assert _without_timestamp(sequential / init_file) == _without_timestamp(direct / init_file)


def test_py_omit_dependencies_generates_no_dependency_namespace(gen_paths: typing.Any) -> None:
    """
    With omit_dependencies, dependencies (and so their namespaces) are still not generated.
    """
    _generate(gen_paths, "py", "user1", gen_paths.out_dir, omit_dependencies=True)

    assert (gen_paths.out_dir / "user1" / "X_1_0.py").exists()
    assert not (gen_paths.out_dir / "dep").exists()


def test_c_generates_only_needed_dependencies(gen_paths: typing.Any) -> None:
    """
    C generates no namespace files, so it keeps generating only the dependency types that are needed.
    """
    _generate(gen_paths, "c", "user1", gen_paths.out_dir)

    dep_ns = gen_paths.out_dir / "dep" / "ns"
    assert (dep_ns / "A_1_0.h").exists()
    for name in ("A_1_1", "B_1_0", "C_1_0"):
        assert not (dep_ns / f"{name}.h").exists()
