#!/usr/bin/env python3
#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
"""
    Command-line script to test nunavut.postprocessors.ExternalProgramEditInPlace
"""
import sys
import pathlib


def main() -> int:

    if len(sys.argv) <= 1:
        return -2

    generated_file = sys.argv[len(sys.argv) - 1]

    if not pathlib.Path(generated_file).exists():
        raise ValueError('Generated file {} does not exist?'.format(generated_file))

    with open(generated_file, 'w') as generated_fp:
        generated_fp.write('{"ext":"changed"}\n')

    return (-1 if '--simulate-error' in sys.argv else 0)


if __name__ == "__main__":
    sys.exit(main())
