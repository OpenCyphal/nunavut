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
from pathlib import Path, PurePath
from typing import Dict, Any, Callable
from typing import Generator as GeneratorType

from pydsdlgen.jinja.jinja2 import (Environment, FileSystemLoader,
                                    TemplateAssertionError, nodes,
                                    select_autoescape, DebugUndefined)

from pydsdlgen.jinja.jinja2.ext import Extension
from pydsdlgen.jinja.jinja2.parser import Parser

from pydsdl.data_type import CompoundType, DataType, PrimitiveType, Constant

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
    uses these statements where missing or False values would result in malformed
    source code.
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
    :param Path templates_dir: The directory containing the jinja templates.

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
            !!python/object:pydsdl.data_type.StructureType
            _attributes:
            - !!python/object:pydsdl.data_type.Field
            _data_type: !!python/object:pydsdl.data_type.UnsignedIntegerType
                _bit_length: 16
                _cast_mode: &id001 !!python/object/apply:pydsdl.data_type.CastMode
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

    @classmethod
    def filter_pydsdl_type_to_template(cls, value: Any) -> str:
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
        return str(
            PurePath(type(value).__name__).with_suffix(cls.TEMPLATE_SUFFIX))

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
    def is_primitive(value: DataType) -> bool:
        """
        Tests if a given ``DataType`` instance is a ``PrimitiveType``.
        Available in all template environments as ``is primitive``.

        Example::

            {% if field.data_type is primitive %}
                {{ field.data_type | c.type_from_primitive }} {{ field.name }};
            {% endif -%}

        :param value: The instance to test.

        :returns: True if value is an instance of ``pydsdl.data_type.PrimitiveType``.
        """
        return isinstance(value, PrimitiveType)

    @staticmethod
    def is_constant(value: DataType) -> bool:
        """
        Tests if a given ``DataType`` instance is a ``Constant``.
        Available in all template environments as ``is constant``.

        Example::

            {%- if field is constant %}
                const {{ field.data_type | c.type_from_primitive(use_standard_types=True) }} {{ field.name }} = {{ field.initialization_expression }};
            {% endif %}

        :param value: The instance to test.

        :returns: True if value is an instance of ``pydsdl.data_type.Constant``.
        """  # noqa: E501
        return isinstance(value, Constant)

    # +-----------------------------------------------------------------------+

    def __init__(self,
                 type_map: Dict[CompoundType, Path],
                 templates_dir: Path):

        super(Generator, self).__init__(type_map)

        if templates_dir is None:
            raise ValueError("Templates directory argument was None")
        if not Path(templates_dir).exists:
            raise ValueError(
                "Templates directory {} did not exist?".format(templates_dir))

        self._templates_dir = Path(templates_dir)

        logger.info("Loading templates from {}".format(templates_dir))

        fsloader = FileSystemLoader([str(templates_dir)], followlinks=True)

        autoesc = select_autoescape(enabled_extensions=('htm', 'html', 'xml', 'json'),
                                    default_for_string=False,
                                    default=False)

        self._env = Environment(loader=fsloader,
                                extensions=[JinjaAssert],
                                autoescape=autoesc,
                                undefined=DebugUndefined,
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

    def get_templates(self) -> GeneratorType[Path, None, None]:
        """
        Enumerate paths to all files within self._templates_dir with
        :data:`~TEMPLATE_SUFFIX` as the suffix for the filename.

        :returns: A Python generator that produces Path elements for all templates
                  found by this Generator object.
        """
        return self._templates_dir.glob("**/*{}".format(self.TEMPLATE_SUFFIX))

    def generate_all(self, is_dryrun: bool = False) -> int:
        for (parsed_type, output_path) in self.type_map.items():
            self._generate_type(parsed_type, output_path, is_dryrun)
        return 0

    def _generate_type(self, input_type: CompoundType, output_path: Path, is_dryrun: bool) -> None:
        template_name = self.filter_pydsdl_type_to_template(input_type)
        self._env.globals["now_utc"] = datetime.utcnow()
        template = self._env.get_template(template_name)
        template_gen = template.generate(T=input_type)
        if not is_dryrun:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(str(output_path), "w") as output_file:
                for part in template_gen:
                    output_file.write(part)
