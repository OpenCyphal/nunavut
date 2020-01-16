#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
Module containing post processing logic to run on generated files.
"""
import abc
import pathlib
import typing
import re
from subprocess import run as subprocess_run  # nosec

# +---------------------------------------------------------------------------+
# | POST PROCESSOR TYPES
# +---------------------------------------------------------------------------+


class PostProcessor(metaclass=abc.ABCMeta):
    """
    Abstract base class for all post processor functors.
    """

    @abc.abstractmethod
    def __call__(self, generated: typing.Any) -> typing.Optional[typing.Any]:
        raise NotImplementedError()


class FilePostProcessor(PostProcessor):
    """
    Abstract base class for all post processor functors that are invoked
    after a file is written.

    All file post processors are callable with the generated file :code:`pathlib.Path`
    as the sole argument.

    Example Usage::

        class ClangFormat(FilePostProcessor):
            \"\"\"
            Invoke clang-format on each file after it is generated.
            \"\"\"
            def __init__(self, clang_format_path: str):
                self._clang_format_args = [clang_format_path, '-i']

            def __call__(self, generated: pathlib.Path) -> pathlib.Path:
                subprocess.run(self._clang_format_args + [str(generated)])
                return generated

        ...

    """

    @abc.abstractmethod
    def __call__(self, generated: pathlib.Path) -> pathlib.Path:
        """
        Performs the post-processing action on the generated file.

        :param pathlib.Path generated: The path of the generated file.
        :returns: A path to the generated file. This may be a modified path for
                  some post-processors.
        """
        raise NotImplementedError()


class LinePostProcessor(PostProcessor):
    """
    Abstract base class for all post processor functors that are invoked
    after a line is generated from a template but before it is written
    to the output file.

    All line post processors are callable with a 2-tuple containing
    the contents of the line as the first item and any newline characters
    as the second item. Note that if there are no newlines generated or
    if the last line generated does not end with a newline then this post-processor
    will be invoked at least once with the second item in the tuple as an
    empty string.

    .. IMPORTANT::
        Providing even a single LinePostProcessor to a generator may have a significant
        impact on generation performance. Some underlying generators (e.g. Jinja)
        are optimized to stream output based on internal buffer sizes and are not
        line oriented. For such implementations nunavut will have to create
        an intermediate line buffer which may impact performance.

    Example Usage::

        class CommentItAllOut(nunavut.postprocessors.LinePostProcessor):

            def __init__(self, open_line_comment: str, close_line_comment: str):
                self._line_comment_pattern = open_line_comment + ' {} ' + close_line_comment

            def __call__(self, line_and_lineend: typing.Tuple[str, str]) -> typing.Tuple[str, str]:
                if len(line_and_lineend[0]) > 0:
                    return (self._line_comment_pattern.format(line_and_lineend[0]), line_and_lineend[1])
                else:
                    return ('', '')

        ...

        c_style = CommentItAllOut('/*', '*/')
        my_generator.generate_all(False, True, [c_style])
    """

    @abc.abstractmethod
    def __call__(self, line_and_lineend: typing.Tuple[str, str]) -> typing.Tuple[str, str]:
        """
        Performs a post-processing action on a generated line of text.

        :param str line_and_lineend: A tuple where the first argument is the
               line generated from the template and the second are any new
               line characters.
        :returns: A tuple with the first item being the content of the line and
                the second being any newline characters to append. It is
                reccommended that the newline characters are treated as opaque
                since these tend to be different on various platforms. Line
                post-processors are encouraged to either pass alone the line
                endings provided as the second item the :code:`line_and_lineend`
                argument or to return an empty string to elide any newline characters
                for this line. Returning a 2-tuple of empty strings is the same
                as eliding the entire line.
        """
        raise NotImplementedError()


# +---------------------------------------------------------------------------+
# | BUILT-IN POST PROCESSORS :: FilePostProcessor
# +---------------------------------------------------------------------------+


class SetFileMode(FilePostProcessor):
    """
    Set the file mode after a file is generated using the :code:`pathlib.Path.chmod(mode)`
    API.

    :param int file_mode:   The file permissions to set for the file.
    """

    def __init__(self, file_mode: int):
        self._file_mode = file_mode

    def __call__(self, generated: pathlib.Path) -> pathlib.Path:
        generated.chmod(self._file_mode)
        return generated


class ExternalProgramEditInPlace(FilePostProcessor):
    """
    Run an external program after generating a file.
    This version expects the program to either not modify the file or to modify it
    in-place (e.g. the functor always returns the same path it was provided).

    :param typing.List[str] command_line: The command and arguments to pass to the
        external program using :code:`subprocess.run`. The file to be processed
        will be appended as the last positional argument in the command before
        it is invoked.

    :param bool check: By default, if the external program returns a non-zero
        exit status a :code:`subprocess.CalledProcessError` is raised. Set
        this argument to :code:`False` to ignore external program errors.
    """

    def __init__(self, command_line: typing.List[str], check: bool = True):
        self._command_line = command_line
        self._check = check

    def __call__(self, generated: pathlib.Path) -> pathlib.Path:
        run_args = self._command_line + [str(generated)]
        subprocess_run(run_args, check=self._check)
        return generated

# +---------------------------------------------------------------------------+
# | BUILT-IN POST PROCESSORS :: LinePostProcessor
# +---------------------------------------------------------------------------+


class TrimTrailingWhitespace(LinePostProcessor):
    """
    Remove all trailing whitespace from each line.

    .. IMPORTANT::
        See performance note in :class:`.LinePostProcessor` documentation. Consider
        invoking a code formatter from a :class:`FilePostProcessor` instead.

    """

    def __init__(self):  # type: ignore
        self._trailing_ws_pattern = re.compile(r'\s+$')

    def __call__(self, line_and_lineend: typing.Tuple[str, str]) -> typing.Tuple[str, str]:
        match_obj = self._trailing_ws_pattern.search(line_and_lineend[0])
        if match_obj is not None:
            return (line_and_lineend[0][:match_obj.start()], line_and_lineend[1])
        else:
            return line_and_lineend


class LimitEmptyLines(LinePostProcessor):
    """
    Set a limit to the number of consecutive empty lines to allow.

    .. IMPORTANT::
        See performance note in :class:`.LinePostProcessor` documentation. Consider
        invoking a code formatter from a :class:`FilePostProcessor` instead.

    """
    def __init__(self, max_empty_lines: int):
        self._max_empty_lines = max_empty_lines
        self._empty_line_count = 0

    def __call__(self, line_and_lineend: typing.Tuple[str, str]) -> typing.Tuple[str, str]:
        if len(line_and_lineend[0]) == 0:
            self._empty_line_count += 1
        else:
            self._empty_line_count = 0

        if self._empty_line_count > self._max_empty_lines:
            return ('', '')
        else:
            return line_and_lineend
