#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Tests for generating into an output directory that already holds generated namespace files
(https://github.com/OpenCyphal/nunavut/issues/403).

The fixture is one root namespace ``my``: ``my.thistype.Foo.1.0`` depends on ``my.othertype.Bar.1.0``, and
``my.othertype.Baz.1.0`` is another type in Bar's namespace that nothing depends on.
"""

import inspect
import re
import typing
from pathlib import Path

import pytest

from nunavut import (
    NamespaceConflictError,
    generate_all,
    generate_all_for_language,
    generate_all_from_namespace,
    generate_all_from_namespace_with_generators,
)
from nunavut._namespace_files import read_namespace_members

_BAR = "my.othertype.Bar.1.0"
_BAZ = "my.othertype.Baz.1.0"


def _target(gen_paths: typing.Any, name: str) -> Path:
    return {
        "foo": gen_paths.dsdl_dir / "my" / "thistype" / "Foo.1.0.dsdl",
        "bar": gen_paths.dsdl_dir / "my" / "othertype" / "Bar.1.0.dsdl",
        "baz": gen_paths.dsdl_dir / "my" / "othertype" / "Baz.1.0.dsdl",
    }[name]


def _generate(
    gen_paths: typing.Any, language: str, targets: typing.List[str], outdir: Path, **kwargs: typing.Any
) -> typing.Any:
    return generate_all(
        language,
        [_target(gen_paths, t) for t in targets],
        [gen_paths.dsdl_dir / "my"],
        outdir,
        include_experimental_languages=True,
        **kwargs,
    )


def _type_files(outdir: Path, suffix: str) -> typing.Set[str]:
    """The generated type files under outdir/my, as paths relative to outdir without their suffix."""
    return {
        p.relative_to(outdir).with_suffix("").as_posix()
        for p in (outdir / "my").rglob(f"*{suffix}")
        if re.fullmatch(r"\w+_\d+_\d+", p.stem)
    }


def _othertype_init(outdir: Path) -> Path:
    return outdir / "my" / "othertype" / "__init__.py"


def test_py_generates_the_same_dependencies_as_c(gen_paths: typing.Any) -> None:
    """
    Python generates the targets and their dependencies, like C: Foo and Bar but not Baz, which only shares Bar's
    namespace. The namespace file lists only what was generated.
    """
    py_out = gen_paths.out_dir / "py"
    c_out = gen_paths.out_dir / "c"
    _generate(gen_paths, "py", ["foo"], py_out)
    _generate(gen_paths, "c", ["foo"], c_out)

    assert _type_files(py_out, ".py") == {"my/thistype/Foo_1_0", "my/othertype/Bar_1_0"}
    assert _type_files(py_out, ".py") == _type_files(c_out, ".h")
    assert read_namespace_members(_othertype_init(py_out)) == {_BAR}


def test_py_regenerating_the_same_types_is_allowed(gen_paths: typing.Any) -> None:
    """
    Generating the same types again into the same directory is idempotent.
    """
    _generate(gen_paths, "py", ["foo"], gen_paths.out_dir)
    first = _othertype_init(gen_paths.out_dir).read_text(encoding="utf-8")
    _generate(gen_paths, "py", ["foo"], gen_paths.out_dir)

    second = _othertype_init(gen_paths.out_dir).read_text(encoding="utf-8")
    assert re.sub("Generated at:.*", "", first) == re.sub("Generated at:.*", "", second)


def test_py_generating_more_types_into_a_namespace_is_allowed(gen_paths: typing.Any) -> None:
    """
    A run whose namespace file lists every type the existing one lists, plus more, may replace it.
    """
    _generate(gen_paths, "py", ["foo"], gen_paths.out_dir)
    _generate(gen_paths, "py", ["foo", "baz"], gen_paths.out_dir)

    init_file = _othertype_init(gen_paths.out_dir)
    assert read_namespace_members(init_file) == {_BAR, _BAZ}
    imports = [line for line in init_file.read_text(encoding="utf-8").splitlines() if line.startswith("from ")]
    assert imports == sorted(imports)


@pytest.mark.parametrize("dry_run", [False, True])
def test_py_dropping_a_type_is_refused_and_nothing_is_written(gen_paths: typing.Any, dry_run: bool) -> None:
    """
    Generating Baz on top of the Foo run would rewrite my/othertype/__init__.py without Bar, so it is refused before
    anything is written. A dry run reports the same refusal.
    """
    _generate(gen_paths, "py", ["foo"], gen_paths.out_dir)
    init_file = _othertype_init(gen_paths.out_dir)
    before = init_file.read_text(encoding="utf-8")

    with pytest.raises(NamespaceConflictError) as error:
        _generate(gen_paths, "py", ["baz"], gen_paths.out_dir, dry_run=dry_run)

    assert str(init_file) in str(error.value)
    assert _BAR in str(error.value)
    assert init_file.read_text(encoding="utf-8") == before
    assert not (gen_paths.out_dir / "my" / "othertype" / "Baz_1_0.py").exists()


def test_py_force_replaces_the_previous_output(gen_paths: typing.Any) -> None:
    """
    With force, the previously generated types and namespace files are removed first, leaving just Baz.
    """
    _generate(gen_paths, "py", ["foo"], gen_paths.out_dir)
    unrelated = gen_paths.out_dir / "my" / "othertype" / "notes.txt"
    unrelated.write_text("not generated", encoding="utf-8")

    _generate(gen_paths, "py", ["baz"], gen_paths.out_dir, force=True)

    assert _type_files(gen_paths.out_dir, ".py") == {"my/othertype/Baz_1_0"}
    assert read_namespace_members(_othertype_init(gen_paths.out_dir)) == {_BAZ}
    assert not (gen_paths.out_dir / "my" / "thistype").exists()
    assert unrelated.exists()


def test_py_force_removes_output_generated_with_another_namespace_stem(gen_paths: typing.Any) -> None:
    """
    Previously generated namespace files are found by their member list, not by name, so forcing a run that uses a
    different namespace file stem still removes the earlier output.
    """
    _generate(gen_paths, "py", ["foo"], gen_paths.out_dir)
    _generate(gen_paths, "py", ["baz"], gen_paths.out_dir, force=True, namespace_output_stem="_ns_")

    assert _type_files(gen_paths.out_dir, ".py") == {"my/othertype/Baz_1_0"}
    assert not _othertype_init(gen_paths.out_dir).exists()
    assert read_namespace_members(gen_paths.out_dir / "my" / "othertype" / "_ns_.py") == {_BAZ}


def test_py_force_removes_output_generated_with_a_compound_extension(gen_paths: typing.Any) -> None:
    """
    Member files generated with a compound extension (e.g. .gen.py) are found from their namespace file's full
    extension, so forcing a run with the default extension removes them.
    """
    _generate(gen_paths, "py", ["foo"], gen_paths.out_dir, output_extension=".gen.py")
    old_files = [
        gen_paths.out_dir / "my" / "thistype" / "Foo_1_0.gen.py",
        gen_paths.out_dir / "my" / "othertype" / "Bar_1_0.gen.py",
        gen_paths.out_dir / "my" / "othertype" / "__init__.gen.py",
    ]
    assert all(f.exists() for f in old_files)

    _generate(gen_paths, "py", ["baz"], gen_paths.out_dir, force=True)

    assert not any(f.exists() for f in old_files)
    assert _type_files(gen_paths.out_dir, ".py") == {"my/othertype/Baz_1_0"}


def test_force_does_not_shift_positional_parameters() -> None:
    """
    force was added after the existing parameters, so positional callers of the generate_all functions are unaffected.
    """
    for function in (generate_all, generate_all_for_language, generate_all_from_namespace):
        names = [p.name for p in inspect.signature(function).parameters.values()]
        assert names[-3:] == ["support_generator_type", "force", names[-1]]
        assert names[-4] == "code_generator_type"
    names = list(inspect.signature(generate_all_from_namespace_with_generators).parameters)
    assert names[-2:] == ["no_overwrite", "force"]


def test_py_force_dry_run_removes_nothing(gen_paths: typing.Any) -> None:
    """
    A forced dry run leaves the previous output in place.
    """
    _generate(gen_paths, "py", ["foo"], gen_paths.out_dir)
    _generate(gen_paths, "py", ["baz"], gen_paths.out_dir, force=True, dry_run=True)

    assert _type_files(gen_paths.out_dir, ".py") == {"my/thistype/Foo_1_0", "my/othertype/Bar_1_0"}


def test_py_member_list_is_read_regardless_of_formatting(gen_paths: typing.Any) -> None:
    """
    Reformatting a generated namespace file (indentation, line endings, line breaks) does not change its member list,
    so regenerating the same types is still allowed.
    """
    _generate(gen_paths, "py", ["foo", "baz"], gen_paths.out_dir)
    init_file = _othertype_init(gen_paths.out_dir)
    init_file.chmod(0o644)
    text = init_file.read_text(encoding="utf-8")
    reformatted = re.sub(
        r"(nunavut-namespace-members-begin).*?(# nunavut-namespace-members-end)",
        lambda m: f"{m.group(1)}\r\n#{' ' * 9}{_BAZ}    {_BAR}\r\n#\r\n{m.group(2)}",
        text,
        flags=re.DOTALL,
    ).replace("\n", "\r\n")
    assert reformatted != text
    init_file.write_bytes(reformatted.encode("utf-8"))

    assert read_namespace_members(init_file) == {_BAR, _BAZ}
    _generate(gen_paths, "py", ["foo", "baz"], gen_paths.out_dir)


def test_py_namespace_file_without_a_member_list_is_refused(gen_paths: typing.Any) -> None:
    """
    A namespace file without a member list (e.g. from an older nunavut) can't be checked, so replacing it is refused
    unless forced.
    """
    _generate(gen_paths, "py", ["foo"], gen_paths.out_dir)
    init_file = _othertype_init(gen_paths.out_dir)
    init_file.chmod(0o644)
    init_file.write_text("from my.othertype.Bar_1_0 import Bar_1_0 as Bar_1_0\n", encoding="utf-8")

    with pytest.raises(NamespaceConflictError, match="has no list of its types"):
        _generate(gen_paths, "py", ["foo"], gen_paths.out_dir)

    _generate(gen_paths, "py", ["foo"], gen_paths.out_dir, force=True)
    assert read_namespace_members(init_file) == {_BAR}


def test_html_dropping_a_type_is_refused(gen_paths: typing.Any) -> None:
    """
    HTML namespace pages carry the same member list.
    """
    _generate(gen_paths, "html", ["foo"], gen_paths.out_dir)
    index_page = gen_paths.out_dir / "my" / "othertype" / "index.html"
    assert read_namespace_members(index_page) == {_BAR}

    with pytest.raises(NamespaceConflictError):
        _generate(gen_paths, "html", ["baz"], gen_paths.out_dir)


def test_c_has_no_namespace_files_to_conflict(gen_paths: typing.Any) -> None:
    """
    C generates one file per type and no namespace files, so generating Baz after Foo just adds Baz.
    """
    _generate(gen_paths, "c", ["foo"], gen_paths.out_dir)
    _generate(gen_paths, "c", ["baz"], gen_paths.out_dir)

    assert _type_files(gen_paths.out_dir, ".h") == {
        "my/thistype/Foo_1_0",
        "my/othertype/Bar_1_0",
        "my/othertype/Baz_1_0",
    }


def test_nnvg_refuses_without_force(
    gen_paths: typing.Any, run_nnvg_main: typing.Callable, caplog: pytest.LogCaptureFixture
) -> None:
    """
    nnvg reports a refusal as an error with a non-zero exit code, and --force replaces the previous output.
    """

    def nnvg(target: str, *extra: str) -> typing.Any:
        args = [
            "--target-language",
            "py",
            "--outdir",
            gen_paths.out_dir.as_posix(),
            "--lookup-dir",
            (gen_paths.dsdl_dir / "my").as_posix(),
            *extra,
            _target(gen_paths, target).as_posix(),
        ]
        return run_nnvg_main(gen_paths, args)

    assert nnvg("foo").returncode == 0
    assert nnvg("baz").returncode == 1
    assert "--force" in caplog.text
    assert nnvg("baz", "--force").returncode == 0
    assert _type_files(gen_paths.out_dir, ".py") == {"my/othertype/Baz_1_0"}
