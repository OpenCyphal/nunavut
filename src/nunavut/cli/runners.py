#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2021  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
"""
    Objects that utilize command-line inputs to run a program using Nunavut.
"""
import argparse
import pathlib
import sys
import typing

from pydsdl import read_namespace as read_dsdl_namespace

from nunavut._generators import create_default_generators
from nunavut._namespace import build_namespace_tree
from nunavut._postprocessors import (
    ExternalProgramEditInPlace,
    FilePostProcessor,
    LimitEmptyLines,
    PostProcessor,
    SetFileMode,
    TrimTrailingWhitespace,
)
from nunavut._utilities import YesNoDefault
from nunavut.lang import Language, LanguageContext, LanguageContextBuilder


class ArgparseRunner:
    """
    Runner that uses Python argparse arguments to define a run.

    :param argparse.Namespace args: The commandline arguments.
    :param typing.Optional[typing.Union[str, typing.List[str]]] extra_includes: A list of paths to additional DSDL
        root folders.
    """

    def __init__(self, args: argparse.Namespace, extra_includes: typing.Optional[typing.Union[str, typing.List[str]]]):
        self._args = args

        if extra_includes is None:
            extra_includes = []
        elif not isinstance(extra_includes, list):
            extra_includes = [extra_includes]

        self._extra_includes = extra_includes

        #
        # nunavut : parse inputs
        #
        self._language_context = self._create_language_context()

        if self._args.generate_support != "only" and not self._args.list_configuration:
            type_map = read_dsdl_namespace(
                self._args.root_namespace,
                self._extra_includes,
                allow_unregulated_fixed_port_id=self._args.allow_unregulated_fixed_port_id,
            )
        else:
            type_map = []

        self._root_namespace = build_namespace_tree(
            type_map, self._args.root_namespace, self._args.outdir, self._language_context
        )

        #
        # nunavut : create generators
        #

        generator_args = {
            "generate_namespace_types": (
                YesNoDefault.YES if self._args.generate_namespace_types else YesNoDefault.DEFAULT
            ),
            "templates_dir": (pathlib.Path(self._args.templates) if self._args.templates is not None else None),
            "trim_blocks": self._args.trim_blocks,
            "lstrip_blocks": self._args.lstrip_blocks,
            "post_processors": self._build_post_processor_list_from_args(),
        }

        self._generator, self._support_generator = create_default_generators(self._root_namespace, **generator_args)

    def run(self) -> None:
        """
        Perform actions defined by the arguments this object was created with. This may generate outputs where
        the arguments have requested this action.

        .. warning::
            :meth:`setup` must be called before calling this method.

        """

        if self._args.list_outputs:
            self._list_outputs_only()

        elif self._args.list_inputs:
            self._list_inputs_only()

        elif self._args.list_configuration:
            self._list_configuration_only()

        else:
            self._generate()

    # +---------------------------------------------------------------------------------------------------------------+
    # | PRIVATE
    # +---------------------------------------------------------------------------------------------------------------+

    def _should_generate_support(self) -> bool:
        if self._args.generate_support == "as-needed":
            return self._args.omit_serialization_support is None or not self._args.omit_serialization_support
        else:
            return bool(self._args.generate_support == "always" or self._args.generate_support == "only")

    def _build_ext_program_postprocessor(self, program: str) -> FilePostProcessor:
        subprocess_args = [program]
        if hasattr(self._args, "pp_run_program_arg") and self._args.pp_run_program_arg is not None:
            for program_arg in self._args.pp_run_program_arg:
                subprocess_args.append(program_arg)
        return ExternalProgramEditInPlace(subprocess_args)

    def _build_post_processor_list_from_args(self) -> typing.List[PostProcessor]:
        """
        Return a list of post processors setup based on the provided command-line arguments. This
        list may be empty but the function will not return None.
        """
        post_processors: typing.List[PostProcessor] = []
        if self._args.pp_trim_trailing_whitespace:
            post_processors.append(TrimTrailingWhitespace())
        if hasattr(self._args, "pp_max_emptylines") and self._args.pp_max_emptylines is not None:
            post_processors.append(LimitEmptyLines(self._args.pp_max_emptylines))
        if hasattr(self._args, "pp_run_program") and self._args.pp_run_program is not None:
            post_processors.append(self._build_ext_program_postprocessor(self._args.pp_run_program))

        post_processors.append(SetFileMode(self._args.file_mode))

        return post_processors

    def _create_language_context(self) -> LanguageContext:
        language_options = dict()
        if self._args.target_endianness is not None:
            language_options["target_endianness"] = self._args.target_endianness
        language_options["omit_float_serialization_support"] = self._args.omit_float_serialization_support
        language_options["enable_serialization_asserts"] = self._args.enable_serialization_asserts
        language_options["enable_override_variable_array_capacity"] = self._args.enable_override_variable_array_capacity
        if self._args.language_standard is not None:
            language_options["std"] = self._args.language_standard

        if self._args.configuration is None:
            additional_config_files = []
        elif isinstance(self._args.configuration, pathlib.Path):
            additional_config_files = [self._args.configuration]
        else:
            additional_config_files = self._args.configuration

        target_language_name = self._args.target_language

        return (
            LanguageContextBuilder(include_experimental_languages=self._args.experimental_languages)
            .set_target_language(target_language_name)
            .set_additional_config_files(additional_config_files)
            .set_target_language_extension(self._args.output_extension)
            .set_target_language_configuration_override(
                Language.WKCV_NAMESPACE_FILE_STEM, self._args.namespace_output_stem
            )
            .set_target_language_configuration_override(Language.WKCV_LANGUAGE_OPTIONS, language_options)
            .create()
        )

    # +---------------------------------------------------------------------------------------------------------------+
    # | PRIVATE :: RUN METHODS
    # +---------------------------------------------------------------------------------------------------------------+
    def _stdout_lister(
        self, things_to_list: typing.Iterable[typing.Any], to_string: typing.Callable[[typing.Any], str]
    ) -> None:
        for thing in things_to_list:
            sys.stdout.write(to_string(thing))
            sys.stdout.write(";")

    def _list_outputs_only(self) -> None:
        if self._args.generate_support != "only":
            self._stdout_lister(self._generator.generate_all(is_dryrun=True), lambda p: str(p))

        if self._should_generate_support():
            self._stdout_lister(self._support_generator.generate_all(is_dryrun=True), lambda p: str(p))

    def _list_inputs_only(self) -> None:
        if self._args.generate_support != "only":
            self._stdout_lister(
                self._generator.get_templates(omit_serialization_support=self._args.omit_serialization_support),
                lambda p: str(p.resolve()),
            )

        if self._should_generate_support():
            self._stdout_lister(
                self._support_generator.get_templates(omit_serialization_support=self._args.omit_serialization_support),
                lambda p: str(p.resolve()),
            )

        if self._args.generate_support != "only":
            if self._generator.generate_namespace_types:
                self._stdout_lister(
                    [x for x, _ in self._root_namespace.get_all_types()], lambda p: str(p.source_file_path.as_posix())
                )
            else:
                self._stdout_lister(
                    [x for x, _ in self._root_namespace.get_all_datatypes()],
                    lambda p: str(p.source_file_path.as_posix()),
                )

    def _list_configuration_only(self) -> None:
        lctx = self._language_context

        import yaml

        sys.stdout.write("target_language: '")
        sys.stdout.write(lctx.get_target_language().name)
        sys.stdout.write("'\n")

        yaml.dump(lctx.config.sections(), sys.stdout, allow_unicode=True)

    def _generate(self) -> None:
        if self._should_generate_support():
            self._support_generator.generate_all(
                is_dryrun=self._args.dry_run,
                allow_overwrite=not self._args.no_overwrite,
                omit_serialization_support=self._args.omit_serialization_support,
            )

        if self._args.generate_support != "only":
            self._generator.generate_all(
                is_dryrun=self._args.dry_run,
                allow_overwrite=not self._args.no_overwrite,
                omit_serialization_support=self._args.omit_serialization_support,
            )
