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
import functools
import inspect
import io
import logging
import pathlib
import re
import typing

import pydsdl

import nunavut.generators
import nunavut.lang
import nunavut.postprocessors
from nunavut.jinja.jinja2 import (ChoiceLoader, Environment, FileSystemLoader,
                                  PackageLoader, StrictUndefined, Template,
                                  TemplateAssertionError, nodes,
                                  select_autoescape)
from nunavut.jinja.jinja2.ext import Extension
from nunavut.jinja.jinja2.parser import Parser
from nunavut.templates import LANGUAGE_FILTER_ATTRIBUTE_NAME

logger = logging.getLogger(__name__)

# +---------------------------------------------------------------------------+
# | JINJA : Extensions
# +---------------------------------------------------------------------------+


class JinjaAssert(Extension):
    """
    Jinja2 extension that allows ``{% assert T.attribute %}`` statements. Templates should
    uses these statements where False values would result in malformed source code ::

       {% assert False %}

    """

    tags = set(['assert'])

    def __init__(self, environment: Environment):
        super().__init__(environment)

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

    :param nunavut.Namespace namespace:    The top-level namespace to generates types
                                           at and from.
    :param nunavut.YesNoDefault generate_namespace_types:  Set to YES to emit files for namespaces.
                                           NO will suppress namespace file generation and DEFAULT will
                                           use the language's preference.
    :param templates_dir:                  Directories containing jinja templates. These will be available along
                                           with any built-in templates provided by the target language. The templates
                                           at these paths will take precedence masking any built-in templates
                                           where the names are the same. See :class:`jinja2.ChoiceLoader` for rules
                                           on the lookup hierarchy.
    :type templates_dir: typing.Optional[typing.Union[pathlib.Path,typing.List[pathlib.Path]]]
    :param bool followlinks:               If True then symbolic links will be followed when
                                           searching for templates.
    :param bool trim_blocks:               If this is set to True the first newline after a
                                           block is removed (block, not variable tag!).
    :param bool lstrip_blocks:             If this is set to True leading spaces and tabs
                                           are stripped from the start of a line to a block.
                                           Defaults to False.
    :param typing.Dict[str, typing.Callable] additional_filters: typing.Optional jinja filters to add to the
                                           global environment using the key as the filter name
                                           and the callable as the filter.
    :param typing.Dict[str, typing.Callable] additional_tests: typing.Optional jinja tests to add to the
                                           global environment using the key as the test name
                                           and the callable as the test.
    :param typing.Dict[str, typing.Any] additional_globals: typing.Optional objects to add to the template
                                            environment globals collection.
    :param post_processors: A list of :class:`nunavut.postprocessors.PostProcessor`
    :type post_processors: typing.Optional[typing.List[nunavut.postprocessors.PostProcessor]]
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

        def _find_template_by_name(name: str, templates: typing.Iterable[pathlib.Path]) \
                -> typing.Optional[pathlib.Path]:
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

            # include "{{ T.my_type | type_to_include_path }}"

        Result Example:

            # include "foo/bar/my_type.h"

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

    @staticmethod
    def filter_alignment_prefix(offset: pydsdl.BitLengthSet) -> str:
        """
        Provides a string prefix based on a given :class:`pydsdl.BitLengthSet`.

        .. invisible-code-block: python

            from nunavut.jinja import Generator
            import pydsdl

        .. code-block:: python

            # Given
            B = pydsdl.BitLengthSet(32)

            # and
            template = '{{ B | alignment_prefix }}'

            # then ('str' is stropped to 'str_' before the version is suffixed)
            rendered = 'aligned'

        .. invisible-code-block: python

            jinja_filter_tester(Generator.filter_alignment_prefix, template, rendered, 'py', B=B)


        .. code-block:: python

            # Given
            B = pydsdl.BitLengthSet(32)
            B.increment(1)

            # and
            template = '{{ B | alignment_prefix }}'

            # then ('str' is stropped to 'str_' before the version is suffixed)
            rendered = 'unaligned'

        .. invisible-code-block: python

            jinja_filter_tester(Generator.filter_alignment_prefix, template, rendered, 'py', B=B)


        :param pydsdl.BitLengthSet offset: A bit length set to test for alignment.
        :return: 'aligned' or 'unaligned' based on the state of the ``offset`` argument.
        """
        if isinstance(offset, pydsdl.BitLengthSet):
            return 'aligned' if offset.is_aligned_at_byte() else 'unaligned'
        else:  # pragma: no cover
            raise TypeError('Expected BitLengthSet, got {}'.format(type(offset).__name__))

    @staticmethod
    def filter_bit_length_set(values: typing.Optional[typing.Union[typing.Iterable[int], int]]) -> pydsdl.BitLengthSet:
        """
        Convert an integer or a list of integers into a :class:`pydsdl.BitLengthSet`.

        .. invisible-code-block: python

            from nunavut.jinja import Generator
            import pydsdl

            assert type(Generator.filter_bit_length_set(23)) == pydsdl.BitLengthSet

        """
        return pydsdl.BitLengthSet(values)

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
                const {{ attribute.data_type | c.type_from_primitive }} {{ attribute.name }} = {{ attribute.initialization_expression }};
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

    @staticmethod
    def is_None(value: typing.Any) -> bool:
        """
        Tests if a value is ``None``

        .. invisible-code-block: python

            from nunavut.jinja import Generator
            assert Generator.is_None(None) is True
            assert Generator.is_None(1) is False

        """
        return (value is None)

    @staticmethod
    def is_padding(value: pydsdl.Field) -> bool:
        """
        Tests if a value is a padding field.

        .. invisible-code-block: python

            from nunavut.jinja import Generator
            from unittest.mock import MagicMock
            import pydsdl

            assert Generator.is_padding(MagicMock(spec=pydsdl.PaddingField)) is True
            assert Generator.is_padding(MagicMock(spec=pydsdl.Field)) is False

        """
        return isinstance(value, pydsdl.PaddingField)

    @staticmethod
    def is_saturated(t: pydsdl.PrimitiveType) -> bool:
        """
        Tests if a type is a saturated type or not.

        .. invisible-code-block: python

            from nunavut.jinja import Generator
            from unittest.mock import MagicMock
            import pydsdl
            import pytest

            saturated_mock = MagicMock(spec=pydsdl.PrimitiveType)
            saturated_mock.cast_mode = pydsdl.PrimitiveType.CastMode.SATURATED
            assert Generator.is_saturated(saturated_mock) is True

            truncated_mock = MagicMock(spec=pydsdl.PrimitiveType)
            truncated_mock.cast_mode = pydsdl.PrimitiveType.CastMode.TRUNCATED
            assert Generator.is_saturated(truncated_mock) is False

            with pytest.raises(TypeError):
                 Generator.is_saturated(MagicMock(spec=pydsdl.SerializableType))

        """
        if isinstance(t, pydsdl.PrimitiveType):
            return {
                pydsdl.PrimitiveType.CastMode.SATURATED: True,
                pydsdl.PrimitiveType.CastMode.TRUNCATED: False,
            }[t.cast_mode]
        else:
            raise TypeError('Cast mode is not defined for {}'.format(type(t).__name__))

    # +-----------------------------------------------------------------------+

    def __init__(self,
                 namespace: nunavut.Namespace,
                 generate_namespace_types: nunavut.YesNoDefault = nunavut.YesNoDefault.DEFAULT,
                 templates_dir: typing.Optional[typing.Union[pathlib.Path, typing.List[pathlib.Path]]] = None,
                 followlinks: bool = False,
                 trim_blocks: bool = False,
                 lstrip_blocks: bool = False,
                 additional_filters: typing.Optional[typing.Dict[str, typing.Callable]] = None,
                 additional_tests: typing.Optional[typing.Dict[str, typing.Callable]] = None,
                 additional_globals: typing.Optional[typing.Dict[str, typing.Any]] = None,
                 post_processors: typing.Optional[typing.List['nunavut.postprocessors.PostProcessor']] = None):

        super().__init__(namespace,
                         generate_namespace_types)

        self._post_processors = post_processors

        if templates_dir is None:
            templates_dirs = []  # type: typing.List[pathlib.Path]
        else:
            if not isinstance(templates_dir, list):
                templates_dirs = [templates_dir]
            else:
                templates_dirs = templates_dir

            for templates_dir_item in templates_dirs:
                if templates_dir_item is None:
                    raise ValueError("Templates directory argument was None")
                if not pathlib.Path(templates_dir_item).exists:
                    raise ValueError(
                        "Templates directory {} did not exist?".format(templates_dir_item))

        self._templates_dirs = templates_dirs

        self._type_to_template_lookup_cache = dict()  # type: typing.Dict[pydsdl.Any, pathlib.Path]

        self._templates_list = None  # type: typing.Optional[typing.List[pathlib.Path]]

        logger.info("Loading templates from {}".format(templates_dirs))

        fs_loader = FileSystemLoader((str(d) for d in self._templates_dirs), followlinks=followlinks)

        target_language = self._namespace.get_language_context().get_target_language()

        if target_language is not None:
            template_loader = ChoiceLoader([
                fs_loader,
                PackageLoader(target_language.get_templates_package_name())
            ])  # type: 'nunavut.jinja.jinja2.loaders.BaseLoader'
        else:
            template_loader = fs_loader

        autoesc = select_autoescape(enabled_extensions=('htm', 'html', 'xml', 'json'),
                                    default_for_string=False,
                                    default=False)

        self._env = Environment(loader=template_loader,  # nosec
                                extensions=[nunavut.jinja.jinja2.ext.do,
                                            nunavut.jinja.jinja2.ext.loopcontrols,
                                            JinjaAssert],
                                autoescape=autoesc,
                                undefined=StrictUndefined,
                                keep_trailing_newline=True,
                                lstrip_blocks=lstrip_blocks,
                                trim_blocks=trim_blocks,
                                auto_reload=False,
                                cache_size=0)

        self._add_language_support()

        if additional_globals is not None:
            self._env.globals.update(additional_globals)

        self._add_nunavut_globals(target_language)
        self._add_instance_tests_from_root(pydsdl.SerializableType)
        self._add_filters_and_tests(additional_filters, additional_tests)

    def get_templates(self) -> typing.Iterable[pathlib.Path]:
        """
        Enumerate all templates found in the templates path.
        :data:`~TEMPLATE_SUFFIX` as the suffix for the filename.

        :returns: A list of paths to all templates found by this Generator object.
        """
        if self._templates_list is None:
            self._templates_list = []
            for template_dir in self._templates_dirs:
                for template in template_dir.glob("**/*{}".format(self.TEMPLATE_SUFFIX)):
                    self._templates_list.append(template)
        return self._templates_list

    def generate_all(self,
                     is_dryrun: bool = False,
                     allow_overwrite: bool = True) \
            -> typing.Iterable[pathlib.Path]:
        generated = []  # type: typing.List[pathlib.Path]
        if self.generate_namespace_types:
            for (parsed_type, output_path) in self.namespace.get_all_types():
                generated.append(
                    self._generate_type(parsed_type, output_path, is_dryrun, allow_overwrite, self._post_processors)
                )
        else:
            for (parsed_type, output_path) in self.namespace.get_all_datatypes():
                generated.append(
                    self._generate_type(parsed_type, output_path, is_dryrun, allow_overwrite, self._post_processors)
                )
        return generated

    @property
    def language_context(self) -> nunavut.lang.LanguageContext:
        return self._namespace.get_language_context()

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _add_nunavut_globals(self, target_language: typing.Optional[nunavut.lang.Language]) -> None:
        """
        Add globals namespaced as 'nunavut'.
        """
        import nunavut.version

        # Helper global so we don't have to futz around with the "omit_serialization_support"
        # logic in the templates. The omit_serialization_support property of the Language
        # object is read-only so this boolean will remain consistent for the Environment.
        if target_language is not None:
            omit_serialization_support = target_language.omit_serialization_support
            support_namespace = target_language.support_namespace
        else:
            # If there is no target language then we cannot generate serialization support.
            omit_serialization_support = True
            support_namespace = []

        self._env.globals['nunavut'] = {
            'version': nunavut.version.__version__,
            'support': {
                'omit': omit_serialization_support,
                'namespace': support_namespace
            }
        }

    def _add_instance_tests_from_root(self, root: typing.Type[object]) -> None:
        def _field_is_instance(field_or_datatype: typing.Any) -> bool:
            if isinstance(field_or_datatype, pydsdl.Field):
                return isinstance(field_or_datatype.data_type, root)
            else:
                return isinstance(field_or_datatype, root)

        self._env.tests[root.__name__] = _field_is_instance
        for derived in root.__subclasses__():
            self._add_instance_tests_from_root(derived)

    def _add_language_support(self) -> None:
        target_language = self.language_context.get_target_language()
        if target_language is not None:
            for key, value in target_language.get_filters().items():
                self._add_filter_to_environment(key, value)
            self._env.globals.update(target_language.get_globals())

        for supported_language in self.language_context.get_supported_languages().values():
            for key, value in supported_language.get_filters().items():
                self._add_filter_to_environment(key, value, supported_language.name)
            self._env.globals[supported_language.name] = supported_language

    def _add_filters_and_tests(self,
                               additional_filters: typing.Optional[typing.Dict[str, typing.Callable]],
                               additional_tests: typing.Optional[typing.Dict[str, typing.Callable]]) -> None:
        # Automatically find the locally defined filters and
        # tests and add them to the jinja environment.
        member_functions = inspect.getmembers(self, inspect.isroutine)
        for function_tuple in member_functions:
            function_name = function_tuple[0]
            function_ref = function_tuple[1]
            if len(function_name) > 3 and function_name[0:3] == "is_":
                self._env.tests[function_name[3:]] = function_ref
            if len(function_name) > 7 and function_name[0:7] == "filter_":
                self._add_filter_to_environment(function_name[7:], function_ref)

        if additional_filters is not None:
            for name, additional_filter in additional_filters.items():
                if name in self._env.filters:
                    raise RuntimeError('filter {} was already defined.'.format(name))
                self._add_filter_to_environment(name, additional_filter)

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
                       post_processors: typing.Optional[typing.List['nunavut.postprocessors.PostProcessor']]) \
            -> pathlib.Path:
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
        return output_path

    def _add_filter_to_environment(self, filter_name: str,
                                   filter: typing.Callable[..., str],
                                   filter_namespace: typing.Optional[str] = None) -> None:
        if hasattr(filter, LANGUAGE_FILTER_ATTRIBUTE_NAME):
            language_name_or_module_name = getattr(filter, LANGUAGE_FILTER_ATTRIBUTE_NAME)
            filter_language = self.language_context.get_language(language_name_or_module_name)
            resolved_filter = functools.partial(filter, filter_language)  # type: typing.Callable[..., str]
        else:
            resolved_filter = filter
        if filter_namespace is None:
            self._env.filters[filter_name] = resolved_filter
        else:
            self._env.filters['{}.{}'.format(filter_namespace, filter_name)] = resolved_filter

    @staticmethod
    def _filter_and_write_line(line_and_lineend: typing.Tuple[str, str],
                               output_file: typing.TextIO,
                               line_pps: typing.List['nunavut.postprocessors.LinePostProcessor']) -> None:
        for line_pp in line_pps:
            line_and_lineend = line_pp(line_and_lineend)
            if line_and_lineend is None:
                raise ValueError('line post processor must return a 2-tuple. To elide a line return a tuple of empty'
                                 'strings. None is not a valid value.')

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
                            post_processors: typing.Optional[typing.List['nunavut.postprocessors.PostProcessor']]) \
            -> None:
        """
        Logic that should run from _generate_type iff is_dryrun is False.
        """

        from ..lang import _UniqueNameGenerator

        # reset the name generator state for this type
        _UniqueNameGenerator.reset()

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
