#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
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

Next a :class:`nunavut.lang.LanguageContext` is needed which is used to
configure all Nunavut objects for a specific target language ::

    from nunavut.lang import LanguageContext

    # Here we are going to generate C headers.
    langauge_context = LanguageContext('c')

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
    from nunavut.jinja import Generator

    # parse the dsdl
    compound_types = read_namespace(root_namespace, include_paths)

    # select a target language
    langauge_context = LanguageContext('c')

    # build the namespace tree
    root_namespace = build_namespace_tree(compound_types,
                                          root_ns_folder,
                                          out_dir,
                                          language_context)

    # give the root namespace to the generator and...
    generator = Generator(root_namespace, False, language_context, templates_dir)

    # generate all the code!
    generator.generate_all()

"""

import collections
import pathlib
import sys
import typing

import pydsdl

from . import lang

if sys.version_info[:2] < (3, 5):   # pragma: no cover
    print('A newer version of Python is required', file=sys.stderr)
    sys.exit(1)

# for now this is set to a value that is internally compatible with the
# embedded version of jinja2 we use in Nunavut. If you use this variable
# instead of its current value you will be insulated from this.
EnvironmentFilterAttributeName = 'environmentfilter'


# +---------------------------------------------------------------------------+

class SupportsTemplateEnv:
    """
    Provided as a pseudo
    `protocol <https://mypy.readthedocs.io/en/latest/protocols.html#simple-user-defined-protocols/>`_.
    (in anticipation of that becoming part of the core Python typing someday).

    :var Dict globals: A dictionary mapping global names (str) to variables (Any) that are available in
                       each template's global environment.
    :var Dict filters: A dictionary mapping filter names (str) to filters (Callable). Filters are simply
                       global functions available to templates but are most often used to transform a
                       given input to output emitted by the template.
    """

    globals = dict()  # type: typing.Dict[str, typing.Any]
    filters = dict()  # type: typing.Dict[str, typing.Callable]
    tests = dict()  # type: typing.Dict[str, typing.Callable[[typing.Any], bool]]


def templateEnvironmentFilter(filter_func: typing.Callable) -> typing.Callable:
    """
    Decorator for marking environment dependent filters.
    An object supporting the :class:`SupportsTemplateEnv` protocol
    will be passed to the filter as the first argument.
    """
    setattr(filter_func, EnvironmentFilterAttributeName, True)
    return filter_func


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
    :param lang.LanguageContext language_context: The generated software language context the namespace is within.
    """

    DefaultOutputStem = '_'

    def __init__(self,
                 full_namespace: str,
                 root_namespace_dir: pathlib.Path,
                 base_output_path: pathlib.PurePath,
                 language_context: lang.LanguageContext):
        self._parent = None  # type: typing.Optional[Namespace]
        self._id_filter = language_context.get_id_filter()
        self._namespace_components = []  # type: typing.List[str]
        self._namespace_components_stropped = []  # type: typing.List[str]
        for component in full_namespace.split('.'):
            self._namespace_components_stropped.append(self._id_filter(component))
            self._namespace_components.append(component)
        self._full_namespace = '.'.join(self._namespace_components_stropped)
        self._output_folder = pathlib.Path(base_output_path / pathlib.PurePath(*self._namespace_components_stropped))
        output_stem = language_context.get_default_namespace_output_stem()
        if output_stem is None:
            output_stem = self.DefaultOutputStem
        output_path = self._output_folder / pathlib.PurePath(output_stem)
        self._output_path = output_path.with_suffix(language_context.get_output_extension())
        self._source_folder = pathlib.Path(
            root_namespace_dir / pathlib.PurePath(*self._namespace_components[1:])).resolve()
        if not self._source_folder.exists():
            # to make Python > 3.5 behave the same as Python 3.5
            raise FileNotFoundError(self._source_folder)
        self._short_name = self._namespace_components_stropped[-1]
        self._data_type_to_outputs = dict()  # type: typing.Dict[pydsdl.CompositeType, pathlib.Path]
        self._nested_namespaces = set()  # type: typing.Set[Namespace]

    @property
    def output_folder(self) -> pathlib.Path:
        """
        The folder where this namespace's output file and datatypes are generated.
        """
        return self._output_folder

    def get_root_namespace(self) -> 'Namespace':
        """
        Traverses the namespace tree up to the root and returns the root node.

        :returns: The root namepace object.
        """
        namespace = self  # type: Namespace
        while namespace._parent is not None:
            namespace = namespace._parent
        return namespace

    def get_nested_namespaces(self) -> typing.Iterator['Namespace']:
        """
        Get an iterator over all the nested namespaces within this namespace.
        This is a shallow iterator that only provides directly nested namespaces.
        """
        return iter(self._nested_namespaces)

    def get_nested_types(self) -> typing.ItemsView[pydsdl.CompositeType, pathlib.Path]:
        """
        Get a view of a tuple relating datatypes in this namepace to the path for the
        type's generated output. This is a shallow view including only the types
        directly within this namespace.
        """
        return self._data_type_to_outputs.items()

    def get_all_datatypes(self) -> typing.Generator[typing.Tuple[pydsdl.CompositeType, pathlib.Path], None, None]:
        """
        Generates tuples relating datatypes at and below this namepace to the path
        for each type's generated output.
        """
        yield from self._recursive_data_type_generator(self)

    def get_all_namespaces(self) -> typing.Generator[typing.Tuple['Namespace', pathlib.Path], None, None]:
        """
        Generates tuples relating nested namespaces at and below this namepace to the path
        for each namespace's generated output.
        """
        yield from self._recursive_namespace_generator(self)

    def get_all_types(self) -> typing.Generator[typing.Tuple[pydsdl.Any, pathlib.Path], None, None]:
        """
        Generates tuples relating datatypes and nested namespaces at and below this
        namepace to the path for each type's generated output.
        """
        yield from self._recursive_data_type_and_namespace_generator(self)

    def find_output_path_for_type(self, any_type: pydsdl.Any) -> pathlib.Path:
        """
        Searches the entire namespace tree to find a mapping of the type to an
        output file path.

        :param Any any_type: Either a Namespace or pydsdl.CompositeType to find the
                             output path for.
        :returns: The path where a file will be generated for a given type.
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
    # | DUCK TYPEING: pydsdl.CompositeType
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
    def _add_data_type(self, dsdl_type: pydsdl.CompositeType, extension: typing.Optional[str]) -> None:
        filestem = "{}_{}_{}".format(
            dsdl_type.short_name, dsdl_type.version.major, dsdl_type.version.minor)
        output_path = self._output_folder / pathlib.PurePath(filestem)
        if extension is not None:
            output_path = output_path.with_suffix(extension)
        self._data_type_to_outputs[dsdl_type] = output_path

    def _add_nested_namespace(self, nested: 'Namespace') -> None:
        self._nested_namespaces.add(nested)
        nested._parent = self

    def _bfs_search_for_output_path(self, data_type: pydsdl.CompositeType, skip_namespace: typing.Set['Namespace']) \
            -> pathlib.Path:
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
    def _recursive_data_type_generator(cls, namespace: 'Namespace') -> \
            typing.Generator[typing.Tuple[pydsdl.CompositeType, pathlib.Path], None, None]:
        for data_type, output_path in namespace.get_nested_types():
            yield (data_type, output_path)

        for nested_namespace in namespace.get_nested_namespaces():
            yield from cls._recursive_data_type_generator(nested_namespace)

    @classmethod
    def _recursive_namespace_generator(cls, namespace: 'Namespace') -> \
            typing.Generator[typing.Tuple['Namespace', pathlib.Path], None, None]:
        yield (namespace, namespace._output_path)

        for nested_namespace in namespace.get_nested_namespaces():
            yield from cls._recursive_namespace_generator(nested_namespace)

    @classmethod
    def _recursive_data_type_and_namespace_generator(cls, namespace: 'Namespace') -> \
            typing.Generator[typing.Tuple[pydsdl.Any, pathlib.Path], None, None]:
        yield (namespace, namespace._output_path)

        for data_type, output_path in namespace.get_nested_types():
            yield (data_type, output_path)

        for nested_namespace in namespace.get_nested_namespaces():
            yield from cls._recursive_data_type_and_namespace_generator(nested_namespace)

# +---------------------------------------------------------------------------+


def build_namespace_tree(types: typing.List[pydsdl.CompositeType],  # noqa: C901
                         root_namespace_dir: str,
                         output_dir: str,
                         language_context: lang.LanguageContext) -> Namespace:
    """Generates a :class:`nunavut.Namespace` tree.

    Given a list of pydsdl types, this method returns a root :class:`nunavut.Namespace`.
    The root :class:`nunavut.Namespace` is the top of a tree where each node contains
    references to nested :class:`nunavut.Namespace` and to any :code:`pydsdl.CompositeType`
    instances contained within the namespace.

    :param list types: A list of pydsdl types.
    :param str root_namespace_dir: A path to the folder which is the root namespace.
    :param str output_dir: The base directory under which all generated files will be created.
    :param lang.LanguageContext language_context: The language context to use when building
            :class:`nunavut.Namespace` objects.
    :returns: The root :class:`nunavut.Namespace`.

    """
    base_path = pathlib.PurePath(output_dir)

    namespace_index = set()  # type: typing.Set[str]
    namespaces = dict()  # type: typing.Dict[str, Namespace]

    def get_or_make_namespace(full_namespace: str) -> typing.Tuple[Namespace, bool]:
        # Local Namespace read through cache and factory.
        try:
            namespace = namespaces[str(full_namespace)]
            return (namespace, True)
        except KeyError:
            pass

        namespace = Namespace(full_namespace,
                              pathlib.Path(root_namespace_dir),
                              base_path,
                              language_context)

        namespaces[str(full_namespace)] = namespace

        return (namespace, False)

    for dsdl_type in types:
        # For each type we form a path with the output_dir as the base; the intermediate
        # folders named for the type's namespaces; and a file name that includes the type's
        # short name, major version, minor version, and the extension argument as a suffix.
        # Python's pathlib adapts the provided folder and file names to the platform
        # this script is running on.
        # We also, lazily, generate Namespace nodes as we encounter new namespaces for the
        # first time.

        namespace, did_exist = get_or_make_namespace(dsdl_type.full_namespace)

        if not did_exist:
            # add all namespaces up to root to index so we trigger
            # empty namespace generation in the final tree building
            # loop below.
            for i in range(len(dsdl_type.name_components) - 1, 0, -1):
                ancestor_ns = '.'.join(dsdl_type.name_components[0:i])
                # This little optimization pushed the complexity metric
                # too high which is why I did noqa here.
                if ancestor_ns in namespace_index:
                    break
                namespace_index.add(ancestor_ns)

        namespace._add_data_type(dsdl_type, language_context.get_output_extension())

    # We now have an index of all namespace names and we have Namespace
    # objects for non-empty namespaces. This final loop will build any
    # missing (i.e. empty) namespaces and all the links to form the
    # namespace tree.
    for full_namespace in namespace_index:
        namespace, _ = get_or_make_namespace(full_namespace)

        parent_namespace_components = namespace._namespace_components[0:-1]
        if (len(parent_namespace_components) > 0):
            parent_name = '.'.join(parent_namespace_components)

            parent, _ = get_or_make_namespace(parent_name)
            parent._add_nested_namespace(namespace)

    try:
        return next(iter(namespaces.values())).get_root_namespace()
    except StopIteration:
        pass

    # The empty namespace
    return get_or_make_namespace('')[0]
