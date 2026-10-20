#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Append-only merging of generated namespace files.

Some target languages generate a namespace file that lists the types in a namespace (for Python, a package's
``__init__.py``). When nnvg generates into an output directory that already holds generated output, each namespace
file it writes is merged with the existing one: the types the existing file lists are kept and this run's types are
added. Generation never deletes files.

To do that, every namespace file carries a manifest: a comment, written last by the namespace template through the
``namespace_manifest_lines`` filter, that records the file's namespace, its members, and a digest of how they were
named::

    nunavut-namespace-manifest-begin
      namespace:uavcan.primitive
      naming-digest sha256:<64 hex digits>
      uavcan.primitive.Empty.1.0
      uavcan.primitive.String.1.0
    nunavut-namespace-manifest-end

The manifest is read without regard to whitespace, line breaks, line endings, or the comment syntax around it, so
reformatting generated code doesn't change it.

A merge that can't be done by appending is a conflict, and generation is refused before anything is written:

* :attr:`NamespaceConflictKind.NO_MANIFEST`: the existing namespace file has no valid manifest: none at all, one cut
  short, or one whose members don't belong to its namespace. ``force`` writes it with this run's members only.
* :attr:`NamespaceConflictKind.NAMING_CHANGED`: this run would name the recorded members differently than the run
  that wrote them, so the recorded digest doesn't match. ``force`` writes it with this run's members only.
* :attr:`NamespaceConflictKind.CASE_COLLISION`: two members' files would differ only in letter case. This can't be
  forced.
* :attr:`NamespaceConflictKind.NAMESPACE_COLLISION`: two DSDL namespaces would share one namespace file, because their
  names differ only in letter case (on a case-insensitive filesystem) or strop to the same directory. Detected within
  a run, by comparing namespace files' paths ignoring case, and across runs, by the namespace the existing file
  records. This can't be forced.

See https://github.com/OpenCyphal/nunavut/issues/403 for the design.
"""

import enum
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Tuple, Union, cast

import pydsdl

from .lang import Language
from .lang._common import IncludeGenerator
from .lang._language import LanguageClassLoader

MANIFEST_BEGIN = "nunavut-namespace-manifest-begin"  #: Starts the manifest in a generated namespace file.
MANIFEST_END = "nunavut-namespace-manifest-end"  #: Ends the manifest in a generated namespace file.

# A versioned DSDL type name, e.g. uavcan.primitive.String.1.0, not part of a longer dotted token.
_MEMBER_PATTERN = re.compile(r"(?<![\w.:])[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\.\d+\.\d+(?![\w.])")
_DIGEST_PATTERN = re.compile(r"(?<![\w:])sha256:[0-9a-f]{64}(?![\w])")
# The namespace token: "namespace:" and the namespace's DSDL name, which is empty for the output root.
_NAMESPACE_PATTERN = re.compile(r"(?<![\w.:-])namespace:([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)?(?![\w.:])")


@dataclass(frozen=True)
class NamespaceManifest:
    """
    The manifest read from a generated namespace file.
    """

    members: FrozenSet[str]
    """The versioned names of the types the namespace file lists, e.g. ``uavcan.primitive.String.1.0``."""

    digest: str
    """The naming digest, ``sha256:`` followed by 64 hex digits."""

    namespace: str
    """The DSDL name of the namespace the file belongs to (empty for the output directory's root namespace file)."""


def parse_manifest(data: Union[bytes, str]) -> Optional[NamespaceManifest]:
    """
    Reads the manifest from the contents of a generated namespace file.

    .. invisible-code-block: python

        from nunavut._namespace_manifest import parse_manifest

    .. code-block:: python

        text = '''
        # nunavut-namespace-manifest-begin
        #     namespace:uavcan.primitive
        #     naming-digest sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
        #     uavcan.primitive.Empty.1.0     uavcan.primitive.String.1.0
        # nunavut-namespace-manifest-end
        '''
        manifest = parse_manifest(text)
        assert manifest.members == {"uavcan.primitive.Empty.1.0", "uavcan.primitive.String.1.0"}
        assert manifest.namespace == "uavcan.primitive"

        # A manifest that was cut off, or doesn't have exactly one digest and one namespace, is not a manifest.
        assert parse_manifest(text.split("nunavut-namespace-manifest-end")[0]) is None

    :param data: The file's contents. Bytes that aren't valid UTF-8 have no manifest.
    :return: The manifest, or None if there is no complete, valid manifest.
    """
    if isinstance(data, bytes):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return None
    else:
        text = data
    begin = text.find(MANIFEST_BEGIN)
    if begin < 0:
        return None
    body_start = begin + len(MANIFEST_BEGIN)
    end = text.find(MANIFEST_END, body_start)
    if end < 0:
        return None
    body = text[body_start:end]
    digests = _DIGEST_PATTERN.findall(body)
    namespaces = _NAMESPACE_PATTERN.findall(body)
    if len(digests) != 1 or len(namespaces) != 1:
        return None
    return NamespaceManifest(frozenset(_MEMBER_PATTERN.findall(body)), digests[0], namespaces[0])


def naming_digest(namespace_file_name: str, entries: Iterable[Tuple[str, str, str]]) -> str:
    """
    The naming digest of a namespace file's members.

    It's the SHA-256 of the namespace file's name and a newline, followed by one line per member, sorted by member
    name: the member's name, its full reference name and its file's path relative to the output directory (with ``/``
    separators), separated by tabs and ended by a newline.

    .. invisible-code-block: python

        from nunavut._namespace_manifest import naming_digest

    .. code-block:: python

        entries = [("mg.ns.B.1.0", "mg.ns.B_1_0", "mg/ns/B_1_0.py"), ("mg.ns.A.1.0", "mg.ns.A_1_0", "mg/ns/A_1_0.py")]
        assert naming_digest("__init__.py", entries) == naming_digest("__init__.py", reversed(entries))

    :param namespace_file_name: The namespace file's name, e.g. ``__init__.py``.
    :param entries: (member name, full reference name, output-relative path) for each member.
    :return: ``sha256:`` followed by 64 hex digits.
    """
    lines = "".join(f"{name}\t{reference}\t{path}\n" for name, reference, path in sorted(entries))
    return "sha256:" + hashlib.sha256(f"{namespace_file_name}\n{lines}".encode("utf-8")).hexdigest()


class NamespaceMemberRef:
    """
    A member of a namespace known only by its versioned name, read from a manifest. It provides what the naming
    functions use from a :class:`pydsdl.CompositeType`: ``full_name``, ``short_name``, ``full_namespace`` and
    ``version``.

    .. invisible-code-block: python

        from nunavut._namespace_manifest import NamespaceMemberRef

    .. code-block:: python

        ref = NamespaceMemberRef("uavcan.primitive.String.1.0")
        assert (ref.full_name, ref.short_name, ref.full_namespace) == (
            "uavcan.primitive.String", "String", "uavcan.primitive"
        )
        assert (ref.version.major, ref.version.minor) == (1, 0)
    """

    def __init__(self, member_name: str):
        *namespace, short_name, major, minor = member_name.split(".")
        self.full_namespace = ".".join(namespace)
        self.short_name = short_name
        self.full_name = f"{self.full_namespace}.{short_name}"
        self.version = pydsdl.Version(major=int(major), minor=int(minor))

    def __repr__(self) -> str:
        return f"NamespaceMemberRef({member_name(self)!r})"


def member_name(data_type: Any) -> str:
    """
    The versioned name a manifest uses for a type, e.g. ``uavcan.primitive.String.1.0``.
    """
    return f"{data_type.full_name}.{data_type.version.major}.{data_type.version.minor}"


class NamespaceConflictKind(enum.Enum):
    """
    Why merging into an existing namespace file was refused.
    """

    NO_MANIFEST = "the existing file has no valid manifest of its types, so it can't be merged"
    NAMING_CHANGED = "this run would name the existing types differently than the run that wrote them"
    CASE_COLLISION = "two types' files would differ only in letter case"
    NAMESPACE_COLLISION = "two namespaces would share this namespace file"

    @property
    def can_be_forced(self) -> bool:
        """
        True if ``force`` lets the namespace file be written anyway (with this run's members only).
        """
        return self in (NamespaceConflictKind.NO_MANIFEST, NamespaceConflictKind.NAMING_CHANGED)


@dataclass(frozen=True)
class NamespaceConflict:
    """
    One namespace file that can't be merged.
    """

    path: Path
    """The namespace file."""

    kind: NamespaceConflictKind
    """Why it can't be merged."""

    detail: str
    """Specifics, e.g. the colliding types."""


class NamespaceConflictError(RuntimeError):
    """
    Raised, before anything is written, when generating would have to change something an existing namespace file
    already provides instead of only adding to it.
    """

    def __init__(self, conflicts: List[NamespaceConflict]):
        self.conflicts = conflicts
        lines = ["Generation refused: these namespace files can't be merged by only adding to them:"]
        for conflict in conflicts:
            detail = f" ({conflict.detail})" if conflict.detail else ""
            lines.append(f"  {conflict.path}: {conflict.kind.value}{detail}")
        kinds = {c.kind for c in conflicts}
        if any(kind.can_be_forced for kind in kinds):
            lines.append(
                "Generate into a clean output directory, or use --force to write these namespace files with only "
                "this run's types (no files are deleted)."
            )
        if NamespaceConflictKind.CASE_COLLISION in kinds:
            lines.append("Types whose files differ only in letter case can't be generated into one namespace.")
        if NamespaceConflictKind.NAMESPACE_COLLISION in kinds:
            lines.append(
                "Namespaces whose names differ only in letter case, or that map to the same directory, can't be "
                "generated into one output directory."
            )
        super().__init__("\n".join(lines))


def _full_reference_name_function(language: Language) -> Any:
    module = LanguageClassLoader.load_language_module(language.name)
    return getattr(module, "filter_full_reference_name", None)


def naming_entries(members: Iterable[Any], language: Language) -> List[Tuple[str, str, str]]:
    """
    (member name, full reference name, output-relative path) for each member, using the same naming functions as the
    generator: the target language's ``full_reference_name`` filter and :meth:`IncludeGenerator.make_path`.
    """
    full_reference_name = _full_reference_name_function(language)
    extension = language.get_config_value(Language.WKCV_DEFINITION_FILE_EXTENSION)
    entries = []
    for member in members:
        data_type = cast(pydsdl.CompositeType, member)
        reference = full_reference_name(language, data_type) if full_reference_name is not None else ""
        path = IncludeGenerator.make_path(data_type, language, extension).as_posix()
        entries.append((member_name(member), reference, path))
    return entries


def namespace_naming_digest(namespace: Any, members: Iterable[Any]) -> str:
    """
    The naming digest of the given members of a namespace, as this run would name them.
    """
    language = namespace.get_language_context().get_target_language()
    return naming_digest(namespace.output_path.name, naming_entries(members, language))


def dsdl_namespace_name(namespace: Any) -> str:
    """
    A namespace's DSDL name, without stropping (empty for the index namespace).
    """
    return ".".join(namespace.namespace_components)


def namespace_manifest_lines(namespace: Any) -> List[str]:
    """
    The lines of a namespace file's manifest, for the namespace template to write inside comments. They describe the
    namespace's merged members (see :meth:`nunavut.Namespace.get_namespace_members`).
    """
    members = namespace.get_namespace_members()
    return [
        MANIFEST_BEGIN,
        f"  namespace:{dsdl_namespace_name(namespace)}",
        f"  naming-digest {namespace_naming_digest(namespace, members)}",
        *(f"  {name}" for name in sorted(member_name(m) for m in members)),
        MANIFEST_END,
    ]


def merge_namespace_files(index: Any, force: bool) -> None:
    """
    Prepares every namespace under ``index`` for an append-only merge with the namespace file already at its output
    path, if any. Nothing is written. On success each namespace's recorded members are set, so
    :meth:`nunavut.Namespace.get_namespace_members` returns the merged set.

    :param index: The index namespace of this generation.
    :param force: Write namespace files whose conflicts can be forced with this run's members only.
    :raises NamespaceConflictError: If any namespace file can't be merged (and, with ``force``, if any of those
        conflicts can't be forced). The error lists every conflict.
    """
    language = index.get_language_context().get_target_language()
    conflicts: List[NamespaceConflict] = []
    recorded_by_namespace: List[Tuple[Any, List[NamespaceMemberRef]]] = []

    colliding = _namespaces_sharing_a_file(index)
    for output_path, names in colliding.items():
        detail = "namespaces " + " and ".join(names)
        conflicts.append(NamespaceConflict(output_path, NamespaceConflictKind.NAMESPACE_COLLISION, detail))
    colliding_names = {name for names in colliding.values() for name in names}

    for namespace, output_path in index.get_all_namespaces():
        if dsdl_namespace_name(namespace) in colliding_names:
            continue
        run_members = {member_name(t): t for t, _ in namespace.get_nested_types()}
        conflict, recorded = _check_existing_namespace_file(namespace, output_path, run_members.keys())
        if conflict is not None:
            conflicts.append(conflict)
        collision = _case_collision(list(run_members.values()) + recorded, language)
        if collision:
            conflicts.append(NamespaceConflict(output_path, NamespaceConflictKind.CASE_COLLISION, collision))
        recorded_by_namespace.append((namespace, recorded))

    blocking = [c for c in conflicts if not (force and c.kind.can_be_forced)]
    if blocking:
        raise NamespaceConflictError(blocking if force else conflicts)

    for namespace, recorded in recorded_by_namespace:
        namespace.set_recorded_members(recorded)


def _check_existing_namespace_file(
    namespace: Any, output_path: Path, run_member_names: Iterable[str]
) -> Tuple[Optional[NamespaceConflict], List[NamespaceMemberRef]]:
    """
    Checks the namespace file already at ``output_path``, if any, for an append-only merge.

    :return: The conflict, if the file can't be merged, and the recorded members this run doesn't generate (empty if
        there's no file or a conflict).
    """
    if not output_path.exists():
        return None, []
    manifest = parse_manifest(output_path.read_bytes())
    if manifest is None:
        return NamespaceConflict(output_path, NamespaceConflictKind.NO_MANIFEST, ""), []

    # The file must belong to this namespace. Another namespace's file is here when the names differ only in letter case
    # (on a case-insensitive filesystem) or strop to the same directory.
    this_namespace = dsdl_namespace_name(namespace)
    if manifest.namespace != this_namespace:
        detail = f"it belongs to namespace {manifest.namespace or '(the output root)'}"
        return NamespaceConflict(output_path, NamespaceConflictKind.NAMESPACE_COLLISION, detail), []
    foreign = sorted(name for name in manifest.members if NamespaceMemberRef(name).full_namespace != this_namespace)
    if foreign:
        detail = f"its manifest lists types outside namespace {this_namespace}: {', '.join(foreign)}"
        return NamespaceConflict(output_path, NamespaceConflictKind.NO_MANIFEST, detail), []

    # The digest is recomputed from the recorded names alone, with this run's settings and naming code.
    if namespace_naming_digest(namespace, map(NamespaceMemberRef, manifest.members)) != manifest.digest:
        return NamespaceConflict(output_path, NamespaceConflictKind.NAMING_CHANGED, ""), []
    return None, [NamespaceMemberRef(name) for name in sorted(manifest.members - set(run_member_names))]


def _namespaces_sharing_a_file(index: Any) -> Dict[Path, List[str]]:
    """
    Namespaces of this run whose namespace files are the same file when compared ignoring case: their names differ
    only in letter case, or they strop to the same directory. Keyed by the first one's namespace file.
    """
    by_folded_path: Dict[str, List[Tuple[Path, str]]] = {}
    for namespace, output_path in index.get_all_namespaces():
        by_folded_path.setdefault(str(output_path).casefold(), []).append((output_path, dsdl_namespace_name(namespace)))
    return {group[0][0]: sorted(name for _, name in group) for group in by_folded_path.values() if len(group) > 1}


def _case_collision(members: List[Any], language: Language) -> str:
    """
    A description of members whose files differ only in letter case, or an empty string.
    """
    by_folded_path: Dict[str, List[str]] = {}
    for name, _, path in naming_entries(members, language):
        by_folded_path.setdefault(path.casefold(), []).append(name)
    groups = [sorted(names) for names in by_folded_path.values() if len(names) > 1]
    return "; ".join(" and ".join(group) for group in sorted(groups))
