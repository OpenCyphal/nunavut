#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    jinja-based :class:`~nunavut.generators.AbstractGenerator` implementation.
"""

import collections
import datetime
import inspect
import logging
import pathlib
import typing
import io
import re

import pydsdl

import nunavut.generators
from nunavut.jinja.lang import (get_supported_languages, add_language_support)

from nunavut.jinja.jinja2 import (Environment, FileSystemLoader,
                                  StrictUndefined, TemplateAssertionError,
                                  nodes, select_autoescape, Template)
from nunavut.jinja.jinja2.ext import Extension
from nunavut.jinja.jinja2.parser import Parser

logger = logging.getLogger(__name__)

# +---------------------------------------------------------------------------+
# | JINJA : Extensions
# +---------------------------------------------------------------------------+


class JinjaAssert(Extension):
    """
    Jinja2 extension that allows ``{% assert T.attribute %}`` statements. Templates should
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
                   caller: typing.Callable) -> typing.Any:
        if not expression:
            raise TemplateAssertionError(message, lineno, name, filename)
        return caller()


class Generator(nunavut.generators.AbstractGenerator):
    """ :class:`~nunavut.generators.AbstractGenerator` implementation that uses
    Jinja2 templates to generate source code.

    :param nunavut.Namespace namespace:  The top-level namespace to generates types
                                           at and from.
    :param bool generate_namespace_types:  typing.Set to true to emit files for namespaces.
                                           False will only generate files for datatypes.
    :param pathlib.Path templates_dir:     The directory containing the jinja templates.

    :param bool followlinks:               If True then symbolic links will be followed when
                                           searching for templates.
    :param typing.Dict[str, typing.Callable] additional_filters: typing.Optional jinja filters to add to the
                                           global environment using the key as the filter name
                                           and the callable as the filter.
    :param typing.Dict[str, typing.Callable] additional_tests: typing.Optional jinja tests to add to the
                                           global environment using the key as the test name
                                           and the callable as the test.
    :raises RuntimeError: If any additional filter or test attempts to replace a built-in
                          or otherwise already defined filter or test.
    """

    TEMPLATE_SUFFIX = ".j2"  #: The suffix expected for Jinja templates.

    # +-----------------------------------------------------------------------+
    # | JINJA : filters
    # +-----------------------------------------------------------------------+

    @staticmethod
    def filter_yamlfy(value: typing.Any) -> str:
        """
        Filter to, optionally, emit a dump of the dsdl input as a yaml document.
        Available as ``yamlfy`` in all template environments.

        Example::

            /*
            {{ T | yamlfy }}
            */

        Result Example (truncated for brevity)::

            /*
            !!python/object:pydsdl.StructureType
            _attributes:
            - !!python/object:pydsdl.Field
            _serializable: !!python/object:pydsdl.UnsignedIntegerType
                _bit_length: 16
                _cast_mode: &id001 !!python/object/apply:pydsdl.CastMode
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

    def filter_type_to_template(self, value: typing.Any) -> str:
        """
        Template for type resolution as a filter. Available as ``type_to_template``
        in all template environments.

        Example::

            {%- for attribute in T.attributes %}
                {%* include attribute.data_type | type_to_template %}
                {%- if not loop.last %},{% endif %}
            {%- endfor %}

        :param value: The input value to change into a template include path.

        :returns: A path to a template named for the type with :any:`Generator.TEMPLATE_SUFFIX`
        """
        search_queue = collections.deque()  # type: typing.Deque[typing.Any]
        discovered = set()  # type: typing.Set[typing.Any]
        search_queue.appendleft(type(value))
        template_path = pathlib.Path(type(value).__name__).with_suffix(self.TEMPLATE_SUFFIX)

        def _find_template_by_name(name: str, templates: typing.List[pathlib.Path]) -> typing.Optional[pathlib.Path]:
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

    def filter_type_to_include_path(self, value: typing.Any, resolve: bool = False) -> str:
        """
        Emits and include path to the output target for a given type.

        Example::

            #include "{{ T.my_type | type_to_include_path }}"

        Result Example:

            #include "foo/bar/my_type.h"

        :param typing.Any value: The type to emit an include for.
        :param bool resolve: If True the path returned will be absolute else the path will
                             be relative to the folder of the root namepace.
        :returns: A string path to output file for the type.
        """

        include_path = self.namespace.find_output_path_for_type(value)
        if resolve:
            return str(include_path.resolve())
        else:
            return str(include_path.relative_to(self.namespace.output_folder.parent))

    @staticmethod
    def filter_typename(value: typing.Any) -> str:
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
    def is_primitive(value: pydsdl.Any) -> bool:
        """
        Tests if a given dsdl instance is a ``pydsdl.PrimitiveType``.
        Available in all template environments as ``is primitive``.

        Example::

            {% if field.data_type is primitive %}
                {{ field.data_type | c.type_from_primitive }} {{ field.name }};
            {% endif -%}

        :param value: The instance to test.

        :returns: True if value is an instance of ``pydsdl.PrimitiveType``.
        """
        return isinstance(value, pydsdl.PrimitiveType)

    @staticmethod
    def is_constant(value: pydsdl.Any) -> bool:
        """
        Tests if a given dsdl instance is a ``pydsdl.Constant``.
        Available in all template environments as ``is constant``.

        Example::

            {%- if attribute is constant %}
                const {{ attribute.data_type | c.type_from_primitive(use_standard_types=True) }} {{ attribute.name }} = {{ attribute.initialization_expression }};
            {% endif %}

        :param value: The instance to test.

        :returns: True if value is an instance of ``pydsdl.Constant``.
        """  # noqa: E501
        return isinstance(value, pydsdl.Constant)

    @staticmethod
    def is_serializable(value: pydsdl.Any) -> bool:
        """
        Tests if a given dsdl instance is a ``pydsdl.SerializableType``.
        Available in all template environments as ``is serializable``.

        Example::

            {%- if attribute is serializable %}
                // Yup, this is serializable
            {% endif %}

        :param value: The instance to test.

        :returns: True if value is an instance of ``pydsdl.SerializableType``.
        """  # noqa: E501
        return isinstance(value, pydsdl.SerializableType)

    # +-----------------------------------------------------------------------+

    def __init__(self,
                 namespace: nunavut.Namespace,
                 generate_namespace_types: bool,
                 templates_dir: pathlib.Path,
                 followlinks: bool = False,
                 additional_filters: typing.Optional[typing.Dict[str, typing.Callable]] = None,
                 additional_tests: typing.Optional[typing.Dict[str, typing.Callable]] = None
                 ):

        super(Generator, self).__init__(namespace, generate_namespace_types)

        if templates_dir is None:
            raise ValueError("Templates directory argument was None")
        if not pathlib.Path(templates_dir).exists:
            raise ValueError(
                "Templates directory {} did not exist?".format(templates_dir))

        self._templates_dir = templates_dir

        self._type_to_template_lookup_cache = dict()  # type: typing.Dict[pydsdl.Any, pathlib.Path]

        self._templates_list = None  # type: typing.Optional[typing.List[pathlib.Path]]

        logger.info("Loading templates from {}".format(templates_dir))

        fs_loader = FileSystemLoader([str(templates_dir)], followlinks=followlinks)

        autoesc = select_autoescape(enabled_extensions=('htm', 'html', 'xml', 'json'),
                                    default_for_string=False,
                                    default=False)

        self._env = Environment(loader=fs_loader,
                                extensions=[nunavut.jinja.jinja2.ext.do,
                                            nunavut.jinja.jinja2.ext.loopcontrols,
                                            JinjaAssert],
                                autoescape=autoesc,
                                undefined=StrictUndefined,
                                keep_trailing_newline=True,
                                auto_reload=False)

        self._add_filters_and_tests(additional_filters, additional_tests)

        # Add in additional filters and tests for built-in languages this
        # module supports.
        for language_name in get_supported_languages():
            add_language_support(language_name, self._env)

    def get_templates(self) -> typing.List[pathlib.Path]:
        """
        Enumerate all templates found in the templates path.
        :data:`~TEMPLATE_SUFFIX` as the suffix for the filename.

        :returns: A list of paths to all templates found by this Generator object.
        """
        if self._templates_list is None:
            self._templates_list = []
            for template in self._templates_dir.glob("**/*{}".format(self.TEMPLATE_SUFFIX)):
                self._templates_list.append(template)
        return self._templates_list

    def generate_all(self,
                     is_dryrun: bool = False,
                     allow_overwrite: bool = True,
                     post_processors: typing.Optional[typing.List['nunavut.postprocessors.PostProcessor']] = None) -> int:
        if self.generate_namespace_types:
            for (parsed_type, output_path) in self.namespace.get_all_types():
                self._generate_type(parsed_type, output_path, is_dryrun, allow_overwrite, post_processors)
        else:
            for (parsed_type, output_path) in self.namespace.get_all_datatypes():
                self._generate_type(parsed_type, output_path, is_dryrun, allow_overwrite, post_processors)
        return 0

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+

    def _add_filters_and_tests(self,
                               additional_filters: typing.Optional[typing.Dict[str, typing.Callable]],
                               additional_tests: typing.Optional[typing.Dict[str, typing.Callable]]) -> None:
        # Automatically find the locally defined filters and
        # tests and add them to the jinja environment.
        member_functions = inspect.getmembers(self, inspect.isroutine)
        for function_tuple in member_functions:
            function_name = function_tuple[0]
            if len(function_name) > 3 and function_name[0:3] == "is_":
                self._env.tests[function_name[3:]] = function_tuple[1]
            if len(function_name) > 7 and function_name[0:7] == "filter_":
                self._env.filters[function_name[7:]] = function_tuple[1]

        if additional_filters is not None:
            for name, additional_filter in additional_filters.items():
                if name in self._env.filters:
                    raise RuntimeError('filter {} was already defined.'.format(name))
                self._env.filters[name] = additional_filter

        if additional_tests is not None:
            for name, additional_test in additional_tests.items():
                if name in self._env.tests:
                    raise RuntimeError('test {} was already defined.'.format(name))
                self._env.tests[name] = additional_test

    def _generate_type(self,
                       input_type: pydsdl.CompositeType,
                       output_path: pathlib.Path,
                       is_dryrun: bool,
                       allow_overwrite: bool,
                       post_processors: typing.Optional[typing.List['nunavut.postprocessors.PostProcessor']]) -> None:
        template_name = self.filter_type_to_template(input_type)
        self._env.globals["now_utc"] = datetime.datetime.utcnow()
        template = self._env.get_template(template_name)
        template_gen = template.generate(T=input_type)
        if not is_dryrun:
            self._generate_type_real(output_path,
                                     template,
                                     template_gen,
                                     allow_overwrite,
                                     post_processors
                                     )

    @staticmethod
    def _filter_and_write_line(line_and_lineend: typing.Tuple[str, str],
                               output_file: typing.TextIO,
                               line_pps: typing.List['nunavut.postprocessors.LinePostProcessor']) -> None:
        for line_pp in line_pps:
            line_and_lineend = line_pp(line_and_lineend)
            if line_and_lineend is None:
                raise ValueError('line post processor must return a 2-tuple. To elide a line return a tuple of empty strings.'
                                 'None is not a valid value.')

        output_file.write(line_and_lineend[0])
        output_file.write(line_and_lineend[1])

    @classmethod
    def _generate_with_line_buffer(cls,
                                   output_file: typing.TextIO,
                                   template_gen: typing.Generator[str, None, None],
                                   line_pps: typing.List['nunavut.postprocessors.LinePostProcessor']) -> None:
        newline_pattern = re.compile(r'\n|\r\n', flags=re.MULTILINE)
        line_buffer = io.StringIO()
        for part in template_gen:
            search_pos = 0  # type: int
            match_obj = newline_pattern.search(part, search_pos)
            while True:
                if search_pos < 0 or search_pos >= len(part):
                    break
                if match_obj is None:
                    line_buffer.write(part[search_pos:])
                    break

                # We have a newline
                line_buffer.write(part[search_pos:match_obj.start()])
                newline_chars = part[match_obj.start():match_obj.end()]
                line = line_buffer.getvalue()  # type: str
                line_buffer = io.StringIO()
                cls._filter_and_write_line((line, newline_chars), output_file, line_pps)
                search_pos = match_obj.end()
                match_obj = newline_pattern.search(part, search_pos)
        remainder = line_buffer.getvalue()
        if len(remainder) > 0:
            cls._filter_and_write_line((remainder, ""), output_file, line_pps)

    def _generate_type_real(self,
                            output_path: pathlib.Path,
                            template: Template,
                            template_gen: typing.Generator[str, None, None],
                            allow_overwrite: bool,
                            post_processors: typing.Optional[typing.List['nunavut.postprocessors.PostProcessor']]) -> None:
        """
        Logic that should run from _generate_type iff is_dryrun is False.
        """

        # Predetermine the post processor types.
        line_pps = []  # type: typing.List['nunavut.postprocessors.LinePostProcessor']
        file_pps = []  # type: typing.List['nunavut.postprocessors.FilePostProcessor']
        if post_processors is not None:
            for pp in post_processors:
                if isinstance(pp, nunavut.postprocessors.LinePostProcessor):
                    line_pps.append(pp)
                elif isinstance(pp, nunavut.postprocessors.FilePostProcessor):
                    file_pps.append(pp)
                else:
                    raise ValueError('PostProcessor type {} is unknown.'.format(type(pp)))

        if output_path.exists():
            if allow_overwrite:
                output_path.chmod(output_path.stat().st_mode | 0o220)
            else:
                raise PermissionError('{} exists and allow_overwrite is False.'.format(output_path))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(output_path), "w") as output_file:
            if len(line_pps) > 0:
                # The logic gets much more complex when doing line post-processing.
                self._generate_with_line_buffer(output_file, template_gen, line_pps)
            else:
                for part in template_gen:
                    output_file.write(part)
        for file_pp in file_pps:
            output_path = file_pp(output_path)
