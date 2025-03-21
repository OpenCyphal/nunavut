#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Filters for generating javascript. All filters in this
module will be available in the template's global namespace as ``ln.js``.
"""


def filter_to_true_or_false(value: str) -> str:
    """
    Jinja filter that takes in a value, casts it to a bool and
    emits ``true`` or ``false``.

    The following example assumes ``deprecated`` as an integer ``1``.

    Example::

        "deprecated": {{ T.deprecated | ln.js.to_true_or_false }},

    Results Example::

        "deprecated": false,

    :param str value: The template value to evaluate.
    :return: ``true`` or ``false``
    """
    return "true" if bool(value) else "false"
