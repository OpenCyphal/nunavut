#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Module containing types and utilities for building generator objects.
Generators abstract the code generation technology used to transform
pydsdl AST into source code.
"""

import abc
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Type, Union

from ._namespace import Generatable, Namespace
from ._utilities import ResourceType, YesNoDefault
from .lang import LanguageContext, LanguageContextBuilder
from .lang._language import Language


@dataclass(frozen=True)
class GenerationResult:
    """
    A simple data class to hold the results of a generation operation.
    """

    lctx: LanguageContext
    """The language context used to generate outputs."""

    generator_targets: Dict[Path, Generatable]
    """The set of explicit files targeted for generation and their dependant files."""

    generated_files: List[Path]
    """
    The set of files that were (or would be, for dry runs) generated for data types.
    """

    support_files: List[Path]
    """
    The set of files that were (or would be, for dry runs) generated to support data types.
    """

    template_files: List[Path]
    """
    The set of template files used to generate the `generated_files`.
    """

    def __add__(self, other: Any) -> "GenerationResult":
        """
        If there exists an isomorphism between this object and other, return a union of the two as a new result.

        .. invisible-code-block: python

            from nunavut._generators import GenerationResult, basic_language_context_builder_from_args
            from pathlib import Path
            from pytest import raises

            c_lang = basic_language_context_builder_from_args(target_language="c").create()
            js_lang = basic_language_context_builder_from_args(
                target_language="js",
                include_experimental_languages=True).create()

            with raises(RuntimeError):
                GenerationResult(c_lang, {}, [], [], []) + 1

            with raises(RuntimeError):
                GenerationResult(c_lang, {}, [], [], []) + GenerationResult(js_lang, {}, [], [], [])

        .. code-block:: python

            ursine = GenerationResult(c_lang,
                                      {Path("bears/grizzly.c"): Path("bears/grizzly.dsdl")},
                                      [Path("bears/grizzly.c")],
                                      [Path("include/support.h")],
                                      [Path("templates/code.j2")])
            bovine = GenerationResult(c_lang,
                                      {Path("cows/jersey.c"): Path("cows/jersey.dsdl")},
                                      [Path("cows/jersey.c")],
                                      [Path("include/support.h")],
                                      [Path("templates/code.j2")])

            mammals = ursine + bovine

            assert(mammals.generator_targets[Path("bears/grizzly.c")] == Path("bears/grizzly.dsdl"))
            assert(mammals.generator_targets[Path("cows/jersey.c")] == Path("cows/jersey.dsdl"))
            assert(len(mammals.support_files) == 1)
            assert(len(mammals.template_files) == 1)

        """
        if not isinstance(other, self.__class__):
            raise RuntimeError(f"Cannot add {type(other)} type to a GenerationResult.")
        if other.lctx != self.lctx:
            raise RuntimeError(
                f"Result with language {str(other.lctx)} is not isomorphic with this result for "
                f"language {str(self.lctx)}."
            )

        return GenerationResult(
            self.lctx,
            {**self.generator_targets, **other.generator_targets},
            self.generated_files + other.generated_files,
            [*{*(self.support_files + other.support_files)}],
            [*{*(self.template_files + other.template_files)}],
        )


class AbstractGenerator(metaclass=abc.ABCMeta):
    """
    Abstract base class for classes that generate source file output
    from a given pydsdl parser result.

    :param nunavut.Namespace namespace:  The top-level namespace to
        generates types at and from.
    :param int resource_types: A bitmask of resources to generate.
        This can be a combination of ResourceType values.
    :param YesNoDefault generate_namespace_types:  Set to YES
        to force generation files for namespaces and NO to suppress.
        DEFAULT will generate namespace files based on the language
        preference.
    :param Iterable[Path] index_file: A list of paths to files that
        should be generated, relative to the output directory, which
        are given access to the full namespace context rather than
        per-type context.
    :param Any kwargs: Additional arguments to pass into generators.
    """

    def __init__(
        self,
        namespace: Namespace,
        resource_types: int,
        generate_namespace_types: YesNoDefault = YesNoDefault.DEFAULT,
        index_file: Optional[Iterable[Path]] = None,
        **kwargs: Any,
    ):  # pylint: disable=unused-argument
        self._namespace = namespace
        self._resource_types = resource_types
        self._generate_namespace_types = self.generate_namespace_types_from_trinary(
            self._namespace.get_language_context().get_target_language(), generate_namespace_types
        )
        if index_file is not None:
            self._index_files = [Path(p) for p in index_file]
        else:
            self._index_files = []

    @classmethod
    def generate_namespace_types_from_trinary(
        cls, target_language: Language, generate_namespace_types: YesNoDefault
    ) -> bool:
        """
        Given the target language and a trinary value, returns a binary result for "should namespace types be generated"
        as a parameter.
        """
        if generate_namespace_types == YesNoDefault.YES:
            return True
        elif generate_namespace_types == YesNoDefault.NO:
            return False
        else:
            if target_language.has_standard_namespace_files:
                return True
            else:
                return False

    @property
    def namespace(self) -> Namespace:
        """
        The root :class:`nunavut.Namespace` for this generator.
        """
        return self._namespace

    @property
    def resource_types(self) -> int:
        """
        The bitmask of resources to generate. This can be a combination of ResourceType values.
        """
        return self._resource_types

    @property
    def generate_namespace_types(self) -> bool:
        """
        If true then the generator is set to emit files for :class:`nunavut.Namespace`
        in addition to the pydsdl datatypes. If false then only files for pydsdl datatypes
        will be generated.
        """
        return self._generate_namespace_types

    @property
    def index_files(self) -> List[Path]:
        """
        A list of paths to files that should be generated, relative to the output directory, which are given access
        to the full namespace context rather than per-type context.
        """
        return self._index_files

    @abc.abstractmethod
    def get_templates(self) -> Iterable[Path]:
        """
        Enumerate all templates found in the templates path.
        :return: A list of paths to all templates found by this Generator object.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def generate_all(
        self,
        is_dryrun: bool = False,
        allow_overwrite: bool = True,
    ) -> Iterable[Path]:
        """
        Generates all output for a given :class:`nunavut.Namespace` and using
        the templates found by this object.

        :param bool is_dryrun: If True then no output files will actually be
                               written but all other operations will be performed.
        :param bool allow_overwrite: If True then the generator will attempt to overwrite any existing files
                                it encounters. If False then the generator will raise an error if the
                                output file exists and the generation is not a dry-run.
        :return: Iterator over the files generated.
        :raises: PermissionError if :attr:`allow_overwrite` is False and the file exists.
        """
        raise NotImplementedError()


# --[GENERATION HELPERS]-------------------------------------------------------


def basic_language_context_builder_from_args(target_language: str, **kwargs: Any) -> LanguageContextBuilder:
    """
    Uses interpreted arguments to create a new LanguageContextBuilder object with support for the most common arguments.
    This method will always support arguments used in the CLI. For more advanced use cases, create a
    LanguageContextBuilder object directly or add additional arguments to the builder after creation.

    .. note:: This is the same method used by :func:`generate_all` to create a LanguageContextBuilder object.

    .. invisible-code-block: python

        from nunavut import basic_language_context_builder_from_args

    .. code-block:: python

        # target_language is the only required argument
        builder = basic_language_context_builder_from_args(target_language="c")

        assert builder.create().get_target_language().name == "c"

    :param str target_language: The name of the language to generate source for.
    :param kwargs: A dictionary of arguments to pass to the :class:`LanguageContextBuilder`.
        The following arguments are supported:

            * **configuration**: A list of additional configuration files to load.
            * **include_experimental_languages**: If true then experimental languages will also be available.
            * **language_options**: Opaque arguments passed through to the language objects. The supported arguments and
                valid values are different depending on the language specified by the :code:`language_key` parameter.
            * **output_extension**: The file extension to use for generated files.
            * **namespace_output_stem**: The stem to use for generated namespace files.
            * **additional_config_files**: A list of :class:`Path` s to additional configuration files to load.

    :return: A new :class:`LanguageContextBuilder` object based on the command line arguments.
    """

    additional_config_files = kwargs.get("configuration", None)
    if additional_config_files is None:
        additional_config_files = []
    if isinstance(additional_config_files, Path):
        additional_config_files = [additional_config_files]

    builder = (
        LanguageContextBuilder(include_experimental_languages=kwargs.get("include_experimental_languages", False))
        .set_target_language(target_language)
        .set_target_language_configuration_override(
            Language.WKCV_LANGUAGE_OPTIONS, kwargs.get("language_options", None)
        )
        .set_target_language_extension(kwargs.get("output_extension", None))
        .set_target_language_configuration_override(
            Language.WKCV_NAMESPACE_FILE_STEM, kwargs.get("namespace_output_stem", None)
        )
        .add_config_files(*additional_config_files)
    )

    return builder


# --[GENERATION FUNCTIONS]-----------------------------------------------------


# pylint: disable=too-many-arguments, too-many-locals, too-many-statements
def generate_all(
    target_language: str,
    target_files: Iterable[Union[str, Path]],
    root_namespace_directories_or_names: Iterable[Union[str, Path]],
    outdir: Path,
    language_options: Optional[Mapping[str, Any]] = None,
    include_experimental_languages: bool = False,
    resource_types: int = ResourceType.ANY.value,
    embed_auditing_info: bool = False,
    dry_run: bool = False,
    jobs: int = 0,
    no_overwrite: bool = False,
    allow_unregulated_fixed_port_id: bool = False,
    omit_dependencies: bool = False,
    code_generator_type: Optional[Type[AbstractGenerator]] = None,
    support_generator_type: Optional[Type[AbstractGenerator]] = None,
    **kwargs: Any,
) -> GenerationResult:
    """
    Helper method that uses default settings and built-in templates to generate types for a given
    language. This method is the most direct way to generate code using Nunavut.

    Generation takes place four steps with a function provided for each step:


    .. code-block:: none

        ┌───────────────────────────────────────────────────┐ 1. generate_all
        │           Language context construction           │
        │                                                   │
        │  ┌─────────────────────────────────────────────┐  │ 2. generate_all_for_language
        │  │ Parsing (pydsdl) and constructing Namespace │  │
        │  │             trees from results              │  │
        │  │                                             │  │
        │  │  ┌───────────────────────────────────────┐  │  │ 3. generate_all_from_namespace
        │  │  │        Generator construction         │  │  │
        │  │  │                                       │  │  │
        │  │  │  ┌─────────────────────────────────┐  │  │  │ 4. generate_all_from_namespace_with_generators
        │  │  │  │        code generation          │  │  │  │
        │  │  │  │                                 │  │  │  │
        │  │  │  │                                 │  │  │  │
        │  │  │  └─────────────────────────────────┘  │  │  │
        │  │  └───────────────────────────────────────┘  │  │
        │  └─────────────────────────────────────────────┘  │
        └───────────────────────────────────────────────────┘

    At each stage the number of options are reduced as objects are constructed based on their values.

    * **generate_all**: Requires no Nunavut objects and can be driven from a command-line.
    * **generate_all_for_language**: This is the best entry point for programmatic use of Nunavut. Simply construct a
        LanguageContext object using a LanguageContextBuilder and pass it to this function.
    * **generate_all_from_namespace**: This function can be used if you have already constructed a Namespace object.
    * **generate_all_from_namespace_with_generators**: This function is used if you have already constructed the
        generators you want to use.

    :param str target_language: The name of the language to generate source for.
                See the :doc:`../../docs/templates` for details on available language support.
    :param target_files: A list of paths to dsdl files. This method will generate code for these files and their
                dependant types.
    :param root_namespace_directories_or_names: This can be a set of names of root namespaces or relative paths to
        root namespaces. All ``dsdl_files`` provided must be under one of these roots. For example, given:

        .. code-block:: python

            target_dsdl_files = [
                            Path("workspace/project/types/animals/felines/Tabby.1.0.dsdl"),
                            Path("workspace/project/types/animals/canines/Boxer.1.0.dsdl"),
                            Path("workspace/project/types/plants/trees/DouglasFir.1.0.dsdl")
                        ]


        then this argument must be one of:

        .. code-block:: python

            root_namespace_directories_or_names = ["animals", "plants"]

            # or

            root_namespace_directories_or_names = [
                            Path("workspace/project/types/animals"),
                            Path("workspace/project/types/plants")
                        ]


    :param Path outdir:
        The path to generate code at and under.
    :param Optional[Mapping[str, Any]] language_options: Opaque arguments passed through to the language objects. The
        supported arguments and valid values are different depending on the language specified by the `language_key`
        parameter.
    :param int resource_types:
        Bitmask of resources to generate. This can be a combination of ResourceType values. For example, to generate
        only serialization support code, set this to ResourceType.SERIALIZATION_SUPPORT.value. To generate all resources
        set this to ResourceType.ANY.value. To only generate resource files (i.e. to omit source code generation) set
        the ResourceType.ONLY.value bit and the resource type bytes you do want to generate.
    :param embed_auditing_info:
        If True then additional information about the inputs and environment used to generate source will be embedded in
        the generated files at the cost of build reproducibility.
    :param bool include_experimental_languages:
        If true then experimental languages will also be available.
    :param bool dry_run:
        If True then no files will be generated/written but all logic will be exercised with commensurate logging and
        errors.
    :param int jobs:
        The number of parallel jobs to use when generating code. If 1 then no parallelism is used. If 0 then the
        number of jobs is determined by the number of CPUs available.

        .. note:: By default, any multiprocessing jobs used will not have a timeout set. To set a timeout for any jobs
            set the environment variable ``NUNAVUT_JOB_TIMEOUT_SECONDS`` to the desired timeout in fractional seconds.
            this is normally not useful as a correct timeout value is highly dependent on the system and the number of
            types being generated.

    :param bool no_overwrite:
        If True then generated files will not be allowed to overwrite existing files under the `outdir` path causing
        errors.
    :param bool allow_unregulated_fixed_port_id:
        If True then errors will become warning when using fixed port identifiers for unregulated datatypes.
    :param bool omit_dependencies:
        If True then only the types explicitly provided in `target_files` will be generated. If False then all
        dependant types will also be generated.
    :param code_generator_type: The type of code generator to use. If None then the default code generator is used.
    :param support_generator_type: The type of support generator to use. If None then the default support generator is
        used.
    :param kwargs: Additional arguments passed into the language context builder and generator constructors. See the
        documentation for :func:`basic_language_context_builder_from_args` and for specific generator types for details
        on supported arguments.

    :returns GenerationResult: A dataclass containing explicit inputs, discovered inputs, and determined outputs.
    :raises pydsdl.FrontendError: Exceptions thrown from the pydsdl frontend. For example, parsing malformed DSDL will
        raise this exception.
    """

    language_context = basic_language_context_builder_from_args(
        target_language,
        language_options=language_options,
        include_experimental_languages=include_experimental_languages,
        **kwargs,
    ).create()

    return generate_all_for_language(
        language_context,
        target_files,
        root_namespace_directories_or_names,
        outdir,
        resource_types,
        embed_auditing_info,
        dry_run,
        jobs,
        no_overwrite,
        allow_unregulated_fixed_port_id,
        omit_dependencies,
        code_generator_type,
        support_generator_type,
        **kwargs,
    )


def generate_all_for_language(
    language_context: LanguageContext,
    target_files: Iterable[Union[str, Path]],
    root_namespace_directories_or_names: Iterable[Union[str, Path]],
    outdir: Path,
    resource_types: int = ResourceType.ANY.value,
    embed_auditing_info: bool = False,
    dry_run: bool = False,
    jobs: int = 0,
    no_overwrite: bool = False,
    allow_unregulated_fixed_port_id: bool = False,
    omit_dependencies: bool = False,
    code_generator_type: Optional[Type[AbstractGenerator]] = None,
    support_generator_type: Optional[Type[AbstractGenerator]] = None,
    **generator_args: Any,
) -> GenerationResult:
    """
    Generate code for a set of target_files using a configured language context. This is the second step in the
    generation process and is the best entry point for programmatic use of Nunavut. See the documentation for
    :func:`generate_all` for more details.

    :param language_context: The language context to generate code for.
    :param target_files: A list of paths to dsdl files. This method will generate code for these files and their
        dependant types.
    :param root_namespace_directories_or_names: This can be a set of names of root namespaces or relative paths to
        root namespaces. All ``dsdl_files`` provided must be under one of these roots. See the documentation for
        :func:`generate_all` for more details.
    :param outdir: The path to generate code at and under.
    :param resource_types: A bitmask of resources to generate. This can be a combination of ResourceType values.
    :param embed_auditing_info: If True then additional information about the inputs and environment used to generate
        source will be embedded in the generated files at the cost of build reproducibility.
    :param dry_run: If True then no files will be generated/written but all logic will be exercised with commensurate
        logging and errors.
    :param int jobs:
        The number of parallel jobs to use when generating code. If 1 then no parallelism is used. If 0 then the
        number of jobs is determined by the number of CPUs available.

        .. note:: By default, any multiprocessing jobs used will not have a timeout set. To set a timeout for any jobs
            set the environment variable ``NUNAVUT_JOB_TIMEOUT_SECONDS`` to the desired timeout in fractional seconds.
            this is normally not useful as a correct timeout value is highly dependent on the system and the number of
            types being generated.

    :param no_overwrite: If True then generated files will not be allowed to overwrite existing files under the `outdir`
        path causing errors.
    :param allow_unregulated_fixed_port_id: If True then errors will become warning when using fixed port identifiers
        for unregulated datatypes.
    :param omit_dependencies: If True then only the types explicitly provided in `target_files` will be generated. If
        False then all dependant types will also be generated.
    :param code_generator_type: The type of code generator to use. If None then the default code generator is used.
    :param support_generator_type: The type of support generator to use. If None then the default support generator is
        used.
    :param generator_args: Additional arguments to pass into the generator constructors. See the documentation for
        specific generator types for details on supported arguments.
    :return: A dataclass containing explicit inputs, discovered inputs, and determined outputs.
    :raises pydsdl.FrontendError: Exceptions thrown from the pydsdl frontend. For example, parsing malformed DSDL will
        raise this exception.
    """
    index = Namespace.read_files(
        outdir,
        language_context,
        target_files,
        root_namespace_directories_or_names,
        jobs,
        float(os.environ.get("NUNAVUT_JOB_TIMEOUT_SECONDS", 0)),
        allow_unregulated_fixed_port_id=allow_unregulated_fixed_port_id,
        omit_dependencies=omit_dependencies,
    )

    return generate_all_from_namespace(
        index,
        resource_types,
        embed_auditing_info,
        dry_run,
        no_overwrite,
        code_generator_type,
        support_generator_type,
        **generator_args,
    )


def generate_all_from_namespace(
    index: Namespace,
    resource_types: int = ResourceType.ANY.value,
    embed_auditing_info: bool = False,
    dry_run: bool = False,
    no_overwrite: bool = False,
    code_generator_type: Optional[Type[AbstractGenerator]] = None,
    support_generator_type: Optional[Type[AbstractGenerator]] = None,
    **generator_args: Any,
) -> GenerationResult:
    """
    Given a populated namespace, generate code for the types found within it. This is the third step in the generation
    process and is used when you have already constructed a Namespace object. See the documentation for
    :func:`generate_all` for more details.

    :param index: The namespace tree to generate code for.
    :param resource_types: A bitmask of resources to generate. This can be a combination of ResourceType values.
    :param embed_auditing_info: If True then additional information about the inputs and environment used to generate
        source will be embedded in the generated files at the cost of build reproducibility.
    :param dry_run: If True then no files will be generated/written but all logic will be exercised with commensurate
        logging and errors.
    :param no_overwrite: If True then generated files will not be allowed to overwrite existing files under the `outdir`
        path causing errors.
    :param code_generator_type: The type of code generator to use. If None then the default code generator is used.
    :param support_generator_type: The type of support generator to use. If None then the default support generator is
        used.
    :param generator_args: Additional arguments to pass into the generator constructors. See the documentation for
        specific generator types for details on supported arguments.
    :return: A dataclass containing explicit inputs, discovered inputs, and determined outputs.
    :raises pydsdl.FrontendError: Exceptions thrown from the pydsdl frontend. For example, parsing malformed DSDL will
        raise this exception.
    """

    support_generator_args = generator_args.copy()
    support_generator_args["templates_dir"] = generator_args.get("support_templates_dir", [])

    # if ResourceType.INDEX.value() | resource_types != 0:
    #     For implementing issue #334 or other features requiring an index template, add an index_generator_type
    #     here to the generators we create and run

    if code_generator_type is None:
        # load default code generator
        from .jinja import DSDLCodeGenerator  # pylint: disable=import-outside-toplevel

        code_generator_type = DSDLCodeGenerator
    if support_generator_type is None:
        # load default support generator
        from .jinja import SupportGenerator  # pylint: disable=import-outside-toplevel

        support_generator_type = SupportGenerator

    code_generator = code_generator_type(
        index, resource_types, embed_auditing_info=embed_auditing_info, **generator_args
    )
    support_generator = support_generator_type(
        index, resource_types, embed_auditing_info=embed_auditing_info, **support_generator_args
    )

    return generate_all_from_namespace_with_generators(index, code_generator, support_generator, dry_run, no_overwrite)


def generate_all_from_namespace_with_generators(
    index: Namespace,
    code_generator: AbstractGenerator,
    support_generator: AbstractGenerator,
    dry_run: bool = False,
    no_overwrite: bool = False,
) -> GenerationResult:
    """
    Given a populated namespace, generate code for the types found within it using the provided generators. This is the
    fourth and final step in the generation process and is used when you have already constructed the generators you
    want to use. See the documentation for :func:`generate_all` for more details.

    :param index: The namespace tree to generate code for.
    :param code_generator: The code generator to use.
    :param support_generator: The support generator to use.
    :param dry_run: If True then no files will be generated/written but all logic will be exercised with commensurate
        logging and errors.
    :param no_overwrite: If True then generated files will not be allowed to overwrite existing files under the `outdir`
        path causing errors.
    :return: A dataclass containing explicit inputs, discovered inputs, and determined outputs.
    :raises pydsdl.FrontendError: Exceptions thrown from the pydsdl frontend. For example, parsing malformed DSDL will
        raise this exception.
    """

    template_files = list(set(support_generator.get_templates()).union(set(code_generator.get_templates())))
    generated_files = list(code_generator.generate_all(dry_run, not no_overwrite))

    if support_generator.resource_types & ResourceType.ONLY.value != 0 or len(generated_files) > 0:
        # if we are specifically generating support files or if we are generating them as-needed and we need them.
        support_files = list(support_generator.generate_all(dry_run, not no_overwrite))
    else:
        # else we don't need to generate support files because there's nothing to support
        support_files = []

    generator_targets = {}
    for file in generated_files:
        if isinstance(file, Generatable):
            generator_targets[Path(file)] = file

    return GenerationResult(
        index.get_language_context(),
        generator_targets,
        generated_files,
        support_files,
        template_files,
    )
