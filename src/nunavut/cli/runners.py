#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
    Objects that utilize command-line inputs to run a program using Nunavut.
"""

import argparse
import itertools
import json
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional

from .._generators import basic_language_context_builder_from_args, generate_all
from .._utilities import ResourceType
from ..lang import LanguageContext


class StandardArgparseRunner:
    """
    Runner based on Python argparse. This class delegates most of the generation logic to the :func:`generate_all`
    function providing only additional console output on top of that method's functionality.

    :param argparse.Namespace args: The command line arguments.
    """

    def __init__(self, args: argparse.Namespace):
        self._args = args

    @property
    def args(self) -> argparse.Namespace:
        """
        Access to the arguments this object interprets.
        """
        return self._args

    def run(self) -> int:
        """
        Perform actions defined by the arguments this object was created with. This may generate outputs where
        the arguments have requested this action.
        """
        if self._args.list_configuration:
            self.list_configuration(basic_language_context_builder_from_args(**vars(self.args)).create())

        result = generate_all(**vars(self.args))

        if self._args.list_outputs:
            file_iterators = []
            if self._args.resource_types != ResourceType.NONE.value:
                file_iterators.append(result.support_files)
            if (self._args.resource_types & ResourceType.ONLY.value) == 0:
                file_iterators.append(result.generated_files)
            self.stdout_lister(itertools.chain(*file_iterators), lambda p: str(p.resolve()), end="")

        elif self._args.list_inputs:
            input_dsdl = set(result.template_files)
            for _, target_data in result.generator_targets.items():
                input_dsdl.add(target_data.definition.source_file_path)
                input_dsdl.update({d.source_file_path for d in target_data.input_types})
            self.stdout_lister(input_dsdl, lambda p: str(p.resolve()), end="")

        return 0

    def list_configuration(self, lctx: LanguageContext) -> None:
        """
        List the configuration of the language context to a json file.
        """

        config: Dict[str, Any] = {}
        config["target_language"] = lctx.get_target_language().name
        config["sections"] = lctx.config.sections()

        json.dump(config, sys.stdout, ensure_ascii=False)

    def stdout_lister(
        self,
        things_to_list: Iterable[Any],
        to_string: Callable[[Any], str],
        sep: str = ";",
        end: str = ";",
    ) -> None:
        """
        Write a list of things to stdout.

        :param Iterable[Any] things_to_list: The things to list.
        :param Callable[[Any], str] to_string: A function that converts a thing to a string.
        :param str sep: The separator to use between things.
        :param str end: The character to print at the end.
        """
        first = True
        for thing in things_to_list:
            if first:
                first = False
            else:
                sys.stdout.write(sep)
            sys.stdout.write(to_string(thing))
        if not first:
            sys.stdout.write(end)


# --[ MAIN ]-----------------------------------------------------------------------------------------------------------
def main(command_line_args: Optional[Any] = None) -> int:
    """
    Main entry point for command-line scripts.
    """

    from . import _make_parser  # pylint: disable=import-outside-toplevel
    from .parsers import NunavutArgumentParser  # pylint: disable=import-outside-toplevel

    #
    # Parse the command-line arguments.
    #
    parser = _make_parser(NunavutArgumentParser)

    try:
        import argcomplete  # pylint: disable=import-outside-toplevel

        argcomplete.autocomplete(parser)
    except ImportError:
        logging.debug("argcomplete not installed, skipping autocomplete")

    args = parser.parse_args(args=command_line_args)

    #
    # Setup Python logging.
    #
    fmt = "%(message)s"
    level = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}.get(args.verbose or 0, logging.DEBUG)
    logging.basicConfig(stream=sys.stderr, level=level, format=fmt)

    logging.info("Running %s using sys.prefix: %s", Path(__file__).name, sys.prefix)

    return StandardArgparseRunner(args).run()
