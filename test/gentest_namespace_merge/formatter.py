#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
A stand-in for a code formatter, run by nnvg --pp-run-program on each generated file. It changes only whitespace and
the layout of comments: it reindents comment text, joins pairs of consecutive comment lines, adds blank comment lines,
and converts line endings to CRLF. The meaning of the file is unchanged.
"""

import sys
from pathlib import Path


def reformat(text: str) -> str:
    out = []
    pending = None  # a comment line waiting to be joined with the next one
    for line in text.splitlines():
        if line.startswith("#"):
            body = " ".join(line[1:].split())
            if pending is None:
                pending = body
            else:
                out.append("#\t  " + pending + "      " + body)
                out.append("#")
                pending = None
            continue
        if pending is not None:
            out.append("#\t  " + pending)
            pending = None
        out.append(line)
    if pending is not None:
        out.append("#\t  " + pending)
    return "\r\n".join(out) + "\r\n"


if __name__ == "__main__":
    target = Path(sys.argv[-1])
    target.write_bytes(reformat(target.read_text(encoding="utf-8")).encode("utf-8"))
