#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2021  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    Command-line for using nunavut and jinja to generate code
    from dsdl definitions.
"""

import argparse
import logging
import os
import pathlib
import sys
import textwrap
import typing


class _LazyVersionAction(argparse._VersionAction):
    """
    Changes argparse._VersionAction so we only load nunavut.version
    if the --version action is requested.
    """

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: typing.Any,
        option_string: typing.Optional[str] = None,
    ) -> None:
        from nunavut.version import __version__

        parser._print_message(__version__, sys.stdout)
        parser.exit()


class _NunavutArgumentParser(argparse.ArgumentParser):
    """
    Specialization of argparse.ArgumentParser to encapsulate inter-argument rules.
    """

    def parse_known_args(
        self, args: typing.Optional[typing.Sequence[str]] = None, namespace: typing.Optional[argparse.Namespace] = None
    ) -> typing.Tuple[argparse.Namespace, typing.List[str]]:
        parsed_args, argv = super().parse_known_args(args, namespace)
        self._post_process_args(parsed_args)
        return (parsed_args, argv)

    def _post_process_args(self, args: argparse.Namespace) -> None:
        """
        Applies rules between different arguments and handles other special cases.
        """
        if args.list_inputs is not None and args.target_language is None and args.output_extension is None:
            # This is a special case where we know we'll never actually use the output extension since
            # we are only listing the input files. All other cases require either an output extension or
            # a valid target language.
            setattr(args, "output_extension", ".tmp")

        if args.omit_serialization_support and args.generate_support == "always":
            self.error(
                textwrap.dedent(
                    """
                Logic error: use of --omit-serialization-support and --generate-support=always

                You cannot both omit serialization support and require generation of support code.
            """
                ).lstrip()
            )


def _make_parser() -> argparse.ArgumentParser:
    """
    Defines the command-line interface. Provided as a separate factory method to
    support sphinx-argparse documentation.
    """

    epilog = textwrap.dedent(
        """

        **Example Usage**::

            # This would include j2 templates for a folder named 'c_jinja'
            # and generate .h files into a directory named 'include' using
            # dsdl root namespaces found under a folder named 'dsdl'.

            nnvg --outdir include --templates c_jinja -e .h dsdl

    """
    )

    parser = _NunavutArgumentParser(
        description="Generate code from UAVCAN DSDL using pydsdl and jinja2",
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("root_namespace", default=".", nargs="?", help="A source directory with DSDL definitions.")

    parser.add_argument(
        "--lookup-dir",
        "-I",
        default=[],
        action="append",
        help=textwrap.dedent(
            """

        List of other namespace directories containing data type definitions that are
        referred to from the target root namespace. For example, if you are reading a
        vendor-specific namespace, the list of lookup directories should always include
        a path to the standard root namespace "uavcan", otherwise the types defined in
        the vendor-specific namespace won't be able to use data types from the standard
        namespace.

        Additional directories can also be specified through the environment variable
        UAVCAN_DSDL_INCLUDE_PATH, where the path entries are
        separated by colons ":"

    """
        ).lstrip(),
    )

    parser.add_argument("--verbose", "-v", action="count", help="verbosity level (-v, -vv)")

    parser.add_argument("--version", action=_LazyVersionAction)

    parser.add_argument("--outdir", "-O", default="nunavut_out", help="output directory")

    parser.add_argument(
        "--templates",
        help=textwrap.dedent(
            """

        Paths to a directory containing templates to use when generating code.

        Templates found under these paths will override the built-in templates for a
        given language. If no target language was provided and no template paths were
        provided then no source will be generated.

    """
        ).lstrip(),
    )

    def extension_type(raw_arg: str) -> str:
        if len(raw_arg) > 0 and not raw_arg.startswith("."):
            return "." + raw_arg
        else:
            return raw_arg

    parser.add_argument(
        "--target-language",
        "-l",
        help=textwrap.dedent(
            """

        Language support to install into the templates.

        If provided then the output extension (--e) can be inferred otherwise the output
        extension must be provided.

    """
        ).lstrip(),
    )

    parser.add_argument(
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

    ext_required = "--list-inputs" not in sys.argv and "--target-language" not in sys.argv and "-l" not in sys.argv
    parser.add_argument(
        "--output-extension",
        "-e",
        type=extension_type,
        required=ext_required,
        help="The extension to use for generated files.",
    )

    parser.add_argument("--dry-run", "-d", action="store_true", help="If True then no files will be generated.")

    parser.add_argument(
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

    """
        ).lstrip(),
    )

    parser.add_argument(
        "--generate-support",
        choices=["always", "never", "as-needed", "only"],
        default="as-needed",
        help=textwrap.dedent(
            """
        Change the criteria used to enable or disable support code generation.

        as-needed (default) - generate support code if serialization is enabled.
        always - always generate support code.
        never - never generate support code.
        only - only generate support code.

    """
        ).lstrip(),
    )

    parser.add_argument(
        "--list-inputs",
        action="store_true",
        help=textwrap.dedent(
            """

        Emit a semicolon-separated list of files.
        (implies --dry-run)
        A list of files that are resolved given input arguments like templates.
        This command is useful for integrating with CMake and other build systems
        that need a list of inputs to determine if a rebuild is necessary.

    """
        ).lstrip(),
    )

    parser.add_argument(
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

    parser.add_argument(
        "--omit-serialization-support",
        "-pod",
        action="store_true",
        help=textwrap.dedent(
            """
        If provided then the types generated will be POD datatypes with no additional logic.
        By default types generated include serialization routines and additional support libraries,
        headers, or methods.

    """
        ).lstrip(),
    )

    parser.add_argument(
        "--namespace-output-stem",
        default=None,
        help="The name of the file generated when --generate-namespace-types is provided.",
    )

    parser.add_argument(
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

    parser.add_argument(
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

    parser.add_argument(
        "--trim-blocks",
        action="store_true",
        help=textwrap.dedent(
            """

        If this is set to True the first newline after a block in a template
        is removed (block, not variable tag!).

    """
        ).lstrip(),
    )

    parser.add_argument(
        "--lstrip-blocks",
        action="store_true",
        help=textwrap.dedent(
            """

        If this is set to True leading spaces and tabs are stripped from the
        start of a line to a block in templates.

    """
        ).lstrip(),
    )

    parser.add_argument(
        "--allow-unregulated-fixed-port-id",
        action="store_true",
        help=textwrap.dedent(
            """

        Do not reject unregulated fixed port identifiers.
        This is a dangerous feature that must not be used unless you understand the
        risks. The background information is provided in the UAVCAN specification.

    """
        ).lstrip(),
    )

    parser.add_argument(
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

    parser.add_argument(
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

    parser.add_argument(
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

    parser.add_argument(
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

    ln_opt_group = parser.add_argument_group(
        "language options",
        description=textwrap.dedent(
            """

        Options passed through to templates as `language_options` on the target language.

        Note that these arguments are passed though without validation, have no effect on the Nunavut
        library, and may or may not be appropriate based on the target language and generator templates
        in use.
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

    return parser


def main() -> int:
    """
    Main entry point for this program.
    """

    #
    # Parse the command-line arguments.
    #
    args = _make_parser().parse_args()

    #
    # Setup Python logging.
    #
    fmt = "%(message)s"
    level = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}.get(args.verbose or 0, logging.DEBUG)
    logging.basicConfig(stream=sys.stderr, level=level, format=fmt)

    logging.info("Running %s using sys.prefix: %s", pathlib.Path(__file__).name, sys.prefix)

    #
    # Parse UAVCAN_DSDL_INCLUDE_PATH
    #
    extra_includes = args.lookup_dir

    try:
        extra_includes_from_env = os.environ["UAVCAN_DSDL_INCLUDE_PATH"].split(":")

        logging.info("Additional include directories from UAVCAN_DSDL_INCLUDE_PATH: %s", str(extra_includes_from_env))
        extra_includes += extra_includes_from_env
    except KeyError:
        pass

    from nunavut.cli.runners import ArgparseRunner

    runner = ArgparseRunner(args, extra_includes)
    runner.setup()
    runner.run()
    return 0
