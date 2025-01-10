#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Namespace object and associated utilities. Nunavut namespaces provide an internal representation of dsdl namespaces
that are also data objects for target languages, like python, that model namespaces as objects.

The one Namespace type can play three roles:

1. **Namespace Index**: The root of a tree of namespaces. This is a special namespace that is used to generate index
    files that reference all the generated files in the tree at once. It is always the parent of each root namespace.
    Index namespaces contain only root namespaces and have no data types. They make no assumptions about the structure
    of the namespaces they contain.
2. **Root Namespace**: A namespace that is a direct child of the index namespace. It contains the namespaces's datatypes
    and nested namespaces.
3. **Nested Namespace**: A namespace that is a child of another namespace. It contains the namespaces's datatypes and
    nested namespaces.

```
        ┌─────────────┐
        │  Namespace  │
        │   «index»   │ (the index cannot contain data types)
        │             │
        └──────┬──────┘
               │1
               │
               │
               │*
               ▼
        ┌─────────────┐            ┌──────────┐
        │  Namespace  │1          *│ DataType │
        │   «root»    ├───────────►│          │
        │             │            └──────────┘
        └──────┬──────┘
               │1
               │
               │
               │*
               ▼
        ┌─────────────┐            ┌──────────┐
        │  Namespace  │1          *│ DataType │
        │  «nested»   ├───────────►│          │
        │             │            └──────────┘
        └─────────────┘
```
"""

import collections
import itertools
import logging
import multiprocessing
import multiprocessing.pool
import sys
from functools import singledispatchmethod
from os import PathLike
from pathlib import Path
from typing import (
    Any,
    Callable,
    Deque,
    Generator,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import pydsdl

from .lang import Language, LanguageContext
from .lang._common import IncludeGenerator

if sys.version_info < (3, 9):
    # Python 3.8 has a bug. This is a workaround per https://stackoverflow.com/a/66518591/310659
    def _register(self, cls, method=None):  # type: ignore
        if hasattr(cls, "__func__"):
            setattr(cls, "__annotations__", cls.__func__.__annotations__)
        return self.dispatcher.register(cls, func=method)

    singledispatchmethod.register = _register  # type: ignore

# +--------------------------------------------------------------------------------------------------------------------+


class AsyncResultProtocol(Protocol):
    """
    Defines the protocol for a duck-type compatible with multiprocessing.pool.AsyncResult.
    """

    def get(self, timeout: Optional[Any] = None) -> Any:
        """
        See multiprocessing.pool.AsyncResult.get
        """


class NotAsyncResult:
    """
    Duck-type compatible with multiprocessing.pool.AsyncResult that is not actually asynchronous. All work is performed
    synchronously when the get method is called.
    """

    def __init__(self, read_method: Callable[..., Any], args: Tuple[Any, ...]) -> None:
        self.read_method = read_method
        self.args = args
        self._logger = logging.getLogger(NotAsyncResult.__name__)

    def get(self, timeout: Optional[Any] = None) -> Any:
        """
        Perform the work synchronously.
        """
        if timeout is not None and timeout > 0:
            self._logger.debug(
                "Timeout value for read_method '%s' ignored when not doing multiple jobs.", self.read_method.__name__
            )
        return self.read_method(*self.args)


ApplyMethodT = TypeVar("ApplyMethodT", bound=Callable[..., AsyncResultProtocol])


def _read_files_strategy(
    index: "Namespace",
    apply_method: ApplyMethodT,
    dsdl_files: Union[Path, str, Iterable[Union[Path, str]]],
    job_timeout_seconds: float,
    omit_dependencies: bool,
    args: Iterable[Any],
) -> "Namespace":
    """
    Strategy for reading a set of dsdl files and building a namespace tree. This strategy is compatible with both
    synchronous and asynchronous invocation of the pydsdl.read_files method.
    """
    if isinstance(dsdl_files, (str, Path)):
        fileset = {Path(dsdl_files)}
    else:
        fileset = {Path(file) for file in dsdl_files}
    resolve_cache: dict[Path, Path] = {}

    def _resolve_file(file: Path) -> Path:
        # limit filesystem access by caching resolved files. This assumes the non-canonical path form
        # is consistent. If not this would not limit filesystem access but would be correct.
        if file not in resolve_cache:
            resolve_cache[file] = file.resolve()
        return resolve_cache[file]

    running_lookups: list[AsyncResultProtocol] = []
    already_read: set[Path] = set()
    while fileset:
        next_file = fileset.pop()
        running_lookups.append(apply_method(pydsdl.read_files, args=itertools.chain([next_file], args)))
        already_read.add(_resolve_file(next_file))
        if not fileset:
            for lookup in running_lookups:
                if job_timeout_seconds <= 0:
                    target_type, dependent_types = lookup.get()
                else:
                    target_type, dependent_types = lookup.get(timeout=job_timeout_seconds)
                Namespace.add_types(index, (target_type[0], dependent_types))
                if not omit_dependencies:
                    for dependent_type in dependent_types:
                        if _resolve_file(dependent_type.source_file_path) not in already_read:
                            fileset.add(dependent_type.source_file_path)
            running_lookups.clear()

    return index


# +--------------------------------------------------------------------------------------------------------------------+
class Generatable(type(Path())):  # type: ignore
    """
    A file that can be generated from a pydsdl type.

    .. invisible-code-block: python

        from nunavut._namespace import Generatable
        from pathlib import Path
        from unittest.mock import MagicMock
        import pydsdl

        dsdl_definition = MagicMock(spec=pydsdl.CompositeType)
        dependent_types = [MagicMock(spec=pydsdl.CompositeType)]

    .. code-block:: python

        # Generatables combine a Path to the generated file with the pydsdl type that can be reified into the file
        # and the types that are required to generate the file. This is useful for tracking dependencies and
        # generating files in the correct order. It also provides a representation of the generated file before it
        # is actually generated.

        generatable = Generatable(dsdl_definition, dependent_types, "test.h")

        # This is a Generatable object.
        assert isinstance(generatable, Generatable)
        assert generatable.definition == dsdl_definition
        assert generatable.input_types == dependent_types

        # But it is also a Path object.
        assert isinstance(generatable, Path)
        assert Path("test.h") == generatable

    :param pydsdl.Any definition: The pydsdl type that can be reified into a generated file.
    :param List[pydsdl.Any] input_types: The types that are required to generate the file.
    :param args: Arguments to pass to the Path constructor.
    :param kwargs: Keyword arguments to pass to the Path constructor.
    """

    @classmethod
    def _check_arguments(
        cls, definition: pydsdl.CompositeType, input_types: List[pydsdl.CompositeType]
    ) -> Tuple[pydsdl.CompositeType, List[pydsdl.CompositeType]]:
        """
        Check the arguments for the Generatable constructor.

        :param pydsdl.Any definition: The pydsdl type that can be reified into a generated file.
        :param List[pydsdl.Any] input_types: The types that are required to generate the file.
        :raises TypeError: If the arguments are not of the correct types.
        :return: The definition and input types.
        """
        if not isinstance(definition, pydsdl.CompositeType):
            raise TypeError("Generatable requires a 'definition' argument of type pydsdl.CompositeType.")
        if not isinstance(input_types, list):
            raise TypeError("Generatable requires an 'input_types' argument of type List[pydsdl.CompositeType].")
        return definition, input_types

    if sys.version_info < (3, 12):

        def __new__(cls, *args: Any, **kwargs: Any) -> "Generatable":
            """
            The override of the __new__ operator is required until python 3.12.
            After that, the __init__ operator can be used.
            """
            if cls is not Generatable:
                raise TypeError("Unknown type passed to Generatable constructor.")

            if len(args) < 3:
                raise TypeError("Generatable requires 'definition', 'input_types', and 'path' arguments.")

            definition, input_types = cls._check_arguments(*args[:2])
            new_pure_path = cast(Generatable, super().__new__(cls, *args[2:], **kwargs))
            new_pure_path._definition = definition
            new_pure_path._input_types = input_types
            return new_pure_path

    else:

        def __init__(
            self, definition: pydsdl.CompositeType, input_types: List[pydsdl.CompositeType], *args: Any, **kwargs: Any
        ):
            super().__init__(*args, **kwargs)
            self._definition, self._input_types = self._check_arguments(definition, input_types)

    @classmethod
    def wrap(
        cls, path: Path, definition: pydsdl.CompositeType, input_types: List[pydsdl.CompositeType]
    ) -> "Generatable":
        """
        Create a Generatable object from a Path, a pydsdl type, and a list of pydsdl types in a Python-version agnostic
        way. This is useful for deferred construction of Generatable objects since __init__ is not available in
        the python 3.11 and earlier versions.

        :param Path path: The path to the generated file.
        :param pydsdl.Any definition: The pydsdl type that can be reified into a generated file.
        :param List[pydsdl.Any] input_types: The types that are required to generate the file.
        :return: A Generatable object.
        """
        return Generatable(definition, input_types, path)

    def with_segments(self, *pathsegments: Union[str, PathLike]) -> Path:
        """
        Path override: Construct a new path object from any number of path-like objects.
        We discard the Generatable type here and continue on with a default Path object.
        """
        return Path(*pathsegments)

    @property
    def definition(self) -> pydsdl.CompositeType:
        """
        The pydsdl type that can be reified into a generated file.
        """
        return self._definition  # pylint: disable=no-member

    @property
    def input_types(self) -> List[pydsdl.CompositeType]:
        """
        The types that are required to generate the file.
        """
        return self._input_types.copy()  # type: ignore # pylint: disable=no-member,

    # --[DATA MODEL]-------------------------------------------------------------------------------------------------
    def __reduce__(self) -> Tuple[Callable, Tuple[Path, pydsdl.CompositeType, List[pydsdl.CompositeType]]]:
        super_reduction = super().__reduce__()
        reduced_path = Path(*super_reduction[1]) if isinstance(super_reduction, tuple) else Path(super_reduction)
        return (self.wrap, (reduced_path, self.definition, self.input_types))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Generatable):
            return bool(
                super().__eq__(other)
                and self._definition == other._definition  # pylint: disable=no-member
                and self._input_types == other._input_types  # pylint: disable=no-member
            )
        else:
            return super().__eq__(other)  # type: ignore

    def __hash__(self) -> int:
        return hash((super().__hash__(), self._definition))  # pylint: disable=no-member

    def __repr__(self) -> str:
        return (
            f"{super().__repr__()}, "  # pylint: disable=no-member
            f"definition={repr(self._definition)}, "  # pylint: disable=no-member
            f"input_types={repr(self._input_types)}"  # pylint: disable=no-member
        )

    def __copy__(self) -> "Generatable":
        return Generatable(self.definition, self.input_types, *self.parts)


# +--------------------------------------------------------------------------------------------------------------------+
class Namespace(pydsdl.Any):  # pylint: disable=too-many-public-methods
    """
    K-ary tree (where K is the largest set of data types in a single dsdl namespace) where
    the nodes represent dsdl namespaces and the children are the datatypes and other nested
    namespaces (with datatypes always being leaf nodes). This structure extends :code:`pydsdl.Any`
    and is a :code:`pydsdl.CompositeType` via duck typing.

    :param str full_namespace:  The full, dot-separated name of the namepace.
    :param Path namespace_dir: If full_namespace is "" then this is interpreted as the directory under which all
        namespaces and datatypes should be generated. Otherwise, it is the directory that contains the namespace's
        datatypes.
    :param LanguageContext language_context: The generated software language context the namespace is within.
    :param Namespace parent: The parent namespace of this namespace or None if this is an index namespace.
    """

    @classmethod
    def strop_namespace(cls, full_namespace: str, language_context: LanguageContext) -> Tuple[List[str], List[str]]:
        """
        Strop a namespace string for a given language context.

        :param str full_namespace: The dot-separated namespace string to strop.
        :param LanguageContext language_context: The language context to use when stroping the namespace.
        :return: A tuple containing the original namespace components and the stropped namespace components.

        .. invisible-code-block: python

            from nunavut.lang import LanguageContext, LanguageContextBuilder
            from nunavut._namespace import Namespace

            lctx = (
                LanguageContextBuilder()
                    .set_target_language("c")
                    .create()
            )

        .. code-block:: python

            full_namespace = "uavcan.node"
            namespace_components, namespace_components_stropped = Namespace.strop_namespace(full_namespace, lctx)

            assert namespace_components == ["uavcan", "node"]
            assert namespace_components_stropped == ["uavcan", "node"]

        """
        namespace_components = full_namespace.split(".")
        return (
            namespace_components,
            [language_context.filter_id_for_target(component, "path") for component in namespace_components],
        )

    @classmethod
    def add_types(
        cls,
        index: "Namespace",
        types: Union[
            Tuple[pydsdl.CompositeType, List[pydsdl.CompositeType]],
            List[Tuple[pydsdl.CompositeType, List[pydsdl.CompositeType]]],
        ],
        extension: Optional[str] = None,
    ) -> None:
        """
        Add a set of types to a namespace tree building new nodes as needed.

        :param Namespace tree: A namespace tree to add types to. This can be any namespace in the tree as
            :meth:`Namespace.get_index_namespace` will be used to find the meta-namespace.
        :param list types: A list of pydsdl types to add.
        :param str extension: Override the file extension to use for the generated files. If None, the extension will be
            determined by the target language.

        .. invisible-code-block: python


        """
        lctx = index.get_language_context()
        if not isinstance(types, list):
            types = [types]
        for dsdl_type, input_types in types:
            # For each type we form a path with the output_dir as the base; the intermediate
            # folders named for the type's namespaces; and a file name that includes the type's
            # short name, major version, minor version, and the extension argument as a suffix.
            # Python's pathlib adapts the provided folder and file names to the platform
            # this script is running on.
            # We also, lazily, generate Namespace nodes as we encounter new namespaces for the
            # first time.

            root_namespace_perhaps = index
            stropped, _ = cls.strop_namespace(dsdl_type.full_namespace, lctx)
            for namespace_component in stropped:
                if root_namespace_perhaps.short_name == namespace_component:
                    break
                root_namespace_perhaps = root_namespace_perhaps.get_nested_namespace(
                    namespace_component, create_if_missing=True
                )
            if root_namespace_perhaps == index:
                raise RuntimeError(f"Type {dsdl_type} has no namespace components and is therefore malformed.")
            root_namespace_perhaps.add_data_type(dsdl_type, input_types, extension)

    @classmethod
    def Identity(cls, output_path: Path, lctx: LanguageContext) -> "Namespace":
        """
        Create a namespace identity object. This is a namespace with no root directory and no parent. It can be used
        as a Namespace index object.

        :param Path output_path: The base path under which all namespaces and datatypes should be generated.
        :param LanguageContext lctx: The language context to use when building the namespace.
        :return: A namespace identity object.
        :rtype: Namespace
        """
        return cls("", output_path, lctx)

    @singledispatchmethod
    @classmethod
    def read_namespace(
        cls,
        index: "Namespace",
        root_namespace_directory: Union[Path, str],
        lookup_directories: Optional[Union[Path, str, Iterable[Union[Path, str]]]] = None,
        print_output_handler: Optional[Callable[[Path, int, str], None]] = None,
        allow_unregulated_fixed_port_id: bool = False,
        allow_root_namespace_name_collision: bool = True,
    ) -> "Namespace":
        """
        Read a namespace from a root namespace directory.

        :param Namespace index: The index namespace to add the new namespaces and types to.
        :param Path | str root_namespace_directory: The root namespace directory.
        :param Path | str | Iterable[Path | str] lookup_directories: The directories to search for dsdl files.
        :param Callable[[Path, int, str], None] print_output_handler: A callback to handle print output.
        :param bool allow_unregulated_fixed_port_id: Allow unregulated fixed port ids.
        :param bool allow_root_namespace_name_collision: Allow root namespace name collisions.
        :return: A new namespace index that contains trees of datatypes.
        """
        if not index.is_index:
            raise ValueError("Namespace passed in as index argument is not an index namespace.")

        composite_types = pydsdl.read_namespace(
            root_namespace_directory,
            lookup_directories,
            print_output_handler,
            allow_unregulated_fixed_port_id,
            allow_root_namespace_name_collision,
        )
        Namespace.add_types(index, [(dsdl_type, []) for dsdl_type in composite_types])
        return index

    @read_namespace.register
    @classmethod
    def _(
        cls,
        output_path: str,
        lctx: LanguageContext,
        root_namespace_directory: Union[Path, str],
        lookup_directories: Optional[Union[Path, str, Iterable[Union[Path, str]]]] = None,
        print_output_handler: Optional[Callable[[Path, int, str], None]] = None,
        allow_unregulated_fixed_port_id: bool = False,
        allow_root_namespace_name_collision: bool = True,
    ) -> pydsdl.Any:
        """
        Read a namespace from a root namespace directory.

        :param str output_path: The base path under which all namespaces and datatypes should be generated.
        :param LanguageContext lctx: The language context to use when building the namespace.
        :param Path | str root_namespace_directory: The root namespace directory.
        :param Path | str | Iterable[Path | str] lookup_directories: The directories to search for dsdl files.
        :param Callable[[Path, int, str], None] print_output_handler: A callback to handle print output.
        :param bool allow_unregulated_fixed_port_id: Allow unregulated fixed port ids.
        :param bool allow_root_namespace_name_collision: Allow root namespace name collisions.
        :return: A new namespace index that contains trees of datatypes.
        """
        return cls.read_namespace(
            cls.Identity(Path(output_path), lctx),
            root_namespace_directory,
            lookup_directories,
            print_output_handler,
            allow_unregulated_fixed_port_id,
            allow_root_namespace_name_collision,
        )

    @read_namespace.register
    @classmethod
    def _(
        cls,
        output_path: Path,
        lctx: LanguageContext,
        root_namespace_directory: Union[Path, str],
        lookup_directories: Optional[Union[Path, str, Iterable[Union[Path, str]]]] = None,
        print_output_handler: Optional[Callable[[Path, int, str], None]] = None,
        allow_unregulated_fixed_port_id: bool = False,
        allow_root_namespace_name_collision: bool = True,
    ) -> pydsdl.Any:
        """
        Read a namespace from a root namespace directory.

        :param Path output_path: The base path under which all namespaces and datatypes should be generated.
        :param LanguageContext lctx: The language context to use when building the namespace.
        :param Path | str root_namespace_directory: The root namespace directory.
        :param Path | str | Iterable[Path | str] lookup_directories: The directories to search for dsdl files.
        :param Callable[[Path, int, str], None] print_output_handler: A callback to handle print output.
        :param bool allow_unregulated_fixed_port_id: Allow unregulated fixed port ids.
        :param bool allow_root_namespace_name_collision: Allow root namespace name collisions.
        :return: A new namespace index that contains trees of datatypes.
        """
        return cls.read_namespace(
            cls.Identity(output_path, lctx),
            root_namespace_directory,
            lookup_directories,
            print_output_handler,
            allow_unregulated_fixed_port_id,
            allow_root_namespace_name_collision,
        )

    @singledispatchmethod
    @classmethod
    def read_files(
        cls,
        index: "Namespace",
        dsdl_files: Union[Path, str, Iterable[Union[Path, str]]],
        root_namespace_directories_or_names: Optional[Union[Path, str, Iterable[Union[Path, str]]]],
        jobs: int = 0,
        job_timeout_seconds: float = 0,
        lookup_directories: Optional[Union[Path, str, Iterable[Union[Path, str]]]] = None,
        print_output_handler: Optional[Callable[[Path, int, str], None]] = None,
        allow_unregulated_fixed_port_id: bool = False,
        omit_dependencies: bool = False,
    ) -> "Namespace":
        """
        For a given set of dsdl_files, read the files and build a namespace tree.

        :param Namespace index: The index namespace to add the new namespaces and types to.
        :param Path | str | Iterable[Path | str] dsdl_files: The dsdl files to read.
        :param Path | str | Iterable[Path | str] root_namespace_directories_or_names: See :meth:`pydsdl.read_files`.
        :param int jobs: The number of parallel jobs to allow when reading multiple files. 0 Indicates no limit and 1
                   diasallows all parallelism.
        :param float job_timeout_seconds: Maximum time in fractional seconds any one read file job is allowed to take
                     before timing out. 0 disables timeouts.
        :param Path | str | Iterable[Path | str] lookup_directories: See :meth:`pydsdl.read_files`.
        :param Callable[[Path, int, str], None] print_output_handler: A callback to handle print output.
        :param bool allow_unregulated_fixed_port_id: Allow unregulated fixed port ids.
        :return: A new namespace index that contains trees of datatypes.
        """
        if not index.is_index:
            raise ValueError("Namespace passed in as index argument is not an index namespace.")

        args = (
            root_namespace_directories_or_names,
            lookup_directories,
            print_output_handler,
            allow_unregulated_fixed_port_id,
        )
        if jobs == 1:
            # Don't use multiprocessing when jobs is 1.
            return _read_files_strategy(index, NotAsyncResult, dsdl_files, job_timeout_seconds, omit_dependencies, args)
        else:
            with multiprocessing.pool.Pool(processes=None if jobs == 0 else jobs) as pool:
                return _read_files_strategy(
                    index, pool.apply_async, dsdl_files, job_timeout_seconds, omit_dependencies, args
                )

    @read_files.register
    @classmethod
    def _(
        cls,
        output_path: Path,
        lctx: LanguageContext,
        dsdl_files: Optional[Union[Path, str, Iterable[Union[Path, str]]]],
        root_namespace_directories_or_names: Optional[Union[Path, str, Iterable[Union[Path, str]]]],
        jobs: int = 0,
        job_timeout_seconds: float = 0,
        lookup_directories: Optional[Union[Path, str, Iterable[Union[Path, str]]]] = None,
        print_output_handler: Optional[Callable[[Path, int, str], None]] = None,
        allow_unregulated_fixed_port_id: bool = False,
        omit_dependencies: bool = False,
    ) -> pydsdl.Any:
        """
        For a given set of dsdl_files, read the files and build a namespace tree.

        :param Path output_path: The base path under which all namespaces and datatypes should be generated.
        :param LanguageContext lctx: The language context to use when building the namespace.
        :param Path | str | Iterable[Path | str] dsdl_files: The dsdl files to read.
        :param Path | str | Iterable[Path | str] root_namespace_directories_or_names: See :meth:`pydsdl.read_files`.
        :param int jobs: The number of parallel jobs to allow when reading multiple files. 0 Indicates no limit and 1
                   diasallows all parallelism.
        :param float job_timeout_seconds: Maximum time in fractional seconds any one read file job is allowed to take
                     before timing out. 0 disables timeouts.
        :param Path | str | Iterable[Path | str] lookup_directories: See :meth:`pydsdl.read_files`.
        :param Callable[[Path, int, str], None] print_output_handler: A callback to handle print output.
        :param bool allow_unregulated_fixed_port_id: Allow unregulated fixed port ids.
        :return: A new namespace index that contains trees of datatypes.
        """
        return cls.read_files(
            Namespace.Identity(output_path, lctx),
            dsdl_files,
            root_namespace_directories_or_names,
            jobs,
            job_timeout_seconds,
            lookup_directories,
            print_output_handler,
            allow_unregulated_fixed_port_id,
            omit_dependencies,
        )

    @read_files.register
    @classmethod
    def _(
        cls,
        output_path: str,
        lctx: LanguageContext,
        dsdl_files: Optional[Union[Path, str, Iterable[Union[Path, str]]]],
        root_namespace_directories_or_names: Optional[Union[Path, str, Iterable[Union[Path, str]]]],
        jobs: int = 0,
        job_timeout_seconds: float = 0,
        lookup_directories: Optional[Union[Path, str, Iterable[Union[Path, str]]]] = None,
        print_output_handler: Optional[Callable[[Path, int, str], None]] = None,
        allow_unregulated_fixed_port_id: bool = False,
        omit_dependencies: bool = False,
    ) -> pydsdl.Any:
        """
        For a given set of dsdl_files, read the files and build a namespace tree.

        :param str output_path: The base path under which all namespaces and datatypes should be generated.
        :param LanguageContext lctx: The language context to use when building the namespace.
        :param Path | str | Iterable[Path | str] dsdl_files: The dsdl files to read.
        :param Path | str | Iterable[Path | str] root_namespace_directories_or_names: See :meth:`pydsdl.read_files`.
        :param int The number of parallel jobs to allow when reading multiple files. 0 Indicates no limit and 1
                   diasallows all parallelism.
        :param float job_timeout_seconds: Maximum time in fractional seconds any one read file job is allowed to take
                     before timing out. 0 disables timeouts.
        :param Path | str | Iterable[Path | str] lookup_directories: See :meth:`pydsdl.read_files`.
        :param Callable[[Path, int, str], None] print_output_handler: A callback to handle print output.
        :param bool allow_unregulated_fixed_port_id: Allow unregulated fixed port ids.
        :return: A new namespace index that contains trees of datatypes.
        """
        return cls.read_files(
            Namespace.Identity(Path(output_path), lctx),
            dsdl_files,
            root_namespace_directories_or_names,
            jobs,
            job_timeout_seconds,
            lookup_directories,
            print_output_handler,
            allow_unregulated_fixed_port_id,
            omit_dependencies,
        )

    DefaultOutputStem = "_"

    def __init__(
        self,
        full_namespace: str,
        namespace_dir: Path,
        language_context: LanguageContext,
        parent: Optional["Namespace"] = None,
    ):
        if full_namespace.startswith("."):
            full_namespace = full_namespace[1:]

        self._language_context = language_context
        self._parent = parent

        if len(full_namespace) == 0:

            # Identity namespace
            if parent is not None:
                raise ValueError("Identity namespaces must not have a parent.")
            self._namespace_components: List[str] = []
            self._namespace_components_stropped: List[str] = []
            self._full_namespace = ""
            self._base_output_path = self._output_folder = namespace_dir
            self._source_folder = Path("")
            self._short_name = ""
        else:
            # Root or nested namespace
            if parent is None:
                raise ValueError("Non-identity namespaces must have a parent.")
            if len(namespace_dir.name) == 0:
                raise ValueError("Root namespace directory must have a name.")
            self._namespace_components, self._namespace_components_stropped = self.strop_namespace(
                full_namespace, language_context
            )
            if self._namespace_components[-1] != namespace_dir.name:
                raise ValueError(f"Namespace {full_namespace} does not match root namespace directory {namespace_dir}")
            self._base_output_path = parent.base_output_path
            self._full_namespace = ".".join(self._namespace_components_stropped)
            self._output_folder = Path(self._base_output_path / Path(*self._namespace_components_stropped))
            self._source_folder = namespace_dir / Path(*self._namespace_components[1:])
            self._short_name = self._namespace_components_stropped[-1]

        target_language = language_context.get_target_language()
        output_stem = target_language.get_config_value(Language.WKCV_NAMESPACE_FILE_STEM, self.DefaultOutputStem)
        output_path = self._output_folder / Path(output_stem)
        self._output_path = output_path.with_suffix(
            target_language.get_config_value(Language.WKCV_DEFINITION_FILE_EXTENSION)
        )
        self._data_type_to_outputs: dict[pydsdl.CompositeType, Generatable] = {}
        self._nested_namespaces: dict[str, Namespace] = {}

        if self._parent is not None and not self.is_index:  # pragma: no cover
            self._parent._nested_namespaces[self._namespace_components[-1]] = self

    # +--[PROPERTIES]-----------------------------------------------------------------------------------------------+
    @property
    def output_folder(self) -> Path:
        """
        The folder where this namespace's output file and datatypes are generated.
        """
        return self._output_folder

    @property
    def output_path(self) -> Path:
        """
        Path to the namespace's output file.
        """
        return self._output_path

    @property
    def parent(self) -> Optional["Namespace"]:
        """
        The parent namespace of this namespace or None if this is a root namespace.
        """
        return self._parent

    @property
    def root_namespace(self) -> "Namespace":
        """
        The root namespace of this namespace.
        :raises RuntimeError: If this is an index namespace.
        """
        if self.is_index:
            raise RuntimeError("Index namespace has no root namespace.")

        root_maybe = self
        while not root_maybe.is_root:
            # All non-index namespaces have a parent and all non-index namespaces are either a root or have a root
            # ancestor.
            root_maybe = root_maybe.parent  # type: ignore

        return root_maybe

    @property
    def base_output_path(self) -> Path:
        """
        The folder under which artifacts are generated.
        """
        return self._base_output_path

    @property
    def is_index(self) -> bool:
        """
        True if this namespace is an index namespace.
        """
        return self._parent is None

    @property
    def is_root(self) -> bool:
        """
        True if this namespace is a root namespace.
        """
        return len(self._namespace_components) == 1

    @property
    def is_nested(self) -> bool:
        """
        True if this namespace is a nested namespace.
        """
        return len(self._namespace_components) > 1

    # +--[PUBLIC]--------------------------------------------------------------------------------------------------+
    def get_index_namespace(self) -> "Namespace":
        """
        The index namespace is a meta-namespace that is empty and has no data types. It contains
        the root output folder, a common language context, and all the namespaces in a tree of DSDL types. It is used to
        generate index files that reference all the generated files in the tree at once. Logically, it is the root of
        the tree and is always the parent of each root namespace. The taxonomy of namespaces is therefore ::

                                          ┌────────────────┐
                                          │  CompoundType  │
                                          │   «duck type»  │
                                          └────────────────┘
                                           ▲             ▲
                        ┌──────────────────┘             │
                        │                                │
                        │              ┌──────┐          │
                        │              │ Path │          │
                        │              │      │          │
                        │              └──────┘          │
                        │               ▲    ▲           │
                        │               │    │           │
                  ┌─────┴─────┐ ┌───────┴┐  ┌┴───────┐   │
                  │ Namespace │ │ Folder │  │  File  │   │
                  │           │ │        │  │        │   │
                  └───────────┘ └────────┘  └────────┘   │
                   ▲    ▲   ▲     ^    ^           ^     │
                   │    │   │     :    :.......    :     │
                   │    │   │     :           :    :     │
                   │    │   └──── : ─────┐    :    :     │
                   │    │         :      │    :    :     │
                   │    └─────┐   :      │    :    :     │
                   │          │   :      │    :    :     │
                ┌──┴──────┐ ┌─┴───┴──┐ ┌─┴────┴─┐ ┌┴─────┴────┐
                │  index  │ │  root  │ │ nested │ │ DSDL Type │
                │         │ │        │ │        │ │           │
                └─────────┘ └────────┘ └────────┘ └───────────┘

        :return: The index namespace.

        .. invisible-code-block: python

            from nunavut._namespace import Namespace
            from nunavut.lang import LanguageContext, LanguageContextBuilder
            from pathlib import Path

            lctx = (
                LanguageContextBuilder()
                    .set_target_language("c")
                    .create()
            )

            base_path = gen_paths.out_dir
            root_namespace_dir = base_path / Path("uavcan")
            root_namespace_dir.mkdir(exist_ok=True)
            nested_namespace_dir = root_namespace_dir / Path("node")
            nested_namespace_dir.mkdir(exist_ok=True)

        .. code-block:: python

            # This is the index namespace identity.
            index_ns = Namespace.Identity(base_path, lctx)
            ns = Namespace("uavcan", root_namespace_dir, lctx, index_ns)

            # This is a root namespace identity.
            assert ns.get_index_namespace() == index_ns

        """
        namespace = self
        while not namespace.is_index:
            # parent is always set for non-index namespaces
            namespace = namespace.parent  # type: ignore
        return namespace

    def get_language_context(self) -> LanguageContext:
        """
        The generated software language context the namespace is within.
        """
        return self._language_context

    def get_root_namespace(self, root_namespace_name: str, create_if_missing: bool = False) -> "Namespace":
        """
        Retrieves or creates a root namespace object for a given name.

        :param Path root_namespace_name: The root namespace name to get.
        :param bool create_if_missing: If True, the namespace will be created if it does not exist.
        :return: The root namespace object.
        :raises KeyError: If the namespace was not found and create_if_missing is False.
        """
        index = self.get_index_namespace()
        return index.get_nested_namespace(root_namespace_name, create_if_missing=create_if_missing)

    def get_nested_namespaces(self) -> Iterator["Namespace"]:
        """
        Get an iterator over all the nested namespaces within this namespace.
        This is a shallow iterator that only provides directly nested namespaces.
        """
        return iter(self._nested_namespaces.values())

    def get_nested_namespace(self, namespace_name: str, create_if_missing: bool = False) -> "Namespace":
        """
        Get a nested namespace by name. Note, this is not recursive.

        :param str namespace_name: The name of the nested namespace to get.
        :param bool create_if_missing: If True, the namespace will be created if it does not exist.
        :return: The nested namespace.
        :raises KeyError: If the namespace was not found and create_if_missing is False.
        """
        try:
            return self._nested_namespaces[namespace_name]
        except KeyError as e:
            if not create_if_missing:
                raise e

        return Namespace(
            ".".join(self._namespace_components + [namespace_name]),
            self.source_file_path / Path(namespace_name),
            self._language_context,
            self,
        )

    def get_nested_types(self) -> ItemsView[pydsdl.CompositeType, Generatable]:
        """
        Get a view of a tuple relating datatypes in this namespace to the path for the
        type's generated output. This is a shallow view including only the types
        directly within this namespace.
        """
        return self._data_type_to_outputs.items()

    def get_all_datatypes(self) -> Generator[Tuple[pydsdl.CompositeType, Generatable], None, None]:
        """
        Generates tuples relating datatypes at and below this namespace to the path
        for each type's generated output.
        """
        yield from self._recursive_data_type_generator(self)

    def get_all_namespaces(self) -> Generator[Tuple["Namespace", Path], None, None]:
        """
        Generates tuples relating nested namespaces at and below this namespace to the path
        for each namespace's generated output.
        """
        yield from self._recursive_namespace_generator(self)

    def get_all_types(self) -> Generator[Tuple[pydsdl.Any, Union[Generatable, Path]], None, None]:
        """
        Generates tuples relating datatypes and nested namespaces at and below this
        namespace to the path for each type's generated output.
        """
        yield from self._recursive_data_type_and_namespace_generator(self)

    def find_output_path_for_type(self, compound_type: Union["Namespace", pydsdl.CompositeType]) -> Path:
        """
        Searches the entire namespace tree to find a mapping of the type to an
        output file path.

        :param pydsdl.CompositeType compound_type: A Namespace or pydsdl.CompositeType to find the output pathfor.
        :return: The path where a file will be generated for a given type.
        :raises KeyError: If the type was not found in this namespace tree.
        """
        if isinstance(compound_type, Namespace):
            return compound_type.output_path
        else:
            # pylint: disable=protected-access
            root_namespace = self.get_index_namespace().get_root_namespace(compound_type.source_file_path_to_root.name)
            return root_namespace._bfs_search_for_output_path(compound_type)  # pylint: disable=protected-access

    def add_data_type(
        self, dsdl_type: pydsdl.CompositeType, input_types: List[pydsdl.CompositeType], extension: Optional[str]
    ) -> Generatable:
        """
        Add a datatype to this namespace.

        :param pydsdl.CompositeType dsdl_type: The datatype to add.
        :param str extension: The file extension to use for the generated file. If None, the
                                extension will be determined by the target language.
        :return: A path to the file this type will be generated in.
        """

        if self.is_index:
            raise RuntimeError("Cannot add types to an index namespace.")

        _, stropped_ns = self.strop_namespace(dsdl_type.full_namespace, self._language_context)
        if stropped_ns[-1] != self._short_name:
            raise ValueError(
                f"Type {dsdl_type.full_name} does not belong in namespace {self._full_namespace}. "
                f"Expected namespace {self._full_namespace}, got {dsdl_type.full_namespace}."
            )

        language = self._language_context.get_target_language()
        if extension is None:
            extension = language.get_config_value(Language.WKCV_DEFINITION_FILE_EXTENSION)
        output_file = Path(self._base_output_path) / IncludeGenerator.make_path(dsdl_type, language, extension)
        output_generatable = Generatable(dsdl_type, input_types, output_file)
        self._data_type_to_outputs[dsdl_type] = output_generatable
        return output_generatable

    # +--[DUCK TYPING: pydsdl.CompositeType]-----------------------------------------------------------------------+
    @property
    def short_name(self) -> str:
        """
        See :py:attr:`pydsdl.CompositeType.short_name`
        """
        return self._short_name

    @property
    def full_name(self) -> str:
        """
        See :py:attr:`pydsdl.CompositeType.full_name`
        """
        return self._full_namespace

    @property
    def full_namespace(self) -> str:
        """
        See :py:attr:`pydsdl.CompositeType.full_namespace`
        """
        return self._full_namespace

    @property
    def namespace_components(self) -> List[str]:
        """
        See :py:attr:`pydsdl.CompositeType.namespace_components`
        """
        return self._namespace_components

    @property
    def source_file_path(self) -> Path:
        """
        See :py:attr:`pydsdl.CompositeType.source_file_path`
        Note that, for Namespace objects, this path is always relative since a single namespace may contain sources
        from files rooted in different directory trees. For example, a namespace may a type
        "/path/to/animals/mammals/Dog.1.0.dsdl" and another type "/a/different/path/to/animals/mammals/Cat.1.0.dsdl".
        """
        return self._source_folder

    @property
    def source_file_path_to_root(self) -> Path:
        """
        See :py:attr:`pydsdl.CompositeType.source_file_path_to_root`
        Note that, for Namespace objects, this path is always relative. See :py:attr:`source_file_path` for more.
        """
        return self.root_namespace.source_file_path

    @property
    def data_types(self) -> KeysView[pydsdl.CompositeType]:
        """
        See :py:attr:`pydsdl.CompositeType.data_types`
        """
        return self._data_type_to_outputs.keys()

    @property
    def attributes(self) -> List[pydsdl.CompositeType]:
        """
        See :py:attr:`pydsdl.CompositeType.attributes`
        """
        return []

    # +--[PYTHON DATA MODEL]--------------------------------------------------------------------------------------+

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Namespace):
            return self._full_namespace == other._full_namespace
        else:
            return False

    def __str__(self) -> str:
        return self.full_name

    def __hash__(self) -> int:
        return hash(self._full_namespace)

    # +--[PRIVATE]------------------------------------------------------------------------------------------------+

    def _bfs_search_for_output_path(self, data_type: pydsdl.CompositeType) -> Path:
        search_queue: Deque[Namespace] = collections.deque()
        search_queue.appendleft(self)
        while len(search_queue) > 0:
            namespace = search_queue.pop()
            try:
                return namespace._data_type_to_outputs[data_type]  # pylint: disable=protected-access
            except KeyError:
                pass
            for nested_namespace in namespace._nested_namespaces.values():  # pylint: disable=protected-access
                search_queue.appendleft(nested_namespace)

        raise KeyError(data_type)

    @classmethod
    def _recursive_data_type_generator(
        cls, namespace: "Namespace"
    ) -> Generator[Tuple[pydsdl.CompositeType, Generatable], None, None]:
        for data_type, output_path in namespace.get_nested_types():
            yield (data_type, output_path)

        for nested_namespace in namespace.get_nested_namespaces():
            yield from cls._recursive_data_type_generator(nested_namespace)

    @classmethod
    def _recursive_namespace_generator(cls, namespace: "Namespace") -> Generator[Tuple["Namespace", Path], None, None]:
        yield (namespace, namespace.output_path)

        for nested_namespace in namespace.get_nested_namespaces():
            yield from cls._recursive_namespace_generator(nested_namespace)

    @classmethod
    def _recursive_data_type_and_namespace_generator(
        cls, namespace: "Namespace"
    ) -> Generator[Tuple[pydsdl.Any, Union[Path, Generatable]], None, None]:
        yield (namespace, namespace.output_path)

        for data_type, output_path in namespace.get_nested_types():
            yield (data_type, output_path)

        for nested_namespace in namespace.get_nested_namespaces():
            yield from cls._recursive_data_type_and_namespace_generator(nested_namespace)


# +---------------------------------------------------------------------------+


def build_namespace_tree(
    types: List[pydsdl.CompositeType],
    root_namespace_dir: Union[str, Path],
    output_dir: Union[str, Path],
    language_context: LanguageContext,
) -> Namespace:
    """
    Generates a :class:`nunavut.Namespace` tree.

    .. note::

        Deprecated. Use :method:`Namespace.add_types` instead. build_namespace_tree creates a new a :class:`Namespace`
        index internally which may lead to unexpected behavior if calling this method multiple times. Furthermore, it
        cannot associate output files with their dependent types and is ambiguous about the root namespace directory.

    Given a list of pydsdl types, this method returns a root :class:`nunavut.Namespace`.
    The root :class:`nunavut.Namespace` is the top of a tree where each node contains
    references to nested :class:`nunavut.Namespace` and to any :code:`pydsdl.CompositeType`
    instances contained within the namespace.

    :param list types: A list of pydsdl types.
    :param str | Path root_namespace_dir: The root namespace directory. This is the directory that contains the
            namespaces's datatypes and nested namespaces.

        .. note::
            Root namespace directories are determined by the source file path of individual types so it is possible
            to pass in a list of types that are not available in the returned Namespace. Only types that are within
            this root namespace directory will be included in the returned Namespace.

    :param str | Path output_dir: The base directory under which all generated files will be created.
    :param nunavut.LanguageContext language_context: The language context to use when building
            :class:`nunavut.Namespace` objects.
    :return: The root :class:`nunavut.Namespace`.
    :rtype: nunavut.Namespace

    """

    index = Namespace.Identity(Path(output_dir), language_context)
    Namespace.add_types(index, [(dsdl_type, []) for dsdl_type in types])
    return index.get_root_namespace(Path(root_namespace_dir).name, create_if_missing=True)


# +---------------------------------------------------------------------------+
