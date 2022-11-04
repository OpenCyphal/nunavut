#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

import json
import typing
from pathlib import Path

import pytest
from nunavut import Namespace, build_namespace_tree
from nunavut._utilities import YesNoDefault
from nunavut.jinja import DSDLCodeGenerator
from nunavut.lang import Language, LanguageContext, LanguageContextBuilder
from pydsdl import Any, CompositeType, read_namespace


class DummyType(Any):
    """Fake dsdl 'any' type for testing."""

    def __init__(self, namespace: str = "uavcan", name: str = "Dummy"):
        self._full_name = "{}.{}".format(namespace, name)

    # +-----------------------------------------------------------------------+
    # | DUCK TYPEING: CompositeType
    # +-----------------------------------------------------------------------+
    @property
    def full_name(self) -> str:
        return self._full_name

    # +-----------------------------------------------------------------------+
    # | PYTHON DATA MODEL
    # +-----------------------------------------------------------------------+

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DummyType):
            return self._full_name == other._full_name
        else:
            return False

    def __str__(self) -> str:
        return self.full_name

    def __hash__(self) -> int:
        return hash(self._full_name)


def gen_test_namespace(
    gen_paths: typing.Any, language_context: LanguageContext
) -> typing.Tuple[Namespace, str, typing.List[CompositeType]]:
    root_namespace_path = str(gen_paths.dsdl_dir / Path("scotec"))
    includes = [str(gen_paths.dsdl_dir / Path("uavcan"))]
    compound_types = read_namespace(root_namespace_path, includes, allow_unregulated_fixed_port_id=True)
    return (
        build_namespace_tree(compound_types, root_namespace_path, gen_paths.out_dir, language_context),
        root_namespace_path,
        compound_types,
    )


def test_namespace_eq(gen_paths):  # type: ignore
    """Verify the get_all_namespaces method in Namespace"""
    language_context = LanguageContextBuilder(include_experimental_languages=True).set_target_language("js").create()
    namespace0, _, _ = gen_test_namespace(gen_paths, language_context)
    namespace1 = Namespace("", gen_paths.dsdl_dir, gen_paths.out_dir, language_context)
    assert namespace0 == namespace0
    assert namespace1 == namespace1
    assert namespace0 != namespace1
    assert "foo" != namespace0


def test_get_all_namespaces(gen_paths):  # type: ignore
    """Verify the get_all_namespaces method in Namespace"""
    language_context = LanguageContextBuilder(include_experimental_languages=True).set_target_language("js").create()
    namespace, _, _ = gen_test_namespace(gen_paths, language_context)
    index = dict()
    for ns, path in namespace.get_all_namespaces():
        index[path] = ns

    assert len(index) == 4


def test_get_all_types(gen_paths):  # type: ignore
    """Verify the get_all_namespaces method in Namespace"""
    language_context = LanguageContextBuilder(include_experimental_languages=True).set_target_language("js").create()
    namespace, _, _ = gen_test_namespace(gen_paths, language_context)
    index = dict()
    for ns, path in namespace.get_all_types():
        index[path] = ns

    assert len(index) == 6


def test_empty_namespace(gen_paths):  # type: ignore
    """Test a namespace object with no children."""
    language_context = (
        LanguageContextBuilder(include_experimental_languages=True)
        .set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".txt")
        .set_target_language_configuration_override(Language.WKCV_NAMESPACE_FILE_STEM, "_")
        .create()
    )
    namespace = Namespace("", gen_paths.dsdl_dir, gen_paths.out_dir, language_context)
    assert namespace.full_name == ""
    assert namespace.output_folder == gen_paths.out_dir
    assert namespace.source_file_path == gen_paths.dsdl_dir
    assert len(namespace.data_types) == 0
    assert (gen_paths.out_dir / Path("_")).with_suffix(".txt") == namespace.find_output_path_for_type(namespace)
    assert namespace == namespace
    assert hash(namespace) == hash(namespace)
    assert str(namespace) == str(namespace)
    with pytest.raises(KeyError):
        namespace.find_output_path_for_type(DummyType())


def parameterized_test_namespace_(gen_paths, templates_subdir):  # type: ignore
    language_context = LanguageContextBuilder(include_experimental_languages=True).set_target_language("js").create()
    namespace, root_namespace_path, _ = gen_test_namespace(gen_paths, language_context)
    generator = DSDLCodeGenerator(
        namespace,
        generate_namespace_types=YesNoDefault.NO,
        templates_dir=gen_paths.templates_dir / Path(templates_subdir),
    )
    generator.generate_all()
    assert namespace.source_file_path == Path(root_namespace_path)
    assert namespace.full_name == "scotec"
    for nested_namespace in namespace.get_nested_namespaces():
        nested_namespace_path = Path(root_namespace_path) / Path(*nested_namespace.full_name.split(".")[1:])
        assert nested_namespace.source_file_path == nested_namespace_path


def test_namespace_any_template(gen_paths):  # type: ignore
    """Basic test of a non-empty namespace using the Any.j2 template."""
    parameterized_test_namespace_(gen_paths, "default")


def test_namespace_namespace_template(gen_paths):  # type: ignore
    """Basic test of a non-empty namespace using the Namespace.j2 template."""
    parameterized_test_namespace_(gen_paths, "namespace")


def test_namespace_generation(gen_paths):  # type: ignore
    """Test actually generating a namepace file."""
    language_context = (
        LanguageContextBuilder(include_experimental_languages=True)
        .set_target_language("js")
        .set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".json")
        .set_target_language_configuration_override(Language.WKCV_NAMESPACE_FILE_STEM, "__module__")
        .create()
    )
    namespace, root_namespace_path, compound_types = gen_test_namespace(gen_paths, language_context)
    assert len(compound_types) == 2
    generator = DSDLCodeGenerator(
        namespace, generate_namespace_types=YesNoDefault.YES, templates_dir=gen_paths.templates_dir / Path("default")
    )
    generator.generate_all()
    for nested_namespace in namespace.get_nested_namespaces():
        nested_namespace_path = Path(root_namespace_path) / Path(*nested_namespace.full_name.split(".")[1:])
        assert nested_namespace.source_file_path == nested_namespace_path

    outfile = gen_paths.find_outfile_in_namespace("scotec.mcu", namespace)

    assert outfile is not None

    with open(str(outfile), "r") as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob["scotec.mcu"]["namespace"] == "scotec.mcu"

    output_path_for_timer = namespace.find_output_path_for_type(compound_types[0])
    assert (gen_paths.out_dir / "scotec" / "mcu" / "Timer_0_1").with_suffix(".json") == output_path_for_timer


def test_build_namespace_tree_from_nothing(gen_paths):  # type: ignore
    language_context = LanguageContextBuilder(include_experimental_languages=True).set_target_language("js").create()
    namespace = build_namespace_tree([], str(gen_paths.dsdl_dir), gen_paths.out_dir, language_context)
    assert namespace is not None
    assert namespace.full_name == ""


@pytest.mark.parametrize(
    "language_key,expected_file_ext,expected_stropp_part_0,expected_stropp_part_1",
    [("c", ".h", "_typedef", "str"), ("py", ".py", "typedef", "str_")],
)  # type: ignore
def test_namespace_stropping(
    gen_paths, language_key, expected_file_ext, expected_stropp_part_0, expected_stropp_part_1
):
    """Test generating a namespace that uses a reserved keyword for a given language."""
    language_context = (
        LanguageContextBuilder(include_experimental_languages=True).set_target_language(language_key).create()
    )
    namespace, root_namespace_path, compound_types = gen_test_namespace(gen_paths, language_context)
    assert len(compound_types) == 2
    generator = DSDLCodeGenerator(
        namespace, generate_namespace_types=YesNoDefault.YES, templates_dir=gen_paths.templates_dir / Path("default")
    )
    generator.generate_all()

    expected_stropped_ns = "scotec.{}.{}".format(expected_stropp_part_0, expected_stropp_part_1)
    outfile = gen_paths.find_outfile_in_namespace(expected_stropped_ns, namespace)

    assert outfile is not None

    with open(str(outfile), "r") as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None

    output_path_for_stropped = namespace.find_output_path_for_type(compound_types[1])
    expected_stable_path = gen_paths.out_dir / "scotec"
    expected_path_and_file = expected_stable_path / expected_stropp_part_0 / expected_stropp_part_1 / "ATOMIC_TYPE_0_1"
    assert expected_path_and_file.with_suffix(expected_file_ext) == output_path_for_stropped
