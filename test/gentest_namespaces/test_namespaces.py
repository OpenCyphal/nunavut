#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
# cSpell: words scotec, animalia, chordata, aves, Uart
"""Tests for the namespace module."""

import json
from copy import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Tuple
from unittest.mock import MagicMock

import pytest
from pydsdl import Any as AnyPydsdlType
from pydsdl import CompositeType, Version

from nunavut import DSDLCodeGenerator, ResourceSearchPolicy, YesNoDefault
from nunavut._namespace import Generatable, Namespace, build_namespace_tree
from nunavut.lang import Language, LanguageContext, LanguageContextBuilder

# -- FIXTURES AND HELPER FUNCTIONS ---------------------------------------------------


@dataclass
class NamspaceTestParameters:
    """Parameters describing various constants in this gentest."""

    root_namespaces = ["scotec", "uavcan"]

    type_count: int
    root_namespace_count: int
    total_namespace_count: int


def gen_test_namespace_folder(
    gen_paths: Any, language_context: LanguageContext, repeat: int = 1
) -> Tuple[Namespace, NamspaceTestParameters]:
    """
    Generate a test namespace tree using pydsdl's read_namespace method. This tree includes all known types in this
    test.

    :param gen_paths (Any): The paths for generating the namespace.
    :param language_context (LanguageContext): The language context for generating the namespace.
    :param repeat (int): The number of times to repeat the generation. This verifies de-duplication of types.

    :return The generated namespace index.

    """
    root_namespace_path = str(gen_paths.dsdl_dir / Path("scotec"))
    includes = [str(gen_paths.dsdl_dir / Path("uavcan"))]
    index = Namespace.read_namespace(
        gen_paths.out_dir, language_context, root_namespace_path, includes, allow_unregulated_fixed_port_id=True
    )
    Namespace.read_namespace(index, str(gen_paths.dsdl_dir / Path("uavcan")), [], allow_unregulated_fixed_port_id=True)

    if repeat > 1:
        for _ in range(repeat - 1):
            Namespace.read_namespace(index, root_namespace_path, includes, allow_unregulated_fixed_port_id=True)
            Namespace.read_namespace(
                index, str(gen_paths.dsdl_dir / Path("uavcan")), [], allow_unregulated_fixed_port_id=True
            )

    return (index, NamspaceTestParameters(4, 2, 6))


def gen_test_namespace_files(
    gen_paths: Any, language_context: LanguageContext, repeat: int = 1
) -> Tuple[Namespace, NamspaceTestParameters]:
    """
    Generate a test namespace tree using pydsdl's read_files method. This tree includes all known types in this
    test.

    :param gen_paths (Any): The paths for generating the namespace.
    :param language_context (LanguageContext): The language context for generating the namespace.
    :param repeat (int): The number of times to repeat the generation. This verifies de-duplication of types.

    :return The generated namespace index.

    """
    files = [
        gen_paths.dsdl_dir / Path("uavcan") / Path("time") / Path("SynchronizedTimestamp.1.0.dsdl"),
        gen_paths.dsdl_dir / Path("scotec") / Path("mcu") / Path("Timer.0.1.dsdl"),
        gen_paths.dsdl_dir / Path("scotec") / Path("mcu") / Path("Uart.0.2.dsdl"),
        gen_paths.dsdl_dir / Path("scotec") / Path("typedef") / Path("str") / Path("ATOMIC_TYPE.0.1.dsdl"),
    ]
    root_namespaces = [gen_paths.dsdl_dir / Path("uavcan"), gen_paths.dsdl_dir / Path("scotec")]
    index = Namespace.read_files(
        gen_paths.out_dir, language_context, files, root_namespaces, allow_unregulated_fixed_port_id=True
    )

    if repeat > 1:
        for _ in range(repeat - 1):
            Namespace.read_files(index, files, root_namespaces, allow_unregulated_fixed_port_id=True)

    return (index, NamspaceTestParameters(4, 2, 6))


# --- TESTS ---------------------------------------------------------------------------


def test_add_types(gen_paths: Any) -> None:
    """Test adding types to the namespace index."""
    lctx = LanguageContextBuilder().set_target_language("c").create()
    base_path = gen_paths.out_dir
    root_namespace_dir = base_path / Path("animalia")
    root_namespace_dir.mkdir(exist_ok=True)

    chordata_folder = root_namespace_dir / Path("chordata")
    chordata_folder.mkdir(exist_ok=True)

    chordata_structures_folder = chordata_folder / Path("structures")
    chordata_structures_folder.mkdir(exist_ok=True)

    animalia_structures_folder = root_namespace_dir / Path("structures")
    animalia_structures_folder.mkdir(exist_ok=True)

    no_namespace = MagicMock(spec=CompositeType)
    no_namespace.full_namespace = ""
    no_namespace.namespace_components = []
    no_namespace.short_name = ""
    no_namespace.version = MagicMock(spec=Version)
    no_namespace.version.major = 1
    no_namespace.version.minor = 0
    no_namespace.source_file_path_to_root = root_namespace_dir
    no_namespace.source_file_path = root_namespace_dir

    aves = MagicMock(spec=CompositeType)
    aves.full_namespace = "animalia.chordata"
    aves.namespace_components = ["animalia", "chordata"]
    aves.short_name = "Aves"
    aves.version = MagicMock(spec=Version)
    aves.version.major = 1
    aves.version.minor = 0
    aves.source_file_path_to_root = root_namespace_dir
    aves.source_file_path = chordata_folder / Path("Aves.1.0.dsdl")

    aves2 = MagicMock(spec=CompositeType)
    aves2.full_namespace = "animalia.chordata"
    aves2.namespace_components = ["animalia", "chordata"]
    aves2.short_name = "Aves"
    aves2.version = MagicMock(spec=Version)
    aves2.version.major = 2
    aves2.version.minor = 0
    aves2.source_file_path_to_root = root_namespace_dir
    aves2.source_file_path = chordata_folder / Path("Aves.2.0.dsdl")

    aves3 = MagicMock(spec=CompositeType)
    aves3.full_namespace = "animalia.chordata"
    aves3.namespace_components = ["animalia", "chordata"]
    aves3.short_name = "Aves"
    aves3.version = MagicMock(spec=Version)
    aves3.version.major = 3
    aves3.version.minor = 0
    aves3.source_file_path_to_root = root_namespace_dir
    aves3.source_file_path = chordata_folder / Path("Aves.3.0.dsdl")

    spine = MagicMock(spec=CompositeType)
    spine.full_namespace = "animalia.chordata.structures"
    spine.namespace_components = ["animalia", "chordata", "structures"]
    spine.short_name = "Spine"
    spine.version = MagicMock(spec=Version)
    spine.version.major = 1
    spine.version.minor = 0
    spine.source_file_path_to_root = root_namespace_dir
    spine.source_file_path = chordata_folder / Path("Spine.1.0.dsdl")

    mammal = MagicMock(spec=CompositeType)
    mammal.full_namespace = "animalia.chordata"
    mammal.short_name = "Mammal"
    mammal.version = MagicMock(spec=Version)
    mammal.version.major = 1
    mammal.version.minor = 0
    mammal.namespace_components = ["animalia", "chordata"]
    mammal.source_file_path_to_root = root_namespace_dir
    mammal.source_file_path = chordata_folder / Path("Mammal.1.0.dsdl")

    wing = MagicMock(spec=CompositeType)
    wing.full_namespace = "animalia.structures"
    wing.short_name = "Wing"
    wing.version = MagicMock(spec=Version)
    wing.version.major = 1
    wing.version.minor = 0
    wing.namespace_components = ["animalia", "structures"]
    wing.source_file_path_to_root = root_namespace_dir
    wing.source_file_path = animalia_structures_folder / Path("Wing.1.0.dsdl")

    index = Namespace.Identity(base_path, lctx)

    with pytest.raises(RuntimeError):
        Namespace.add_types(index, [(no_namespace, [])])

    with pytest.raises(RuntimeError):
        _ = index.root_namespace

    with pytest.raises(RuntimeError):
        _ = index.add_data_type(no_namespace, [], None)

    assert no_namespace != index

    Namespace.add_types(index, [(spine, [])])

    expected_spine_output_path = (
        index.output_folder / Path("animalia") / Path("chordata") / Path("structures") / Path("Spine_1_0")
    ).with_suffix(".h")
    spine_output_path = index.find_output_path_for_type(spine)
    assert Path(spine_output_path) == expected_spine_output_path

    # Add the types to the index filling out the namespace tree as needed.
    Namespace.add_types(index, [(aves, []), (aves2, []), (mammal, []), (wing, [])])

    assert index.get_root_namespace(root_namespace_dir.name) == index.get_root_namespace(root_namespace_dir.name)
    with pytest.raises(KeyError):
        index.get_root_namespace(chordata_folder.name, create_if_missing=False)
    assert index.get_root_namespace(root_namespace_dir.name) != index.get_root_namespace(
        chordata_folder.name, create_if_missing=True
    )

    chordata = index.get_nested_namespace("animalia").get_nested_namespace("chordata")
    _ = chordata.find_output_path_for_type(aves)
    _ = chordata.find_output_path_for_type(aves2)
    with pytest.raises(KeyError):
        _ = chordata.find_output_path_for_type(aves3)

    with pytest.raises(ValueError):
        chordata.add_data_type(wing, [], None)

    chordata.add_data_type(aves3, [], ".foo")
    assert index.find_output_path_for_type(aves3) == chordata.find_output_path_for_type(aves3)


def test_read_with_non_index_value(gen_paths: Any) -> None:
    """Test the read_files method with a bad value."""

    root_namespace_dir = gen_paths.out_dir / Path("animalia")
    spine = MagicMock(spec=CompositeType)
    spine.full_namespace = "animalia.chordata.structures"
    spine.namespace_components = ["animalia", "chordata", "structures"]
    spine.short_name = "Spine"
    spine.version = MagicMock()
    spine.version.major = 1
    spine.version.minor = 0
    spine.source_file_path_to_root = root_namespace_dir
    spine.source_file_path = root_namespace_dir / Path("Spine.1.0.dsdl")

    index = Namespace.Identity(gen_paths.out_dir, LanguageContextBuilder().set_target_language("c").create())

    Namespace.add_types(index, [(spine, [])])
    animalia_root = index.get_nested_namespace("animalia")

    with pytest.raises(ValueError):
        # animalia_root is not an index so this should fail.
        Namespace.read_namespace(animalia_root, root_namespace_dir)

    with pytest.raises(ValueError):
        # animalia_root is not an index so this should fail.
        Namespace.read_files(animalia_root, root_namespace_dir, None)


def test_generatable_constructor():  # type: ignore
    """Test the Generatable constructor."""
    path = Path("test")
    definition = MagicMock(spec=CompositeType)
    input_types = [MagicMock(spec=CompositeType)]
    input_types[0].__hash__ = MagicMock(return_value=1)  # type: ignore

    gen = Generatable(definition, input_types, path)

    assert gen.definition == definition
    assert gen.input_types == input_types
    assert gen == path

    with pytest.raises(TypeError):
        Generatable(path)

    with pytest.raises(TypeError):
        Generatable(None, path)

    with pytest.raises(TypeError):
        Generatable(None, None, path)


def test_generatable_copy():  # type: ignore
    """Test copying Generatable objects."""

    path = Path("test")
    definition = MagicMock(spec=CompositeType)
    input_types = [MagicMock(spec=CompositeType)]
    input_types[0].__hash__ = MagicMock(return_value=1)  # type: ignore

    gen = Generatable.wrap(path, definition, input_types)

    copy_of_gen = copy(gen)
    assert gen == copy_of_gen
    assert hash(gen) == hash(copy_of_gen)

    # Ensure the copy is shallow
    gen._input_types.clear()  # pylint: disable=protected-access
    assert gen != copy_of_gen
    gen = copy(copy_of_gen)
    assert gen == copy_of_gen
    gen._definition = MagicMock(spec=AnyPydsdlType)  # pylint: disable=protected-access
    assert gen != copy_of_gen


def test_generatable_as_path_like():  # type: ignore
    """Test Generatable objects as Path-like objects."""
    gen = Generatable(MagicMock(spec=CompositeType), [MagicMock(spec=CompositeType)], Path("test"))

    assert Path("path", "to", "test") == Path("path", "to") / gen

    with pytest.raises(TypeError):
        Generatable("foo")

    print(f"{str(gen)}:{repr(gen)}")

    assert str(Path("foo")) == str(
        Generatable(MagicMock(spec=CompositeType), [MagicMock(spec=CompositeType)], Path("foo"))
    )
    assert (
        Path("foo")
        == Generatable(MagicMock(spec=CompositeType), [MagicMock(spec=CompositeType)], Path("foo/bar")).parent
    )
    assert (
        Path("foo/bar").name
        == Generatable(MagicMock(spec=CompositeType), [MagicMock(spec=CompositeType)], Path("foo/bar")).name
    )
    assert Path("foo/bar") == Generatable(
        MagicMock(spec=CompositeType), [MagicMock(spec=CompositeType)], Path("foo/bar")
    )
    assert Generatable(MagicMock(spec=CompositeType), [MagicMock(spec=CompositeType)], Path("foo/bar")) == Path(
        "foo/bar"
    )
    assert repr(Generatable(MagicMock(spec=CompositeType), [MagicMock(spec=CompositeType)], Path("foo/bar"))) != repr(
        Path("foo/bar")
    )


def test_namespace_constructor(gen_paths):  # type: ignore
    """Test the Namespace constructor."""
    language_context = LanguageContextBuilder(include_experimental_languages=True).set_target_language("js").create()
    index = Namespace.Identity(gen_paths.out_dir, language_context)
    assert index == index.get_index_namespace()

    # Identity namespace must not have a parent.
    with pytest.raises(ValueError):
        Namespace("", Path("foo"), language_context, index)

    # Non-identity namespaces must have a parent
    with pytest.raises(ValueError):
        _ = Namespace(".planets", Path("planets"), language_context, None)

    # Non-identity namespaces must have a source file path
    with pytest.raises(ValueError):
        _ = Namespace(".planets", Path(""), language_context, index)

    # Non-identity namespaces must have a source file path that matches the namespace
    with pytest.raises(ValueError):
        _ = Namespace(".planets", Path("dwarf_planets"), language_context, index)

    planets = Namespace(".planets", Path("planets"), language_context, index)
    assert planets.get_index_namespace() == index
    assert planets.full_name == "planets"
    assert planets.output_folder == gen_paths.out_dir / Path("planets")
    assert planets.source_file_path == Path("planets")
    assert planets.source_file_path_to_root == Path("planets")
    assert planets.is_root
    assert not planets.is_index
    assert not planets.is_nested


@pytest.mark.parametrize(
    "read_method, repeat",
    [
        (gen_test_namespace_folder, 1),
        (gen_test_namespace_files, 1),
        (gen_test_namespace_folder, 3),
        (gen_test_namespace_files, 3),
    ],
)  # type: ignore
def test_get_nested_namespaces(gen_paths, read_method, repeat):  # type: ignore
    """Verify the get_nested_namespaces method in Namespace"""
    language_context = LanguageContextBuilder(include_experimental_languages=True).set_target_language("js").create()
    index, test_params = read_method(gen_paths, language_context, repeat)
    top_level_namespaces = list(index.get_nested_namespaces())
    assert len(top_level_namespaces) == test_params.root_namespace_count
    total_namespaces = 0

    def verify_nested_namespaces(root_namespace: Namespace) -> None:
        nonlocal total_namespaces
        for nested_namespace in root_namespace.get_nested_namespaces():
            total_namespaces += 1
            assert nested_namespace.is_nested
            verify_nested_namespaces(nested_namespace)

    for root_namespace in top_level_namespaces:
        total_namespaces += 1
        assert root_namespace.is_root
        assert not root_namespace.is_index
        assert not root_namespace.is_nested
        assert root_namespace == root_namespace
        assert hash(root_namespace) == hash(root_namespace)
        verify_nested_namespaces(root_namespace)

    assert total_namespaces == test_params.total_namespace_count


@pytest.mark.parametrize("read_method", [gen_test_namespace_folder, gen_test_namespace_files])  # type: ignore
def test_get_all_types(gen_paths, read_method):  # type: ignore
    """Verify the get_all_namespaces method in Namespace"""
    language_context = LanguageContextBuilder(include_experimental_languages=True).set_target_language("js").create()
    index, test_params = read_method(gen_paths, language_context)
    type_index = {}
    for root_namespace in index.get_nested_namespaces():
        for ns, path in root_namespace.get_all_types():
            type_index[path] = ns

    assert len(type_index) == (test_params.type_count + test_params.total_namespace_count)

    type_index.clear()

    for ns, path in index.get_all_types():
        type_index[path] = ns

    assert len(type_index) == (
        test_params.type_count + test_params.total_namespace_count + 1
    )  # +1 for the index itself


def test_identity_namespace(gen_paths):  # type: ignore
    """Test a namespace object with no children."""
    language_context = (
        LanguageContextBuilder(include_experimental_languages=True)
        .set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".txt")
        .set_target_language_configuration_override(Language.WKCV_NAMESPACE_FILE_STEM, "_")
        .create()
    )
    namespace = Namespace.Identity(gen_paths.out_dir, language_context)
    assert namespace.full_name == ""
    assert namespace.output_folder == gen_paths.out_dir
    assert len(namespace.data_types) == 0
    assert (gen_paths.out_dir / Path("_")).with_suffix(".txt") == namespace.find_output_path_for_type(namespace)
    assert namespace == namespace
    assert hash(namespace) == hash(namespace)
    assert str(namespace) == str(namespace)

    aves = MagicMock(spec=CompositeType)
    aves.full_namespace = "animalia.chordata"
    aves.namespace_components = ["animalia", "chordata"]
    aves.short_name = "Aves"
    aves.version = MagicMock(spec=Version)
    aves.version.major = 1
    aves.version.minor = 0
    aves.source_file_path_to_root = Path("")
    aves.source_file_path = Path("")

    with pytest.raises(KeyError):
        namespace.find_output_path_for_type(aves)


@pytest.mark.parametrize("read_method", [gen_test_namespace_folder, gen_test_namespace_files])
@pytest.mark.parametrize("templates_subdir", ["default", "namespace"])
def test_namespace_any_template(gen_paths, read_method, templates_subdir):  # type: ignore
    """Basic test of a non-empty namespace using the Any.j2 then Namespace.j2 templates."""
    language_context = LanguageContextBuilder(include_experimental_languages=True).set_target_language("js").create()
    index, test_params = read_method(gen_paths, language_context)
    assert test_params.root_namespace_count > 0

    for root_namespace in index.get_nested_namespaces():
        generator = DSDLCodeGenerator(
            root_namespace,
            generate_namespace_types=YesNoDefault.NO,
            templates_dir=gen_paths.templates_dir / Path(templates_subdir),
            search_policy=ResourceSearchPolicy.FIND_FIRST,
        )
        generator.generate_all()
        assert not root_namespace.source_file_path.is_absolute()
        assert gen_paths.dsdl_dir / root_namespace.source_file_path == gen_paths.dsdl_dir / root_namespace.short_name
        assert root_namespace.source_file_path_to_root == root_namespace.source_file_path
        assert root_namespace.full_name in test_params.root_namespaces
        for nested_namespace in root_namespace.get_nested_namespaces():
            assert nested_namespace.source_file_path_to_root == root_namespace.source_file_path


def test_build_namespace_tree_from_nothing(gen_paths):  # type: ignore
    """Legacy test to ensure backwards compatibility with the build_namespace_tree function."""
    language_context = LanguageContextBuilder(include_experimental_languages=True).set_target_language("js").create()
    namespace = build_namespace_tree([], str(gen_paths.dsdl_dir), gen_paths.out_dir, language_context)
    assert namespace is not None
    assert namespace.is_root


@pytest.mark.parametrize("read_method", [gen_test_namespace_folder, gen_test_namespace_files])  # type: ignore
def test_namespace_generation(gen_paths, read_method):  # type: ignore
    """Test actually generating a namespace file."""
    language_context = (
        LanguageContextBuilder(include_experimental_languages=True)
        .set_target_language("js")
        .set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".json")
        .set_target_language_configuration_override(Language.WKCV_NAMESPACE_FILE_STEM, "__module__")
        .create()
    )
    namespace, test_params = read_method(gen_paths, language_context)
    assert test_params.type_count > 0
    generator = DSDLCodeGenerator(
        namespace,
        generate_namespace_types=YesNoDefault.YES,
        templates_dir=gen_paths.templates_dir / Path("default"),
        search_policy=ResourceSearchPolicy.FIND_FIRST,
    )
    generator.generate_all()

    # first go-around includes namespace files
    data_type_count = 0
    for data_type, out_file in namespace.get_all_types():
        data_type_count += 1
        with out_file.open("r", encoding="utf-8") as json_file:
            json_blob = json.load(json_file)
            assert json_blob is not None
            assert data_type.full_name in json_blob
            assert "namespace" in json_blob[data_type.full_name]
            assert json_blob[data_type.full_name]["namespace"] == data_type.full_namespace

    assert data_type_count == test_params.type_count + test_params.total_namespace_count + 1  # +1 for the index itself

    # second go-around is only the data types
    data_type_count = 0
    for data_type, out_file in namespace.get_all_datatypes():
        data_type_count += 1
        with out_file.open("r", encoding="utf-8") as json_file:
            json_blob = json.load(json_file)
            assert json_blob is not None
            assert data_type.full_name in json_blob
            assert "namespace" in json_blob[data_type.full_name]
            assert json_blob[data_type.full_name]["namespace"] == data_type.full_namespace

    assert data_type_count == test_params.type_count

    # The third is only the namespace files
    data_type_count = 0
    for data_type, out_file in namespace.get_all_namespaces():
        data_type_count += 1
        with out_file.open("r", encoding="utf-8") as json_file:
            json_blob = json.load(json_file)
            assert json_blob is not None
            assert data_type.full_name in json_blob
            assert "namespace" in json_blob[data_type.full_name]
            assert json_blob[data_type.full_name]["namespace"] == data_type.full_namespace

    assert data_type_count == test_params.total_namespace_count + 1  # +1 for the index itself


@pytest.mark.parametrize("read_method", [gen_test_namespace_folder, gen_test_namespace_files])
@pytest.mark.parametrize(
    "language_key,expected_file_ext,expected_strop_part_0,expected_strop_part_1",
    [
        ("c", ".h", "_typedef", "str"),
        ("py", ".py", "typedef", "str_"),
    ],
)  # type: ignore
def test_namespace_stropping(
    gen_paths,
    read_method,
    language_key: str,
    expected_file_ext: str,
    expected_strop_part_0: str,
    expected_strop_part_1: str,
):
    """Test generating a namespace that uses a reserved keyword for a given language."""
    language_context = (
        LanguageContextBuilder(include_experimental_languages=True).set_target_language(language_key).create()
    )
    namespace, test_params = read_method(gen_paths, language_context)
    assert test_params.type_count > 0
    generator = DSDLCodeGenerator(
        namespace, generate_namespace_types=YesNoDefault.YES, templates_dir=gen_paths.templates_dir / Path("default")
    )
    generator.generate_all()

    expected_stropped_ns = f"scotec.{expected_strop_part_0}.{expected_strop_part_1}"
    outfile = gen_paths.find_outfile_in_namespace(expected_stropped_ns, namespace)

    assert outfile is not None

    with open(outfile, "r", encoding="utf-8") as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None

    scotec = namespace.get_root_namespace("scotec")
    typedef = scotec.get_nested_namespace("typedef")
    str_ = typedef.get_nested_namespace("str")

    real_atomic_type = None
    for data_type, _ in str_.get_all_types():
        if data_type.short_name == "ATOMIC_TYPE":
            real_atomic_type = data_type
            break

    assert real_atomic_type is not None
    output_path_for_stropped = str_.find_output_path_for_type(real_atomic_type)

    expected_stable_path = gen_paths.out_dir / "scotec"
    expected_path_and_file = expected_stable_path / expected_strop_part_0 / expected_strop_part_1 / "ATOMIC_TYPE_0_1"
    assert expected_path_and_file.with_suffix(expected_file_ext) == output_path_for_stropped

    # The namespace parts is not stropped. Only the outputs are since stropping is output-specific.
    assert ["scotec", "typedef", "str"] == str_.namespace_components
