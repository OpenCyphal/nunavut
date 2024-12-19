#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
import typing
from pathlib import Path

import pytest

from nunavut import ResourceType, generate_all


@pytest.mark.parametrize(
    "lang_key,resource_types,language_options",
    [
        ("cpp", ResourceType.NONE.value, {}),
        ("cpp", ResourceType.TYPE_SUPPORT.value, {}),
        ("cpp", ResourceType.ANY.value, {}),
        ("cpp", ResourceType.ANY.value, {"std": "c++17"}),
        ("c", ResourceType.NONE.value, {}),
        ("c", ResourceType.ANY.value, {}),
        ("c", ResourceType.SERIALIZATION_SUPPORT.value | ResourceType.TYPE_SUPPORT.value, {}),
        ("py", ResourceType.ANY.value, {}),
        ("html", ResourceType.NONE.value, {}),
    ],
)
def test_realgen(
    gen_paths: typing.Any,
    lang_key: str,
    resource_types: int,
    language_options: typing.Mapping[str, typing.Any],
) -> None:
    """
    Sanity test that runs through the entire public, regulated set of
    Cyphal types and generates code for each internally supported language.
    """
    root_namespace_dir = gen_paths.root_dir / Path("submodules") / Path("public_regulated_data_types") / Path("uavcan")

    targets = list(root_namespace_dir.glob("**/*.dsdl"))

    assert len(targets) > 100
    # Sanity check that we found the dsdl source.

    result = generate_all(
        lang_key,
        targets,
        root_namespace_dir,
        gen_paths.out_dir,
        resource_types=resource_types,
        language_options=language_options,
        include_experimental_languages=True,
    )

    # We only expect one root namespace directory in the public regulated data types.
    assert len(result.generator_targets.values()) > 0
    root_namespace_directories = {x.definition.source_file_path_to_root for x in result.generator_targets.values()}
    assert len(root_namespace_directories) == 1
    assert root_namespace_directories.pop().stem == "uavcan"


def test_realgen_heartbeat(gen_paths: typing.Any) -> None:
    """
    Sanity test that generates the heartbeat message from the public types, ensuring its dependent types are also
    generated.
    """
    root_namespace_dir = gen_paths.root_dir / Path("submodules") / Path("public_regulated_data_types") / Path("uavcan")

    heartbeat = root_namespace_dir / Path("node", "7509.Heartbeat.1.0.dsdl")

    assert heartbeat.exists()

    generate_all("c", [heartbeat], root_namespace_dir, gen_paths.out_dir)

    assert (gen_paths.out_dir / Path("uavcan", "node", "Heartbeat_1_0.h")).exists()
    assert (gen_paths.out_dir / Path("nunavut", "support", "serialization.h")).exists()
    assert (gen_paths.out_dir / Path("uavcan", "node", "Health_1_0.h")).exists()
    assert (gen_paths.out_dir / Path("uavcan", "node", "Mode_1_0.h")).exists()
