#!/usr/bin/env python3
#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
    Cmake presets has a problem (see https://gitlab.kitware.com/cmake/cmake/-/issues/22538) where a matrix of options
    causes a combinatorial explosion of presets that are tedious to generate and maintain. This script automates the
    generation and modification of such large lists of presets for the Nunavut verification project.
"""

import argparse
import functools
import itertools
import json
import sys
import textwrap
from pathlib import Path
from collections import OrderedDict

dimensions: OrderedDict[str, dict] = OrderedDict(
    [
        (
            "toolchain",
            {
                "short_name": "tc",
                "help": "The toolchain to use. Optionally provide colon separated platform name.",
                "split": ":",
                "values": {
                    "toolchainFile": lambda tc: f"${{sourceDir}}/cmake/toolchains/{tc.split(':')[0]}.cmake",
                    "cacheVariables": lambda tc: (
                        {"NUNAVUT_VERIFICATION_TARGET_PLATFORM": tc.split(":")[1]} if len(tc.split(":")) > 1 else {}
                    ),
                },
            },
        ),
        (
            "language",
            {
                "short_name": "ln",
                "help": "A pair of language name and language standard to use separated by a dash. For example, 'c-11'.",
                "split": "-",
                "values": {
                    "cacheVariables": lambda las: {
                        "NUNAVUT_VERIFICATION_LANG": las.split("-")[0],
                        "NUNAVUT_VERIFICATION_LANG_STANDARD": las.split("-")[1],
                    }
                },
            },
        ),
    ]
)


def parse_arguments() -> argparse.Namespace:
    """
    Define and parse the command line arguments.
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent(
            """
            Generate CMake presets based on given options. See
            https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html for details on cmake presets.

            This script is most useful when given a pre-existing CMakePresets.json file that contains common
            configurations that are used as a base for generating a large number of configurations. See the
            `--common-configuration` option for the default common configuration or to specify your own.

            The script will look for CMAKE_CONFIGURATION_TYPES in the common configurations and generate
            build presets for each of the configurations found. If CMAKE_CONFIGURATION_TYPES is not found,
            it will look for CMAKE_DEFAULT_BUILD_TYPE. If neither are found, it will raise an error.

            An error will be raised in the preset version does not match the --preset-version value.
    """
        ).lstrip(),
        epilog=textwrap.dedent(
            """

        Copyright (C) OpenCyphal Development Team  <opencyphal.org>
        Copyright Amazon.com Inc. or its affiliates.
        Released under SPDX-License-Identifier: MIT

        **Example Usage** ::

            # a single --clean is reccomended which will remove all visible configurations and build presets before
            # generating new ones from the common, hidden, and given options.

            ./preset_generator.py --clean -ln c-11 -tc gcc:linux -ln c++-17 -tc gcc:armv7m

            # Double clean will remove everything except the common configurations.

            ./preset_generator.py --clean --clean -ln c-11 -tc gcc:linux -ln c++-17 -tc gcc:armv7m

            # Triple clean will remove everything including the common configurations.

            ./preset_generator.py --clean --clean --clean -ln c-11 -tc gcc:linux -ln c++-17 -tc gcc:armv7m

        ᓄᓇᕗᑦ
    """
        ),
    )
    parser.add_argument(
        "--preset-file",
        type=Path,
        default="CMakePresets.json",
        help=textwrap.dedent(
            """
            The file to read, modify, and/or write the presets to. The file should be in the format of a CMake presets
            json file.

    """
        ).lstrip(),
    )

    parser.add_argument("--indent", type=int, default=4, help="The number of spaces to indent the output by.")

    parser.add_argument("--presets-version", type=int, default=7, help="The required version of the presets file.")

    parser.add_argument("--clean", action="count", help="Clean the presets file of all presets first.")

    parser.add_argument(
        "--common-configuration",
        action="append",
        type=str,
        default=["config-common"],
        help="Common configuration all visible configurations inherit from.",
    )

    parser.add_argument(
        "--build-targets", action="append", type=str, default=["test_all"], help="The build targets to use."
    )

    options_args = parser.add_argument_group(title="Options")
    for option, config in dimensions.items():
        options_args.add_argument(
            f"--{option}", f"-{config['short_name']}", type=str, action="append", help=config["help"]
        )

    return parser.parse_args()


def validate_json_schema(args: argparse.Namespace, presets: dict) -> bool:
    """
    Validates the preset file against certain assumptions this script makes. If jsonschema and requests is available
    the script will also validate the file against the CMake presets schema pulled from gihub.
    """
    try:
        import jsonschema  # pylint: disable=import-outside-toplevel
        import urllib.request  # pylint: disable=import-outside-toplevel

        schema_url = "https://raw.githubusercontent.com/Kitware/CMake/master/Help/manual/presets/schema.json"
        with urllib.request.urlopen(schema_url, timeout=10) as response:
            schema = json.loads(response.read().decode())

        try:
            jsonschema.validate(instance=presets, schema=schema)
        except jsonschema.ValidationError as e:
            print(f"JSON schema validation error: {e.message}")
            return False

    except ImportError:
        if not getattr(args, "validate_json_schema_warn_once", False):
            print("jsonschema is not available. Skipping schema validation.")
            args.validate_json_schema_warn_once = True

    if "version" not in presets or presets["version"] != args.presets_version:
        print("The version field is missing from the presets file.")
        return False
    if "configurePresets" not in presets:
        print("The configurePresets field is missing from the presets file.")
        return False
    for common_config in args.common_configuration:
        configure_presets = presets["configurePresets"]
        if not any(preset["name"] == common_config for preset in configure_presets):
            print(f"Common configuration '{common_config}' not found in the configure presets.")
            return False
    return True


def find_configuration_types(args: argparse.Namespace, hidden_presets: list[dict]) -> list[str]:
    """
    Find the semi-colon delinated CMAKE_CONFIGURATION_TYPES types in the common configurations.

    @param args: The parsed command line arguments.
    @param hidden_presets: The hidden configure presets.
    @return: A list of the CMAKE_CONFIGURATION_TYPES found in the common configurations, if any.
    @raises ValueError: If multiple common configurations have different CMAKE_CONFIGURATION_TYPES or if no
    MAKE_CONFIGURATION_TYPES were found and CMAKE_DEFAULT_BUILD_TYPE is not set.
    """
    configuration_types: set[str] = set()
    default_build_types: set[str] = set()

    for preset in hidden_presets:
        if preset["name"] in args.common_configuration:
            cache_variables = preset.get("cacheVariables", {})
            config_types = cache_variables.get("CMAKE_CONFIGURATION_TYPES")
            if config_types:
                config_types_set = set(config_types.split(";"))
                if configuration_types and configuration_types != config_types_set:
                    raise ValueError("Multiple common configurations have different CMAKE_CONFIGURATION_TYPES.")
                configuration_types = config_types_set
            default_build_type = cache_variables.get("CMAKE_DEFAULT_BUILD_TYPE")
            if default_build_type:
                default_build_types.add(default_build_type)

    if len(default_build_types) > 1:
        raise ValueError("Multiple common configurations have different CMAKE_DEFAULT_BUILD_TYPE values.")

    if not configuration_types and not default_build_types:
        raise ValueError(
            "No CMAKE_CONFIGURATION_TYPES found in common configurations and CMAKE_DEFAULT_BUILD_TYPE is not set."
        )

    return sorted(configuration_types) if configuration_types else sorted(default_build_types)


def update_hidden_configure_presets(args: argparse.Namespace, configure_presets: dict) -> list[dict]:
    """
    Update the hidden configure presets based on the arguments given to the script.

    @return: The updated hidden configure presets merged from the given presets and the arguments.
    """
    configure_hidden_presets_index = {
        d["name"].lower(): d for d in filter(lambda x: "hidden" in x and x["hidden"], configure_presets)
    }

    for argument_name, aspect_template in dimensions.items():
        parameters = getattr(args, argument_name.replace("-", "_"))
        if parameters:
            for parameter in parameters:
                unsplit_name = parameter.replace(aspect_template["split"], "-")
                preset_name = f"config-{argument_name}-{unsplit_name}"
                configure_preset = {"name": preset_name, "hidden": True}
                for key, value_template in aspect_template["values"].items():
                    if callable(value_template):
                        configure_preset[key] = value_template(parameter)
                    elif isinstance(value_template, dict):
                        configure_preset[key] = {k: v.format(parameter) for k, v in value_template.items()}
                    elif isinstance(value_template, str):
                        configure_preset[key] = value_template.format(parameter)  # pylint: disable=no-member
                    else:
                        raise ValueError(f"Unsupported value template type: {type(value_template)}")
                if preset_name in configure_hidden_presets_index:
                    configure_hidden_presets_index[preset_name].update(configure_preset)
                else:
                    configure_hidden_presets_index[preset_name] = configure_preset

    return list(configure_hidden_presets_index.values())


def generate_visible_configure_presets(args: argparse.Namespace, hidden_configure_presets: list[dict]) -> list[dict]:
    """
    Generate visible configure presets based on the hidden configure presets.

    @return: The visible configure presets as generated by calculating the cartisian product of the hidden configure
    presets.
    """
    configurations_index: dict[str, list[tuple]] = {}

    # investigate the hidden presets to see what configurations are available
    for dimension in dimensions:
        prefix = f"config-{dimension}-"
        configurations: list[tuple[str, str]] = configurations_index.get(dimension, [])
        configurations += [
            (x["name"], x["name"].replace(prefix, "")) for x in hidden_configure_presets if x["name"].startswith(prefix)
        ]
        configurations_index[dimension] = configurations

    # generate all permutations of the hidden configurations as visible configurations
    visible_configure_presets: list[dict] = []
    product = itertools.product(*configurations_index.values())
    for configuration in product:
        config_name = functools.reduce(lambda x, y: f"{x}-{y[1]}", configuration, "config")
        inherited = args.common_configuration + [x[0] for x in configuration]
        visible_configure_presets.append({"name": config_name, "inherits": inherited})

    return visible_configure_presets


def generate_build_presets(
    args: argparse.Namespace, configurations: list[str], visible_configure_presets: list[dict]
) -> list[dict]:
    """
    Generate build presets based on the visible configure presets.

    @return: A list of build presets, one for each visible configure preset.
    """
    build_presets = []

    for configuration in configurations:
        for preset in visible_configure_presets:
            build_presets.append(
                {
                    "name": f"build-{preset['name'].replace('config-', '')}-{configuration.lower()}",
                    "configurePreset": preset["name"],
                    "configuration": configuration,
                    "targets": args.build_targets,
                }
            )
    return build_presets


def main() -> int:
    """
    Idempotent (mostly) generation of CMake presets based on the given options and the contents of the given presets
    file.
    """
    args = parse_arguments()

    with args.preset_file.open("r", encoding="UTF-8") as f:
        json_presets = json.loads(f.read())

    if not validate_json_schema(args, json_presets):
        return 1

    if args.clean is not None and args.clean >= 1:
        # clean level 1 deletes all existing buildPresets
        json_presets["buildPresets"] = []

        if args.clean == 2:
            # clean level 2 deletes all existing configurePresets except for the common configurations
            json_presets["configurePresets"] = [
                preset for preset in json_presets["configurePresets"] if preset["name"] in args.common_configuration
            ]
        elif args.clean >= 3:
            # clean level 3 deletes all existing configurePresets
            json_presets["configurePresets"] = []

    hidden_presets = update_hidden_configure_presets(args, json_presets["configurePresets"])
    visible_presets = generate_visible_configure_presets(args, hidden_presets)
    json_presets["configurePresets"] = hidden_presets + visible_presets

    json_presets["buildPresets"] = generate_build_presets(
        args, find_configuration_types(args, hidden_presets), visible_presets
    )

    if not validate_json_schema(args, json_presets):
        return 1

    with args.preset_file.open("w", encoding="UTF-8") as f:
        f.write(json.dumps(json_presets, indent=args.indent))
        f.write("\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
