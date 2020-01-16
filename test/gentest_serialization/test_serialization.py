#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
Test the generation of serialization support generically and for python.
"""
from pathlib import Path

from nunavut import generate_types


def test_no_serialization_cpp(gen_paths):  # type: ignore
    root_namespace_dir = gen_paths.root_dir / Path("submodules") / Path("public_regulated_data_types") / Path("uavcan")
    generate_types('cpp',
                   root_namespace_dir,
                   gen_paths.out_dir,
                   omit_serialization_support=True)
