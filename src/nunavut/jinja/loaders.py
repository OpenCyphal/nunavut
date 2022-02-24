#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2021  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
import collections
import importlib
import logging
import pathlib
import typing

import pydsdl

from ..lang._config import VersionReader
from .jinja2 import BaseLoader, Environment, FileSystemLoader, PackageLoader, TemplateNotFound

logger = logging.getLogger(__name__)


TEMPLATE_SUFFIX = ".j2"  #: The suffix expected for Jinja templates.

DEFAULT_TEMPLATE_PATH = "templates"


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

    :param Optional[List[Path]] templates_dirs: A list of directories to load templates from using a
        :class:`nunavut.jinja.jinja2.FileSystemLoader`. If ``None`` no filesystem loader is created.
    :param bool followlinks: Argument passed on to the :class:`nunavut.jinja.jinja2.FileSystemLoader` instance.
    :param Optional[str] package_name_for_templates: The name of the package to load templates from. If ``None``
        then no :class:`nunavut.jinja.jinja2.PackageLoader` is created.
    :param str builtin_template_path: The name of the package under the ``package_name_for_templates`` package to load
        templates from. This is ignored if ``package_name_for_templates`` is None.
    :param Any kwargs: Arguments forwarded to the :class:`jinja.jinja2.BaseLoader`.
    """

    def __init__(
        self,
        templates_dirs: typing.Optional[typing.List[pathlib.Path]] = None,
        followlinks: bool = False,
        package_name_for_templates: typing.Optional[str] = None,
        builtin_template_path: str = DEFAULT_TEMPLATE_PATH,
        **kwargs: typing.Any
    ):
        super().__init__(**kwargs)
        self._type_to_template_lookup_cache = dict()  # type: typing.Dict[pydsdl.Any, pathlib.Path]
        self._templates_package_name = None  # type: typing.Optional[str]

        if templates_dirs is not None:
            for templates_dir_item in templates_dirs:
                if not pathlib.Path(templates_dir_item).exists:
                    raise ValueError("Templates directory {} did not exist?".format(templates_dir_item))
            logger.info("Loading templates from file system at {}".format(templates_dirs))
            self._fsloader = FileSystemLoader((str(d) for d in templates_dirs), followlinks=followlinks)
        else:
            self._fsloader = None

        if package_name_for_templates is not None:
            logger.info("Loading templates from package {}.{}".format(builtin_template_path, builtin_template_path))
            self._package_loader = PackageLoader(package_name_for_templates, package_path=builtin_template_path)
            self._templates_package_name = "{}.{}".format(package_name_for_templates, builtin_template_path)
        else:
            self._package_loader = None

    def get_source(
        self, environment: Environment, template: str
    ) -> typing.Tuple[typing.Any, str, typing.Callable[..., bool]]:
        if self._fsloader is not None:
            try:
                return typing.cast(
                    typing.Tuple[typing.Any, str, typing.Callable[..., bool]],
                    self._fsloader.get_source(environment, template),
                )
            except TemplateNotFound:
                if self._package_loader is None:
                    raise
        if self._package_loader is not None:
            return typing.cast(
                typing.Tuple[typing.Any, str, typing.Callable[..., bool]],
                self._package_loader.get_source(environment, template),
            )
        raise TemplateNotFound(template)

    def list_templates(self) -> typing.Iterable[str]:
        """
        Override of :meth:`BaseLoader.list_templates` that returns an aggregate of the filesystem loader and
        package loader templates.

        :return: A list of templates names (i.e. file stems) found by this Generator object.

        .. invisible-code-block: python

            from nunavut.jinja.loaders import DSDLTemplateLoader, TEMPLATE_SUFFIX

            template_loaders = DSDLTemplateLoader(package_name_for_templates='nunavut.lang.c')

            templates = template_loaders.list_templates()

            structure_type = None

            for template in templates:
                if template == 'StructureType' + TEMPLATE_SUFFIX:
                    structure_type = template

            assert structure_type is not None

        """
        files = []
        if self._fsloader is not None:
            files += self._filter_template_list_by_suffix(self._fsloader.list_templates())
        if self._package_loader is not None:
            files += self._filter_template_list_by_suffix(self._package_loader.list_templates())

        return files

    def get_template_sets(self) -> typing.List[typing.Tuple[str, str, typing.Tuple[int, int, int]]]:
        template_sets = []  # type: typing.List[typing.Tuple[str, str, typing.Tuple[int, int, int]]]
        if self._templates_package_name is not None:
            vr = VersionReader(self._templates_package_name)
            template_sets.append(("package", self._templates_package_name, vr.version))
        return template_sets

    def get_templates(self) -> typing.Iterable[pathlib.Path]:
        """
        Enumerate all templates found in the templates path.
        :data:`~TEMPLATE_SUFFIX` as the suffix for the filename. This method differs from the :class:`BaseLoader`
        override of :meth:`BaseLoader.list_templates` in that it returns paths instead of just file name stems.

        :return: A list of paths to all templates found by this Generator object.

        .. invisible-code-block: python

            from nunavut.jinja.loaders import DSDLTemplateLoader, TEMPLATE_SUFFIX

            template_loaders = DSDLTemplateLoader(package_name_for_templates='nunavut.lang.c')

            templates = template_loaders.get_templates()

            structure_type = None

            for template in templates:
                if template.stem == 'StructureType':
                    structure_type = template

            assert structure_type is not None
            assert structure_type.suffix == TEMPLATE_SUFFIX
            assert structure_type.exists()

        """
        files = set()
        if self._fsloader is not None:
            for template_dir in self._fsloader.searchpath:
                for template in pathlib.Path(template_dir).glob("**/*{}".format(TEMPLATE_SUFFIX)):
                    files.add(template)
        if self._package_loader is not None and self._templates_package_name is not None:
            templates_module = importlib.import_module(self._templates_package_name)
            spec_perhaps = templates_module.__spec__
            file_perhaps = None  # type: typing.Optional[str]
            if spec_perhaps is not None:
                file_perhaps = spec_perhaps.origin
            if file_perhaps is None or file_perhaps == "builtin":
                raise RuntimeError("Unknown template package origin?")
            templates_base_path = pathlib.Path(file_perhaps).parent
            for t in self._package_loader.list_templates():
                files.add(templates_base_path / pathlib.Path(t))
        return sorted(files)

    def type_to_template(self, value_type: typing.Type) -> typing.Optional[pathlib.Path]:
        """
        Given a type object, return a template used to generate code for the type.

        :return: a template or None if no template could be found for the given type.

        .. invisible-code-block: python
            from nunavut.jinja.loaders import DSDLTemplateLoader
            import pydsdl

            l = DSDLTemplateLoader(package_name_for_templates='nunavut.lang.py')
            template_name = l.type_to_template(pydsdl.StructureType)

            assert template_name is not None
            assert template_name.name == 'Any.j2'

        """
        template_path = None
        if self._fsloader is not None:
            filtered_templates = self._filter_template_list_by_suffix(self._fsloader.list_templates())
            template_path = self._type_to_template_internal(
                value_type, dict(map(lambda x: (pathlib.Path(x).stem, pathlib.Path(x)), filtered_templates))
            )
        if template_path is None and self._package_loader is not None:
            filtered_templates = self._filter_template_list_by_suffix(self._package_loader.list_templates())
            template_path = self._type_to_template_internal(
                value_type, dict(map(lambda x: (pathlib.Path(x).stem, pathlib.Path(x)), filtered_templates))
            )

        return template_path

    # +----------------------------------------------------------------------------------------------------------------+
    # | PRIVATE
    # +----------------------------------------------------------------------------------------------------------------+
    @staticmethod
    def _filter_template_list_by_suffix(files: typing.List[str]) -> typing.List[str]:
        return [f for f in files if (pathlib.Path(f).suffix == TEMPLATE_SUFFIX)]

    def _type_to_template_internal(
        self, value_type: typing.Type, templates: typing.Mapping[str, pathlib.Path]
    ) -> typing.Optional[pathlib.Path]:
        search_queue = collections.deque()  # type: typing.Deque[typing.Any]
        discovered = set()  # type: typing.Set[typing.Any]
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
                    "NunavutTemplateLoader.type_to_template for {}: considering {}...".format(
                        value_type.__name__, current_search_type.__name__
                    )
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
