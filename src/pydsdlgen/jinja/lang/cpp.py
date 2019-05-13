#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
    jinja-based filters for generating C++. All filters in this
    module will be available in the template's global namespace as ``cpp``.
"""

import io
import os


def filter_open_namespace(full_namespace: str, bracket_on_next_line: bool = True) -> str:
    """
        Emits c++ opening namspace syntax parsed from a pydsdl "full_namespace",
        dot-seperated  value.

        The following example assumes a string "uavcan.foo" as ``full_namespace``.

        Example::

            {{T.full_namespace | cpp.open_namespace}}

        Result Example::

            namespace uavcan
            {
            namespace foo
            {

        :param str full_namespace: A dot-seperated namespace string.
        :param bool bracket_on_next_line: If True (the default) then the opening
            brackets are placed on a newline after the namespace keyword.

        :returns: C++ namespace declarations with opening brackets.
    """

    with io.StringIO() as content:
        for name in full_namespace.split('.'):
            content.write('namespace ')
            content.write(name)
            if bracket_on_next_line:
                content.write(os.linesep)
            else:
                content.write(' ')
            content.write('{')
            content.write(os.linesep)
        return content.getvalue()


def filter_close_namespace(full_namespace: str, omit_comments: bool = False) -> str:
    """
        Emits c++ closing namspace syntax parsed from a pydsdl "full_namespace",
        dot-seperated  value.

        The following example assumes a string "uavcan.foo" as ``full_namespace``.

        Example::

            {{T.full_namespace | cpp.close_namespace}}

        Result Example::

            } // namespace foo
            } // namespace uavcan

        :param str full_namespace: A dot-seperated namespace string.
        :param omit_comments: If True then the comments following the closing
                              bracket are omitted.

        :returns: C++ namespace declarations with opening brackets.
    """
    with io.StringIO() as content:
        for name in reversed(full_namespace.split('.')):
            content.write('}')
            if not omit_comments:
                content.write(' // ')
                content.write(name)
            content.write(os.linesep)
        return content.getvalue()
