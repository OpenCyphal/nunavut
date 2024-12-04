#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Contains template loaders for Nunavut's Jinja2 environment.
"""

import collections
import importlib
import itertools
import logging
from pathlib import Path
from typing import Any, Callable, Deque, Dict, Iterable, List, Mapping, Optional, Tuple, Type, TypeVar, cast

import pydsdl

from nunavut import Namespace as NunavutNamespace
from nunavut._utilities import TEMPLATE_SUFFIX, ResourceSearchPolicy

from .jinja2 import BaseLoader, Environment, FileSystemLoader, PackageLoader, TemplateNotFound

logger = logging.getLogger(__name__)


DEFAULT_TEMPLATE_PATH = "templates"
DEFAULT_SUPPORT_TEMPLATE_PATH = "support"


# +--------------------------------------------------------------------------------------------------------------------+
# | LOADERS : DSDLTemplateLoader
# +--------------------------------------------------------------------------------------------------------------------+


class DSDLTemplateLoader(BaseLoader):
    """
    Nunavut's DSDL template loader is similar to a choice loader with a file-system loader
    first and a package loader as a fallback. The major difference is a DFS is performed
    on the type hierarchy of the type a template is being loaded for. So, for example,
    if no ``StructureType.j2`` template is found then this loader will look for a ``CompositeType.j2``
    and so on.

    :param Optional[NunavutNamespace] namespace: The namespace to use for loading templates. If None then no package
        loader is created.
    :param Optional[List[Path]] templates_dirs: A list of directories to load templates from using a
        :class:`nunavut.jinja.jinja2.FileSystemLoader`. If ``None`` no filesystem loader is created.
    :param bool followlinks: Argument passed on to the :class:`nunavut.jinja.jinja2.FileSystemLoader` instance.
    :param str builtin_template_path: The name of the package under the target language support package to load
        templates from. This is ignored if ``namespace`` is None.
    :param search_policy: If set to "FIND_ALL" then this loader will search using all loaders and will enumerate
                          templates from all loaders. If set to "FIND_FIRST" then the loader will only use the first
                          loader configured for both search and enumeration.
    :param str encoding: The encoding to use when reading templates from the filesystem.
    :param Any kwargs: Arguments forwarded to the :class:`jinja.jinja2.BaseLoader`.
    """

    def __init__(
        self,
        namespace: Optional[NunavutNamespace] = None,
        templates_dirs: Optional[List[Path]] = None,
        followlinks: bool = False,
        builtin_template_path: str = DEFAULT_TEMPLATE_PATH,
        search_policy: ResourceSearchPolicy = ResourceSearchPolicy.FIND_ALL,
        encoding: str = "utf-8",
        **_: Any,
    ):
        super().__init__()
        self._encoding = encoding
        self._type_to_template_lookup_cache: Dict[pydsdl.Any, Path] = dict()

        if templates_dirs is not None:
            for templates_dir_item in templates_dirs:
                if not templates_dir_item.exists():
                    raise ValueError(f"Templates directory {str(templates_dir_item)} did not exist?")
            logger.info("Loading templates from file system at %s", templates_dirs)
            self._fs_loader = FileSystemLoader(
                list(str(d) for d in templates_dirs), followlinks=followlinks, encoding=encoding
            )
        else:
            self._fs_loader = None

        if namespace is not None and (search_policy == ResourceSearchPolicy.FIND_ALL or self._fs_loader is None):
            package_name_for_templates = (
                namespace.get_language_context().get_target_language().get_templates_package_name()
            )
            logger.info("Loading templates from package %s.%s", builtin_template_path, builtin_template_path)
            self._package_loader = PackageLoader(
                package_name_for_templates, package_path=builtin_template_path, encoding=encoding
            )
            self._templates_package_name = f"{package_name_for_templates}.{builtin_template_path}"
        else:
            self._package_loader = None
            self._templates_package_name = ""

    # --[ BaseLoader Overrides ]---------------------------------------------------------------------------------------

    def get_source(self, environment: Environment, template: str) -> Tuple[Any, str, Callable[..., bool]]:
        """
        Override of :meth:`BaseLoader.get_source` that returns the sources of the template from the filesystem loader
        and/or the package loader.
        """
        if self._fs_loader is not None:
            try:
                return cast(
                    Tuple[Any, str, Callable[..., bool]],
                    self._fs_loader.get_source(environment, template),
                )
            except TemplateNotFound:
                if self._package_loader is None:
                    raise
        if self._package_loader is not None:
            return cast(
                Tuple[Any, str, Callable[..., bool]],
                self._package_loader.get_source(environment, template),
            )
        raise TemplateNotFound(template)

    def list_templates(self) -> Iterable[str]:
        """
        Override of :meth:`BaseLoader.list_templates` that returns an aggregate of the filesystem loader and
        package loader templates.

        :return: A list of templates names (i.e. file stems) found by this Generator object.

        .. invisible-code-block: python

            from nunavut.jinja.loaders import DSDLTemplateLoader
            from nunavut._utilities import TEMPLATE_SUFFIX
            from unittest.mock import MagicMock

            mock_namespace = MagicMock()
            mock_get_target_language = mock_namespace.get_language_context.return_value.get_target_language
            mock_get_target_language.return_value.get_templates_package_name.return_value = 'nunavut.lang.c'

            template_loaders = DSDLTemplateLoader(namespace=mock_namespace)

            templates = template_loaders.list_templates()

            structure_type = None

            for template in templates:
                if template == 'StructureType' + TEMPLATE_SUFFIX:
                    structure_type = template

            assert structure_type is not None

        """
        iterables = []
        if self._fs_loader is not None:
            iterables.append(self._filter_template_list_by_suffix(self._fs_loader.list_templates()))
        if self._package_loader is not None:
            iterables.append(self._filter_template_list_by_suffix(self._package_loader.list_templates()))

        return itertools.chain(*iterables)

    # --[ PUBLIC ]-----------------------------------------------------------------------------------------------------

    @property
    def encoding(self) -> str:
        """
        The encoding used to read templates from the filesystem.
        """
        return self._encoding

    def get_templates(self) -> Iterable[Path]:
        """
        Enumerate all templates found in the templates path.
        :data:`~TEMPLATE_SUFFIX` as the suffix for the filename. This method differs from the :class:`BaseLoader`
        override of :meth:`BaseLoader.list_templates` in that it returns paths instead of just file name stems.

        :return: A list of paths to all templates found by this Generator object.

        .. invisible-code-block: python

            from nunavut.jinja.loaders import DSDLTemplateLoader
            from nunavut._utilities import TEMPLATE_SUFFIX
            from unittest.mock import MagicMock

            mock_namespace = MagicMock()
            mock_get_target_language = mock_namespace.get_language_context.return_value.get_target_language
            mock_get_target_language.return_value.get_templates_package_name.return_value = 'nunavut.lang.c'

            template_loaders = DSDLTemplateLoader(namespace=mock_namespace)

            templates = template_loaders.get_templates()

            structure_type = None

            for template in templates:
                if template.stem == 'StructureType':
                    structure_type = template
                assert template.suffix == TEMPLATE_SUFFIX

            assert structure_type is not None
            assert structure_type.suffix == TEMPLATE_SUFFIX
            assert structure_type.exists()

        """
        files = set()
        if self._fs_loader is not None:
            for template_dir in self._fs_loader.searchpath:
                for template in Path(str(template_dir)).glob(f"**/*{TEMPLATE_SUFFIX}"):
                    files.add(template)
        if self._package_loader is not None:
            templates_module = importlib.import_module(self._templates_package_name)
            spec_perhaps = templates_module.__spec__
            file_perhaps: Optional[str] = None
            if spec_perhaps is not None:
                file_perhaps = spec_perhaps.origin
            if file_perhaps is None or file_perhaps == "builtin":
                raise RuntimeError("Unknown template package origin?")
            templates_base_path = Path(file_perhaps).parent
            for t in map(Path, self._filter_template_list_by_suffix(self._package_loader.list_templates())):
                files.add(templates_base_path / t)
        return sorted(files)

    def type_to_template(self, value_type: Type) -> Optional[Path]:
        """
        Given a type object, return a template used to generate code for the type.

        :return: a template or None if no template could be found for the given type.

        .. invisible-code-block: python
            from nunavut.jinja.loaders import DSDLTemplateLoader
            import pydsdl
            from unittest.mock import MagicMock

            mock_namespace = MagicMock()
            mock_get_target_language = mock_namespace.get_language_context.return_value.get_target_language
            mock_get_target_language.return_value.get_templates_package_name.return_value = 'nunavut.lang.py'

            l = DSDLTemplateLoader(namespace=mock_namespace)
            template_name = l.type_to_template(pydsdl.StructureType)

            assert template_name is not None
            assert template_name.name == 'StructureType.j2'

        """
        return self._to_template(self._type_to_template_internal, value_type)

    def index_file_to_template(self, index_file: Path) -> Optional[Path]:
        """
        Given an index file output path, return a template used to render the index.

        :return: a template or None if no template could be found for the given index file.

        .. invisible-code-block: python
            from nunavut.jinja.loaders import DSDLTemplateLoader
            import pydsdl
            from pathlib import Path
            from unittest.mock import MagicMock

            mock_namespace = MagicMock()
            mock_get_target_language = mock_namespace.get_language_context.return_value.get_target_language
            mock_get_target_language.return_value.get_templates_package_name.return_value = 'nunavut.lang.c'

            l = DSDLTemplateLoader(namespace=mock_namespace)
            template_name = l.index_file_to_template(Path("depfile.dep"))

            assert template_name is not None
            assert template_name.name == 'depfile.j2'

        """
        return self._to_template(self._index_file_to_template_internal, index_file)

    # +----------------------------------------------------------------------------------------------------------------+
    # | PRIVATE
    # +----------------------------------------------------------------------------------------------------------------+
    @classmethod
    def _filter_template_list_by_suffix(cls, template_list: Iterable[str]) -> Iterable[str]:
        return filter(lambda x: Path(x).suffix == TEMPLATE_SUFFIX, template_list)

    FromType = TypeVar("FromType")

    def _to_template(
        self,
        converter: Callable[[FromType, Mapping[str, Path]], Optional[Path]],
        value: FromType,
    ) -> Optional[Path]:
        """
        Adapter that uses a provided template resolution function to resolve a template using the loaders configured
        for this instance.
        :param converter: A function that takes a value and a dictionary of templates and returns a template path.
        """
        template_path = None
        if self._fs_loader is not None:
            filtered_templates = map(Path, self._filter_template_list_by_suffix(self._fs_loader.list_templates()))
            template_path = converter(value, dict(map(lambda x: (x.stem, x), filtered_templates)))
        if template_path is None and self._package_loader is not None:
            filtered_templates = map(Path, self._filter_template_list_by_suffix(self._package_loader.list_templates()))
            template_path = converter(value, dict(map(lambda x: (x.stem, x), filtered_templates)))
        return template_path

    def _index_file_to_template_internal(self, index_file: Path, templates: Mapping[str, Path]) -> Optional[Path]:
        try:
            return templates[index_file.stem]
        except KeyError:
            pass
        try:
            return templates["index"]
        except KeyError:
            return None

    def _type_to_template_internal(self, value_type: Type, templates: Mapping[str, Path]) -> Optional[Path]:
        search_queue: Deque[Type] = collections.deque()
        discovered = set()
        search_queue.appendleft(value_type)
        template_path = None

        while len(search_queue) > 0:
            current_search_type = search_queue.pop()
            try:
                template_path = self._type_to_template_lookup_cache[current_search_type]
                break
            except KeyError:
                pass

            try:
                logging.debug(
                    "NunavutTemplateLoader.type_to_template for %s: considering %s...",
                    value_type.__name__,
                    current_search_type.__name__,
                )
                template_path = templates[current_search_type.__name__]
                self._type_to_template_lookup_cache[current_search_type] = template_path
                break
            except KeyError:
                for base_type in current_search_type.__bases__:
                    if base_type != object and base_type not in discovered:
                        search_queue.appendleft(base_type)
                        discovered.add(current_search_type)

        return template_path


# +--------------------------------------------------------------------------------------------------------------------+
# | LOADERS : DSDLSupportTemplateLoader
# +--------------------------------------------------------------------------------------------------------------------+


class DSDLSupportTemplateLoader(DSDLTemplateLoader):
    """
    DSDLTemplateLoader that specializes in loading language support templates.

    :param Any kwargs: Arguments forwarded to the :class:`DSDLTemplateLoader` baseclass.
    """

    def __init__(
        self,
        namespace: NunavutNamespace,
        resource_types: int,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._target_language = namespace.get_language_context().get_target_language()
        self._resource_types = resource_types
        self._support_files_index: Optional[dict[str, Path]] = None

    # --[ BaseLoader Overrides ]---------------------------------------------------------------------------------------

    def get_source(self, environment: Environment, template: str) -> Tuple[Any, str, Callable[..., bool]]:
        """
        Override of :meth:`DSDLTemplateLoader.get_source` that returns the source a the template from the filesystem.
        Nunavut loaders work differently than Jinja2 loaders in that they discover all templates and support files
        at initialization time.
        """
        try:
            return super().get_source(environment, template)
        except TemplateNotFound:
            pass

        support_file = self.find_support_file(template)

        if support_file is None:
            raise TemplateNotFound(template)

        with support_file.open(encoding=self.encoding) as f:
            contents = f.read()

        mtime = support_file.stat().st_mtime

        def is_modified() -> bool:  # pragma: no cover
            try:
                return support_file.stat().st_mtime == mtime
            except OSError:
                return False

        return contents, support_file.as_posix(), is_modified

    def list_templates(self) -> Iterable[str]:
        """
        Override of :meth:`DSDLTemplateLoader.list_templates` that returns an aggregate that loader's templates and
        support file templates.

        :return: A list of templates names (i.e. file names) found by this Generator object.

        .. invisible-code-block: python

            from nunavut.jinja.loaders import DSDLTemplateLoader, DSDLSupportTemplateLoader
            from nunavut._utilities import ResourceType, TEMPLATE_SUFFIX
            from nunavut.lang import LanguageContext, LanguageContextBuilder
            from unittest.mock import MagicMock

            lctx = LanguageContextBuilder().set_target_language("c").create()

            namespace = MagicMock()
            namespace.get_language_context.return_value = lctx

            template_loaders = DSDLSupportTemplateLoader(namespace, ResourceType.SERIALIZATION_SUPPORT.value)

            templates = template_loaders.list_templates()

            serialization_template = None

            for template in templates:
                if template == f"serialization{TEMPLATE_SUFFIX}":
                    serialization_template = template

            assert serialization_template is not None

        """
        return itertools.chain(
            super().list_templates(),
            map(lambda p: p.name, self.get_support_files()),
        )

    # --[ DSDLTemplateLoader Overrides ]------------------------------------------------------------------------------

    def get_templates(self) -> Iterable[Path]:
        """
        Override of :meth:`DSDLTemplateLoader.get_templates` that returns an aggregate that loader's templates and
        support file templates.

        :return: A list of templates paths found by this Generator object.

        .. invisible-code-block: python

            from nunavut.jinja.loaders import DSDLTemplateLoader, DSDLSupportTemplateLoader
            from nunavut._utilities import ResourceType, TEMPLATE_SUFFIX
            from nunavut.lang import LanguageContext, LanguageContextBuilder
            from unittest.mock import MagicMock

            lctx = LanguageContextBuilder().set_target_language("c").create()

            namespace = MagicMock()
            namespace.get_language_context.return_value = lctx

            template_loaders = DSDLSupportTemplateLoader(namespace, ResourceType.SERIALIZATION_SUPPORT.value)

            templates = template_loaders.get_templates()

            serialization_template = None

            for template in templates:
                if template.name == f"serialization{TEMPLATE_SUFFIX}":
                    serialization_template = template

            assert serialization_template is not None

        """
        return itertools.chain(super().get_templates(), self.get_support_files())

    # --[ PUBLIC ]-----------------------------------------------------------------------------------------------------

    def get_support_files(self) -> Iterable[Path]:
        """
        Enumerate all support files found for the target language based on the resource types provided in the
        constructor.
        """
        return self._get_support_file_index().values()

    def find_support_file(self, name: str, default: Optional[Path] = None) -> Optional[Path]:
        """
        Find a support file by name.
        """
        return self._get_support_file_index().get(name, default)

    # --[ PRIVATE ]----------------------------------------------------------------------------------------------------

    def _get_support_file_index(self) -> Dict[str, Path]:
        if self._support_files_index is None:
            self._support_files_index = dict(
                map(lambda x: (x.name, x), self._target_language.get_support_files(self._resource_types))
            )
        return self._support_files_index
