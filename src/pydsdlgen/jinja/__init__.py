#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    jinja-based :class:`~pydsdlgen.generators.AbstractGenerator` implementation.
"""

import logging
from datetime import datetime
from pathlib import Path
from collections import deque

from typing import Dict, Any, Callable, Optional, List, Iterable

from pydsdlgen.jinja.jinja2 import (Environment, FileSystemLoader,
                                    TemplateAssertionError, nodes,
                                    select_autoescape, StrictUndefined)

from pydsdlgen.jinja.jinja2.ext import Extension
from pydsdlgen.jinja.jinja2.parser import Parser

from pydsdl.expression import Any as DsdlAny
from pydsdl.serializable import (CompositeType, PrimitiveType,
                                 Constant, SerializableType)

from ..generators import AbstractGenerator

import inspect
from .lang import add_language_support

logger = logging.getLogger(__name__)

# +---------------------------------------------------------------------------+
# | JINJA : Extensions
# +---------------------------------------------------------------------------+


class JinjaAssert(Extension):
    """
    Jinja2 extension that allows ``{% assert T.field %}`` statements. Templates should
    uses these statements where False values would result in malformed source code.
    """

    tags = set(['assert'])

    def __init__(self, environment: Environment):
        super(JinjaAssert, self).__init__(environment)

    def parse(self, parser: Parser) -> nodes.Node:
        """
        See http://jinja.pocoo.org/docs/2.10/extensions/ for help writing
        extensions.
        """

        # This will be the macro name "assert"
        token = next(parser.stream)

        # now we parse a single expression that must evalute to True
        args = [parser.parse_expression(),
                nodes.Const(token.lineno),
                nodes.Const(parser.name),
                nodes.Const(parser.filename)]

        if parser.stream.skip_if('comma'):
            args.append(parser.parse_expression())
        else:
            args.append(nodes.Const("Template assertion failed."))

        return nodes.CallBlock(self.call_method('_do_assert', args),
                               [], [], "").set_lineno(token.lineno)

    def _do_assert(self,
                   expression: str,
                   lineno: int,
                   name: str,
                   filename: str,
                   message: str,
                   caller: Callable) -> Any:
        if not expression:
            raise TemplateAssertionError(message, lineno, name, filename)
        return caller()


class Generator(AbstractGenerator):
    """ :class:`~pydsdlgen.generators.AbstractGenerator` implementation that uses
    Jinja2 templates to generate source code.

    :param dict type_map:       A map of pydsdl types to the path the output file for
                                this type will be generated at.
    :param Path templates_dir:  The directory containing the jinja templates.

    :param bool followlinks:    If True then symbolic links will be followed when
                                searching for templates.
    """

    TEMPLATE_SUFFIX = ".j2"  #: The suffix expected for Jinja templates.

    # +-----------------------------------------------------------------------+
    # | JINJA : filters
    # +-----------------------------------------------------------------------+

    @staticmethod
    def filter_yamlfy(value: Any) -> str:
        """
        Filter to, optionally, emit a dump of the dsdl input as a yaml document.
        Available as ``yamlfy`` in all template environments.

        Example::

            /*
            {{ T | yamlfy }}
            */

        Result Example (truncated for brevity)::

            /*
            !!python/object:pydsdl.serializable.StructureType
            _attributes:
            - !!python/object:pydsdl.serializable.Field
            _serializable: !!python/object:pydsdl.serializable.UnsignedIntegerType
                _bit_length: 16
                _cast_mode: &id001 !!python/object/apply:pydsdl.serializable.CastMode
                - 0
            _name: value
            */

        :param value: The input value to parse as yaml.

        :returns: If pyyaml is available, a pretty dump of the given value as yaml.
                  If pyyaml is not available then an empty string is returned.
        """
        try:
            from yaml import dump
            return str(dump(value))
        except ImportError:
            return ""

    def filter_pydsdl_type_to_template(self, value: Any) -> str:
        """
        Template for type resolution as a filter. Available as ``pydsdl_type_to_template``
        in all template environments.

        Example::

            {%- for field in T.attributes %}
                {%* include field.data_type | pydsdl_type_to_template %}
                {%- if not loop.last %},{% endif %}
            {%- endfor %}

        :param value: The input value to change into a template include path.

        :returns: A path to a template named for the type with :any:`Generator.TEMPLATE_SUFFIX`
        """
        search_queue = deque()  # type: ignore
        discovered = set()  # type: ignore
        search_queue.appendleft(type(value))
        template_path = Path(type(value).__name__).with_suffix(self.TEMPLATE_SUFFIX)

        def _find_template_by_name(name: str, templates: Iterable[Path]) -> Optional[Path]:
            for template_path in templates:
                if template_path.stem == name:
                    return template_path
            return None

        while len(search_queue) > 0:
            data_type = search_queue.pop()
            try:
                template_path = self._type_to_template_lookup_cache[data_type]
                break
            except KeyError:
                pass

            optional_template_path = _find_template_by_name(data_type.__name__, self.get_templates())

            if optional_template_path is not None:
                template_path = optional_template_path
                self._type_to_template_lookup_cache[data_type] = template_path
                break
            else:
                for base_type in data_type.__bases__:
                    if base_type != object and base_type not in discovered:
                        search_queue.appendleft(base_type)
                        discovered.add(data_type)

        return template_path.name

    @staticmethod
    def filter_typename(value: Any) -> str:
        """
        Filters a given token as its type name. Available as ``typename``
        in all template environments.

        This example supposes that ``T.some_value == "some string"``

        Example::

            {{ T.some_value | typename }}

        Result Example::

            str

        :param value: The input value to filter into a type name.

        :returns: The ``__name__`` of the python type.
        """
        return type(value).__name__

    # +-----------------------------------------------------------------------+
    # | JINJA : tests
    # +-----------------------------------------------------------------------+

    @staticmethod
    def is_primitive(value: DsdlAny) -> bool:
        """
        Tests if a given dsdl instance is a ``PrimitiveType``.
        Available in all template environments as ``is primitive``.

        Example::

            {% if field.data_type is primitive %}
                {{ field.data_type | c.type_from_primitive }} {{ field.name }};
            {% endif -%}

        :param value: The instance to test.

        :returns: True if value is an instance of ``pydsdl.serializable.PrimitiveType``.
        """
        return isinstance(value, PrimitiveType)

    @staticmethod
    def is_constant(value: DsdlAny) -> bool:
        """
        Tests if a given dsdl instance is a ``Constant``.
        Available in all template environments as ``is constant``.

        Example::

            {%- if field is constant %}
                const {{ field.data_type | c.type_from_primitive(use_standard_types=True) }} {{ field.name }} = {{ field.initialization_expression }};
            {% endif %}

        :param value: The instance to test.

        :returns: True if value is an instance of ``pydsdl.serializable.Constant``.
        """  # noqa: E501
        return isinstance(value, Constant)

    @staticmethod
    def is_serializable(value: DsdlAny) -> bool:
        """
        Tests if a given dsdl instance is a ``SerializableType``.
        Available in all template environments as ``is serializable``.

        Example::

            {%- if field is serializable %}
                // Yup, this is serializable
            {% endif %}

        :param value: The instance to test.

        :returns: True if value is an instance of ``pydsdl.serializable.SerializableType``.
        """  # noqa: E501
        return isinstance(value, SerializableType)

    # +-----------------------------------------------------------------------+

    def __init__(self,
                 type_map: Dict[CompositeType, Path],
                 templates_dir: Path,
                 followlinks: bool = False):

        super(Generator, self).__init__(type_map)

        if templates_dir is None:
            raise ValueError("Templates directory argument was None")
        if not Path(templates_dir).exists:
            raise ValueError(
                "Templates directory {} did not exist?".format(templates_dir))

        self._templates_dir = templates_dir

        self._type_to_template_lookup_cache = dict()  # type: Dict[DsdlAny, Path]

        self._templates_list = None  # type: Optional[List[Path]]

        logger.info("Loading templates from {}".format(templates_dir))

        fs_loader = FileSystemLoader([str(templates_dir)], followlinks=followlinks)

        autoesc = select_autoescape(enabled_extensions=('htm', 'html', 'xml', 'json'),
                                    default_for_string=False,
                                    default=False)

        self._env = Environment(loader=fs_loader,
                                extensions=[JinjaAssert],
                                autoescape=autoesc,
                                undefined=StrictUndefined,
                                keep_trailing_newline=True,
                                auto_reload=False)

        # Automatically find the locally defined filters and
        # tests and add them to the jinja environment.
        member_functions = inspect.getmembers(self, inspect.isroutine)
        for function_tuple in member_functions:
            function_name = function_tuple[0]
            if len(function_name) > 3 and function_name[0:3] == "is_":
                self._env.tests[function_name[3:]] = function_tuple[1]
            if len(function_name) > 7 and function_name[0:7] == "filter_":
                self._env.filters[function_name[7:]] = function_tuple[1]

        # Add in additional filters and tests for built-in languages this
        # module supports.
        add_language_support('c', self._env)
        add_language_support('cpp', self._env)
        add_language_support('js', self._env)

    def get_templates(self) -> Iterable[Path]:
        """
        Enumerate all templates found in the templates path.
        :data:`~TEMPLATE_SUFFIX` as the suffix for the filename.

        :returns: A Python generator that produces Path elements for all templates
                  found by this Generator object.
        """
        return self._templates_dir.glob("**/*{}".format(self.TEMPLATE_SUFFIX))

    def generate_all(self, is_dryrun: bool = False) -> int:
        for (parsed_type, output_path) in self.type_map.items():
            self._generate_type(parsed_type, output_path, is_dryrun)
        return 0

    def _generate_type(self, input_type: CompositeType, output_path: Path, is_dryrun: bool) -> None:
        template_name = self.filter_pydsdl_type_to_template(input_type)
        self._env.globals["now_utc"] = datetime.utcnow()
        template = self._env.get_template(template_name)
        template_gen = template.generate(T=input_type)
        if not is_dryrun:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(str(output_path), "w") as output_file:
                for part in template_gen:
                    output_file.write(part)
