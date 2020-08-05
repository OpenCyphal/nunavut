#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
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


def _run(args: argparse.Namespace, extra_includes: typing.List[str]) -> int:  # noqa: C901
    '''
        Post command-line setup and parsing logic to execute nunavut
        library routines based on input.
    '''
    #
    # nunavut : load module
    #
    import pydsdl
    import nunavut
    import nunavut.jinja
    import nunavut.lang

    def _build_ext_program_postprocessor(program: str, args: argparse.Namespace) \
            -> nunavut.postprocessors.FilePostProcessor:
        subprocess_args = [program]
        if hasattr(args, 'pp_run_program_arg') and args.pp_run_program_arg is not None:
            for program_arg in args.pp_run_program_arg:
                subprocess_args.append(program_arg)
        return nunavut.postprocessors.ExternalProgramEditInPlace(subprocess_args)

    def _build_post_processor_list_from_args(args: argparse.Namespace) \
            -> typing.List[nunavut.postprocessors.PostProcessor]:
        '''
        Return a list of post processors setup based on the provided commandline arguments. This
        list may be empty but the function will not return None.
        '''
        post_processors = []  # type: typing.List[nunavut.postprocessors.PostProcessor]
        if args.pp_trim_trailing_whitespace:
            post_processors.append(nunavut.postprocessors.TrimTrailingWhitespace())
        if hasattr(args, 'pp_max_emptylines') and args.pp_max_emptylines is not None:
            post_processors.append(nunavut.postprocessors.LimitEmptyLines(args.pp_max_emptylines))
        if hasattr(args, 'pp_run_program') and args.pp_run_program is not None:
            post_processors.append(_build_ext_program_postprocessor(args.pp_run_program, args))

        post_processors.append(nunavut.postprocessors.SetFileMode(args.file_mode))

        return post_processors

    #
    # nunavut: language context.
    #
    if args.list_inputs is not None and args.target_language is None and args.output_extension is None:
        # This is a special case where we know we'll never actually use the output extension since
        # we are only listing the input files. All other cases require either an output extension or
        # a valid target language.
        setattr(args, 'output_extension', '.tmp')

    language_context = nunavut.lang.LanguageContext(
        args.target_language,
        args.output_extension,
        args.namespace_output_stem,
        omit_serialization_support_for_target=args.omit_serialization_support)

    #
    # nunavut: inferred target language from extension
    #
    if args.output_extension is not None and language_context.get_target_language() is None:

        inferred_target_language_name = None  # type: typing.Optional[str]
        for name, lang in language_context.get_supported_languages().items():
            extension = lang.get_config_value('extension', None)
            if extension is not None and extension == args.output_extension:
                inferred_target_language_name = name
                break

        if inferred_target_language_name is not None:
            logging.info('Inferring target language %s based on extension "%s".',
                         inferred_target_language_name, args.output_extension)
            language_context = nunavut.lang.LanguageContext(
                inferred_target_language_name,
                args.output_extension,
                args.namespace_output_stem,
                omit_serialization_support_for_target=args.omit_serialization_support)
        elif args.templates is None:
            logging.warn(
                textwrap.dedent('''
                ***********************************************************************
                    No target language was given, none could be inferred from the output extension (-e) argument "%s",
                    and no user templates were specified. You will fail to find templates if you have provided any
                    DSDL types to generate.
                ***********************************************************************
                ''').lstrip(),
                args.output_extension
            )

    #
    # nunavut : parse
    #
    type_map = pydsdl.read_namespace(args.root_namespace, extra_includes)

    root_namespace = nunavut.build_namespace_tree(
        type_map,
        args.root_namespace,
        args.outdir,
        language_context)

    #
    # nunavut : generate
    #

    generator_args = {
        'generate_namespace_types': (nunavut.YesNoDefault.YES
                                     if args.generate_namespace_types
                                     else nunavut.YesNoDefault.DEFAULT),
        'templates_dir': (pathlib.Path(args.templates) if args.templates is not None else None),
        'trim_blocks': args.trim_blocks,
        'lstrip_blocks': args.lstrip_blocks,
        'post_processors': _build_post_processor_list_from_args(args)
    }

    from nunavut.generators import create_generators
    generator, support_generator = create_generators(root_namespace, **generator_args)

    if args.list_outputs:
        for output_path in generator.generate_all(is_dryrun=True):
            sys.stdout.write(str(output_path))
            sys.stdout.write(';')
        for output_path in support_generator.generate_all(is_dryrun=True):
            sys.stdout.write(str(output_path))
            sys.stdout.write(';')
        return 0

    if args.list_inputs:
        for input_path in generator.get_templates():
            sys.stdout.write(str(input_path.resolve()))
            sys.stdout.write(';')
        for input_path in support_generator.get_templates():
            sys.stdout.write(str(input_path.resolve()))
            sys.stdout.write(';')
        if generator.generate_namespace_types:
            for output_type, _ in root_namespace.get_all_types():
                sys.stdout.write(str(output_type.source_file_path))
                sys.stdout.write(';')
        else:
            for output_type, _ in root_namespace.get_all_datatypes():
                sys.stdout.write(str(output_type.source_file_path))
                sys.stdout.write(';')
        return 0

    if args.omit_serialization_support is None or not args.omit_serialization_support:
        support_generator.generate_all(is_dryrun=args.dry_run,
                                       allow_overwrite=not args.no_overwrite)

    generator.generate_all(is_dryrun=args.dry_run,
                           allow_overwrite=not args.no_overwrite)
    return 0


class _LazyVersionAction(argparse._VersionAction):
    '''
    Changes argparse._VersionAction so we only load nunavut.version
    if the --version action is requested.
    '''

    def __call__(self,
                 parser: argparse.ArgumentParser,
                 namespace: argparse.Namespace,
                 values: typing.Any,
                 option_string: typing.Optional[str] = None) -> None:
        from nunavut.version import __version__
        parser._print_message(__version__, sys.stdout)
        parser.exit()


def _make_parser() -> argparse.ArgumentParser:
    """
        Defines the command-line interface. Provided as a separate factory method to
        support sphinx-argparse documentation.
    """

    epilog = textwrap.dedent('''

        **Example Usage**::

            # This would include j2 templates for a folder named 'c_jinja'
            # and generate .h files into a directory named 'include' using
            # dsdl root namespaces found under a folder named 'dsdl'.

            nnvg --outdir include --templates c_jinja -e .h dsdl

    ''')

    parser = argparse.ArgumentParser(
        description='Generate code from UAVCAN DSDL using pydsdl and jinja2',
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('root_namespace',
                        help='A source directory with DSDL definitions.')

    parser.add_argument('--lookup-dir', '-I', default=[], action='append',
                        help=textwrap.dedent('''

        List of other namespace directories containing data type definitions that are
        referred to from the target root namespace. For example, if you are reading a
        vendor-specific namespace, the list of lookup directories should always include
        a path to the standard root namespace "uavcan", otherwise the types defined in
        the vendor-specific namespace won't be able to use data types from the standard
        namespace.

        Additional directories can also be specified through the environment variable
        UAVCAN_DSDL_INCLUDE_PATH, where the path entries are
        separated by colons ":"

    ''').lstrip())

    parser.add_argument('--verbose', '-v', action='count',
                        help='verbosity level (-v, -vv)')

    parser.add_argument('--version', action=_LazyVersionAction)

    parser.add_argument(
        '--outdir', '-O', default='nunavut_out', help='output directory')

    parser.add_argument('--templates',
                        help=textwrap.dedent('''

        Paths to a directory containing templates to use when generating code.

        Templates found under these paths will override the built-in templates for a
        given language. If no target language was provided and no template paths were
        provided then no source will be generated.

    ''').lstrip())

    def extension_type(raw_arg: str) -> str:
        if len(raw_arg) > 0 and not raw_arg.startswith('.'):
            return '.' + raw_arg
        else:
            return raw_arg

    parser.add_argument('--target-language', '-l',
                        help=textwrap.dedent('''

        Language support to install into the templates.

        If provided then the output extension (--e) can be inferred otherwise the output
        extension must be provided.

    ''').lstrip())

    ext_required = '--list-inputs' not in sys.argv and '--target-language' not in sys.argv and '-l' not in sys.argv
    parser.add_argument('--output-extension', '-e', type=extension_type,
                        required=ext_required,
                        help='The extension to use for generated files.')

    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='If True then no files will be generated.')

    parser.add_argument('--list-outputs', action='store_true',
                        help=textwrap.dedent('''
        Emit a semicolon-separated list of files.
        (implies --dry-run)
        Emits files that would be generated if invoked without --dry-run.
        This command is useful for integrating with CMake and other build
        systems that need a list of targets to determine if a rebuild is
        necessary.

    ''').lstrip())

    parser.add_argument('--list-inputs', action='store_true',
                        help=textwrap.dedent('''

        Emit a semicolon-separated list of files.
        (implies --dry-run)
        A list of files that are resolved given input arguments like templates.
        This command is useful for integrating with CMake and other build systems
        that need a list of inputs to determine if a rebuild is necessary.

    ''').lstrip())

    parser.add_argument('--generate-namespace-types',
                        action='store_true',
                        help=textwrap.dedent('''
        If enabled this script will generate source for namespaces.
        All namespaces including and under the root namespace will be treated as a
        pseudo-type and the appropriate template will be used. The generator will
        first look for a template with the stem "Namespace" and will then use the
        "Any" template if that is available. The name of the output file will be
        the default value for the --namespace-output-stem argument and can be
        changed using that argument.

    ''').lstrip())

    parser.add_argument('--omit-serialization-support',
                        '-pod',
                        action='store_true',
                        help=textwrap.dedent('''
        If provided then the types generated will be POD datatypes with no additional logic.
        By default types generated include serialization routines and additional support libraries,
        headers, or methods.

    ''').lstrip())

    parser.add_argument('--namespace-output-stem',
                        default='Namespace',
                        help='The name of the file generated when --generate-namespace-types is provided.')

    parser.add_argument('--no-overwrite',
                        action='store_true',
                        help=textwrap.dedent('''

        By default, generated files will be silently overwritten by
        subsequent invocations of the generator. If this argument is specified an
        error will be raised instead preventing overwrites.

    ''').lstrip())

    parser.add_argument('--file-mode',
                        default=0o444,
                        type=lambda value: int(value, 0),
                        help=textwrap.dedent('''

        The filemode each generated file is set to after it is created.
        Note that this value is interpreted using python auto base detection.
        Because of this, to provide an octal value, you'll need to prefix your
        literal with '0o' (e.g. --file-mode 0o664).

    ''').lstrip())

    parser.add_argument('--trim-blocks',
                        action='store_true',
                        help=textwrap.dedent('''

        If this is set to True the first newline after a block in a template
        is removed (block, not variable tag!).

    ''').lstrip())

    parser.add_argument('--lstrip-blocks',
                        action='store_true',
                        help=textwrap.dedent('''

        If this is set to True leading spaces and tabs are stripped from the
        start of a line to a block in templates.

    ''').lstrip())

    parser.add_argument('--pp-max-emptylines',
                        type=int,
                        help=textwrap.dedent('''

        If provided this will suppress generation of additional consecutive
        empty lines beyond the limit set by this argument.

        Note that this will insert a line post-processor which may reduce
        performance. Consider using a code formatter on the generated output
        to enforce whitespace rules instead.

    ''').lstrip())

    parser.add_argument('--pp-trim-trailing-whitespace',
                        action='store_true',
                        help=textwrap.dedent('''

        Enables a line post-processor that will elide all whitespace at the
        end of each line.

        Note that this will insert a line post-processor which may reduce
        performance. Consider using a code formatter on the generated output
        to enforce whitespace rules instead.

    ''').lstrip())

    parser.add_argument('-pp-rp', '--pp-run-program',
                        help=textwrap.dedent('''

        Runs a program after each file is generated but before the file is
        set to read-only.

        example ::

            # invokes clang-format with the "in-place" argument on each file after it is
            # generated.

            nnvg --outdir include --templates c_jinja -e .h -pp-rp clang-format -pp-rpa=-i dsdl

    ''').lstrip())

    parser.add_argument('-pp-rpa', '--pp-run-program-arg',
                        action='append',
                        help=textwrap.dedent('''

        Additional arguments to provide to the program specified by --pp-run-program.
        The last argument will always be the path to the generated file.

    ''').lstrip())

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
    fmt = '%(message)s'
    level = {0: logging.WARNING, 1: logging.INFO,
             2: logging.DEBUG}.get(args.verbose or 0, logging.DEBUG)
    logging.basicConfig(stream=sys.stderr, level=level, format=fmt)

    logging.info('Running %s using sys.prefix: %s',
                 pathlib.Path(__file__).name, sys.prefix)

    #
    # Parse UAVCAN_DSDL_INCLUDE_PATH
    #
    extra_includes = args.lookup_dir

    try:
        extra_includes_from_env = os.environ['UAVCAN_DSDL_INCLUDE_PATH'].split(':')

        logging.info('Additional include directories from UAVCAN_DSDL_INCLUDE_PATH: %s',
                     str(extra_includes_from_env))
        extra_includes += extra_includes_from_env
    except KeyError:
        pass

    return _run(args, extra_includes)
