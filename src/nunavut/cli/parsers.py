#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Command-line parsers for the Nunavut command-line interface.
"""

import argparse
import itertools
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from nunavut._postprocessors import (
    ExternalProgramEditInPlace,
    LimitEmptyLines,
    PostProcessor,
    SetFileMode,
    TrimTrailingWhitespace,
)
from nunavut._utilities import DefaultValue, QuaternaryLogic, ResourceSearchPolicy, ResourceType, YesNoDefault


class NunavutArgumentParser(argparse.ArgumentParser):
    """
    Specialization of argparse.ArgumentParser to encapsulate inter-argument rules, aggregate path arguments, and
    combine language options. The output of this parser can be fed directly into the :func:`nunavut.generate_all`
    function.

    Arguments Added
    ---------------

    - **target_files**
        A list of target files to process with colon syntax resolved.

    - **root_namespace_directories_or_names**
        A list of additional directories to search for DSDL files. This is a combination of the
        lookup_dir, results after parsing target file colon syntax, and paths from supported
        environment variables.

    - **language_options**
        A dictionary of options to pass to a language context builder.

    - **resource_types**
        Bitmask of ResourceType values to generate based on omit_serialization_support and generate_support arguments.

    - **post_processors**
        A list of post processors to run on generated files.

    - **search_policy**
        The ResourceSearchPolicy to use when searching for templates.

    Arguments Removed
    -----------------

    - **generate_support**
        The original argument is replaced with resource_types bitmask.

    - **target_files_or_root_namespace**
        The original argument is replaced with target_files and root_namespace_directories_or_names.

    - **lookup_dir**
        The original argument is replaced with root_namespace_directories_or_names.

    - **fallback_to_builtin_templates**
        Transformed into search_policy

    - **pp_trim_trailing_whitespace**
        The original arguments are replaced with post_processors.

    - **pp_max_emptylines**
        The original arguments are replaced with post_processors.

    - **pp_run_program**
        The original arguments are replaced with post_processors.

    - **pp_run_program_arg**
        The original arguments are replaced with post_processors.

    Arguments Modified
    ------------------

    - **verbose**
        If not provided, defaults to 0.

    - **list_outputs**
        If provided, sets dry_run to True.

    - **list_inputs**
        If provided, sets dry_run to True.

    - **generate_namespace_types**
        Converts the argument to a YesNoDefault enum.

    """

    DSDL_FILE_SUFFIXES = (".uavcan", ".dsdl")

    # --[ OVERRIDE ]--------------------------------------------------------------------------------------------------
    def parse_known_args(self, args=None, namespace=None):  # type: ignore
        parsed_args, argv = super().parse_known_args(args, namespace)
        self._post_process_args(parsed_args)
        return (parsed_args, argv)

    # --[ PRIVATE ]---------------------------------------------------------------------------------------------------
    def _post_process_log(self, args: argparse.Namespace, message: str) -> None:
        """
        Print a message to the log.
        """
        if args.verbose <= 0:
            return
        self._print_message(message, sys.stdout)

    def _post_process_args(self, args: argparse.Namespace) -> None:
        """
        Applies rules between different arguments and handles other special cases.
        """

        if args.verbose is None:
            args.verbose = 0

        if args.list_outputs:
            args.dry_run = True

        if args.list_inputs:
            args.dry_run = True

        if args.fallback_to_builtin_templates:
            args.search_policy = ResourceSearchPolicy.FIND_ALL
        else:
            args.search_policy = ResourceSearchPolicy.FIND_FIRST

        del args.fallback_to_builtin_templates

        # Convert omit_serialization_support and generate_support to resource_types bitmask.
        args.resource_types = self._create_resource_types_bitmask(args)

        # Find all possible path specifications and combine into two collections: root_namespace_directories_or_names
        # and target_files.
        # TARGETS
        root_namespace_directories_or_names, target_files = self._parse_target_paths(
            args.target_files_or_root_namespace, True, error_if_folder=args.no_target_namespaces
        )
        del args.target_files_or_root_namespace

        # LOOKUP PATHS
        lookup_paths = args.lookup_dir
        del args.lookup_dir

        root_namespace_directories_or_names_from_lookups, target_files_from_lookups = self._parse_target_paths(
            lookup_paths,
            False,
        )

        root_namespace_directories_or_names.update(root_namespace_directories_or_names_from_lookups)
        target_files.update(target_files_from_lookups)

        # PATHS FROM ENVIRONMENT

        root_namespace_directories_or_names_from_environment, target_files_from_environment = self._parse_target_paths(
            [str(env_path) for env_path in self._lookup_paths_from_environment(args)],
            False,
        )

        root_namespace_directories_or_names.update(root_namespace_directories_or_names_from_environment)
        target_files.update(target_files_from_environment)

        # Store the combined paths in args
        args.target_files = list(target_files)
        args.root_namespace_directories_or_names = list(root_namespace_directories_or_names)

        # Create a dictionary of language options.
        args.language_options = self._create_language_options(args)

        # Create a list of post processors.
        args.post_processors = self._create_post_processors(args)

        # Generator arguments
        args.generate_namespace_types = YesNoDefault.YES if args.generate_namespace_types else YesNoDefault.DEFAULT

        # Can't list configuration as csv. Has to be a structured return format.
        if args.list_configuration and args.list_format in ("scsv", "csv"):
            self.error(
                textwrap.dedent(
                    f"""

            --list-format {args.list_format} is not supported for --list-configuration. Use a structured format like
            --list-format json to list configuration information.

            """
                )
            )

    def _parse_target_paths(
        self, target_files_or_root_namespace: Optional[List[str]], greedy: bool, error_if_folder: bool = False
    ) -> Tuple[Set[Path], Set[Path]]:
        """
        Parse the target paths from the command line arguments.

        :param target_files_or_root_namespace: The target files or root namespace directories.
        :param greedy: If True, and if a path is a simple folder (i.e. no colon-syntax), then the path will
            be considered a root path and all DSDL files found in the folder, using globular magic, will be considered
            target files.

        :return: A list of root paths (folders) and a list of target paths (files).

        .. invisible-code-block: python

            from nunavut.cli.parsers import NunavutArgumentParser
            from pytest import raises
            from pathlib import Path

            real_root = Path().cwd().as_posix()

            parser = NunavutArgumentParser()
            # Happy path
            root_paths, target_files = parser._parse_target_paths(
                [
                    f"{real_root}one/to/root",
                    f"{real_root}two/to/file.dsdl",
                    "three/path/four:to/file.dsdl",
                    f"{real_root}five/path/six:to/file.dsdl",
                    "seven/path/eight\\\\:to/file.dsdl",
                    f"{real_root}nine/path/ten/:to/file.dsdl",
                ],
                False,
            )
            print(root_paths, target_files)
            assert len(root_paths) == 4
            assert len(target_files) == 5

            assert Path(f"{real_root}one/to/root") in root_paths
            assert Path("three/path/four") in root_paths
            assert Path(f"{real_root}five/path/six") in root_paths
            assert Path(f"{real_root}nine/path/ten") in root_paths

            assert Path(f"{real_root}two/to/file.dsdl") in target_files
            assert Path("four/to/file.dsdl") in target_files
            assert Path("six/to/file.dsdl") in target_files
            assert Path("seven/path/eight\\\\:to/file.dsdl") in target_files
            assert Path("ten/to/file.dsdl") in target_files

            # Happy path: default root path, no dependencies
            default_root_paths, default_target_files = parser._parse_target_paths([""], False)
            assert len(default_root_paths) == 1
            assert len(default_target_files) == 0
            assert default_root_paths.pop() == Path().cwd()

            # Happy path: single target file
            single_target_file_root_paths, single_target_file_target_files = parser._parse_target_paths(
                [f"{real_root}one/to/file.dsdl"], True
            )
            assert len(single_target_file_root_paths) == 0
            assert len(single_target_file_target_files) == 1
            assert single_target_file_target_files.pop() == Path(f"{real_root}one/to/file.dsdl")

            # errors: multiple colons
            with raises(SystemExit):
                parser._parse_target_paths(["one:two:three"], False)

            # errors: leading slash
            with raises(SystemExit):
                parser._parse_target_paths([f"path/to:{Path.cwd().anchor}root/to/file.dsdl"], False)

        """

        def _parse_lookup_dir(lookup_dir: str) -> Tuple[Optional[Path], Optional[Path]]:

            lookup_path = Path(lookup_dir)
            if lookup_path.is_absolute():
                relative_lookup_dir = lookup_path.relative_to(lookup_path.anchor).as_posix()
            else:
                relative_lookup_dir = lookup_dir
            split_path = re.split(r"(?<!\\):", relative_lookup_dir)
            if len(split_path) > 2:
                self.error(f"Invalid lookup path (too many colons) > {lookup_dir}")
            if lookup_path.is_absolute():
                root_path = Path(lookup_path.anchor, split_path[0])
            else:
                root_path = Path(split_path[0])
            if len(split_path) == 2:
                return root_path, Path(root_path.stem, split_path[1])
            elif root_path.suffix in self.DSDL_FILE_SUFFIXES:
                return None, root_path
            else:
                return root_path, None

        if target_files_or_root_namespace is None:
            return set(), set()

        root_paths = set()
        target_files = set()
        for target_path in target_files_or_root_namespace:
            root_dir, target_file_maybe = _parse_lookup_dir(target_path)
            if root_dir is not None:
                if target_file_maybe is None:
                    if error_if_folder:
                        self.error(f"Root directory cannot be a folder (--error-if-folder) > {root_dir}")
                    root_dir_resolved = root_dir.expanduser().resolve()
                    if root_dir_resolved.parent == root_dir_resolved:
                        raise RuntimeError(f"Refusing to search root directory > {root_dir_resolved}")
                    # only a path so we'll use globular magic to find all the DSDL files in the directory
                    root_paths.add(root_dir_resolved)
                    if greedy:
                        for dsdl_suffix in self.DSDL_FILE_SUFFIXES:
                            target_files.update(set(root_dir_resolved.glob(f"**/*{dsdl_suffix}")))
                else:
                    root_paths.add(root_dir)
            if target_file_maybe is not None:
                if root_dir is not None and target_file_maybe.is_absolute():
                    self.exit(
                        1,
                        f"Target file path cannot be absolute when using colon syntax > {root_dir}:{target_file_maybe}",
                    )
                target_files.add(target_file_maybe)

        return root_paths, target_files

    def _lookup_paths_from_environment(self, args: argparse.Namespace) -> Set[Path]:
        """
        Parse supported environment variables
        """

        def _extra_includes_from_env(env_var_name: str) -> List[Path]:
            try:
                return [Path(extra) for extra in os.environ[env_var_name].split(os.pathsep)]
            except KeyError:
                return []

        extra_includes: List[Path] = []

        dsdl_include_path = _extra_includes_from_env("DSDL_INCLUDE_PATH")

        if len(dsdl_include_path) > 0:
            self._post_process_log(args, f"Extra includes from DSDL_INCLUDE_PATH: {dsdl_include_path}")

        cyphal_root_paths = _extra_includes_from_env("CYPHAL_PATH")
        cyphal_paths = [
            c
            for c in itertools.chain.from_iterable(map(lambda cyphal_path: cyphal_path.glob("*"), cyphal_root_paths))
            if c.is_dir()
        ]

        if len(cyphal_paths) > 0:
            self._post_process_log(args, f"Extra includes from CYPHAL_PATH: {cyphal_paths}")

        extra_includes += sorted(itertools.chain(dsdl_include_path, cyphal_paths))

        return set(extra_includes)

    @classmethod
    def _create_language_options(cls, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Group all language options into a dictionary.
        """
        language_options = {}
        if args.target_endianness is not None:
            language_options["target_endianness"] = args.target_endianness

        language_options["omit_float_serialization_support"] = (
            True if args.omit_float_serialization_support else DefaultValue(False)
        )

        language_options["omit_serialization_support"] = (
            True if args.omit_serialization_support else DefaultValue(False)
        )

        language_options["enable_serialization_asserts"] = (
            True if args.enable_serialization_asserts else DefaultValue(False)
        )

        language_options["enable_override_variable_array_capacity"] = (
            True if args.enable_override_variable_array_capacity else DefaultValue(False)
        )

        if args.language_standard is not None:
            language_options["std"] = args.language_standard

        return language_options

    @classmethod
    def _create_post_processors(cls, args: argparse.Namespace) -> List[PostProcessor]:
        """
        A, possibly empty, list of post processors to run based on provided arguments.
        """

        def _build_ext_program_postprocessor_args(program: str) -> List[str]:
            """
            Build an array of arguments for the program.
            """
            subprocess_args = [program]
            if hasattr(args, "pp_run_program_arg") and args.pp_run_program_arg is not None:
                for program_arg in args.pp_run_program_arg:
                    subprocess_args.append(program_arg)
            return subprocess_args

        post_processors: List[PostProcessor] = []
        if args.pp_trim_trailing_whitespace:
            post_processors.append(TrimTrailingWhitespace())
            del args.pp_trim_trailing_whitespace
        if hasattr(args, "pp_max_emptylines") and args.pp_max_emptylines is not None:
            post_processors.append(LimitEmptyLines(args.pp_max_emptylines))
            del args.pp_max_emptylines
        if hasattr(args, "pp_run_program") and args.pp_run_program is not None:
            post_processors.append(
                ExternalProgramEditInPlace(_build_ext_program_postprocessor_args(args.pp_run_program))
            )
            del args.pp_run_program
            del args.pp_run_program_arg

        post_processors.append(SetFileMode(args.file_mode))

        return post_processors

    @classmethod
    def _create_resource_types_bitmask(cls, args: argparse.Namespace) -> int:
        """
        Create a bitmask of ResourceType values based on the provided arguments. This method utilizes generate_support
        and omit_serialization_support arguments to determine the bitmask. It also removes the generate_support argument
        from the namespace.

        :param args: The parsed arguments.

        .. invisible-code-block: python

            from nunavut.cli.parsers import NunavutArgumentParser, QuaternaryLogic, ResourceType

            def _test_create_resource_types_bitmask(generate_support, omit_serialization_support, expected):
                namespace = argparse.Namespace(
                    generate_support=generate_support,
                    omit_serialization_support=omit_serialization_support
                )

                resource_types = NunavutArgumentParser._create_resource_types_bitmask(namespace)
                assert resource_types == expected
                assert "generate_support" not in namespace


            _test_create_resource_types_bitmask("only", False, (
                ResourceType.ONLY.value | ResourceType.SERIALIZATION_SUPPORT.value | ResourceType.TYPE_SUPPORT.value)
            )
            _test_create_resource_types_bitmask("never", True, ResourceType.NONE.value)
            _test_create_resource_types_bitmask("as-needed", False, (
                ResourceType.ANY.value | ResourceType.SERIALIZATION_SUPPORT.value | ResourceType.TYPE_SUPPORT.value)
            )
            _test_create_resource_types_bitmask("always", False, (
                ResourceType.ONLY.value | ResourceType.SERIALIZATION_SUPPORT.value | ResourceType.TYPE_SUPPORT.value)
            )

        """
        generate_support = QuaternaryLogic.from_en_us(args.generate_support)
        del args.generate_support

        resource_types = ResourceType.ANY.value

        if generate_support is QuaternaryLogic.ALWAYS_FALSE:
            resource_types &= ~ResourceType.TYPE_SUPPORT.value
            resource_types &= ~ResourceType.SERIALIZATION_SUPPORT.value

        elif generate_support is QuaternaryLogic.TRUE_IF:
            resource_types = (
                ResourceType.ANY.value | ResourceType.SERIALIZATION_SUPPORT.value | ResourceType.TYPE_SUPPORT.value
            )
        elif generate_support is QuaternaryLogic.ALWAYS_TRUE or generate_support is QuaternaryLogic.TRUE_UNLESS:
            resource_types = (
                ResourceType.ONLY.value | ResourceType.SERIALIZATION_SUPPORT.value | ResourceType.TYPE_SUPPORT.value
            )

        if args.omit_serialization_support:
            resource_types &= ~ResourceType.SERIALIZATION_SUPPORT.value

        return resource_types
