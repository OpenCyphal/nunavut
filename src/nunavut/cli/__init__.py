#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Command-line for using nunavut and jinja to generate code
from dsdl definitions.
"""

import argparse
import sys
import textwrap
from pathlib import Path
from typing import Any, Optional, Type, TypeVar, cast


class _LazyVersionAction(argparse._VersionAction):
    """
    Changes argparse._VersionAction so we only load nunavut.version
    if the --version action is requested.
    """

    # pylint: disable=protected-access

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: Optional[str] = None,
    ) -> None:
        # pylint: disable=import-outside-toplevel
        from nunavut._version import __version__

        parser._print_message(__version__, sys.stdout)
        parser.exit()


ParserT = TypeVar("ParserT")
"""
Type variable for the concrete parser to create.
"""


def _make_parser(parser_type: Type[ParserT]) -> ParserT:
    """
    Defines the command-line interface. Provided as a separate factory method to
    support sphinx-argparse documentation.

    :param parser_type: The type of parser to create. This should be a subclass of argparse.ArgumentParser
    :return: A parser instance with the command-line interface defined.
    :raises ValueError: If parser_type is not a subclass of argparse

    .. invisible-code-block: python

        from nunavut.cli import _make_parser
        from pytest import raises

        with raises(ValueError):
            _make_parser(str)

    """

    epilog = textwrap.dedent(
        """

        Copyright (C) OpenCyphal Development Team  <opencyphal.org>
        Copyright Amazon.com Inc. or its affiliates.
        Released under SPDX-License-Identifier: MIT

        **Example Usage** ::

            # This would include j2 templates for a folder named 'c_jinja'
            # and generate .h files into a directory named 'include' for
            # the uavcan.node.Heartbeat.1.0 data type and its dependencies

            nnvg --outdir include --templates c_jinja -e .h dsdl/uavcan:node/7509.Heartbeat.1.0.dsdl

        ᓄᓇᕗᑦ
    """
    )

    if not issubclass(parser_type, argparse.ArgumentParser):
        raise ValueError("parser_type must be a subclass of argparse.ArgumentParser")

    parser = parser_type(
        description="Generate code from Cyphal DSDL using pydsdl and jinja2",
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "target_files_or_root_namespace",
        nargs="*",
        help=textwrap.dedent(
            """

        One or more dsdl files to generate from.

        All dependent types found in the target dsdl files will be generated and must be available
        either as another target or as a dsdl file under one of the --lookup-dir directories.

        A --lookup-dir argument for each unique root path among the list of files is required if
        not using the colon syntax.

        Colon Syntax
        ------------

            The standard syntax allows the path to the root to be specified at the same
            time as the type ::

                path/to/root:name/space/Type.1.0.dsdl

            This also adds the path to a list of valid paths. You can continue to specify
            it (duplicates are ignored) or you can specify it once ::

                path/to/root:name/space/Type.1.0.dsdl name/space/Type.1.0.dsdl

                ...is the same as...

                path/to/root:name/space/Type.1.0.dsdl path/to/root:name/space/Type.1.0.dsdl

        Globular Expansion
        ------------------

            Any target paths that are folders will be considered to be root namespaces. nnvg
            will then search for all dsdl files under that folder and generate target paths
            for all .dsdl files found. To disable this behavior use the --no-target-namespaces
            argument which will cause an error if a folder is provided as a target.

    """
        ).lstrip(),
    )

    parser.add_argument(
        "--no-target-namespaces",
        action="store_true",
        help=textwrap.dedent(
            """

        If provided then all target paths must be to individual DSDL files and not folders. If
        set and a folder is provided as a target an error will be raised.

        Normally, if a folder is provided as a target path, nnvg will search for all dsdl files
        under that folder and generate target paths for all .dsdl files found using the
        path itself as the root namespace.

        see target_files_or_root_namespace for more information.
    """
        ).lstrip(),
    )

    parser.add_argument(
        "--lookup-dir",
        "-I",
        action="append",
        help=textwrap.dedent(
            """

        List of other namespace directories containing data type definitions that are referred to
        from the target root namespace. For example, if you are reading a vendor-specific namespace,
        the list of lookup directories should always include a path to the standard root namespace
        "uavcan", otherwise the types defined in the vendor-specific namespace won't be able to use
        data types from the standard namespace.

        For a given target set of dsdl files this argument is required to specify a set of valid
        paths to or folder names of root namespaces. For example ::

            nnvg types/animals/felines/Tabby.1.0.dsdl types/animals/canines/Boxer.1.0.dsdl

        will fail unless the path describing the root is provided ::

            nnvg --lookup-dir types/animals types/animals/cats/Tabby.1.0.dsdl \\
                                            types/animals/dogs/Boxer.1.0.dsdl

        If multiple roots are targeted then each root path will need to be enabled ::

            nnvg -I types/animals -I types/plants types/animals/cats/Tabby.1.0.dsdl \\
                                                  types/plants/trees/Fir.1.0.dsdl


        For target files this argument is required to specify a set of valid paths to or folder
        names of root namespaces, however; an additional syntax is supported where the root for a
        target file can be specified as part of the target path using a colon to separate the two ::

            nnvg types/animals:cats/Tabby.1.0.dsdl types/plants:trees/Fir.1.0.dsdl


        This is the recommended syntax as it allows all target files to be specified as relative
        paths and reserves this argument to specify concrete lookup directories ::

            nnvg --lookup-dir /path/to/types types/animals:mammals/cats/Tabby.1.0.dsdl \\
                                             types/plants:trees/conifers/Fir.1.0.dsdl

        Additional directories can also be specified through an environment variable
        DSDL_INCLUDE_PATH where the path entries are separated by colons ":" on posix systems and
        ";" on Windows ::

            DSDL_INCLUDE_PATH=/path/to/types/animals:/path/to/types/plants \\
                nnvg animals:mammals/cats/Tabby.1.0.dsdl \\
                     plants:trees/conifers/Fir.1.0.dsdl

        CYPHAL_PATH is similarly used (and formatted) but the paths in this variable are listed and
        each folder under each path will be a lookup directory ::

            CYPHAL_PATH=/path/to/types nnvg animals:mammals/cats/Tabby.1.0.dsdl \\
                                            plants:trees/conifers/Fir.1.0.dsdl

    """
        ).lstrip(),
    )

    parser.add_argument("--outdir", "-O", default="nunavut_out", help="output directory")

    parser.add_argument(
        "--target-language",
        "-l",
        help=textwrap.dedent(
            """

        Language support to install into the templates.

        If provided then the output extension (-e) can be inferred otherwise the output
        extension must be provided.

    """
        ).lstrip(),
    )

    # +-----------------------------------------------------------------------+
    # | Extended Generation Options
    # +-----------------------------------------------------------------------+

    extended_group = parser.add_argument_group(
        "extended options",
        description=textwrap.dedent(
            """

        Additional options to control output generation.

    """
        ).lstrip(),
    )

    extended_group.add_argument(
        "--templates-dir",
        "--templates",
        type=Path,
        help=textwrap.dedent(
            """

        Paths to a directory containing templates to use when generating code.

        Templates found under these paths will override the built-in templates for a
        given language.

    """
        ).lstrip(),
    )

    extended_group.add_argument(
        "--support-templates-dir",
        "--support-templates",
        type=Path,
        help=textwrap.dedent(
            """

        Paths to a directory containing templates to use when generating support code.

        Templates found under these paths will override the built-in support templates for a
        given language.

    """
        ).lstrip(),
    )

    extended_group.add_argument(
        "--fallback-to-builtin-templates",
        "-tfb",
        action="store_true",
        help=textwrap.dedent(
            """

        Normally, if providing a custom templates directory, the built-in templates are not
        searched for. This option will cause the built-in templates to be searched for if a
        template is not found in the custom templates directory first.

    """
        ).lstrip(),
    )

    extended_group.add_argument(
        "--index-file",
        type=Path,
        action="append",
        help=textwrap.dedent(
            """

        Index-files are generated from special templates that are given access to all types in
        all namespaces. This is useful for generating files that are not specific to a single
        type like dependency files, manifests, or aggregate headers.

        The template lookup paths are the same as for DSDL types but the template is selected
        based on the filename of the all-file first and falls back to `index.j2` if no specific
        template is found. Note that the DSDL type hierarchy will be searched first so you
        cannot name your index-file the same as a DSDL data type like `StructureType.j2`.

        Example ::

            # looks for all_types.j2 in the c_jinja template directory and generates
            # generated/include/all_types.h from all types in all DSDL namespaces.
            nnvg --index-file all_types.h --outdir generated/include --templates c_jinja \
                path/to/types/animal:cat.1.0.dsdl \
                path/to/types/animal:dog.1.0.dsdl

            # looks for manifest.j2 in the json_jinja template directory and generates
            # generated/include/manifest.json from all types in all DSDL namespaces.
            nnvg --index-file include/manifest.json --outdir generated --templates json_jinja \
                path/to/types/animal:cat.1.0.dsdl \
                path/to/types/animal:dog.1.0.dsdl

    """
        ).lstrip(),
    )

    extended_group.add_argument(
        "--include-experimental-languages",
        "--experimental-languages",
        "-Xlang",
        action="store_true",
        help=textwrap.dedent(
            """

        Activate languages with unstable, experimental support.

        By default, target languages where support is not finalized are not
        enabled when running nunavut, to make it clear that the code output
        may change in a non-backwards-compatible way in future versions, or
        that it might not even work yet.

    """
        ).lstrip(),
    )

    def extension_type(raw_arg: str) -> str:
        if len(raw_arg) > 0 and not raw_arg.startswith("."):
            return "." + raw_arg
        else:
            return raw_arg

    extended_group.add_argument(
        "--output-extension",
        "-e",
        type=extension_type,
        help=textwrap.dedent(
            """
        The output extension for generated files. If target language is provided an extension is
        inferred based on language configuration. This option allows overriding this inference.

        Note that, if --target-language is omitted and this argument is provided the program
        will attempt to infer the language based on the file extension. This may lead to unexpected
        results (e.g. `--output-extension .h` generating C instead of C++).

        If a dot (.) is omitted one will be added, therefore; `-e h` and `-e .h` will both result
        in an extension of `.h`.

    """
        ).lstrip(),
    )

    extended_group.add_argument(
        "--generate-support",
        choices=["always", "never", "as-needed", "only"],
        default="as-needed",
        help=textwrap.dedent(
            """
        Change the criteria used to enable or disable support code generation.

        as-needed (default) - generate support if it is needed.
        always - always generate support code.
        never - never generate support code.
        only - only generate support code.

        Note that serialization logic is only one type of support code. This option covers all
        types of support code. Where `--omit-serialization-support` is set different types of
        support code may still be generated unless this option is set to `never`.

    """
        ).lstrip(),
    )

    extended_group.add_argument(
        "--generate-namespace-types",
        action="store_true",
        help=textwrap.dedent(
            """
        If enabled this script will generate source for namespaces.
        All namespaces including and under the root namespace will be treated as a
        pseudo-type and the appropriate template will be used. The generator will
        first look for a template with the stem "Namespace" and will then use the
        "Any" template if that is available. The name of the output file will be
        the default value for the --namespace-output-stem argument and can be
        changed using that argument.

    """
        ).lstrip(),
    )

    extended_group.add_argument(
        "--omit-serialization-support",
        "-pod",
        action="store_true",
        help=textwrap.dedent(
            """
        If provided then the types generated will be POD datatypes with no additional logic.
        By default types generated include serialization routines and additional support libraries,
        headers, or methods as needed. These additional support artifacts can be suppressed using
        the `--generate-support` option.

    """
        ).lstrip(),
    )

    extended_group.add_argument(
        "--namespace-output-stem",
        help="The name of the file generated when --generate-namespace-types is provided.",
    )

    extended_group.add_argument(
        "--no-overwrite",
        action="store_true",
        help=textwrap.dedent(
            """

        By default, generated files will be silently overwritten by
        subsequent invocations of the generator. If this argument is specified an
        error will be raised instead preventing overwrites.

    """
        ).lstrip(),
    )

    extended_group.add_argument(
        "--file-mode",
        default=0o444,
        type=lambda value: int(value, 0),
        help=textwrap.dedent(
            """

        The file-mode each generated file is set to after it is created.
        Note that this value is interpreted using python auto base detection.
        Because of this, to provide an octal value, you'll need to prefix your
        literal with '0o' (e.g. --file-mode 0o664).

    """
        ).lstrip(),
    )

    extended_group.add_argument(
        "--allow-unregulated-fixed-port-id",
        action="store_true",
        help=textwrap.dedent(
            """

        Do not reject unregulated fixed port identifiers.
        This is a dangerous feature that must not be used unless you understand the
        risks. The background information is provided in the Cyphal specification.

    """
        ).lstrip(),
    )

    extended_group.add_argument(
        "--embed-auditing-info",
        action="store_true",
        help=textwrap.dedent(
            """

        If set, generators are instructed to add additional information in the form of
        language-specific comments or meta-data to use when auditing source code generated by
        Nunavut. This data may change based on the environment in use which may interfere with
        the reproducibility of your builds. For example, paths to input files used to generate
        a type may be included with this option where these paths will be different depending
        on the server used to run nnvg.

    """
        ).lstrip(),
    )

    extended_group.add_argument(
        "--omit-dependencies",
        action="store_true",
        help=textwrap.dedent(
            """

        Disables the generation of dependent types. This is useful when setting up build
        rules for a project where the dependent types are generated separately.

    """
        ).lstrip(),
    )

    # +-----------------------------------------------------------------------+
    # | Operation Options
    # +-----------------------------------------------------------------------+

    run_mode_group = parser.add_argument_group(
        "run mode options",
        description=textwrap.dedent(
            """

        Options that control the operation mode of the script.

    """
        ).lstrip(),
    )

    run_mode_group.add_argument("--verbose", "-v", action="count", help="verbosity level (-v, -vv)")

    run_mode_group.add_argument("--version", action=_LazyVersionAction)

    run_mode_group.add_argument("--dry-run", "-d", action="store_true", help="If True then no files will be generated.")

    run_mode_group.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=0,
        help=textwrap.dedent(
            """

        Limits the number of subprocesses nnvg can use to parallelize type discovery
        and code generation.

        If set to 0 then the number of jobs will be set to the number of CPUs available
        on the system.

        If set to 1 then no subprocesses will be used and all work will be done in th
        main process.

    """
        ).lstrip(),
    )

    run_mode_group.add_argument(
        "--list-outputs",
        action="store_true",
        help=textwrap.dedent(
            """
        Emit a semicolon-separated list of files.
        (implies --dry-run)
        Emits files that would be generated if invoked without --dry-run.
        This command is useful for integrating with CMake and other build
        systems that need a list of targets to determine if a rebuild is
        necessary.

        If used with --list-inputs the list of inputs will be emitted first followed
        by the list of outputs. A single empty value will separate the two lists when
        using value-delimited formats. Use --list-format to control the output format
        including using json to avoid the need for an empty-value delimiter.

    """
        ).lstrip(),
    )

    run_mode_group.add_argument(
        "--list-inputs",
        action="store_true",
        help=textwrap.dedent(
            """

        Emit a semicolon-separated list of files.
        (implies --dry-run)
        A list of files that are resolved given input arguments like templates.
        This command is useful for integrating with CMake and other build systems
        that need a list of inputs to determine if a rebuild is necessary.

        If used with --list-outputs the list of inputs will be emitted first followed
        by the list of outputs. A single empty value will separate the two lists. Use
        --list-format to control the output format including using json to avoid the
        need for an empty-value delimiter.

    """
        ).lstrip(),
    )

    run_mode_group.add_argument(
        "--list-configuration",
        "-lc",
        action="store_true",
        help=textwrap.dedent(
            """

        Lists all configuration values resolved for the given arguments. Unlike --list-inputs
        and --list-outputs this command does *not* imply --dry-run but can be used in conjunction
        with it.

        This option is only available if --list-format is set to json.

    """
        ).lstrip(),
    )

    run_mode_group.add_argument(
        "--list-format",
        default="scsv",
        choices=["csv", "scsv", "json", "json-pretty"],
        help=textwrap.dedent(
            """

        For commands that emit lists of files this option controls the format of the output.

        csv         - comma separated values
        scsv        - semicolon separated values
        json        - json formatted results
        json-pretty - json formatted results with indentation

    """
        ).lstrip(),
    )

    run_mode_group.add_argument(
        "--list-to-file",
        type=Path,
        help=textwrap.dedent(
            """

        If provided then the output of --list-outputs, --list-inputs, or --list-configuration
        will also be written to the file specified. If the file exists it will be overwritten.
        This utf-8-encoded file will be written in the format specified by --list-format even
        if --dry-run is set.

    """
        ).lstrip(),
    )

    # +-----------------------------------------------------------------------+
    # | Post-Processing Options
    # +-----------------------------------------------------------------------+

    ln_pp_group = parser.add_argument_group(
        "post-processing options",
        description=textwrap.dedent(
            """

        This options are all deprecated and will be removed in a future release.

    """
        ).lstrip(),
    )

    ln_pp_group.add_argument(
        "--trim-blocks",
        action="store_true",
        help=textwrap.dedent(
            """

        If this is set to True the first newline after a block in a template
        is removed (block, not variable tag!).

    """
        ).lstrip(),
    )

    ln_pp_group.add_argument(
        "--lstrip-blocks",
        action="store_true",
        help=textwrap.dedent(
            """

        If this is set to True leading spaces and tabs are stripped from the
        start of a line to a block in templates.

    """
        ).lstrip(),
    )

    ln_pp_group.add_argument(
        "--pp-max-emptylines",
        type=int,
        help=textwrap.dedent(
            """

        If provided this will suppress generation of additional consecutive
        empty lines beyond the limit set by this argument.

        Note that this will insert a line post-processor which may reduce
        performance. Consider using a code formatter on the generated output
        to enforce whitespace rules instead.

    """
        ).lstrip(),
    )

    ln_pp_group.add_argument(
        "--pp-trim-trailing-whitespace",
        action="store_true",
        help=textwrap.dedent(
            """

        Enables a line post-processor that will elide all whitespace at the
        end of each line.

        Note that this will insert a line post-processor which may reduce
        performance. Consider using a code formatter on the generated output
        to enforce whitespace rules instead.

    """
        ).lstrip(),
    )

    ln_pp_group.add_argument(
        "-pp-rp",
        "--pp-run-program",
        help=textwrap.dedent(
            """

        Runs a program after each file is generated but before the file is
        set to read-only.

        example ::

            # invokes clang-format with the "in-place" argument on each file after it is
            # generated.

            nnvg --outdir include --templates c_jinja -e .h -pp-rp clang-format -pp-rpa=-i dsdl

    """
        ).lstrip(),
    )

    ln_pp_group.add_argument(
        "-pp-rpa",
        "--pp-run-program-arg",
        action="append",
        help=textwrap.dedent(
            """

        Additional arguments to provide to the program specified by --pp-run-program.
        The last argument will always be the path to the generated file.

    """
        ).lstrip(),
    )

    # +-----------------------------------------------------------------------+
    # | Language Options
    # +-----------------------------------------------------------------------+
    ln_opt_group = parser.add_argument_group(
        "language options",
        description=textwrap.dedent(
            """

        Options passed through to templates as `options` on the target language.

        Note that these arguments are passed though without validation, have no effect on the
        Nunavut library, and may or may not be appropriate based on the target language and
        generator templates in use.
    """
        ).lstrip(),
    )

    ln_opt_group.add_argument(
        "--target-endianness",
        choices=["any", "big", "little"],
        help=textwrap.dedent(
            """

        Specify the endianness of the target hardware. This allows serialization
        logic to be optimized for different CPU architectures.

    """
        ).lstrip(),
    )

    ln_opt_group.add_argument(
        "--omit-float-serialization-support",
        action="store_true",
        help=textwrap.dedent(
            """

        Instruct support header generators to omit support for floating point operations
        in serialization routines. This will result in errors if floating point types are used,
        however; if you are working on a platform without IEEE754 support and do not use floating
        point types in your message definitions this option will avoid dead code or compiler
        errors in generated serialization logic.

    """
        ).lstrip(),
    )

    ln_opt_group.add_argument(
        "--enable-serialization-asserts",
        action="store_true",
        help=textwrap.dedent(
            """

        Instruct support header generators to generate language-specific assert statements as part
        of serialization routines. By default the serialization logic generated may make assumptions
        based on documented requirements for calling logic that could expose a system to undefined
        behavior. The alternative, for languages that do not support exception handling, is to
        use assertions designed to halt a program rather than execute undefined logic.

    """
        ).lstrip(),
    )

    ln_opt_group.add_argument(
        "--enable-override-variable-array-capacity",
        action="store_true",
        help=textwrap.dedent(
            """

        Instruct support header generators to add the possibility to override max capacity of a
        variable length array in serialization routines. This option will disable serialization
        buffer checks and add conditional compilation statements which violates MISRA.

    """
        ).lstrip(),
    )

    ln_opt_group.add_argument(
        "--language-standard",
        "-std",
        choices=["c11", "c++14", "cetl++14-17", "c++17", "c++17-pmr", "c++20", "c++20-pmr"],
        help=textwrap.dedent(
            """

        For language generators that support different standards of their core language this option
        can be used to optimize the output. For example, C templates may generate slightly different
        code for the the c99 standard then for c11. For available support in Nunavut see the
        documentation for built-in templates
        (https://nunavut.readthedocs.io/en/latest/docs/templates.html#built-in-template-guide).

    """
        ).lstrip(),
    )

    ln_opt_group.add_argument(
        "--configuration",
        "-c",
        nargs="*",
        type=Path,
        help=textwrap.dedent(
            """

        There is a set of built-in configuration for Nunavut that provides default values for known
        languages as documented `in the template guide
        <https://nunavut.readthedocs.io/en/latest/docs/templates.html#language-options>`_. This
        argument lets you specify an override configuration json file where any value provided will
        override the built-in defaults. To see the built-in defaults you can use::

            nnvg --list-configuration --list-format json-pretty > built-in.json

        This will generate a json file with all the built-in configuration values as the "configuration.sections"
        value. If you have `jq` installed you can use this to filter the output to just the configuration::

            nnvg --list-configuration --list-format json-pretty | jq '.configuration.sections' > my-config.json

        Then you can edit the my-config.json file to provide overrides for the built-in defaults and use
        this option to provide the file to nnvg::

            nnvg --configuration my-config.json ...


        Also see ``--list-to-file`` which writes this configuration to disk if combined with ``--list-configuration``.

    """
        ).lstrip(),
    )

    return cast(ParserT, parser)


def make_argparse_parser() -> argparse.ArgumentParser:
    """
    Defines the command-line interface using generic argparse.ArgumentParser.
    This should be used for documentation and tab-completion tools.
    """
    return _make_parser(argparse.ArgumentParser)
