#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Tests for Nunavut's auto-indent extension to the embedded Jinja (``{%* ... %}`` and ``{{* ... }}``).
"""

import pytest

from nunavut.jinja.jinja2 import DictLoader, Environment
from nunavut.jinja.markupsafe import Markup


def _render(templates: dict, name: str = "main", **kwargs: object) -> str:
    env = Environment(loader=DictLoader(templates), **kwargs)  # type: ignore
    return env.get_template(name).render()


def test_block_autoindent() -> None:
    """Every non-empty line rendered by a ``{%* ... %}`` block gets the whitespace that preceded the tag."""
    templates = {"inner": "one\n\ntwo", "main": "[\n    {%* include 'inner' %}\n]"}
    assert _render(templates) == "[\n    one\n\n    two\n]"


def test_variable_autoindent() -> None:
    """``{{* ... }}`` prefixes every line of the expression, including the first."""
    assert _render({"main": "x:\n\t{{* 'a\\nb' }}\n"}) == "x:\n\ta\n\tb"


def test_autoindent_after_text() -> None:
    """Only the spaces and tabs right before the tag become the prefix."""
    assert _render({"main": "foo  {{* 'a\\nb' }}"}) == "foo  a\n  b"


def test_autoindent_without_leading_whitespace() -> None:
    """With nothing before the tag the output is unchanged."""
    assert _render({"main": "{{* 'a\\nb' }}"}) == "a\nb"


@pytest.mark.parametrize(
    "trim_blocks,lstrip_blocks,expected",
    [
        (False, False, "\n  1\n  1\n\n  2\n  2\n"),
        # The prefixed output loses its trailing newline (str.splitlines) so, once trim_blocks also removes the
        # newline after the endif, the loop iterations run together. This matches the behaviour of the
        # extension when it was first written against Jinja 2.
        (True, True, "  1\n  1  2\n  2"),
    ],
)
def test_autoindent_with_whitespace_control(trim_blocks: bool, lstrip_blocks: bool, expected: str) -> None:
    """Auto-indent takes precedence over lstrip_blocks for the whitespace before the tag."""
    templates = {
        "main": "{% for i in [1, 2] %}\n  {%* if true %}{{ i }}\n{{ i }}{% endif %}\n{% endfor %}",
    }
    assert _render(templates, trim_blocks=trim_blocks, lstrip_blocks=lstrip_blocks) == expected


def test_autoindent_filter_block() -> None:
    """Auto-indent composes with other block statements."""
    assert _render({"main": "a\n  {%* filter upper %}x\ny{% endfilter %}\nb"}) == "a\n  X\n  Y\nb"


def test_lineprefix_filter_preserves_markup() -> None:
    """The filter behind auto-indent keeps Markup as Markup. The prefix is template whitespace so it is
    treated as safe rather than escaped."""
    env = Environment()
    result = env.filters["lineprefix"](Markup("<b>\n</b>"), "<")
    assert isinstance(result, Markup)
    assert result == Markup("<<b>\n<</b>")
