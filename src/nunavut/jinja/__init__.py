#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2021  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    jinja-based :class:`~nunavut.generators.AbstractGenerator` implementation.
"""

import datetime
import io
import logging
import pathlib
import re
import shutil
import typing

import nunavut.generators
import nunavut.lang
import nunavut.postprocessors
import pydsdl
from nunavut._utilities import ResourceType, YesNoDefault
from yaml import Dumper as YamlDumper
from yaml import dump as yaml_dump

from .environment import CodeGenEnvironment
from .jinja2 import Template
from .loaders import DEFAULT_TEMPLATE_PATH, TEMPLATE_SUFFIX, DSDLTemplateLoader

logger = logging.getLogger(__name__)

# +---------------------------------------------------------------------------+
# | JINJA : CodeGenerator
# +---------------------------------------------------------------------------+


class CodeGenerator(nunavut.generators.AbstractGenerator):
    """
    Abstract base class for all Generators that build source code using Jinja templates.

    :param nunavut.Namespace namespace:    The top-level namespace to generates code
                                           at and from.
    :param YesNoDefault generate_namespace_types:  Set to YES to emit files for namespaces.
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
    :param builtin_template_path: If provided overrides the folder name under which built-in templates are loaded from
                                            within a target language's package (i.e. ignored if no target language is
                                            specified). For example, if the target language is ``c`` and this parameter
                                            was set to ``foo`` then built-in templates would be loaded from
                                            ``nunavut.lang.c.foo``.
    :raises RuntimeError: If any additional filter or test attempts to replace a built-in
                          or otherwise already defined filter or test.
    """

    @staticmethod
    def __augment_post_processors_with_ln_limit_empty_lines(
        post_processors: typing.Optional[typing.List["nunavut.postprocessors.PostProcessor"]], limit_empty_lines: int
    ) -> typing.List["nunavut.postprocessors.PostProcessor"]:
        """
        Subroutine of _handle_post_processors method.
        """
        from nunavut.postprocessors import LimitEmptyLines

        if post_processors is None:
            post_processors = [LimitEmptyLines(limit_empty_lines)]
        else:
            found_pp = False
            for pp in post_processors:
                if isinstance(pp, LimitEmptyLines):
                    found_pp = True
                    break
            if not found_pp:
                post_processors.append(LimitEmptyLines(limit_empty_lines))
        return post_processors

    @staticmethod
    def __augment_post_processors_with_ln_trim_trailing_whitespace(
        post_processors: typing.Optional[typing.List["nunavut.postprocessors.PostProcessor"]],
    ) -> typing.List["nunavut.postprocessors.PostProcessor"]:
        """
        Subroutine of _handle_post_processors method.
        """
        from nunavut.postprocessors import TrimTrailingWhitespace

        if post_processors is None:
            post_processors = [TrimTrailingWhitespace()]
        else:
            found_pp = False
            for pp in post_processors:
                if isinstance(pp, TrimTrailingWhitespace):
                    found_pp = True
                    break
            if not found_pp:
                post_processors.append(TrimTrailingWhitespace())
        return post_processors

    @classmethod
    def _handle_post_processors(
        cls,
        post_processors: typing.Optional[typing.List["nunavut.postprocessors.PostProcessor"]],
        target_language: typing.Optional["nunavut.lang.Language"],
    ) -> typing.Optional[typing.List["nunavut.postprocessors.PostProcessor"]]:
        """
        Used by constructor to process an optional list of post-processors and to augment or create this list
        if needed to support language options.
        """
        if target_language is not None:

            try:
                limit_empty_lines = target_language.get_config_value("limit_empty_lines")
                post_processors = cls.__augment_post_processors_with_ln_limit_empty_lines(
                    post_processors, int(limit_empty_lines)
                )
            except KeyError:
                pass

            if target_language.get_config_value_as_bool("trim_trailing_whitespace"):
                post_processors = cls.__augment_post_processors_with_ln_trim_trailing_whitespace(post_processors)

        return post_processors

    def __init__(
        self,
        namespace: nunavut.Namespace,
        generate_namespace_types: YesNoDefault = YesNoDefault.DEFAULT,
        templates_dir: typing.Optional[typing.Union[pathlib.Path, typing.List[pathlib.Path]]] = None,
        followlinks: bool = False,
        trim_blocks: bool = False,
        lstrip_blocks: bool = False,
        additional_filters: typing.Optional[typing.Dict[str, typing.Callable]] = None,
        additional_tests: typing.Optional[typing.Dict[str, typing.Callable]] = None,
        additional_globals: typing.Optional[typing.Dict[str, typing.Any]] = None,
        post_processors: typing.Optional[typing.List["nunavut.postprocessors.PostProcessor"]] = None,
        builtin_template_path: str = DEFAULT_TEMPLATE_PATH,
    ):

        super().__init__(namespace, generate_namespace_types)

        if templates_dir is not None and not isinstance(templates_dir, list):
            templates_dir = [templates_dir]

        language_context = self._namespace.get_language_context()
        target_language = language_context.get_target_language()

        self._dsdl_template_loader = DSDLTemplateLoader(
            templates_dirs=templates_dir,
            package_name_for_templates=(
                None if target_language is None else target_language.get_templates_package_name()
            ),
            followlinks=followlinks,
            builtin_template_path=builtin_template_path,
        )

        self._post_processors = self._handle_post_processors(post_processors, target_language)

        self._env = CodeGenEnvironment(
            lctx=language_context,
            loader=self._dsdl_template_loader,
            lstrip_blocks=lstrip_blocks,
            trim_blocks=trim_blocks,
            additional_filters=additional_filters,
            additional_tests=additional_tests,
            additional_globals=additional_globals,
        )

    @property
    def dsdl_loader(self) -> DSDLTemplateLoader:
        return self._dsdl_template_loader

    @property
    def language_context(self) -> nunavut.lang.LanguageContext:
        return self._namespace.get_language_context()

    # +-----------------------------------------------------------------------+
    # | PROTECTED
    # +-----------------------------------------------------------------------+
    def _handle_overwrite(self, output_path: pathlib.Path, allow_overwrite: bool) -> None:
        if output_path.exists():
            if allow_overwrite:
                output_path.chmod(output_path.stat().st_mode | 0o220)
            else:
                raise PermissionError("{} exists and allow_overwrite is False.".format(output_path))

    # +-----------------------------------------------------------------------+
    # | AbstractGenerator
    # +-----------------------------------------------------------------------+

    def get_templates(self) -> typing.Iterable[pathlib.Path]:
        """
        Enumerate all templates found in the templates path.
        :data:`~TEMPLATE_SUFFIX` as the suffix for the filename.

        :return: A list of paths to all templates found by this Generator object.
        """
        return self._dsdl_template_loader.get_templates()

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+

    @staticmethod
    def _filter_and_write_line(
        line_and_lineend: typing.Tuple[str, str],
        output_file: typing.TextIO,
        line_pps: typing.List["nunavut.postprocessors.LinePostProcessor"],
    ) -> None:
        for line_pp in line_pps:
            line_and_lineend = line_pp(line_and_lineend)
            if line_and_lineend is None:
                raise ValueError(
                    "line post processor must return a 2-tuple. To elide a line return a tuple of empty"
                    "strings. None is not a valid value."
                )

        output_file.write(line_and_lineend[0])
        output_file.write(line_and_lineend[1])

    @classmethod
    def _generate_with_line_buffer(
        cls,
        output_file: typing.TextIO,
        template_gen: typing.Generator[str, None, None],
        line_pps: typing.List["nunavut.postprocessors.LinePostProcessor"],
    ) -> None:
        newline_pattern = re.compile(r"\n|\r\n", flags=re.MULTILINE)
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
                line_buffer.write(part[search_pos : match_obj.start()])
                newline_chars = part[match_obj.start() : match_obj.end()]
                line = line_buffer.getvalue()  # type: str
                line_buffer = io.StringIO()
                cls._filter_and_write_line((line, newline_chars), output_file, line_pps)
                search_pos = match_obj.end()
                match_obj = newline_pattern.search(part, search_pos)
        remainder = line_buffer.getvalue()
        if len(remainder) > 0:
            cls._filter_and_write_line((remainder, ""), output_file, line_pps)

    def _generate_code(
        self,
        output_path: pathlib.Path,
        template: Template,
        template_gen: typing.Generator[str, None, None],
        allow_overwrite: bool,
    ) -> None:
        """
        Logic that should run from _generate_type iff is_dryrun is False.
        """

        self._env.now_utc = datetime.datetime.utcnow()

        from ..lang._common import UniqueNameGenerator

        # reset the name generator state for this type
        UniqueNameGenerator.reset()

        # Predetermine the post processor types.
        line_pps = []  # type: typing.List['nunavut.postprocessors.LinePostProcessor']
        file_pps = []  # type: typing.List['nunavut.postprocessors.FilePostProcessor']
        if self._post_processors is not None:
            for pp in self._post_processors:
                if isinstance(pp, nunavut.postprocessors.LinePostProcessor):
                    line_pps.append(pp)
                elif isinstance(pp, nunavut.postprocessors.FilePostProcessor):
                    file_pps.append(pp)
                else:
                    raise ValueError("PostProcessor type {} is unknown.".format(type(pp)))
        logger.debug("Using post-processors: %r %r", line_pps, file_pps)

        self._handle_overwrite(output_path, allow_overwrite)
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


# +---------------------------------------------------------------------------+
# | JINJA : DSDLCodeGenerator
# +---------------------------------------------------------------------------+


class DSDLCodeGenerator(CodeGenerator):
    """
    :class:`~CodeGenerator` implementation that generates code for a given set
    of DSDL types.
    """

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

        :return: If a yaml parser is available, a pretty dump of the given value as yaml.
                  If a yaml parser is not available then an empty string is returned.
        """
        return str(yaml_dump(value, Dumper=YamlDumper))

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

        :return: A path to a template named for the type with :any:`TEMPLATE_SUFFIX`
        """
        result = self.dsdl_loader.type_to_template(type(value))
        if result is None:
            raise RuntimeError("No template found for type {}".format(type(value)))
        return result.name

    def filter_type_to_include_path(self, value: typing.Any, resolve: bool = False) -> str:
        """
        Emits an include path to the output target for a given type.

        Example::

            # include "{{ T.my_type | type_to_include_path }}"

        Result Example:

            # include "foo/bar/my_type.h"

        :param typing.Any value: The type to emit an include for.
        :param bool resolve: If True the path returned will be absolute else the path will
                             be relative to the folder of the root namespace.
        :return: A string path to output file for the type.
        """

        include_path = self.namespace.find_output_path_for_type(value)
        if resolve:
            return include_path.resolve().as_posix()
        else:
            return include_path.relative_to(self.namespace.output_folder.parent).as_posix()

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

        :return: The ``__name__`` of the python type.
        """
        return type(value).__name__

    @staticmethod
    def filter_alignment_prefix(offset: pydsdl.BitLengthSet) -> str:
        """
        Provides a string prefix based on a given :class:`pydsdl.BitLengthSet`.

        .. invisible-code-block: python

            from nunavut.jinja import DSDLCodeGenerator
            import pydsdl

        .. code-block:: python

            # Given
            B = pydsdl.BitLengthSet(32)

            # and
            template = '{{ B | alignment_prefix }}'

            # then ('str' is stropped to 'str_' before the version is suffixed)
            rendered = 'aligned'

        .. invisible-code-block: python

            jinja_filter_tester(DSDLCodeGenerator.filter_alignment_prefix, template, rendered, 'py', B=B)


        .. code-block:: python

            # Given
            B = pydsdl.BitLengthSet(32)
            B += 1

            # and
            template = '{{ B | alignment_prefix }}'

            # then ('str' is stropped to 'str_' before the version is suffixed)
            rendered = 'unaligned'

        .. invisible-code-block: python

            jinja_filter_tester(DSDLCodeGenerator.filter_alignment_prefix, template, rendered, 'py', B=B)


        :param pydsdl.BitLengthSet offset: A bit length set to test for alignment.
        :return: 'aligned' or 'unaligned' based on the state of the ``offset`` argument.
        """
        if isinstance(offset, pydsdl.BitLengthSet):
            return "aligned" if offset.is_aligned_at_byte() else "unaligned"
        else:  # pragma: no cover
            raise TypeError("Expected BitLengthSet, got {}".format(type(offset).__name__))

    @staticmethod
    def filter_bit_length_set(values: typing.Optional[typing.Union[typing.Iterable[int], int]]) -> pydsdl.BitLengthSet:
        """
        Convert an integer or a list of integers into a :class:`pydsdl.BitLengthSet`.

        .. invisible-code-block: python

            from nunavut.jinja import DSDLCodeGenerator
            import pydsdl

            assert type(DSDLCodeGenerator.filter_bit_length_set(23)) == pydsdl.BitLengthSet

        """
        return pydsdl.BitLengthSet(values)

    @staticmethod
    def filter_remove_blank_lines(text: str) -> str:
        """
        Remove blank lines from the supplied string.
        Lines that contain only whitespace characters are also considered blank.

        .. invisible-code-block: python

            from nunavut.jinja import DSDLCodeGenerator
            import pydsdl

            assert DSDLCodeGenerator.filter_remove_blank_lines('123\n  \n\n456\n\t\n\v\f\n789') == '123\n456\n789'

        """
        return re.sub(r"\n([ \t\f\v]*\n)+", r"\n", text)

    @staticmethod
    def filter_bits2bytes_ceil(n_bits: int) -> int:
        """
        Implements ``int(ceil(x/8)) | x >= 0``.

        .. invisible-code-block: python

            from nunavut.jinja import DSDLCodeGenerator
            assert DSDLCodeGenerator.filter_bits2bytes_ceil(50) == 7
            assert DSDLCodeGenerator.filter_bits2bytes_ceil(8) == 1
            assert DSDLCodeGenerator.filter_bits2bytes_ceil(7) == 1
            assert DSDLCodeGenerator.filter_bits2bytes_ceil(1) == 1
            assert DSDLCodeGenerator.filter_bits2bytes_ceil(0) == 0

        """
        if n_bits < 0:
            raise ValueError("The number of bits cannot be negative")
        return (int(n_bits) + 7) // 8

    # +-----------------------------------------------------------------------+
    # | JINJA : tests
    # +-----------------------------------------------------------------------+

    @staticmethod
    def is_None(value: typing.Any) -> bool:
        """
        Tests if a value is ``None``

        .. invisible-code-block: python

            from nunavut.jinja import DSDLCodeGenerator
            assert DSDLCodeGenerator.is_None(None) is True
            assert DSDLCodeGenerator.is_None(1) is False

        """
        return value is None

    @staticmethod
    def is_saturated(t: pydsdl.PrimitiveType) -> bool:
        """
        Tests if a type is a saturated type or not.

        .. invisible-code-block: python

            from nunavut.jinja import DSDLCodeGenerator
            from unittest.mock import MagicMock
            import pydsdl
            import pytest

            saturated_mock = MagicMock(spec=pydsdl.PrimitiveType)
            saturated_mock.cast_mode = pydsdl.PrimitiveType.CastMode.SATURATED
            assert DSDLCodeGenerator.is_saturated(saturated_mock) is True

            truncated_mock = MagicMock(spec=pydsdl.PrimitiveType)
            truncated_mock.cast_mode = pydsdl.PrimitiveType.CastMode.TRUNCATED
            assert DSDLCodeGenerator.is_saturated(truncated_mock) is False

            with pytest.raises(TypeError):
                 DSDLCodeGenerator.is_saturated(MagicMock(spec=pydsdl.SerializableType))

        """
        if isinstance(t, pydsdl.PrimitiveType):
            return {
                pydsdl.PrimitiveType.CastMode.SATURATED: True,
                pydsdl.PrimitiveType.CastMode.TRUNCATED: False,
            }[t.cast_mode]
        else:
            raise TypeError("Cast mode is not defined for {}".format(type(t).__name__))

    @staticmethod
    def is_service_request(instance: pydsdl.Any) -> bool:
        """
        Tests if a type is request type of a service type.

        .. invisible-code-block: python

            from nunavut.jinja import DSDLCodeGenerator
            from unittest.mock import MagicMock
            import pydsdl

            service_request_mock = MagicMock(spec=pydsdl.SerializableType)
            service_request_mock.has_parent_service = True
            service_request_mock.full_name = 'foo.bar.Service_1_0.Request'
            assert DSDLCodeGenerator.is_service_request(service_request_mock) is True

            service_request_mock.has_parent_service = False
            assert DSDLCodeGenerator.is_service_request(service_request_mock) is False

            service_request_mock.has_parent_service = True
            service_request_mock.full_name = 'foo.bar.Service_1_0.Response'
            assert DSDLCodeGenerator.is_service_request(service_request_mock) is False

        """
        return instance.has_parent_service and instance.full_name.split(".")[-1] == "Request"  # type: ignore

    @staticmethod
    def is_service_response(instance: pydsdl.Any) -> bool:
        """
        Tests if a type is response type of a service type.

        .. invisible-code-block: python

            from nunavut.jinja import DSDLCodeGenerator
            from unittest.mock import MagicMock
            import pydsdl

            service_request_mock = MagicMock(spec=pydsdl.SerializableType)
            service_request_mock.has_parent_service = True
            service_request_mock.full_name = 'foo.bar.Service_1_0.Response'
            assert DSDLCodeGenerator.is_service_response(service_request_mock) is True

            service_request_mock.has_parent_service = False
            assert DSDLCodeGenerator.is_service_response(service_request_mock) is False

            service_request_mock.has_parent_service = True
            service_request_mock.full_name = 'foo.bar.Service_1_0.Request'
            assert DSDLCodeGenerator.is_service_response(service_request_mock) is False

        """
        return instance.has_parent_service and instance.full_name.split(".")[-1] == "Response"  # type: ignore

    @staticmethod
    def is_deprecated(instance: pydsdl.Any) -> bool:
        """
        Tests if a type is marked as deprecated

        .. invisible-code-block: python

            from nunavut.jinja import DSDLCodeGenerator
            from unittest.mock import MagicMock
            import pydsdl

            composite_type_mock = MagicMock(spec=pydsdl.CompositeType)
            composite_type_mock.deprecated = True
            assert DSDLCodeGenerator.is_deprecated(composite_type_mock) is True

            array_type_mock = MagicMock(spec=pydsdl.ArrayType)
            array_type_mock.element_type = composite_type_mock
            assert DSDLCodeGenerator.is_deprecated(array_type_mock) is True

            other_type_mock = MagicMock(spec=pydsdl.SerializableType)
            assert DSDLCodeGenerator.is_deprecated(other_type_mock) is False

        """
        if isinstance(instance, pydsdl.CompositeType):
            return instance.deprecated  # type: ignore
        elif isinstance(instance, pydsdl.ArrayType) and isinstance(instance.element_type, pydsdl.CompositeType):
            return instance.element_type.deprecated  # type: ignore
        else:
            return False

    # +-----------------------------------------------------------------------+

    def __init__(self, namespace: nunavut.Namespace, **kwargs: typing.Any):

        super().__init__(namespace, **kwargs)
        for test_name, test in self._create_all_dsdl_tests().items():
            self._env.add_test(test_name, test)
        self._env.add_conventional_methods_to_environment(self)

    # +-----------------------------------------------------------------------+
    # | AbstractGenerator
    # +-----------------------------------------------------------------------+

    def generate_all(self, is_dryrun: bool = False, allow_overwrite: bool = True) -> typing.Iterable[pathlib.Path]:
        generated = []  # type: typing.List[pathlib.Path]
        provider = self.namespace.get_all_types if self.generate_namespace_types else self.namespace.get_all_datatypes
        for (parsed_type, output_path) in provider():
            logger.info("Generating: %s", parsed_type)
            generated.append(self._generate_type(parsed_type, output_path, is_dryrun, allow_overwrite))
        return generated

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    @classmethod
    def _create_instance_tests_for_type(cls, root: pydsdl.Any) -> typing.Dict[str, typing.Callable]:
        tests = dict()

        def _field_is_instance(field_or_datatype: pydsdl.Any) -> bool:
            if isinstance(field_or_datatype, pydsdl.Attribute):
                return isinstance(field_or_datatype.data_type, root)
            else:
                return isinstance(field_or_datatype, root)

        tests[root.__name__] = _field_is_instance
        root_name_lower = root.__name__.lower()
        if len(root_name_lower) > 4 and root_name_lower.endswith("type"):
            tests[root_name_lower[:-4]] = _field_is_instance
        elif len(root_name_lower) > 5 and root_name_lower.endswith("field"):
            tests[root_name_lower[:-5]] = _field_is_instance
        else:
            tests[root_name_lower] = _field_is_instance

        for derived in root.__subclasses__():
            tests.update(cls._create_instance_tests_for_type(derived))
        return tests

    @classmethod
    def _create_all_dsdl_tests(cls) -> typing.Mapping[str, typing.Callable]:
        """
        Create a collection of jinja tests for all base dsdl types.

        .. invisible-code-block: python

            import pydsdl
            from unittest.mock import MagicMock
            from nunavut.jinja import DSDLCodeGenerator

            test_set = DSDLCodeGenerator._create_all_dsdl_tests()

            def _do_pydsdl_instance_test_test(pydsdl_obj, test_name):

                if not test_set[test_name](pydsdl_obj):
                    raise AssertionError(test_name)

            def _do_pydsdl_instance_test_tests(pydsdl_type):
                mock_instance = MagicMock(spec=pydsdl_type)
                _do_pydsdl_instance_test_test(mock_instance, pydsdl_type.__name__)
                if pydsdl_type.__name__.endswith('Type'):
                    _do_pydsdl_instance_test_test(mock_instance, pydsdl_type.__name__[:-4].lower())
                if pydsdl_type.__name__.endswith('Field'):
                    _do_pydsdl_instance_test_test(mock_instance, pydsdl_type.__name__[:-5].lower())
                mock_attribute = MagicMock(spec=pydsdl.Attribute)
                mock_attribute.data_type = mock_instance
                _do_pydsdl_instance_test_test(mock_attribute, pydsdl_type.__name__)

            _do_pydsdl_instance_test_tests(pydsdl.SerializableType)
            _do_pydsdl_instance_test_tests(pydsdl.PrimitiveType)
            _do_pydsdl_instance_test_tests(pydsdl.IntegerType)
            _do_pydsdl_instance_test_tests(pydsdl.ServiceType)

        """
        all_tests = dict()
        all_tests.update(cls._create_instance_tests_for_type(pydsdl.SerializableType))
        all_tests.update(cls._create_instance_tests_for_type(pydsdl.Attribute))
        return all_tests

    def _generate_type(
        self, input_type: pydsdl.CompositeType, output_path: pathlib.Path, is_dryrun: bool, allow_overwrite: bool
    ) -> pathlib.Path:
        template_name = self.filter_type_to_template(input_type)
        template = self._env.get_template(template_name)
        template_gen = template.generate(T=input_type)
        if not is_dryrun:
            self._generate_code(output_path, template, template_gen, allow_overwrite)
        return output_path


# +---------------------------------------------------------------------------+
# | JINJA : SupportGenerator
# +---------------------------------------------------------------------------+


class SupportGenerator(CodeGenerator):
    """
    Generates output files by copying them from within the Nunavut package itself
    for non templates but uses jinja to generate headers from templates with the
    language environment provided but no ``T`` (DSDL type) global set.
    This generator always copies files from those returned by the ``file_iterator``
    to locations under :func:`nunavut.Namespace.get_support_output_folder()`
    """

    def __init__(self, namespace: nunavut.Namespace, **kwargs: typing.Any):

        super().__init__(namespace, builtin_template_path="support", **kwargs)

        target_language = self.language_context.get_target_language()

        self._sub_folders = None  # type: typing.Optional[pathlib.Path]
        self._serialization_support_enabled = False
        if target_language is not None:
            self._serialization_support_enabled = not target_language.omit_serialization_support

            #  Create the sub-folder to copy-to based on the support namespace.
            self._sub_folders = pathlib.Path("")

            for namespace_part in target_language.support_namespace:
                self._sub_folders = self._sub_folders / pathlib.Path(namespace_part)

    # +-----------------------------------------------------------------------+
    # | AbstractGenerator
    # +-----------------------------------------------------------------------+
    def get_templates(self) -> typing.Iterable[pathlib.Path]:
        files = []
        if self._serialization_support_enabled:
            for resource in self._get_templates_by_support_type(ResourceType.SERIALIZATION_SUPPORT):
                files.append(resource)
        for resource in self._get_templates_by_support_type(ResourceType.TYPE_SUPPORT):
            files.append(resource)
        return files

    def generate_all(self, is_dryrun: bool = False, allow_overwrite: bool = True) -> typing.Iterable[pathlib.Path]:
        target_language = self.language_context.get_target_language()
        if self._sub_folders is None or target_language is None:
            logger.info("No target language, therefore, no support headers")
            return []
        else:
            return self._generate_all(target_language, self._sub_folders, is_dryrun, allow_overwrite)

    # +-----------------------------------------------------------------------+
    # | Private
    # +-----------------------------------------------------------------------+
    def _get_templates_by_support_type(self, resource_type: ResourceType) -> typing.Iterable[pathlib.Path]:
        files = []
        target_language = self.language_context.get_target_language()

        if target_language is not None:
            for resource in target_language.get_support_files(resource_type):
                files.append(resource)
        return files

    def _generate_all(
        self, target_language: nunavut.lang.Language, sub_folders: pathlib.Path, is_dryrun: bool, allow_overwrite: bool
    ) -> typing.Iterable[pathlib.Path]:
        target_path = pathlib.Path(self.namespace.get_support_output_folder()) / sub_folders

        line_pps = []  # type: typing.List['nunavut.postprocessors.LinePostProcessor']
        file_pps = []  # type: typing.List['nunavut.postprocessors.FilePostProcessor']
        if self._post_processors is not None:
            for pp in self._post_processors:
                if isinstance(pp, nunavut.postprocessors.LinePostProcessor):
                    line_pps.append(pp)
                elif isinstance(pp, nunavut.postprocessors.FilePostProcessor):
                    file_pps.append(pp)
                else:
                    raise ValueError("PostProcessor type {} is unknown.".format(type(pp)))

        generated = []  # type: typing.List[pathlib.Path]
        for resource in self.get_templates():
            target = (target_path / resource.name).with_suffix(target_language.extension)
            logger.info("Generating support file: %s", target)
            if resource.suffix == TEMPLATE_SUFFIX:
                self._generate_header(resource, target, is_dryrun, allow_overwrite)
                generated.append(target)
            else:
                self._copy_header(resource, target, is_dryrun, allow_overwrite, line_pps, file_pps)
                generated.append(target)
        return generated

    def _generate_header(
        self, template_path: pathlib.Path, output_path: pathlib.Path, is_dryrun: bool, allow_overwrite: bool
    ) -> pathlib.Path:
        template = self._env.get_template(template_path.name)
        template_gen = template.generate()
        if not is_dryrun:
            self._generate_code(output_path, template, template_gen, allow_overwrite)
        return output_path

    def _copy_header(
        self,
        resource: pathlib.Path,
        target: pathlib.Path,
        is_dryrun: bool,
        allow_overwrite: bool,
        line_pps: typing.List["nunavut.postprocessors.LinePostProcessor"],
        file_pps: typing.List["nunavut.postprocessors.FilePostProcessor"],
    ) -> pathlib.Path:

        if not is_dryrun:
            self._handle_overwrite(target, allow_overwrite)
            target.parent.mkdir(parents=True, exist_ok=True)
            if len(line_pps) == 0:
                shutil.copy(str(resource), str(target))
            else:
                self._copy_header_using_line_pps(resource, target, line_pps)
            for file_pp in file_pps:
                target = file_pp(target)
        return target

    def _copy_header_using_line_pps(
        self,
        resource: pathlib.Path,
        target: pathlib.Path,
        line_pps: typing.List["nunavut.postprocessors.LinePostProcessor"],
    ) -> None:
        with open(str(target), "w") as target_file:
            with open(str(resource), "r") as resource_file:
                for resource_line in resource_file:
                    if len(resource_line) > 1 and resource_line[-2] == "\r":
                        resource_line_tuple = (resource_line[0:-2], "\r\n")
                    else:
                        resource_line_tuple = (resource_line[0:-1], "\n")
                    for line_pp in line_pps:
                        resource_line_tuple = line_pp(resource_line_tuple)
                    target_file.write(resource_line_tuple[0])
                    target_file.write(resource_line_tuple[1])
