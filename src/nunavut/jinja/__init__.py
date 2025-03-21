#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
jinja-based :class:`~nunavut.generators.AbstractGenerator` implementation.
"""

import abc
import datetime
import io
import logging
import re
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterable, List, Mapping, Optional, TextIO, Tuple, Type, Union

import pydsdl

import nunavut.lang

from .._generators import AbstractGenerator
from .._postprocessors import FilePostProcessor, LinePostProcessor, PostProcessor
from .._utilities import TEMPLATE_SUFFIX, ResourceSearchPolicy, ResourceType, YesNoDefault
from .environment import CodeGenEnvironment, CodeGenEnvironmentBuilder
from .loaders import DEFAULT_TEMPLATE_PATH, DSDLSupportTemplateLoader, DSDLTemplateLoader

logger = logging.getLogger(__name__)

# +---------------------------------------------------------------------------+
# | JINJA : CodeGenerator
# +---------------------------------------------------------------------------+


class CodeGenerator(AbstractGenerator):
    """
    Abstract base class for all Generators that build source code using Jinja templates.

    :param int resource_types:             A bitfield of :class:`nunavut._utilities.ResourceType` for filtering the
                                           types of resources this generator will emit.
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
    :type templates_dir: Optional[Union[Path,List[Path]]]
    :param Optional[Type[DSDLTemplateLoader]] template_loader:
        If None uses an internal default implementation of :class:`DSDLTemplateLoader` otherwise instantiates the given
        class with the arguments specified by the :class:`DSDLTemplateLoader` constructor.
    :param bool followlinks:               If True then symbolic links will be followed when
                                           searching for templates.
    :param bool trim_blocks:               If this is set to True the first newline after a
                                           block is removed (block, not variable tag!).
    :param bool lstrip_blocks:             If this is set to True leading spaces and tabs
                                           are stripped from the start of a line to a block.
                                           Defaults to False.
    :param Dict[str, Callable] additional_filters: Optional jinja filters to add to the
                                           global environment using the key as the filter name
                                           and the callable as the filter.
    :param Dict[str, Callable] additional_tests: Optional jinja tests to add to the
                                           global environment using the key as the test name
                                           and the callable as the test.
    :param Dict[str, Any] additional_globals: Optional objects to add to the template
                                            environment globals collection.
    :param post_processors: A list of :class:`nunavut.postprocessors.PostProcessor`
    :type post_processors: Optional[List[nunavut.postprocessors.PostProcessor]]
    :param builtin_template_path: If provided overrides the folder name under which built-in templates are loaded from
                                            within a target language's package (i.e. ignored if no target language is
                                            specified). For example, if the target language is ``c`` and this parameter
                                            was set to ``foo`` then built-in templates would be loaded from
                                            ``nunavut.lang.c.foo``.
    :type builtin_template_path: str
    :param search_policy: The policy to use when searching for templates.
    :type search_policy: ResourceSearchPolicy
    :param embed_auditing_info: If True then the generator will embed auditing information in the generated code.
    :type embed_auditing_info: bool
    :raises RuntimeError: If any additional filter or test attempts to replace a built-in
                          or otherwise already defined filter or test.
    """

    @staticmethod
    def __augment_post_processors_with_ln_limit_empty_lines(
        post_processors: Optional[List[PostProcessor]], limit_empty_lines: int
    ) -> List[PostProcessor]:
        """
        Subroutine of _handle_post_processors method.
        """
        from nunavut._postprocessors import LimitEmptyLines  # pylint: disable=import-outside-toplevel

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
        post_processors: Optional[List[PostProcessor]],
    ) -> List[PostProcessor]:
        """
        Subroutine of _handle_post_processors method.
        """
        from nunavut._postprocessors import TrimTrailingWhitespace  # pylint: disable=import-outside-toplevel

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
        target_language: "nunavut.lang.Language",
        post_processors: Optional[List["PostProcessor"]],
    ) -> Optional[List["PostProcessor"]]:
        """
        Used by constructor to process an optional list of post-processors and to augment or create this list
        if needed to support language options.
        """
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
        resource_types: int = ResourceType.ANY.value,
        generate_namespace_types: YesNoDefault = YesNoDefault.DEFAULT,
        templates_dir: Optional[Union[Path, List[Path]]] = None,
        template_loader: Optional[Type[DSDLTemplateLoader]] = None,
        followlinks: bool = False,
        trim_blocks: bool = False,
        lstrip_blocks: bool = False,
        additional_filters: Optional[Dict[str, Callable]] = None,
        additional_tests: Optional[Dict[str, Callable]] = None,
        additional_globals: Optional[Dict[str, Any]] = None,
        post_processors: Optional[List["PostProcessor"]] = None,
        builtin_template_path: str = DEFAULT_TEMPLATE_PATH,
        search_policy: ResourceSearchPolicy = ResourceSearchPolicy.FIND_ALL,
        embed_auditing_info: bool = False,
        **kwargs: Any,
    ):
        super().__init__(namespace, resource_types, generate_namespace_types, **kwargs)

        if templates_dir is not None and not isinstance(templates_dir, list):
            templates_dir = [templates_dir]

        language_context = self._namespace.get_language_context()
        target_language = language_context.get_target_language()

        if template_loader is None:
            template_loader = DSDLTemplateLoader

        self._dsdl_template_loader = template_loader(
            namespace=namespace,
            resource_types=resource_types,
            templates_dirs=templates_dir,
            followlinks=followlinks,
            builtin_template_path=builtin_template_path,
            search_policy=search_policy,
            **kwargs,
        )

        self._post_processors = self._handle_post_processors(target_language, post_processors)

        env_builder = (
            CodeGenEnvironmentBuilder(self._dsdl_template_loader)
            .set_trim_blocks(trim_blocks)
            .set_lstrip_blocks(lstrip_blocks)
        )
        if additional_filters is not None:
            env_builder.add_filters(**additional_filters)
        if additional_tests is not None:
            env_builder.add_tests(**additional_tests)
        if additional_globals is not None:
            env_builder.add_globals(**additional_globals)
        env_builder.set_embed_auditing_info(embed_auditing_info)

        self._env = env_builder.create(language_context)

    @property
    def dsdl_loader(self) -> DSDLTemplateLoader:
        """
        The template loader used by this generator.
        """
        return self._dsdl_template_loader

    @property
    def language_context(self) -> nunavut.lang.LanguageContext:
        """
        The language context used by this generator.
        """
        return self._namespace.get_language_context()

    @property
    def environment(self) -> CodeGenEnvironment:
        """
        The generator environment.
        """
        return self._env

    # +-----------------------------------------------------------------------+
    # | PROTECTED
    # +-----------------------------------------------------------------------+
    def _handle_overwrite(self, output_path: Path, allow_overwrite: bool) -> None:
        if output_path.exists():
            if allow_overwrite:
                output_path.chmod(output_path.stat().st_mode | 0o220)
            else:
                raise PermissionError("{output_path} exists and allow_overwrite is False.")

    # +-----------------------------------------------------------------------+
    # | AbstractGenerator
    # +-----------------------------------------------------------------------+

    def get_templates(self) -> Iterable[Path]:
        """
        Enumerate all templates found in the templates path.
        :data:`~TEMPLATE_SUFFIX` as the suffix for the filename.

        :return: A list of paths to all templates found by this Generator object.
        """
        return self._dsdl_template_loader.get_templates()

    @abc.abstractmethod
    def generate_all(
        self,
        is_dryrun: bool = False,
        allow_overwrite: bool = True,
    ) -> Iterable[Path]:
        raise NotImplementedError()

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+

    @staticmethod
    def _filter_and_write_line(
        line_and_lineend: Tuple[str, str],
        output_file: TextIO,
        line_pps: List["LinePostProcessor"],
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
        output_file: TextIO,
        template_gen: Generator[str, None, None],
        line_pps: List["LinePostProcessor"],
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
        output_path: Path,
        template_gen: Generator[str, None, None],
        allow_overwrite: bool,
    ) -> None:
        """
        Logic that should run from _generate_type iff is_dryrun is False.
        """

        try:
            self._env.now_utc = datetime.datetime.now(datetime.UTC)  # type: ignore
        except AttributeError:
            self._env.now_utc = datetime.datetime.utcnow()

        from ..lang._common import UniqueNameGenerator  # pylint: disable=import-outside-toplevel

        # reset the name generator state for this type
        UniqueNameGenerator.reset()

        # Predetermine the post processor types.
        line_pps = []  # type: List['LinePostProcessor']
        file_pps = []  # type: List['FilePostProcessor']
        if self._post_processors is not None:
            for pp in self._post_processors:
                if isinstance(pp, LinePostProcessor):
                    line_pps.append(pp)
                elif isinstance(pp, FilePostProcessor):
                    file_pps.append(pp)
                else:
                    raise ValueError(f"PostProcessor type {type(pp)} is unknown.")
        logger.debug("Using post-processors: %r %r", line_pps, file_pps)

        self._handle_overwrite(output_path, allow_overwrite)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(output_path), "w", encoding="utf-8") as output_file:
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
        from yaml import Dumper as YamlDumper  # pylint: disable=import-outside-toplevel
        from yaml import dump as yaml_dump  # pylint: disable=import-outside-toplevel

        return str(yaml_dump(value, Dumper=YamlDumper))

    def filter_type_to_template(self, value: Any) -> str:
        """
        Template for type resolution as a filter. Available as ``type_to_template``
        in all template environments.

        Example::

            {%- for attribute in T.attributes %}
                {%* include attribute.data_type | type_to_template %}
                {%- if not loop.last %},{% endif %}
            {%- endfor %}

        :param value: The input value to change into a template include path.

        :return: A path to a template named for the type with :data:`TEMPLATE_SUFFIX`
        """
        result = self.dsdl_loader.type_to_template(type(value))
        if result is None:
            raise RuntimeError(f"No template found for type {value}")
        return result.name

    def filter_type_to_include_path(self, value: Any, resolve: bool = False) -> str:
        """
        Emits an include path to the output target for a given type.

        Example::

            # include "{{ T.my_type | type_to_include_path }}"

        Result Example:

            # include "foo/bar/my_type.h"

        :param Any value: The type to emit an include for.
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

            # outputs
            rendered = 'aligned'

        .. invisible-code-block: python

            jinja_filter_tester(DSDLCodeGenerator.filter_alignment_prefix, template, rendered, 'py', B=B)


        .. code-block:: python

            # Given
            B = pydsdl.BitLengthSet(32)
            B += 1

            # and
            template = '{{ B | alignment_prefix }}'

            # outputs
            rendered = 'unaligned'

        .. invisible-code-block: python

            jinja_filter_tester(DSDLCodeGenerator.filter_alignment_prefix, template, rendered, 'py', B=B)


        :param pydsdl.BitLengthSet offset: A bit length set to test for alignment.
        :return: 'aligned' or 'unaligned' based on the state of the ``offset`` argument.
        """
        if isinstance(offset, pydsdl.BitLengthSet):
            return "aligned" if offset.is_aligned_at_byte() else "unaligned"
        else:  # pragma: no cover
            raise TypeError(f"Expected BitLengthSet, got {type(offset).__name__}")

    @staticmethod
    def filter_bit_length_set(values: Optional[Union[Iterable[int], int]]) -> pydsdl.BitLengthSet:
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

        .. code-block:: python

            # Given
            text = '''123

            456
            \t
            \v\f
            789'''

            # and
            template = '{{ text | remove_blank_lines }}'

            # then the black lines will be removed leaving...
            rendered = '''123
            456
            789'''

        .. invisible-code-block: python

            jinja_filter_tester(DSDLCodeGenerator.filter_remove_blank_lines, template, rendered, 'c', text=text)

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

    @staticmethod
    def filter_text_table(data: Dict, start_each_line: str, column_sep: str = " : ", line_end: str = "\n") -> str:
        """
        Create a text table from a dictionary of data.

        .. invisible-code-block: python

            from nunavut.jinja import DSDLCodeGenerator
            import pydsdl

        .. code-block:: python

            # Given
            table = {
                "banana": "yellow",
                "apple": "red",
                "grape": "purple"
            }

            # and
            template = '''
            {{ table | text_table("//  ", " | ", "\\n") }}'''

            # then
            rendered = '''
            //  banana | yellow
            //  apple  | red
            //  grape  | purple'''

        .. invisible-code-block: python

            jinja_filter_tester(DSDLCodeGenerator.filter_text_table, template, rendered, 'c', table=table)

        """
        # Find the longest key to set the width of the first column
        key_width = max(len(key) for key in data.keys())

        output = []
        for key, value in data.items():
            output.append(f"{start_each_line}{key:<{key_width}}{column_sep}{value}".rstrip())
        return line_end.join(output)

    # +-----------------------------------------------------------------------+
    # | JINJA : tests
    # +-----------------------------------------------------------------------+

    @staticmethod
    def is_None(value: Any) -> bool:  # pylint: disable=invalid-name
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
            raise TypeError(f"Cast mode is not defined for {type(t).__name__}")

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

    def __init__(self, namespace: nunavut.Namespace, resource_types: int = ResourceType.ANY.value, **kwargs: Any):
        super().__init__(namespace, resource_types=resource_types, **kwargs)
        for test_name, test in self._create_all_dsdl_tests().items():
            self._env.add_test(test_name, test)
        self._env.add_conventional_methods_to_environment(self)

    # +-----------------------------------------------------------------------+
    # | AbstractGenerator
    # +-----------------------------------------------------------------------+
    def get_templates(self) -> Iterable[Path]:
        if (self.resource_types & ResourceType.ONLY.value) == ResourceType.ONLY.value:
            # This generator doesn't generate resources and the "only resources" flag is set.
            return []
        return super().get_templates()

    def generate_all(
        self,
        is_dryrun: bool = False,
        allow_overwrite: bool = True,
    ) -> Iterable[Path]:
        generated = []  # type: List[Path]
        if (self.resource_types & ResourceType.ONLY.value) == ResourceType.ONLY.value:
            # This generator doesn't generate resources and the "only resources" flag is set.
            # We'll set the dryrun flag to True to avoid generating anything but we'll still return the list of
            # types that would have been generated.
            is_dryrun = True
        provider = self.namespace.get_all_types if self.generate_namespace_types else self.namespace.get_all_datatypes
        for parsed_type, output_path in provider():
            logger.info("Generating: %s", parsed_type)
            generated.append(self._generate_type(parsed_type, output_path, is_dryrun, allow_overwrite))

        generated.extend(self._generate_index_files(is_dryrun, allow_overwrite))
        return generated

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    @classmethod
    def _create_instance_tests_for_type(cls, root: pydsdl.Any) -> Dict[str, Callable]:
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
    def _create_all_dsdl_tests(cls) -> Mapping[str, Callable]:
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
        self, input_type: pydsdl.CompositeType, output_path: Path, is_dryrun: bool, allow_overwrite: bool
    ) -> Path:
        template_name = self.filter_type_to_template(input_type)
        template = self._env.get_template(template_name)
        template_gen = template.generate(T=input_type)
        if not is_dryrun:
            self._generate_code(output_path, template_gen, allow_overwrite)
        return output_path

    def _generate_index_files(
        self,
        is_dryrun: bool,
        allow_overwrite: bool,
    ) -> List[Path]:
        """
        Renders index files which are each given access to all namespaces as `N`.
        """
        output_paths = []
        index = self.namespace.get_index_namespace()
        index_file_path = index.output_folder
        target_extension = self.language_context.get_target_language().get_config_value(
            nunavut.lang.Language.WKCV_DEFINITION_FILE_EXTENSION
        )
        for index_file in self.index_files:
            template_name = self.dsdl_loader.index_file_to_template(index_file)
            if template_name is None:
                raise RuntimeError(f"No template found for index file {index_file}")
            template = self._env.get_template(template_name.name)
            template_gen = template.generate(N=index)
            index_file_output = index_file_path / index_file
            if len(index_file.suffix) == 0:
                index_file_output = index_file_output.with_suffix(target_extension)
            output_paths.append(index_file_output)
            if not is_dryrun:
                self._generate_code(index_file_output, template_gen, allow_overwrite)
        return output_paths


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

    def __init__(
        self,
        namespace: nunavut.Namespace,
        resource_types: int,
        generate_namespace_types: YesNoDefault = YesNoDefault.DEFAULT,
        templates_dir: Optional[Union[Path, List[Path]]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            namespace,
            resource_types,
            generate_namespace_types=generate_namespace_types,
            templates_dir=templates_dir,
            builtin_template_path="support",
            template_loader=DSDLSupportTemplateLoader,
            **kwargs,
        )

        target_language = self.language_context.get_target_language()

        #  Create the sub-folder to copy-to based on the support namespace.
        self._sub_folders = Path("")

        for namespace_part in target_language.support_namespace:
            self._sub_folders = self._sub_folders / Path(namespace_part)

    # +-----------------------------------------------------------------------+
    # | AbstractGenerator
    # +-----------------------------------------------------------------------+
    def get_templates(self) -> Iterable[Path]:
        if self.resource_types == 0:
            # This generator only generates resources and the "no resources" flag is set.
            return []
        return super().get_templates()

    def generate_all(
        self,
        is_dryrun: bool = False,
        allow_overwrite: bool = True,
    ) -> Iterable[Path]:
        generated = []  # type: List[Path]
        if self.resource_types == 0:
            # This generator only generates resources and the "no resources" flag is set.
            return generated

        target_language = self.language_context.get_target_language()
        target_path = Path(self.namespace.get_index_namespace().base_output_path) / self._sub_folders

        line_pps: List[LinePostProcessor] = []
        file_pps: List[FilePostProcessor] = []
        if self._post_processors is not None:
            for pp in self._post_processors:
                if isinstance(pp, LinePostProcessor):
                    line_pps.append(pp)
                elif isinstance(pp, FilePostProcessor):
                    file_pps.append(pp)
                else:
                    raise ValueError(f"PostProcessor type {type(pp)} is unknown.")

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

    # +-----------------------------------------------------------------------+
    # | Private
    # +-----------------------------------------------------------------------+

    def _generate_header(self, template_path: Path, output_path: Path, is_dryrun: bool, allow_overwrite: bool) -> Path:
        template = self._env.get_template(template_path.name)
        template_gen = template.generate()
        if not is_dryrun:
            self._generate_code(output_path, template_gen, allow_overwrite)
        return output_path

    def _copy_header(
        self,
        resource: Path,
        target: Path,
        is_dryrun: bool,
        allow_overwrite: bool,
        line_pps: List["LinePostProcessor"],
        file_pps: List["FilePostProcessor"],
    ) -> Path:
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
        resource: Path,
        target: Path,
        line_pps: List["LinePostProcessor"],
    ) -> None:
        with open(str(target), "w", encoding="utf-8") as target_file:
            with open(str(resource), "r", encoding="utf-8") as resource_file:
                for resource_line in resource_file:
                    if len(resource_line) > 1 and resource_line[-2] == "\r":
                        resource_line_tuple = (resource_line[0:-2], "\r\n")
                    else:
                        resource_line_tuple = (resource_line[0:-1], "\n")
                    for line_pp in line_pps:
                        resource_line_tuple = line_pp(resource_line_tuple)
                    target_file.write(resource_line_tuple[0])
                    target_file.write(resource_line_tuple[1])
