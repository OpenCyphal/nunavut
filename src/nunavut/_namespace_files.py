#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Conflict detection for generated namespace files (for example a Python package's ``__init__.py``).

A namespace file lists the types generated into its namespace. Generating into an output directory that already holds
a namespace file is only safe if no type it lists would be dropped, so every namespace file carries a marker naming its
members::

    nunavut-namespace-members-begin
        my.othertype.bar.1.0
    nunavut-namespace-members-end

The marker is read without regard to whitespace, line breaks, or the comment syntax around it, so running a formatter
over generated code does not change what it says.
See https://github.com/OpenCyphal/nunavut/issues/403.
"""

import logging
import re
import stat
from pathlib import Path
from typing import FrozenSet, Iterator, List, Optional, Set, Tuple, cast

import pydsdl

from ._namespace import Namespace
from .lang import Language
from .lang._common import IncludeGenerator

NAMESPACE_MEMBERS_BEGIN = "nunavut-namespace-members-begin"  #: Starts the member list in a namespace file.
NAMESPACE_MEMBERS_END = "nunavut-namespace-members-end"  #: Ends the member list in a namespace file.

# A versioned DSDL type name: dotted identifiers followed by the major and minor version.
_MEMBER_PATTERN = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\.\d+\.\d+")

_logger = logging.getLogger(__name__)


class NamespaceConflictError(RuntimeError):
    """
    Raised when generating would replace a namespace file that lists types this generation would drop, or a namespace
    file without a member list. Generating with ``force`` removes the previously generated files instead.
    """


def namespace_member_name(data_type: pydsdl.CompositeType) -> str:
    """
    The name a namespace file's member list uses for a type, e.g. ``my.othertype.bar.1.0``.

    .. invisible-code-block: python

        from unittest.mock import MagicMock
        from nunavut._namespace_files import namespace_member_name

        t = MagicMock()
        t.full_name = "my.othertype.bar"
        t.version.major = 1
        t.version.minor = 0

    .. code-block:: python

        assert namespace_member_name(t) == "my.othertype.bar.1.0"
    """
    return f"{data_type.full_name}.{data_type.version.major}.{data_type.version.minor}"


def read_namespace_members(namespace_file: Path) -> Optional[FrozenSet[str]]:
    """
    Reads the member list from a generated namespace file.

    .. invisible-code-block: python

        from pathlib import Path
        import tempfile
        from nunavut._namespace_files import read_namespace_members

    .. code-block:: python

        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "__init__.py"
            # Whitespace, line breaks, and comment characters around the names do not matter.
            f.write_text("#   nunavut-namespace-members-begin\\r\\n#\\tmy.a.1.0   my.b.2.1\\n# nunavut-namespace-members-end")
            assert read_namespace_members(f) == {"my.a.1.0", "my.b.2.1"}
            f.write_text("# nunavut-namespace-members-begin\\n# nunavut-namespace-members-end")
            assert read_namespace_members(f) == set()
            f.write_text("from my.a_1_0 import a_1_0")
            assert read_namespace_members(f) is None

    :param namespace_file: The file to read.
    :return: The member names, or None if the file has no member list.
    """
    text = namespace_file.read_text(encoding="utf-8", errors="replace")
    begin = text.find(NAMESPACE_MEMBERS_BEGIN)
    if begin < 0:
        return None
    end = text.find(NAMESPACE_MEMBERS_END, begin + len(NAMESPACE_MEMBERS_BEGIN))
    if end < 0:
        return None
    return frozenset(_MEMBER_PATTERN.findall(text[begin + len(NAMESPACE_MEMBERS_BEGIN) : end]))


def find_namespace_conflicts(index: Namespace) -> List[Tuple[Path, Optional[FrozenSet[str]]]]:
    """
    Finds the namespace files that generating ``index`` would overwrite unsafely.

    A namespace file that already exists may be overwritten if the new one lists all of its members (the same types,
    or more). Otherwise it conflicts: either it would drop members, or it has no member list so it cannot be checked.

    :param index: The index namespace of the types to generate.
    :return: For each conflicting file, its path and the members it would drop (None if it has no member list).
    """
    conflicts: List[Tuple[Path, Optional[FrozenSet[str]]]] = []
    for namespace, output_path in index.get_all_namespaces():
        if not output_path.exists():
            continue
        existing = read_namespace_members(output_path)
        if existing is None:
            conflicts.append((output_path, None))
            continue
        generating = {namespace_member_name(t) for t, _ in namespace.get_nested_types()}
        dropped = existing - generating
        if dropped:
            conflicts.append((output_path, frozenset(dropped)))
    return conflicts


def describe_namespace_conflicts(conflicts: List[Tuple[Path, Optional[FrozenSet[str]]]]) -> str:
    """
    A message explaining why generation was refused, listing each conflicting file.
    """
    lines = ["Generating would replace namespace files that list types this generation does not include:"]
    for path, dropped in conflicts:
        if dropped is None:
            lines.append(f"  {path}: has no list of its types (it was not generated by this version of nunavut)")
        else:
            lines.append(f"  {path}: would drop {', '.join(sorted(dropped))}")
    lines.append(
        "Generate all of these types in one run, use a separate output directory, or use --force to remove the "
        "previously generated files first."
    )
    return "\n".join(lines)


def remove_generated_namespaces(index: Namespace, dry_run: bool) -> List[Path]:
    """
    Removes previously generated output from the index's output directory: every namespace file that has a member
    list, and the files generated for each of its members. A namespace file without a member list is removed only if
    this generation would overwrite it. Other files are not touched. Directories left empty are removed.

    Namespace files are found by their member list, not by name, so output from a run that used a different
    namespace file stem or file extension is removed too. A member's file has the same extension as the namespace
    file that lists it, which may be compound (e.g. ``.gen.py``), so each member's file is looked for under the
    namespace file's last suffix, all of its suffixes, and this run's extension. Only files with exactly those names
    are removed.

    :param index: The index namespace of the types about to be generated.
    :param dry_run: If True then only log what would be removed.
    :return: The files removed (or that would be removed).
    """
    language = index.get_language_context().get_target_language()
    output_root = index.output_folder
    current_extension = language.get_config_value(Language.WKCV_DEFINITION_FILE_EXTENSION)

    to_remove: Set[Path] = set()
    for namespace_file, members in _find_namespace_files(output_root):
        to_remove.add(namespace_file)
        to_remove.update(_member_files(namespace_file, members, output_root, language, current_extension))
    # Namespace files without a member list are removed only because this generation overwrites them anyway.
    to_remove.update(path for _, path in index.get_all_namespaces())

    removed = sorted(path for path in to_remove if path.exists())
    for path in removed:
        _logger.info("%s previously generated file: %s", "Would remove" if dry_run else "Removing", path)
    if not dry_run:
        for path in removed:
            _unlink_generated_file(path)
        _remove_empty_directories({path.parent for path in removed}, output_root)
    return removed


# +---------------------------------------------------------------------------+
# | PRIVATE
# +---------------------------------------------------------------------------+


class _MemberRef:
    """
    The parts of a type that :meth:`IncludeGenerator.make_path` uses, parsed from a member name.
    """

    def __init__(self, member: str):
        *namespace, short_name, major, minor = member.split(".")
        self.full_namespace = ".".join(namespace)
        self.short_name = short_name
        self.version = pydsdl.Version(major=int(major), minor=int(minor))


def _find_namespace_files(output_root: Path) -> Iterator[Tuple[Path, FrozenSet[str]]]:
    """
    Yields each file under output_root that has a member list, with its members.
    """
    for candidate in output_root.rglob("*"):
        if candidate.is_file() and _starts_with_member_list(candidate):
            members = read_namespace_members(candidate)
            if members is not None:
                yield candidate, members


def _member_files(
    namespace_file: Path, members: FrozenSet[str], output_root: Path, language: Language, current_extension: str
) -> Iterator[Path]:
    """
    Yields the paths the members of a namespace file may have been generated at. A member's file has the namespace
    file's extension, but the stem may contain dots and the extension may be compound (e.g. ``.gen.py``), so the
    extension can't be split off for sure: try the last suffix, all suffixes, and this run's extension.
    """
    extensions = {namespace_file.suffix, "".join(namespace_file.suffixes), current_extension}
    for member in members:
        member_ref = cast(pydsdl.CompositeType, _MemberRef(member))
        for extension in extensions:
            yield output_root / IncludeGenerator.make_path(member_ref, language, extension)


# Generated namespace files put the start of their member list near the top, so only this much of each file under the
# output directory is read when looking for them.
_MEMBER_LIST_SEARCH_BYTES = 16 * 1024


def _starts_with_member_list(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return NAMESPACE_MEMBERS_BEGIN.encode("ascii") in f.read(_MEMBER_LIST_SEARCH_BYTES)
    except OSError:
        return False


def _unlink_generated_file(path: Path) -> None:
    try:
        path.unlink()
    except PermissionError:
        # Generated files are read-only by default (nnvg --file-mode) and Windows refuses to delete read-only files.
        path.chmod(path.stat().st_mode | stat.S_IWRITE)
        path.unlink()


def _remove_empty_directories(directories: Set[Path], output_root: Path) -> None:
    for directory in sorted(directories, key=lambda d: len(d.parts), reverse=True):
        while directory != output_root and output_root in directory.parents:
            try:
                directory.rmdir()  # Only succeeds if the directory is empty.
            except OSError:
                break
            directory = directory.parent
