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
from typing import Dict, List, Any, Callable
from typing import Generator as GeneratorType

from pydsdlgen.jinja.jinja2 import (Environment, FileSystemLoader, Template,
                                    TemplateAssertionError, nodes)

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

    :param Path output_basedir: The directory under which all output will be placed.
    :param dict parser_result: The output from pydsdl's parser.
    :param Path templates_dir: The directory containing the jinja templates.

    """

    TEMPLATE_SUFFIX = ".j2"  #: The suffix expected for Jinja templates.

    # +-----------------------------------------------------------------------+
    # | JINJA : filters
    # +-----------------------------------------------------------------------+

    @staticmethod
    def _jinja2_filter_yamlfy(value: str) -> str:
        try:
            from yaml import dump
            return str(dump(value))
        except ImportError:
            return "(pyyaml not installed)"

    @staticmethod
    def _jinja2_filter_split(value: str, seperator: str) -> List[str]:
        return str.split(value, seperator)

    @classmethod
    def _jinja2_filter_pydsdl_type_to_template(cls, value: Any) -> str:
        return str(
            PurePath(type(value).__name__).with_suffix(cls.TEMPLATE_SUFFIX))

    @staticmethod
    def _jinja2_filter_typename(value: str) -> str:
        return type(value).__name__

    # +-----------------------------------------------------------------------+
    # | JINJA : tests
    # +-----------------------------------------------------------------------+

    @staticmethod
    def _jinja2_test_primative(value: DataType) -> bool:
        return isinstance(value, PrimitiveType)

    @staticmethod
    def _jinja2_test_constant(value: DataType) -> bool:
        return isinstance(value, Constant)

    # +-----------------------------------------------------------------------+

    def __init__(self,
                 output_basedir: Path,
                 parser_result: Dict[CompoundType, Path],
                 templates_dir: Path):

        super(Generator, self).__init__(output_basedir, parser_result)

        if templates_dir is None:
            raise ValueError("Templates directory argument was None")
        if not Path(templates_dir).exists:
            raise ValueError(
                "Templates directory {} did not exist?".format(templates_dir))

        self._templates_dir = Path(templates_dir)

        logger.info("Loading templates from {}".format(templates_dir))

        self._env = Environment(loader=FileSystemLoader(
            [str(templates_dir)], followlinks=True),
            extensions=[JinjaAssert])

        # Automatically find the locally defined filters and
        # tests and add them to the jinja environment.
        member_functions = inspect.getmembers(self, inspect.isroutine)
        for function_tuple in member_functions:
            function_name = function_tuple[0]
            if len(function_name) > 13 and function_name[0:13] == "_jinja2_test_":
                self._env.tests[function_name[13:]] = function_tuple[1]
            if len(function_name) > 15 and function_name[0:15] == "_jinja2_filter_":
                self._env.filters[function_name[15:]] = function_tuple[1]

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
        for (parsed_type, output_path) in self.parser_results:
            self._generate_type(parsed_type, output_path, is_dryrun)
        return 0

    def _generate_type(self, input_type: CompoundType, output_path: Path, is_dryrun: bool) -> None:
        template_name = self._jinja2_filter_pydsdl_type_to_template(input_type)
        self._env.globals["now_utc"] = datetime.utcnow()
        template = self._env.get_template(template_name)
        result = template.render(T=input_type)
        if not is_dryrun:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(str(output_path), "w") as output_file:
                output_file.write(result)
