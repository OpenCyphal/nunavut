#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Tests for append-only merging of generated namespace files (https://github.com/OpenCyphal/nunavut/issues/403).

Test IDs (U*, G*, L*, A*) refer to the approved test plan:
https://github.com/OpenCyphal/nunavut/issues/403#issuecomment-6297320522

These tests pin down the interfaces the change adds:

* ``nunavut.NamespaceConflictError`` with ``conflicts``: objects with ``path``, ``kind`` (an enum whose names are
  ``NO_MANIFEST``, ``NAMING_CHANGED`` and ``CASE_COLLISION``) and ``detail``.
* ``nunavut._namespace_manifest.parse_manifest(text_or_bytes)``: a manifest with ``members`` (a frozenset of versioned
  type names) and ``digest`` (``"sha256:<hex>"``), or ``None``; and ``naming_digest(namespace_file_name, entries)``.
* ``Namespace.get_namespace_members()`` and the ``namespace_manifest_lines`` filter, for namespace templates.

New interfaces are imported inside the tests so that the module still loads on a nunavut without them, which lets
the tests that reproduce #403 fail on their assertions there.

Fixtures (``dsdl/``): root ``mg`` has ``mg.ns.A.1.0``, ``A.1.1``, ``A.2.0`` and ``B.1.0``; ``mg.user.X.1.0`` uses
``mg.ns.A.1.0`` and ``mg.user.Y.1.0`` uses ``mg.ns.B.1.0``; ``mg.import.K.1.0`` lives in a namespace named with a
Python keyword, as does ``mg.import.L.1.0``; ``mg.ns.S.1.0`` is a service. ``case_a/cc`` and ``case_b/cc`` are two
roots named ``cc`` holding ``cc.ns.Foo.1.0`` and ``cc.ns.foo.1.0``; ``case_c/cc`` and ``case_d/cc`` hold
``cc.NS.Foo.1.0`` and ``cc.ns.Bar.1.0``, whose namespaces differ only in letter case.

Tests marked ``slow`` run only when ``NUNAVUT_RUN_SLOW_TESTS`` is set (see conftest.py).
"""

import hashlib
import inspect
import itertools
import json
import re
import shutil
import typing
from pathlib import Path

import pytest

import nunavut
from nunavut import (
    LanguageContextBuilder,
    Namespace,
    ResourceType,
    YesNoDefault,
    generate_all,
    generate_all_for_language,
    generate_all_from_namespace,
)

_X = "mg/user/X.1.0.dsdl"
_Y = "mg/user/Y.1.0.dsdl"
_A10 = "mg/ns/A.1.0.dsdl"
_A11 = "mg/ns/A.1.1.dsdl"
_A20 = "mg/ns/A.2.0.dsdl"
_K = "mg/import/K.1.0.dsdl"
_L = "mg/import/L.1.0.dsdl"
_S = "mg/ns/S.1.0.dsdl"

_NS_INIT = Path("mg", "ns", "__init__.py")
_USER_INIT = Path("mg", "user", "__init__.py")

# The manifest marker as text, so tests of languages without manifests don't depend on the new module.
_MANIFEST_BEGIN_TEXT = "nunavut-namespace-manifest-begin"

_IMPORT_LINE = re.compile(r"^from (\S+) import (\w+) as (\w+)\s*$")
_ALIAS_LINE = re.compile(r"^(\w+) = (\w+)\s*$")


# +---------------------------------------------------------------------------+
# | Helpers
# +---------------------------------------------------------------------------+


@pytest.fixture(autouse=True)
def _empty_output_directory(gen_paths: typing.Any) -> None:
    """
    Every test starts from an empty output directory, even when generated output is kept between runs
    (``--keep-generated``).
    """
    for entry in list(gen_paths.out_dir.iterdir()):
        # Generated files are read-only by default, which Windows refuses to delete.
        for path in [entry, *entry.rglob("*")]:
            _make_writable(path)
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def _generate(
    gen_paths: typing.Any,
    outdir: Path,
    targets: typing.Iterable[str],
    language: str = "py",
    roots: typing.Optional[typing.List[Path]] = None,
    dsdl_dir: typing.Optional[Path] = None,
    check: bool = True,
    **kwargs: typing.Any,
) -> typing.Any:
    """
    Generates, then (for Python) checks every namespace file in the output with
    :func:`assert_all_namespaces_consistent`. Pass ``check=False`` only for the test plan's named exceptions.
    """
    dsdl = dsdl_dir if dsdl_dir is not None else gen_paths.dsdl_dir
    kwargs.setdefault("jobs", 1)
    result = generate_all(
        language,
        [dsdl / t for t in targets],
        roots if roots is not None else [dsdl / "mg"],
        outdir,
        include_experimental_languages=True,
        **kwargs,
    )
    if check and language == "py":
        assert_all_namespaces_consistent(outdir)
    return result


def _nnvg(
    run_nnvg_main: typing.Callable,
    gen_paths: typing.Any,
    outdir: Path,
    targets: typing.Iterable[str],
    *extra: str,
    check: bool = True,
) -> typing.Any:
    """
    Runs nnvg for Python, then, if it succeeded, checks every namespace file like :func:`_generate`.
    """
    args = [
        "--target-language",
        "py",
        "--outdir",
        outdir.as_posix(),
        "--lookup-dir",
        (gen_paths.dsdl_dir / "mg").as_posix(),
        *extra,
        *[(gen_paths.dsdl_dir / t).as_posix() for t in targets],
    ]
    result = run_nnvg_main(gen_paths, args)
    if check and result.returncode == 0 and outdir.exists():
        assert_all_namespaces_consistent(outdir)
    return result


def _lines(path: Path) -> typing.List[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _imports(init_file: Path) -> typing.Set[str]:
    """The names a generated Python namespace file imports."""
    return {m.group(3) for m in map(_IMPORT_LINE.match, _lines(init_file)) if m}


def _aliases(init_file: Path) -> typing.Dict[str, str]:
    return {m.group(1): m.group(2) for m in map(_ALIAS_LINE.match, _lines(init_file)) if m}


def _manifest(path: Path) -> typing.Any:
    from nunavut._namespace_manifest import parse_manifest  # pylint: disable=import-outside-toplevel

    return parse_manifest(path.read_bytes())


def _members(path: Path) -> typing.FrozenSet[str]:
    manifest = _manifest(path)
    assert manifest is not None, f"{path} has no manifest"
    return frozenset(manifest.members)


def _short_reference_name(member: str) -> str:
    *_, short_name, major, minor = member.split(".")
    return f"{short_name}_{major}_{minor}"


def assert_namespace_consistent(init_file: Path) -> None:
    """
    The namespace file's imports are exactly its manifest's members, and each alias points at the newest minor
    version of its name and major version, which is itself imported.
    """
    members = _members(init_file)
    imports = _imports(init_file)
    assert imports == {_short_reference_name(m) for m in members}

    newest: typing.Dict[str, typing.Tuple[int, str]] = {}
    for member in members:
        *_, short_name, major, minor = member.split(".")
        key = f"{short_name}_{major}"
        if key not in newest or int(minor) > newest[key][0]:
            newest[key] = (int(minor), _short_reference_name(member))
    aliases = _aliases(init_file)
    assert aliases == {alias: target for alias, (_, target) in newest.items()}
    assert set(aliases.values()) <= imports


def _python_namespace_files(outdir: Path) -> typing.List[Path]:
    return sorted(outdir.rglob("__init__.py"))


def assert_all_namespaces_consistent(outdir: Path) -> None:
    for init_file in _python_namespace_files(outdir):
        assert_namespace_consistent(init_file)


def snapshot(outdir: Path) -> typing.Dict[str, bytes]:
    """Every file under outdir: its path relative to outdir and its contents."""
    return {p.relative_to(outdir).as_posix(): p.read_bytes() for p in sorted(outdir.rglob("*")) if p.is_file()}


def _conflicts(excinfo: typing.Any, outdir: Path) -> typing.Set[typing.Tuple[str, str]]:
    return {(Path(c.path).relative_to(outdir).as_posix(), c.kind.name) for c in excinfo.value.conflicts}


def _conflict_error() -> typing.Type[Exception]:
    return typing.cast(typing.Type[Exception], getattr(nunavut, "NamespaceConflictError"))


def _make_writable(path: Path) -> None:
    path.chmod(path.stat().st_mode | 0o200)


def _replace_without_manifest(init_file: Path) -> None:
    """Simulate a namespace file written by a nunavut without manifests: imports only."""
    imports = [line for line in _lines(init_file) if _IMPORT_LINE.match(line)]
    _make_writable(init_file)
    init_file.write_text("# AUTOGENERATED, DO NOT EDIT.\n" + "\n".join(imports) + "\n", encoding="utf-8")


def _copy_dsdl(gen_paths: typing.Any, tmp_path: Path) -> Path:
    copy = tmp_path / "dsdl"
    shutil.copytree(gen_paths.dsdl_dir, copy)
    return copy


# +---------------------------------------------------------------------------+
# | U: manifest parsing and the digest
# +---------------------------------------------------------------------------+

_DIGEST = "sha256:" + "0123456789abcdef" * 4


def _canonical_manifest(members: typing.Iterable[str], digest: str = _DIGEST, namespace: str = "mg.ns") -> str:
    from nunavut._namespace_manifest import (  # pylint: disable=import-outside-toplevel
        MANIFEST_BEGIN,
        MANIFEST_END,
    )

    body = "".join(f"#   {m}\n" for m in members)
    return f"# {MANIFEST_BEGIN}\n#   namespace:{namespace}\n#   naming-digest {digest}\n{body}# {MANIFEST_END}\n"


def test_u1_manifest_is_read_regardless_of_formatting() -> None:
    from nunavut._namespace_manifest import parse_manifest  # pylint: disable=import-outside-toplevel

    members = ["mg.ns.A.1.0", "mg.ns.A.1.1", "mg.ns.B.1.0"]
    canonical = _canonical_manifest(members)
    reformatted = [
        canonical.replace("\n", "\r\n"),
        canonical.replace("#   ", "#\t\t"),
        canonical.replace("\n#   mg.ns.A.1.1", "    mg.ns.A.1.1").replace("\n#   mg.ns.B.1.0", "  mg.ns.B.1.0"),
        canonical.replace("\n", "\n#\n\n"),
        # Split lines: the digest label and the digest apart, and each member on its own line between blank lines.
        canonical.replace("naming-digest ", "naming-digest\n#\n#      ").replace("#   mg.", "#\n#\n#   mg."),
    ]
    for text in [canonical, *reformatted]:
        manifest = parse_manifest(text)
        assert manifest is not None, text
        assert set(manifest.members) == set(members)
        assert manifest.digest == _DIGEST


def test_u2_text_outside_the_markers_and_labels_are_not_members() -> None:
    from nunavut._namespace_manifest import parse_manifest  # pylint: disable=import-outside-toplevel

    text = "# see mg.other.Z.9.9 for details\n" + _canonical_manifest(["mg.ns.A.1.0"]) + "# mg.later.W.1.0\n"
    manifest = parse_manifest(text)
    assert manifest is not None
    assert set(manifest.members) == {"mg.ns.A.1.0"}


def test_u3_begin_marker_without_end_marker_is_no_manifest() -> None:
    from nunavut._namespace_manifest import MANIFEST_END, parse_manifest  # pylint: disable=import-outside-toplevel

    text = _canonical_manifest(["mg.ns.A.1.0"])
    assert parse_manifest(text[: text.index(MANIFEST_END)]) is None


@pytest.mark.parametrize("digests", [0, 2])
def test_u4_zero_or_two_digests_is_no_manifest(digests: int) -> None:
    from nunavut._namespace_manifest import parse_manifest  # pylint: disable=import-outside-toplevel

    text = _canonical_manifest(["mg.ns.A.1.0"])
    if digests == 0:
        text = text.replace(_DIGEST, "")
    else:
        text = text.replace(_DIGEST, f"{_DIGEST} {_DIGEST.replace('0', '1')}")
    assert parse_manifest(text) is None


def test_u5_bytes_that_are_not_utf8_are_no_manifest() -> None:
    from nunavut._namespace_manifest import parse_manifest  # pylint: disable=import-outside-toplevel

    data = _canonical_manifest(["mg.ns.A.1.0"]).encode("utf-8") + b"\xff\xfe\xfa"
    assert parse_manifest(data) is None


def test_u6_digest_does_not_depend_on_member_order() -> None:
    from nunavut._namespace_manifest import naming_digest  # pylint: disable=import-outside-toplevel

    entries = [
        ("mg.ns.A.1.0", "mg.ns.A_1_0", "mg/ns/A_1_0.py"),
        ("mg.ns.B.1.0", "mg.ns.B_1_0", "mg/ns/B_1_0.py"),
    ]
    assert naming_digest("__init__.py", entries) == naming_digest("__init__.py", list(reversed(entries)))
    assert naming_digest("__init__.py", entries).startswith("sha256:")


def test_u8_manifest_needs_exactly_one_namespace() -> None:
    from nunavut._namespace_manifest import parse_manifest  # pylint: disable=import-outside-toplevel

    text = _canonical_manifest(["mg.ns.A.1.0"])
    assert parse_manifest(text).namespace == "mg.ns"
    assert parse_manifest(text.replace("namespace:mg.ns", "")) is None
    assert parse_manifest(text.replace("namespace:mg.ns", "namespace:mg.ns namespace:mg.other")) is None
    root = parse_manifest(_canonical_manifest([], namespace=""))
    assert root is not None
    assert root.namespace == ""
    assert root.members == frozenset()


def test_u7_digest_matches_the_generated_output(gen_paths: typing.Any) -> None:
    """
    The digest written in a manifest equals the canonical digest computed independently from the generated files:
    the namespace file's name, then one line per member sorted by name with the member's name, full reference name
    and output-relative path, separated by tabs.
    """
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X, _Y])
    init_file = out / _NS_INIT
    references = {m.group(3): m.group(1) for m in map(_IMPORT_LINE.match, _lines(init_file)) if m}

    lines = []
    for member in sorted(_members(init_file)):
        short = _short_reference_name(member)
        module = references[short]
        module_path = (out / Path(*module.split("."))).with_suffix(".py")
        assert module_path.exists()
        lines.append(f"{member}\t{module}\t{module_path.relative_to(out).as_posix()}\n")
    expected = "sha256:" + hashlib.sha256(("__init__.py\n" + "".join(lines)).encode("utf-8")).hexdigest()
    assert _manifest(init_file).digest == expected


# +---------------------------------------------------------------------------+
# | G: generation, Python
# +---------------------------------------------------------------------------+


def test_g1_fresh_output_directory(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    assert _members(out / _NS_INIT) == {"mg.ns.A.1.0"}
    assert _members(out / _USER_INIT) == {"mg.user.X.1.0"}
    assert_all_namespaces_consistent(out)


def test_g2_same_command_twice_is_idempotent(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X, _Y])
    first = {p: (_members(p), _imports(p), _aliases(p)) for p in _python_namespace_files(out)}
    _generate(gen_paths, out, [_X, _Y])
    second = {p: (_members(p), _imports(p), _aliases(p)) for p in _python_namespace_files(out)}
    assert first == second
    assert_all_namespaces_consistent(out)


def test_g3_generating_more_targets_keeps_earlier_types(gen_paths: typing.Any) -> None:
    """
    The #403 reproduction: generating Y after X into the same directory must keep mg.ns.A_1_0, which only X uses.
    """
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    _generate(gen_paths, out, [_Y])
    assert _imports(out / _NS_INIT) == {"A_1_0", "B_1_0"}
    assert _imports(out / _USER_INIT) == {"X_1_0", "Y_1_0"}
    assert_all_namespaces_consistent(out)


def test_g4_fewer_targets_keep_recorded_members(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X, _Y])
    _generate(gen_paths, out, [_X])
    assert _members(out / _NS_INIT) == {"mg.ns.A.1.0", "mg.ns.B.1.0"}
    assert (out / "mg" / "ns" / "B_1_0.py").exists()
    assert_all_namespaces_consistent(out)


def test_g5_omit_dependencies_merges_with_recorded_members(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    _generate(gen_paths, out, [_Y], omit_dependencies=True)
    assert _members(out / _USER_INIT) == {"mg.user.X.1.0", "mg.user.Y.1.0"}
    assert _members(out / _NS_INIT) == {"mg.ns.A.1.0"}
    assert_all_namespaces_consistent(out)


def test_g6_edited_definition_rewrites_the_type_file(gen_paths: typing.Any, tmp_path: Path) -> None:
    dsdl = _copy_dsdl(gen_paths, tmp_path)
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X], dsdl_dir=dsdl)
    (dsdl / _A10).write_text("uint8 renamed_field\n@sealed\n", encoding="utf-8")
    _generate(gen_paths, out, [_X], dsdl_dir=dsdl)
    assert "renamed_field" in (out / "mg" / "ns" / "A_1_0.py").read_text(encoding="utf-8")
    assert _members(out / _NS_INIT) == {"mg.ns.A.1.0"}
    assert_all_namespaces_consistent(out)


def test_g7_deleted_definition_stays_in_the_output(gen_paths: typing.Any, tmp_path: Path) -> None:
    dsdl = _copy_dsdl(gen_paths, tmp_path)
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X, _Y], dsdl_dir=dsdl)
    (dsdl / _Y).unlink()
    (dsdl / "mg" / "ns" / "B.1.0.dsdl").unlink()
    _generate(gen_paths, out, [_X], dsdl_dir=dsdl)
    assert "mg.ns.B.1.0" in _members(out / _NS_INIT)
    assert (out / "mg" / "ns" / "B_1_0.py").exists()
    assert_all_namespaces_consistent(out)


def test_g8_newer_minor_moves_the_alias_and_keeps_the_older_binding(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_A10])
    _generate(gen_paths, out, [_A11])
    assert _aliases(out / _NS_INIT)["A_1"] == "A_1_1"
    assert {"A_1_0", "A_1_1"} <= _imports(out / _NS_INIT)
    assert_all_namespaces_consistent(out)


def test_g9_older_minor_leaves_the_alias(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_A11])
    _generate(gen_paths, out, [_A10])
    assert _aliases(out / _NS_INIT)["A_1"] == "A_1_1"
    assert_all_namespaces_consistent(out)


def test_g10_new_major_adds_an_alias(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_A10])
    _generate(gen_paths, out, [_A20])
    aliases = _aliases(out / _NS_INIT)
    assert aliases["A_1"] == "A_1_0"
    assert aliases["A_2"] == "A_2_0"
    assert_all_namespaces_consistent(out)


# Each subset of these targets generates these members.
_G11_TARGETS = {
    "X": (_X, {"mg.user.X.1.0", "mg.ns.A.1.0"}),
    "Y": (_Y, {"mg.user.Y.1.0", "mg.ns.B.1.0"}),
    "A11": (_A11, {"mg.ns.A.1.1"}),
    "A20": (_A20, {"mg.ns.A.2.0"}),
}
_G11_MAX_RUNS = 3


@pytest.mark.slow
def test_g11_members_never_shrink(gen_paths: typing.Any, tmp_path: Path) -> None:
    """
    For every ordered sequence of up to three runs, each over a non-empty subset of the targets above, every
    namespace file's members after each run are exactly the union of what all runs so far generated into it.
    Sequences that share a prefix share its output, so each distinct prefix is generated once.
    """
    names = sorted(_G11_TARGETS)
    subsets = [combo for size in range(1, len(names) + 1) for combo in itertools.combinations(names, size)]
    counter = itertools.count()

    def namespace_of(member: str) -> Path:
        return Path(*member.split(".")[:-3], "__init__.py")

    def explore(state: typing.Optional[Path], generated: typing.FrozenSet[str], depth: int) -> None:
        for subset in subsets:
            out = tmp_path / f"run{next(counter)}"
            if state is not None:
                shutil.copytree(state, out)
            _generate(gen_paths, out, [_G11_TARGETS[k][0] for k in subset])
            now = generated.union(*(_G11_TARGETS[k][1] for k in subset))
            expected: typing.Dict[Path, typing.Set[str]] = {}
            for member in now:
                expected.setdefault(namespace_of(member), set()).add(member)
            for init_file, members in expected.items():
                assert _members(out / init_file) == members, (subset, depth)
            assert_all_namespaces_consistent(out)
            if depth + 1 < _G11_MAX_RUNS:
                explore(out, now, depth + 1)
            for path in out.rglob("*"):
                _make_writable(path)  # Generated files are read-only, which Windows refuses to delete.
            shutil.rmtree(out)

    explore(None, frozenset(), 0)


def test_g12_namespace_file_without_manifest_is_refused(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    _replace_without_manifest(out / _NS_INIT)
    before = snapshot(out)
    with pytest.raises(_conflict_error()) as excinfo:
        _generate(gen_paths, out, [_Y])
    assert ("mg/ns/__init__.py", "NO_MANIFEST") in _conflicts(excinfo, out)
    assert snapshot(out) == before


def test_g13_forced_no_manifest_lists_this_runs_members_and_deletes_nothing(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    _replace_without_manifest(out / _NS_INIT)
    before = snapshot(out)
    _generate(gen_paths, out, [_Y], force=True)
    after = snapshot(out)
    assert _members(out / _NS_INIT) == {"mg.ns.B.1.0"}
    assert set(before) <= set(after)
    for unchanged in ("mg/ns/A_1_0.py", "mg/user/X_1_0.py"):
        assert after[unchanged] == before[unchanged]
    assert_all_namespaces_consistent(out)


def test_g14_truncated_manifest_is_refused(gen_paths: typing.Any) -> None:
    from nunavut._namespace_manifest import MANIFEST_END  # pylint: disable=import-outside-toplevel

    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    init_file = out / _NS_INIT
    text = init_file.read_text(encoding="utf-8")
    _make_writable(init_file)
    init_file.write_text(text[: text.index(MANIFEST_END)], encoding="utf-8")
    with pytest.raises(_conflict_error()) as excinfo:
        _generate(gen_paths, out, [_X])
    assert ("mg/ns/__init__.py", "NO_MANIFEST") in _conflicts(excinfo, out)


def test_g15_stropping_change_relocates_the_namespace(gen_paths: typing.Any, tmp_path: Path) -> None:
    """
    In Python a stropping change renames namespace directories (mg/import_ to mg/import__), so the namespace is
    written to a new location and the old one is left untouched; nothing is detected (design D6).
    """
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_K, _X])
    old = snapshot(out / "mg" / "import_")
    config = tmp_path / "stropping.json"
    config.write_text(json.dumps({"nunavut.lang.py": {"stropping_suffix": "__"}}), encoding="utf-8")
    _generate(gen_paths, out, [_K, _Y], configuration=[config])
    assert snapshot(out / "mg" / "import_") == old
    assert _members(out / "mg" / "import__" / "__init__.py") == {"mg.import.K.1.0"}
    assert _members(out / _NS_INIT) == {"mg.ns.A.1.0", "mg.ns.B.1.0"}
    assert_all_namespaces_consistent(out)


def _change_naming_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate a nunavut version whose naming code names types differently."""
    from nunavut.lang._language import Language  # pylint: disable=import-outside-toplevel

    def renamed(self: typing.Any, t: typing.Any, *args: typing.Any, **kwargs: typing.Any) -> str:
        return f"{t.short_name}_v{t.version.major}_{t.version.minor}"

    monkeypatch.setattr(Language, "filter_short_reference_name", renamed)


def test_g16_naming_code_change_is_refused(gen_paths: typing.Any, monkeypatch: pytest.MonkeyPatch) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    before = snapshot(out)
    _change_naming_code(monkeypatch)
    with pytest.raises(_conflict_error()) as excinfo:
        _generate(gen_paths, out, [_X])
    assert ("mg/ns/__init__.py", "NAMING_CHANGED") in _conflicts(excinfo, out)
    assert snapshot(out) == before


def test_g17_forced_naming_change_lists_this_runs_members_only(
    gen_paths: typing.Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X, _Y])
    before = snapshot(out)
    _change_naming_code(monkeypatch)
    _generate(gen_paths, out, [_X], force=True, check=False)  # The simulated naming no longer matches file names.
    after = snapshot(out)
    assert _members(out / _NS_INIT) == {"mg.ns.A.1.0"}
    assert set(before) <= set(after)
    assert after["mg/ns/B_1_0.py"] == before["mg/ns/B_1_0.py"]


def test_g18_different_nunavut_version_merges(gen_paths: typing.Any, monkeypatch: pytest.MonkeyPatch) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    monkeypatch.setattr(nunavut, "__version__", "999.0.0")
    _generate(gen_paths, out, [_Y])
    assert _members(out / _NS_INIT) == {"mg.ns.A.1.0", "mg.ns.B.1.0"}
    assert_all_namespaces_consistent(out)


def _generate_case(gen_paths: typing.Any, out: Path, root: str, target: str, **kwargs: typing.Any) -> None:
    case_root = gen_paths.dsdl_dir / root / "cc"
    _generate(gen_paths, out, [f"{root}/cc/ns/{target}"], roots=[case_root], **kwargs)


def test_g19_case_only_collision_is_refused(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate_case(gen_paths, out, "case_a", "Foo.1.0.dsdl")
    before = snapshot(out)
    with pytest.raises(_conflict_error()) as excinfo:
        _generate_case(gen_paths, out, "case_b", "foo.1.0.dsdl")
    assert ("cc/ns/__init__.py", "CASE_COLLISION") in _conflicts(excinfo, out)
    assert snapshot(out) == before


def test_g20_case_only_collision_cannot_be_forced(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate_case(gen_paths, out, "case_a", "Foo.1.0.dsdl")
    before = snapshot(out)
    with pytest.raises(_conflict_error()) as excinfo:
        _generate_case(gen_paths, out, "case_b", "foo.1.0.dsdl", force=True)
    assert ("cc/ns/__init__.py", "CASE_COLLISION") in _conflicts(excinfo, out)
    assert snapshot(out) == before


def test_g21_refusal_writes_nothing_even_where_merging_was_possible(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    _replace_without_manifest(out / _USER_INIT)
    before = snapshot(out)
    with pytest.raises(_conflict_error()) as excinfo:
        _generate(gen_paths, out, [_X, _Y])
    assert _conflicts(excinfo, out) == {("mg/user/__init__.py", "NO_MANIFEST")}
    assert snapshot(out) == before


def test_g22_dry_run_reports_conflicts(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    _replace_without_manifest(out / _NS_INIT)
    before = snapshot(out)
    with pytest.raises(_conflict_error()) as dry:
        _generate(gen_paths, out, [_Y], dry_run=True)
    assert snapshot(out) == before
    with pytest.raises(_conflict_error()) as real:
        _generate(gen_paths, out, [_Y])
    assert _conflicts(dry, out) == _conflicts(real, out)
    assert snapshot(out) == before


def test_g23_dry_run_of_a_clean_merge_writes_nothing(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    before = snapshot(out)
    _generate(gen_paths, out, [_Y], dry_run=True)
    assert snapshot(out) == before


def test_g24_output_extension_change_writes_a_new_namespace_file(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    old = (out / _NS_INIT).read_bytes()
    _generate(gen_paths, out, [_X], output_extension=".gen.py")
    assert (out / _NS_INIT).read_bytes() == old
    assert _members(out / "mg" / "ns" / "__init__.gen.py") == {"mg.ns.A.1.0"}
    assert_namespace_consistent(out / "mg" / "ns" / "__init__.gen.py")
    assert_all_namespaces_consistent(out)


def test_g25_namespace_stem_change_writes_a_new_namespace_file(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    old = (out / _NS_INIT).read_bytes()
    _generate(gen_paths, out, [_X], namespace_output_stem="pkg")
    assert (out / _NS_INIT).read_bytes() == old
    assert _members(out / "mg" / "ns" / "pkg.py") == {"mg.ns.A.1.0"}
    assert_namespace_consistent(out / "mg" / "ns" / "pkg.py")
    assert_all_namespaces_consistent(out)


def test_g26_custom_template_with_the_helper_merges(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    templates = [gen_paths.test_dir / "templates_with_helper"]
    # Named exception: this custom template writes no aliases, so only the imports are checked.
    _generate(gen_paths, out, [_X], templates_dir=templates, check=False)
    _generate(gen_paths, out, [_Y], templates_dir=templates, check=False)
    assert _members(out / _NS_INIT) == {"mg.ns.A.1.0", "mg.ns.B.1.0"}
    assert _imports(out / _NS_INIT) == {"A_1_0", "B_1_0"}


def test_g27_custom_template_without_the_helper_is_refused_on_rerun(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    templates = [gen_paths.test_dir / "templates_without_helper"]
    _generate(gen_paths, out, [_X], templates_dir=templates, check=False)  # The template writes no manifest.
    with pytest.raises(_conflict_error()) as excinfo:
        _generate(gen_paths, out, [_Y], templates_dir=templates)
    assert ("mg/ns/__init__.py", "NO_MANIFEST") in _conflicts(excinfo, out)


def test_g28_content_only_options_merge(gen_paths: typing.Any, run_nnvg_main: typing.Callable) -> None:
    out = gen_paths.out_dir
    assert _nnvg(run_nnvg_main, gen_paths, out, [_X]).returncode == 0
    second = _nnvg(
        run_nnvg_main,
        gen_paths,
        out,
        [_Y],
        "--embed-auditing-info",
        "--omit-serialization-support",
        "--target-endianness",
        "little",
        "--enable-serialization-asserts",
    )
    assert second.returncode == 0
    assert _members(out / _NS_INIT) == {"mg.ns.A.1.0", "mg.ns.B.1.0"}
    assert_all_namespaces_consistent(out)


def test_g29_no_namespace_types_means_no_merging(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    _replace_without_manifest(out / _NS_INIT)
    old = (out / _NS_INIT).read_bytes()
    _generate(gen_paths, out, [_Y], generate_namespace_types=YesNoDefault.NO, check=False)  # Damaged on purpose.
    assert (out / _NS_INIT).read_bytes() == old
    assert (out / "mg" / "user" / "Y_1_0.py").exists()


def test_g30_support_only_means_no_merging(gen_paths: typing.Any, run_nnvg_main: typing.Callable) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    _replace_without_manifest(out / _NS_INIT)
    old = (out / _NS_INIT).read_bytes()
    assert _nnvg(run_nnvg_main, gen_paths, out, [_Y], "--generate-support", "only", check=False).returncode == 0
    assert (out / _NS_INIT).read_bytes() == old


def test_g31_list_outputs_is_unchanged(gen_paths: typing.Any, run_nnvg_main: typing.Callable) -> None:
    out = gen_paths.out_dir
    assert _nnvg(run_nnvg_main, gen_paths, out, [_X]).returncode == 0
    result = _nnvg(run_nnvg_main, gen_paths, out, [_Y], "--list-outputs", "--list-format", "csv")
    assert result.returncode == 0
    listed = {Path(p).resolve() for p in result.stdout.decode().replace("\n", ",").split(",") if p.strip()}
    for expected in (_NS_INIT, _USER_INIT, Path("mg", "ns", "B_1_0.py"), Path("mg", "user", "Y_1_0.py")):
        assert (out / expected).resolve() in listed
    assert (out / "mg" / "user" / "X_1_0.py").resolve() not in listed


def test_g32_no_overwrite_is_unchanged(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    with pytest.raises(PermissionError):
        _generate(gen_paths, out, [_Y], no_overwrite=True)


def _is_read_only(path: Path) -> bool:
    # Checks the permission bits rather than os.access, which reports every file writable when running as root.
    return (path.stat().st_mode & 0o222) == 0


def test_g33_read_only_files_are_merged(gen_paths: typing.Any, run_nnvg_main: typing.Callable) -> None:
    out = gen_paths.out_dir
    assert _nnvg(run_nnvg_main, gen_paths, out, [_X]).returncode == 0
    assert _is_read_only(out / _NS_INIT)
    assert _nnvg(run_nnvg_main, gen_paths, out, [_Y]).returncode == 0
    assert _members(out / _NS_INIT) == {"mg.ns.A.1.0", "mg.ns.B.1.0"}
    assert _is_read_only(out / _NS_INIT)
    assert_all_namespaces_consistent(out)


def test_g34_jobs_do_not_change_the_result(gen_paths: typing.Any, tmp_path: Path) -> None:
    manifests = []
    for jobs in (1, 0):
        out = tmp_path / f"jobs{jobs}"
        _generate(gen_paths, out, [_X], jobs=jobs)
        _generate(gen_paths, out, [_Y], jobs=jobs)
        manifest = _manifest(out / _NS_INIT)
        manifests.append((frozenset(manifest.members), manifest.digest))
        assert_all_namespaces_consistent(out)
    assert manifests[0] == manifests[1]


def test_g35_whitespace_post_processors_merge(gen_paths: typing.Any, run_nnvg_main: typing.Callable) -> None:
    out = gen_paths.out_dir
    flags = ("--pp-trim-trailing-whitespace", "--pp-max-emptylines", "1")
    assert _nnvg(run_nnvg_main, gen_paths, out, [_X], *flags).returncode == 0
    assert _nnvg(run_nnvg_main, gen_paths, out, [_Y], *flags).returncode == 0
    assert _members(out / _NS_INIT) == {"mg.ns.A.1.0", "mg.ns.B.1.0"}
    assert_all_namespaces_consistent(out)


def test_g36_reformatted_manifest_merges(gen_paths: typing.Any, run_nnvg_main: typing.Callable) -> None:
    out = gen_paths.out_dir
    flags = ("-pp-rp", (gen_paths.test_dir / "formatter.py").as_posix())
    assert _nnvg(run_nnvg_main, gen_paths, out, [_X], *flags).returncode == 0
    assert b"\r\n" in (out / _NS_INIT).read_bytes()
    assert _nnvg(run_nnvg_main, gen_paths, out, [_Y], *flags).returncode == 0
    assert _members(out / _NS_INIT) == {"mg.ns.A.1.0", "mg.ns.B.1.0"}
    assert_all_namespaces_consistent(out)


def test_g37_index_namespace_file_has_an_empty_manifest(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    _generate(gen_paths, out, [_X])
    assert _members(out / "__init__.py") == frozenset()
    assert_all_namespaces_consistent(out)


@pytest.mark.parametrize("list_flag", ["--list-outputs", "--list-inputs"])
def test_g38_list_only_runs_report_conflicts(
    gen_paths: typing.Any, run_nnvg_main: typing.Callable, list_flag: str
) -> None:
    out = gen_paths.out_dir
    assert _nnvg(run_nnvg_main, gen_paths, out, [_X]).returncode == 0
    _replace_without_manifest(out / _NS_INIT)
    before = snapshot(out)
    result = _nnvg(run_nnvg_main, gen_paths, out, [_Y], list_flag)
    assert result.returncode == 1
    assert result.stdout.decode().strip() == ""
    assert snapshot(out) == before


def test_g39_no_overwrite_reports_conflicts_first(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    _replace_without_manifest(out / _NS_INIT)
    before = snapshot(out)
    with pytest.raises(_conflict_error()) as excinfo:
        _generate(gen_paths, out, [_Y], no_overwrite=True)
    assert ("mg/ns/__init__.py", "NO_MANIFEST") in _conflicts(excinfo, out)
    assert snapshot(out) == before


@pytest.mark.parametrize("force", [False, True])
def test_g40_namespaces_differing_only_in_case_are_refused(
    gen_paths: typing.Any, tmp_path: Path, force: bool
) -> None:
    """
    On a case-insensitive filesystem cc/NS and cc/ns are one directory, so generating cc.ns finds cc.NS's namespace
    file at cc/ns/__init__.py. The test builds that state on any filesystem: it generates cc.NS elsewhere and places
    its namespace file at cc/ns/__init__.py, so the output directory never holds names differing only in case.
    """
    elsewhere = tmp_path / "elsewhere"
    _generate(gen_paths, elsewhere, ["case_c/cc/NS/Foo.1.0.dsdl"], roots=[gen_paths.dsdl_dir / "case_c" / "cc"])
    out = gen_paths.out_dir
    (out / "cc" / "ns").mkdir(parents=True)
    shutil.copyfile(elsewhere / "cc" / "NS" / "__init__.py", out / "cc" / "ns" / "__init__.py")
    before = snapshot(out)
    with pytest.raises(_conflict_error()) as excinfo:
        _generate(
            gen_paths, out, ["case_d/cc/ns/Bar.1.0.dsdl"], roots=[gen_paths.dsdl_dir / "case_d" / "cc"], force=force
        )
    assert ("cc/ns/__init__.py", "NAMESPACE_COLLISION") in _conflicts(excinfo, out)
    assert snapshot(out) == before


def test_g41a_namespace_file_of_another_namespace_is_a_namespace_collision(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X, _Y])
    user_init = (out / _USER_INIT).read_bytes()
    _make_writable(out / _NS_INIT)
    (out / _NS_INIT).write_bytes(user_init)
    for force in (False, True):
        with pytest.raises(_conflict_error()) as excinfo:
            _generate(gen_paths, out, [_X], force=force)
        assert ("mg/ns/__init__.py", "NAMESPACE_COLLISION") in _conflicts(excinfo, out)


def test_g41b_members_outside_the_recorded_namespace_are_refused(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    init_file = out / _NS_INIT
    text = init_file.read_text(encoding="utf-8")
    _make_writable(init_file)
    init_file.write_text(text.replace("#   mg.ns.A.1.0", "#   mg.ns.A.1.0\n#   mg.user.X.1.0"), encoding="utf-8")
    with pytest.raises(_conflict_error()) as excinfo:
        _generate(gen_paths, out, [_X])
    assert ("mg/ns/__init__.py", "NO_MANIFEST") in _conflicts(excinfo, out)


def test_g42_manifest_is_last_and_a_file_cut_before_it_is_refused(gen_paths: typing.Any) -> None:
    from nunavut._namespace_manifest import (  # pylint: disable=import-outside-toplevel
        MANIFEST_BEGIN,
        MANIFEST_END,
    )

    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X])
    for init_file in _python_namespace_files(out):
        text = init_file.read_text(encoding="utf-8")
        assert text[text.index(MANIFEST_END) + len(MANIFEST_END) :].strip() == ""
    init_file = out / _NS_INIT
    text = init_file.read_text(encoding="utf-8")
    _make_writable(init_file)
    init_file.write_text(text[: text.index(MANIFEST_BEGIN)], encoding="utf-8")
    assert "A_1_0" in _imports(init_file)
    with pytest.raises(_conflict_error()) as excinfo:
        _generate(gen_paths, out, [_X])
    assert ("mg/ns/__init__.py", "NO_MANIFEST") in _conflicts(excinfo, out)


def test_g43_recorded_member_in_a_stropped_namespace(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_K])
    _generate(gen_paths, out, [_L])
    init_file = out / "mg" / "import_" / "__init__.py"
    assert _members(init_file) == {"mg.import.K.1.0", "mg.import.L.1.0"}
    assert "from mg.import_.K_1_0 import K_1_0 as K_1_0" in _lines(init_file)
    assert_all_namespaces_consistent(out)


def test_g44_recorded_service_member(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_S])
    _generate(gen_paths, out, [_A10])
    assert _members(out / _NS_INIT) == {"mg.ns.S.1.0", "mg.ns.A.1.0"}
    assert "from mg.ns.S_1_0 import S_1_0 as S_1_0" in _lines(out / _NS_INIT)
    assert_all_namespaces_consistent(out)


@pytest.mark.parametrize("force", [False, True])
def test_g45_namespaces_stropping_to_one_directory_are_refused(gen_paths: typing.Any, force: bool) -> None:
    out = gen_paths.out_dir
    with pytest.raises(_conflict_error()) as excinfo:
        _generate(gen_paths, out, [_K, "mg/import_/J.1.0.dsdl"], force=force)
    assert ("mg/import_/__init__.py", "NAMESPACE_COLLISION") in _conflicts(excinfo, out)
    assert snapshot(out) == {}


@pytest.mark.parametrize("force", [False, True])
def test_g48_namespaces_stropping_to_one_directory_across_runs_are_refused(gen_paths: typing.Any, force: bool) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_K])
    before = snapshot(out)
    with pytest.raises(_conflict_error()) as excinfo:
        _generate(gen_paths, out, ["mg/import_/J.1.0.dsdl"], force=force)
    assert ("mg/import_/__init__.py", "NAMESPACE_COLLISION") in _conflicts(excinfo, out)
    assert snapshot(out) == before


def test_g46_namespaces_differing_only_in_case_within_one_run_are_refused(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    roots = [gen_paths.dsdl_dir / "case_e" / "CC", gen_paths.dsdl_dir / "case_f" / "cc"]
    with pytest.raises(_conflict_error()) as excinfo:
        _generate(gen_paths, out, ["case_e/CC/x/Foo.1.0.dsdl", "case_f/cc/y/Bar.1.0.dsdl"], roots=roots)
    assert {kind for _, kind in _conflicts(excinfo, out)} == {"NAMESPACE_COLLISION"}
    assert {path.casefold() for path, _ in _conflicts(excinfo, out)} == {"cc/__init__.py"}
    assert snapshot(out) == {}


def test_g47_namespace_without_types_differing_only_in_case_is_refused(
    gen_paths: typing.Any, tmp_path: Path
) -> None:
    """
    On a case-insensitive filesystem cc/ is CC/, so generating cc.y finds CC's namespace file, which records namespace
    CC and has no types. The test builds that state on any filesystem, as in G40.
    """
    elsewhere = tmp_path / "elsewhere"
    _generate(gen_paths, elsewhere, ["case_e/CC/x/Foo.1.0.dsdl"], roots=[gen_paths.dsdl_dir / "case_e" / "CC"])
    out = gen_paths.out_dir
    (out / "cc").mkdir()
    shutil.copyfile(elsewhere / "CC" / "__init__.py", out / "cc" / "__init__.py")
    before = snapshot(out)
    with pytest.raises(_conflict_error()) as excinfo:
        _generate(gen_paths, out, ["case_f/cc/y/Bar.1.0.dsdl"], roots=[gen_paths.dsdl_dir / "case_f" / "cc"])
    assert ("cc/__init__.py", "NAMESPACE_COLLISION") in _conflicts(excinfo, out)
    assert snapshot(out) == before


# +---------------------------------------------------------------------------+
# | L: other languages
# +---------------------------------------------------------------------------+


@pytest.mark.parametrize("language", ["c", "cpp"])
def test_l1_c_and_cpp_are_order_independent_and_have_no_manifest(
    gen_paths: typing.Any, tmp_path: Path, language: str
) -> None:
    sequential = tmp_path / "sequential"
    _generate(gen_paths, sequential, [_X], language=language)
    _generate(gen_paths, sequential, [_Y], language=language)
    together = tmp_path / "together"
    _generate(gen_paths, together, [_X, _Y], language=language)
    files = snapshot(sequential)
    assert files == snapshot(together)
    assert not any(_MANIFEST_BEGIN_TEXT.encode() in data for data in files.values())


def test_l2_html_is_not_merged(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    _generate(gen_paths, out, [_X], language="html")
    _generate(gen_paths, out, [_Y], language="html")
    for page in out.rglob("index.html"):
        assert _MANIFEST_BEGIN_TEXT not in page.read_text(encoding="utf-8")


def test_l3_python_and_c_generate_the_same_types(gen_paths: typing.Any, tmp_path: Path) -> None:
    def type_files(out: Path, suffix: str) -> typing.Set[str]:
        return {
            p.relative_to(out).with_suffix("").as_posix()
            for p in (out / "mg").rglob(f"*{suffix}")
            if re.fullmatch(r"\w+_\d+_\d+", p.stem)
        }

    outputs = {}
    for language, suffix in (("py", ".py"), ("c", ".h")):
        out = tmp_path / language
        _generate(gen_paths, out, [_X], language=language)
        _generate(gen_paths, out, [_Y], language=language)
        outputs[language] = type_files(out, suffix)
    assert outputs["py"] == outputs["c"] == {"mg/ns/A_1_0", "mg/ns/B_1_0", "mg/user/X_1_0", "mg/user/Y_1_0"}


# +---------------------------------------------------------------------------+
# | A: API and CLI
# +---------------------------------------------------------------------------+

# The parameters of each function before this change, in order.
_ORIGINAL_PARAMETERS = {
    "generate_all": [
        "target_language",
        "target_files",
        "root_namespace_directories_or_names",
        "outdir",
        "language_options",
        "include_experimental_languages",
        "resource_types",
        "embed_auditing_info",
        "dry_run",
        "jobs",
        "no_overwrite",
        "allow_unregulated_fixed_port_id",
        "omit_dependencies",
        "code_generator_type",
        "support_generator_type",
    ],
    "generate_all_for_language": [
        "language_context",
        "target_files",
        "root_namespace_directories_or_names",
        "outdir",
        "resource_types",
        "embed_auditing_info",
        "dry_run",
        "jobs",
        "no_overwrite",
        "allow_unregulated_fixed_port_id",
        "omit_dependencies",
        "code_generator_type",
        "support_generator_type",
    ],
    "generate_all_from_namespace": [
        "index",
        "resource_types",
        "embed_auditing_info",
        "dry_run",
        "no_overwrite",
        "code_generator_type",
        "support_generator_type",
    ],
    "generate_all_from_namespace_with_generators": [
        "index",
        "code_generator",
        "support_generator",
        "dry_run",
        "no_overwrite",
    ],
}


@pytest.mark.parametrize("function_name", sorted(_ORIGINAL_PARAMETERS))
def test_a1_force_is_added_last(function_name: str) -> None:
    parameters = inspect.signature(getattr(nunavut, function_name)).parameters.values()
    named = [p.name for p in parameters if p.kind is not inspect.Parameter.VAR_KEYWORD]
    assert named == _ORIGINAL_PARAMETERS[function_name] + ["force"]


def test_a2_positional_calls_still_work(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    result = generate_all(
        "py",
        [gen_paths.dsdl_dir / _X],
        [gen_paths.dsdl_dir / "mg"],
        out,
        None,
        False,
        ResourceType.ANY.value,
        False,
        False,
        1,
        False,
        False,
        False,
        None,
        None,
    )
    assert (out / "mg" / "user" / "X_1_0.py").exists()
    assert_all_namespaces_consistent(out)
    assert len(result.generated_files) > 0


def _python_language_context() -> typing.Any:
    return LanguageContextBuilder().set_target_language("py").create()


def test_a2_positional_calls_still_work_for_language(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    generate_all_for_language(
        _python_language_context(),
        [gen_paths.dsdl_dir / _X],
        [gen_paths.dsdl_dir / "mg"],
        out,
        ResourceType.ANY.value,
        False,
        False,
        1,
        False,
        False,
        False,
        None,
        None,
    )
    assert (out / "mg" / "user" / "X_1_0.py").exists()
    assert_all_namespaces_consistent(out)


def test_a2_positional_calls_still_work_for_namespace(gen_paths: typing.Any) -> None:
    out = gen_paths.out_dir
    index = Namespace.read_files(
        out, _python_language_context(), [gen_paths.dsdl_dir / _X], [gen_paths.dsdl_dir / "mg"], 1
    )
    generate_all_from_namespace(index, ResourceType.ANY.value, False, False, False, None, None)
    assert (out / "mg" / "user" / "X_1_0.py").exists()
    assert_all_namespaces_consistent(out)


def test_a3_nnvg_reports_a_refusal(
    gen_paths: typing.Any, run_nnvg_main: typing.Callable, caplog: pytest.LogCaptureFixture
) -> None:
    out = gen_paths.out_dir
    assert _nnvg(run_nnvg_main, gen_paths, out, [_X]).returncode == 0
    _replace_without_manifest(out / _NS_INIT)
    assert _nnvg(run_nnvg_main, gen_paths, out, [_Y]).returncode == 1
    assert "mg" in caplog.text
    assert "__init__.py" in caplog.text
    assert "--force" in caplog.text
    assert "Traceback" not in caplog.text


def test_a4_nnvg_force_is_accepted(gen_paths: typing.Any, run_nnvg_main: typing.Callable) -> None:
    out = gen_paths.out_dir
    assert _nnvg(run_nnvg_main, gen_paths, out, [_X]).returncode == 0
    _replace_without_manifest(out / _NS_INIT)
    assert _nnvg(run_nnvg_main, gen_paths, out, [_Y], "--force").returncode == 0


def test_a6_each_conflict_kind_has_an_accurate_message() -> None:
    from nunavut import (  # pylint: disable=import-outside-toplevel
        NamespaceConflict,
        NamespaceConflictError,
        NamespaceConflictKind,
    )

    force_advice = "--force"
    case_advice = "Types whose files differ only in letter case"
    namespace_advice = "Namespaces whose names differ only in letter case"
    expectations = {
        NamespaceConflictKind.NO_MANIFEST: (True, False, False),
        NamespaceConflictKind.NAMING_CHANGED: (True, False, False),
        NamespaceConflictKind.CASE_COLLISION: (False, True, False),
        NamespaceConflictKind.NAMESPACE_COLLISION: (False, False, True),
    }
    for kind, (forced, case, namespace) in expectations.items():
        message = str(NamespaceConflictError([NamespaceConflict(Path("ns", "__init__.py"), kind, "detail")]))
        assert str(Path("ns", "__init__.py")) in message
        assert kind.value in message
        assert "(detail)" in message
        assert (force_advice in message) == forced, kind
        assert (case_advice in message) == case, kind
        assert (namespace_advice in message) == namespace, kind
        assert kind.can_be_forced == forced


def test_a5_conflict_error_is_exported() -> None:
    from nunavut import NamespaceConflictError  # pylint: disable=import-outside-toplevel

    assert issubclass(NamespaceConflictError, Exception)
