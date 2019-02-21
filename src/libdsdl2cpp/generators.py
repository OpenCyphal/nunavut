#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

import logging
from abc import ABCMeta, abstractmethod
from datetime import datetime
from pathlib import Path, PurePath
from typing import Dict, ItemsView, KeysView, List
from typing import Generator as GeneratorType

from jinja2 import (Environment, FileSystemLoader, Template,
                    TemplateRuntimeError, TemplateAssertionError, environmentfilter, nodes)
from jinja2.runtime import Undefined
from jinja2.ext import Extension

from pydsdl.data_type import (CompoundType, ServiceType, StructureType,
                              UnionType)

logger = logging.getLogger(__name__)

# +---------------------------------------------------------------------------+


class Generator(metaclass=ABCMeta):

    def __init__(self, output_basedir: Path, parser_result: Dict[CompoundType, Path]):
        self._output_basedir = output_basedir
        self._parser_result = parser_result

    @property
    def input_types(self) -> KeysView[CompoundType]:
        return self._parser_result.keys()

    @property
    def parser_results(self) -> ItemsView[CompoundType, Path]:
        return self._parser_result.items()

    @abstractmethod
    def generate_all(self, is_dryrun: bool = False) -> int:
        raise NotImplementedError()

# +---------------------------------------------------------------------------+
# | JINJA : filters
# +---------------------------------------------------------------------------+
def _jinja2_filter_yamlfy(value):
    try:
        from yaml import dump
        return dump(value)
    except ModuleNotFoundError:
        return "(pyyaml not installed)"

@environmentfilter
def _jinja2_filter_required_value(env: Environment, value):
    if type(value) is Undefined:
        raise TemplateRuntimeError("Missing required value.")
    return value

def _jinja2_filter_macrofy(value: str) -> str:
    return value.replace(' ', '_').replace('.', '_').upper()

# +---------------------------------------------------------------------------+
# | JINJA : Extensions
# +---------------------------------------------------------------------------+
class JinjaAssert(Extension):
    """
    Jinja2 extension that allows {% assert T.field %} statements. Templates should
    uses these statements where missing or False values would result in malformed
    C++.
    """

    tags = set(['assert'])

    def __init__(self, environment):
        super(JinjaAssert, self).__init__(environment)
    
    def parse(self, parser) -> nodes.Node :
        """
        See http://jinja.pocoo.org/docs/2.10/extensions/ for help writing
        extensions.
        """

        # This will be the macro name "assert"
        token : nodes.Token = next(parser.stream)

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
    
    def _do_assert(self, expression, lineno, name, filename, message, caller):
        if not expression:
            raise TemplateAssertionError(message, lineno, name, filename)
        return caller()

# +---------------------------------------------------------------------------+
# | JINJA : Generator
# +---------------------------------------------------------------------------+
class Jinja2Generator(Generator):

    TEMPLATE_SUFFIX = ".j2"

    def __init__(self, output_basedir: Path, parser_result: Dict[CompoundType, Path], templates_dir: Path):
        super(Jinja2Generator, self).__init__(
            output_basedir, parser_result)
        if templates_dir is None:
            raise ValueError("Tempaltes directory argument was None")
        if not Path(templates_dir).exists:
            raise ValueError(
                "Tempaltes directory {} did not exist?".format(templates_dir))
        self._templates_dir : Path = Path(templates_dir)
        logger.info("Loading templates from {}".format(templates_dir))
        self._env = Environment(loader=FileSystemLoader(
            [str(templates_dir)], followlinks=True),
            extensions=[JinjaAssert])
        self._env.filters["yamlfy"] = _jinja2_filter_yamlfy
        self._env.filters["required"] = _jinja2_filter_required_value
        self._env.filters["macrofy"] = _jinja2_filter_macrofy

    def get_templates(self) -> GeneratorType[Path, None, None] :
        return self._templates_dir.glob("**/*{}".format(self.TEMPLATE_SUFFIX))

    def generate_all(self, is_dryrun: bool = False) -> int:
        for (parsed_type, output_path) in self.parser_results:
            self._generate_type(parsed_type, output_path, is_dryrun)
        return 0

    def _generate_type(self, input_type: CompoundType, output_path: Path, is_dryrun: bool):
        template_name = str(
            PurePath(type(input_type).__name__).with_suffix(self.TEMPLATE_SUFFIX))
        self._env.globals["now_utc"] = datetime.utcnow()
        template: Template = self._env.get_template(template_name)
        result: str = template.render(T=input_type)
        if not is_dryrun:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as output_file:
                output_file.write(result)
