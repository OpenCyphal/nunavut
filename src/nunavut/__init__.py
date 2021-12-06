#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2021  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""Code generator built on top of pydsdl.

Nunavut uses pydsdl to generate text files using templates. While these
text files are often source code this module could also be used to generate
documentation or data interchange formats like JSON or XML.

The input to the nunavut library is a list of templates and a list of
``pydsdl.pydsdl.CompositeType`` objects. The latter is typically obtained
by calling pydsdl::

    from pydsdl import read_namespace

    compound_types = read_namespace(root_namespace, include_paths)

Next a :class:`nunavut.LanguageContext` is needed which is used to
configure all Nunavut objects for a specific target language ::

    from nunavut.lang import LanguageContext

    # Here we are going to generate C headers.
    language_context = LanguageContext('c')

:class:`nunavut.generators.AbstractGenerator` objects require
a :class:`nunavut.Namespace` tree which can be built from the
pydsdl type map using :meth:`nunavut.build_namespace_tree`::

    from nunavut import build_namespace_tree

    root_namespace = build_namespace_tree(compound_types,
                                          root_ns_folder,
                                          out_dir,
                                          language_context)

Putting this all together, the typical use of this library looks something like this::

    from pydsdl import read_namespace
    from nunavut import build_namespace_tree
    from nunavut.lang import LanguageContext
    from nunavut.jinja import DSDLCodeGenerator

    # parse the dsdl
    compound_types = read_namespace(root_namespace, include_paths)

    # select a target language
    language_context = LanguageContext('c')

    # build the namespace tree
    root_namespace = build_namespace_tree(compound_types,
                                          root_ns_folder,
                                          out_dir,
                                          language_context)

    # give the root namespace to the generator and...
    generator = DSDLCodeGenerator(root_namespace)

    # generate all the code!
    generator.generate_all()

"""

import collections
import pathlib
import sys
import typing

import pydsdl

from .lang import LanguageContext
from .lang._common import IncludeGenerator

# library users can access the utility types directly from the nunvut namespace. Internally
# we us the _utilities package to break circular imports.
from ._utilities import YesNoDefault  # noqa # pylint: disable=unused-import

if sys.version_info[:2] < (3, 5):  # pragma: no cover
    print("A newer version of Python is required", file=sys.stderr)
    sys.exit(1)


__all__ = ["Namespace", "YesNoDefault", "build_namespace_tree", "generate_types"]

# +---------------------------------------------------------------------------+


class Namespace(pydsdl.Any):
    """
    K-ary tree (where K is the largest set of data types in a single dsdl namespace) where
    the nodes represent dsdl namespaces and the children are the datatypes and other nested
    namespaces (with datatypes always being leaf nodes). This structure extends :code:`pydsdl.Any`
    and is a :code:`pydsdl.pydsdl.CompositeType` via duck typing.

    :param str full_namespace:  The full, dot-separated name of the namepace. This is expected to be
                                a unique identifier.
    :param pathlib.Path root_namespace_dir: The directory representing the dsdl namespace and containing the
                                namespaces's datatypes and nested namespaces.
    :param pathlib.PurePath base_output_path: The base path under which all namespaces and datatypes should
                                be generated.
    :param LanguageContext language_context: The generated software language context the namespace is within.
    """

    DefaultOutputStem = "_"

    def __init__(
        self,
        full_namespace: str,
        root_namespace_dir: pathlib.Path,
        base_output_path: pathlib.PurePath,
        language_context: LanguageContext,
    ):
        self._parent = None  # type: typing.Optional[Namespace]
        self._namespace_components = []  # type: typing.List[str]
        self._namespace_components_stropped = []  # type: typing.List[str]
        for component in full_namespace.split("."):
            self._namespace_components_stropped.append(language_context.filter_id_for_target(component, "path"))
            self._namespace_components.append(component)
        self._full_namespace = ".".join(self._namespace_components_stropped)
        self._output_folder = pathlib.Path(base_output_path / pathlib.PurePath(*self._namespace_components_stropped))
        output_stem = language_context.get_default_namespace_output_stem()
        if output_stem is None:
            output_stem = self.DefaultOutputStem
        output_path = self._output_folder / pathlib.PurePath(output_stem)
        self._base_output_path = base_output_path
        self._output_path = output_path.with_suffix(language_context.get_output_extension())
        self._source_folder = pathlib.Path(
            root_namespace_dir / pathlib.PurePath(*self._namespace_components[1:])
        ).resolve()
        if not self._source_folder.exists():
            # to make Python > 3.5 behave the same as Python 3.5
            raise FileNotFoundError(self._source_folder)
        self._short_name = self._namespace_components_stropped[-1]
        self._data_type_to_outputs = dict()  # type: typing.Dict[pydsdl.CompositeType, pathlib.Path]
        self._nested_namespaces = set()  # type: typing.Set[Namespace]
        self._language_context = language_context

    @property
    def output_folder(self) -> pathlib.Path:
        """
        The folder where this namespace's output file and datatypes are generated.
        """
        return self._output_folder

    def get_support_output_folder(self) -> pathlib.PurePath:
        """
        The folder under which support artifacts are generated.
        """
        return self._base_output_path

    def get_language_context(self) -> LanguageContext:
        """
        The generated software language context the namespace is within.
        """
        return self._language_context

    def get_root_namespace(self) -> "Namespace":
        """
        Traverses the namespace tree up to the root and returns the root node.

        :return: The root namespace object.
        """
        namespace = self  # type: Namespace
        while namespace._parent is not None:
            namespace = namespace._parent
        return namespace

    def get_nested_namespaces(self) -> typing.Iterator["Namespace"]:
        """
        Get an iterator over all the nested namespaces within this namespace.
        This is a shallow iterator that only provides directly nested namespaces.
        """
        return iter(self._nested_namespaces)

    def get_nested_types(self) -> typing.ItemsView[pydsdl.CompositeType, pathlib.Path]:
        """
        Get a view of a tuple relating datatypes in this namespace to the path for the
        type's generated output. This is a shallow view including only the types
        directly within this namespace.
        """
        return self._data_type_to_outputs.items()

    def get_all_datatypes(self) -> typing.Generator[typing.Tuple[pydsdl.CompositeType, pathlib.Path], None, None]:
        """
        Generates tuples relating datatypes at and below this namespace to the path
        for each type's generated output.
        """
        yield from self._recursive_data_type_generator(self)

    def get_all_namespaces(self) -> typing.Generator[typing.Tuple["Namespace", pathlib.Path], None, None]:
        """
        Generates tuples relating nested namespaces at and below this namespace to the path
        for each namespace's generated output.
        """
        yield from self._recursive_namespace_generator(self)

    def get_all_types(self) -> typing.Generator[typing.Tuple[pydsdl.Any, pathlib.Path], None, None]:
        """
        Generates tuples relating datatypes and nested namespaces at and below this
        namespace to the path for each type's generated output.
        """
        yield from self._recursive_data_type_and_namespace_generator(self)

    def find_output_path_for_type(self, any_type: pydsdl.Any) -> pathlib.Path:
        """
        Searches the entire namespace tree to find a mapping of the type to an
        output file path.

        :param Any any_type: Either a Namespace or pydsdl.CompositeType to find the
                             output path for.
        :return: The path where a file will be generated for a given type.
        :raises KeyError: If the type was not found in this namespace tree.
        """
        if isinstance(any_type, Namespace):
            return any_type._output_path
        else:
            try:
                return self._data_type_to_outputs[any_type]
            except KeyError:
                pass

            # We could get fancier but this should do
            return self.get_root_namespace()._bfs_search_for_output_path(any_type, set([self]))

    # +-----------------------------------------------------------------------+
    # | DUCK TYPING: pydsdl.CompositeType
    # +-----------------------------------------------------------------------+
    @property
    def full_name(self) -> str:
        return self._full_namespace

    @property
    def full_namespace(self) -> str:
        return self._full_namespace

    @property
    def source_file_path(self) -> str:
        return str(self._source_folder)

    @property
    def data_types(self) -> typing.KeysView[pydsdl.CompositeType]:
        return self._data_type_to_outputs.keys()

    @property
    def attributes(self) -> typing.List[pydsdl.CompositeType]:
        return []

    # +-----------------------------------------------------------------------+
    # | PYTHON DATA MODEL
    # +-----------------------------------------------------------------------+

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Namespace):
            return self._full_namespace == other._full_namespace
        else:
            return False

    def __str__(self) -> str:
        return self.full_name

    def __hash__(self) -> int:
        return hash(self._full_namespace)

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _add_data_type(self, dsdl_type: pydsdl.CompositeType, extension: str) -> None:
        self._data_type_to_outputs[dsdl_type] = pathlib.Path(self._base_output_path) / IncludeGenerator.make_path(
            dsdl_type, self._language_context.get_target_language(), extension
        )

    def _add_nested_namespace(self, nested: "Namespace") -> None:
        self._nested_namespaces.add(nested)
        nested._parent = self

    def _bfs_search_for_output_path(
        self, data_type: pydsdl.CompositeType, skip_namespace: typing.Set["Namespace"]
    ) -> pathlib.Path:
        search_queue = collections.deque()  # type: typing.Deque[Namespace]
        search_queue.appendleft(self)
        while len(search_queue) > 0:
            namespace = search_queue.pop()
            if namespace not in skip_namespace:
                try:
                    return namespace._data_type_to_outputs[data_type]
                except KeyError:
                    pass
            for nested_namespace in namespace._nested_namespaces:
                search_queue.appendleft(nested_namespace)

        raise KeyError(data_type)

    @classmethod
    def _recursive_data_type_generator(
        cls, namespace: "Namespace"
    ) -> typing.Generator[typing.Tuple[pydsdl.CompositeType, pathlib.Path], None, None]:
        for data_type, output_path in namespace.get_nested_types():
            yield (data_type, output_path)

        for nested_namespace in namespace.get_nested_namespaces():
            yield from cls._recursive_data_type_generator(nested_namespace)

    @classmethod
    def _recursive_namespace_generator(
        cls, namespace: "Namespace"
    ) -> typing.Generator[typing.Tuple["Namespace", pathlib.Path], None, None]:
        yield (namespace, namespace._output_path)

        for nested_namespace in namespace.get_nested_namespaces():
            yield from cls._recursive_namespace_generator(nested_namespace)

    @classmethod
    def _recursive_data_type_and_namespace_generator(
        cls, namespace: "Namespace"
    ) -> typing.Generator[typing.Tuple[pydsdl.Any, pathlib.Path], None, None]:
        yield (namespace, namespace._output_path)

        for data_type, output_path in namespace.get_nested_types():
            yield (data_type, output_path)

        for nested_namespace in namespace.get_nested_namespaces():
            yield from cls._recursive_data_type_and_namespace_generator(nested_namespace)


# +---------------------------------------------------------------------------+


class _NamespaceFactory:
    """
    Read-through cache and factory for :class:`Namespace` objects.
    """

    def __init__(self, lctx: LanguageContext, base_path: pathlib.PurePath, root_namespace_dir: pathlib.Path):
        self._lctx = lctx
        self._base_path = base_path
        self._namespaces = dict()  # type: typing.Dict[str, Namespace]
        self._root_namespace_dir = root_namespace_dir

    def get_root_namesapce(self) -> Namespace:
        try:
            return next(iter(self._namespaces.values())).get_root_namespace()
        except StopIteration:
            pass
        return self.get_empty_namespace()

    def get_empty_namespace(self) -> Namespace:
        return self.get_or_make_namespace("")[0]

    def get_or_make_namespace(self, full_namespace: str) -> typing.Tuple[Namespace, bool]:
        try:
            namespace = self._namespaces[str(full_namespace)]
            return (namespace, True)
        except KeyError:
            pass

        namespace = Namespace(full_namespace, self._root_namespace_dir, self._base_path, self._lctx)

        self._namespaces[str(full_namespace)] = namespace

        return (namespace, False)


def build_namespace_tree(
    types: typing.List[pydsdl.CompositeType],
    root_namespace_dir: str,
    output_dir: str,
    language_context: LanguageContext,
) -> Namespace:
    """Generates a :class:`nunavut.Namespace` tree.

    Given a list of pydsdl types, this method returns a root :class:`nunavut.Namespace`.
    The root :class:`nunavut.Namespace` is the top of a tree where each node contains
    references to nested :class:`nunavut.Namespace` and to any :code:`pydsdl.CompositeType`
    instances contained within the namespace.

    :param list types: A list of pydsdl types.
    :param str root_namespace_dir: A path to the folder which is the root namespace.
    :param str output_dir: The base directory under which all generated files will be created.
    :param nunavut.lang.LanguageContext language_context: The language context to use when building
            :class:`nunavut.Namespace` objects.
    :return: The root :class:`nunavut.Namespace`.

    """
    namespace_index = set()  # type: typing.Set[str]

    nsf = _NamespaceFactory(language_context, pathlib.PurePath(output_dir), pathlib.Path(root_namespace_dir))

    for dsdl_type in types:
        # For each type we form a path with the output_dir as the base; the intermediate
        # folders named for the type's namespaces; and a file name that includes the type's
        # short name, major version, minor version, and the extension argument as a suffix.
        # Python's pathlib adapts the provided folder and file names to the platform
        # this script is running on.
        # We also, lazily, generate Namespace nodes as we encounter new namespaces for the
        # first time.

        namespace, did_exist = nsf.get_or_make_namespace(dsdl_type.full_namespace)

        if not did_exist:
            # add all namespaces up to root to index so we trigger
            # empty namespace generation in the final tree building
            # loop below.
            for i in range(len(dsdl_type.name_components) - 1, 0, -1):
                ancestor_ns = ".".join(dsdl_type.name_components[0:i])
                if ancestor_ns in namespace_index:
                    break
                namespace_index.add(ancestor_ns)

        namespace._add_data_type(dsdl_type, language_context.get_output_extension())

    # We now have an index of all namespace names and we have Namespace
    # objects for non-empty namespaces. This final loop will build any
    # missing (i.e. empty) namespaces and all the links to form the
    # namespace tree.
    for full_namespace in namespace_index:
        namespace, _ = nsf.get_or_make_namespace(full_namespace)

        parent_namespace_components = namespace._namespace_components[0:-1]
        if len(parent_namespace_components) > 0:
            parent_name = ".".join(parent_namespace_components)

            parent, _ = nsf.get_or_make_namespace(parent_name)
            parent._add_nested_namespace(namespace)

    return nsf.get_root_namesapce()


# +---------------------------------------------------------------------------+

# +---------------------------------------------------------------------------+
# | GENERATION HELPERS
# +---------------------------------------------------------------------------+


def generate_types(
    language_key: str,
    root_namespace_dir: pathlib.Path,
    out_dir: pathlib.Path,
    omit_serialization_support: bool = True,
    is_dryrun: bool = False,
    allow_overwrite: bool = True,
    lookup_directories: typing.Optional[typing.Iterable[str]] = None,
    allow_unregulated_fixed_port_id: bool = False,
    language_options: typing.Optional[typing.Mapping[str, typing.Any]] = None,
) -> None:
    """
    Helper method that uses default settings and built-in templates to generate types for a given
    language. This method is the most direct way to generate code using Nunavut.

    :param str language_key: The name of the language to generate source for.
                See the :doc:`../../docs/templates` for details on available language support.
    :param pathlib.Path root_namespace_dir: The path to the root of the DSDL types to generate
                code for.
    :param pathlib.Path out_dir: The path to generate code at and under.
    :param bool omit_serialization_support: If True then logic used to serialize and deserialize data is omitted.
    :param bool is_dryrun: If True then nothing is generated but all other activity is performed and any errors
                that would have occurred are reported.
    :param bool allow_overwrite: If True then generated files are allowed to overwrite existing files under the
                `out_dir` path.
    :param typing.Optional[typing.Iterable[str]] lookup_directories: Additional directories to search for dependent
                types referenced by the types provided under the `root_namespace_dir`. Types will not be generated
                for these unless they are used by a type in the root namespace.
    :param bool allow_unregulated_fixed_port_id: If True then errors will become warning when using fixed port
                identifiers for unregulated datatypes.
    :param typing.Optional[typing.Mapping[str, typing.Any]] language_options: Opaque arguments passed through to the
                language objects. The supported arguments and valid values are different depending on the language
                specified by the `language_key` parameter.
    """
    from nunavut.generators import create_generators

    language_context = LanguageContext(
        language_key,
        omit_serialization_support_for_target=omit_serialization_support,
        language_options=language_options,
    )

    if lookup_directories is None:
        lookup_directories = []

    type_map = pydsdl.read_namespace(
        str(root_namespace_dir), lookup_directories, allow_unregulated_fixed_port_id=allow_unregulated_fixed_port_id
    )

    namespace = build_namespace_tree(type_map, str(root_namespace_dir), str(out_dir), language_context)

    generator, support_generator = create_generators(namespace)
    support_generator.generate_all(is_dryrun, allow_overwrite)
    generator.generate_all(is_dryrun, allow_overwrite)
