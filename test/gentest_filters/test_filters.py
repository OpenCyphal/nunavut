#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#

import json
import pathlib
import typing
from pathlib import Path, PurePath

import pytest
from pydsdl import read_namespace

from nunavut import Namespace
from nunavut._namespace import build_namespace_tree # deprecated
from nunavut.jinja import DSDLCodeGenerator
from nunavut.jinja.jinja2.exceptions import TemplateAssertionError
from nunavut.lang import Language, LanguageClassLoader, LanguageContextBuilder


def test_template_assert(gen_paths):  # type: ignore
    """
    Tests our template assertion extension.
    """
    root_path = str(gen_paths.dsdl_dir / Path("uavcan"))
    output_path = gen_paths.out_dir / "assert"
    compound_types = read_namespace(root_path, [])
    language_context = (
        LanguageContextBuilder()
        .set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".json")
        .create()
    )
    namespace = build_namespace_tree(compound_types, root_path, output_path, language_context)
    template_path = gen_paths.templates_dir / Path("assert")
    generator = DSDLCodeGenerator(namespace, templates_dir=template_path)
    try:
        generator.generate_all()
        assert False
    except TemplateAssertionError as e:
        assert e.filename == str(template_path / "Any.j2")
        assert e.message == "Template assertion failed."


def test_type_to_include(gen_paths):  # type: ignore
    """Test the type_to_include filter."""
    root_path = (gen_paths.dsdl_dir / Path("uavcan")).as_posix()
    output_path = gen_paths.out_dir / "type_to_include"
    compound_types = read_namespace(root_path, [])
    language_context = (
        LanguageContextBuilder()
        .set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".json")
        .create()
    )
    namespace = build_namespace_tree(compound_types, root_path, output_path, language_context)
    template_path = gen_paths.templates_dir / Path("type_to_include")
    generator = DSDLCodeGenerator(namespace, templates_dir=template_path)
    generator.generate_all()
    outfile = gen_paths.find_outfile_in_namespace("uavcan.time.SynchronizedTimestamp", namespace)

    assert outfile is not None

    with open(str(outfile), "r", encoding="utf-8") as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob["include"] == "uavcan/time/SynchronizedTimestamp_1_0.json"


def test_custom_filter_and_test(gen_paths):  # type: ignore
    root_path = str(gen_paths.dsdl_dir / Path("uavcan"))
    output_path = gen_paths.out_dir / "filter_and_test"
    compound_types = read_namespace(root_path, [])
    language_context = (
        LanguageContextBuilder()
        .set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".json")
        .create()
    )
    namespace = build_namespace_tree(compound_types, root_path, output_path, language_context)
    template_path = gen_paths.templates_dir / Path("custom_filter_and_test")
    generator = DSDLCodeGenerator(
        namespace,
        templates_dir=template_path,
        additional_filters={"custom_filter": lambda T: "hi mum"},
        additional_tests={"custom_test": lambda T: True},
    )

    generator.generate_all()
    outfile = gen_paths.find_outfile_in_namespace("uavcan.time.SynchronizedTimestamp", namespace)

    assert outfile is not None

    with open(str(outfile), "r", encoding="utf-8") as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob["filter_result"] == "hi mum"
    assert json_blob["test_result"] == "yes"


def test_custom_filter_and_test_redefinition():  # type: ignore
    language_context = (
        LanguageContextBuilder()
        .set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".json")
        .create()
    )
    namespace = Namespace.Identity(Path("uavcan"), language_context)

    with pytest.raises(RuntimeError):
        DSDLCodeGenerator(
            namespace,
            additional_filters={"type_to_include_path": lambda T: ""},
            additional_tests={"custom_test": lambda T: False},
        )

    with pytest.raises(RuntimeError):
        DSDLCodeGenerator(
            namespace,
            additional_filters={"custom_filter": lambda T: ""},
            additional_tests={"primitive": lambda T: False},
        )


def test_python_filter_full_reference_name(gen_paths):  # type: ignore
    lctx = LanguageContextBuilder().create()
    type_map = read_namespace(str(gen_paths.dsdl_dir / pathlib.Path("uavcan")), [])

    from nunavut.lang.py import filter_full_reference_name

    test_subject = next(filter(lambda type: (type.short_name == "SynchronizedTimestamp"), type_map))

    full_reference_name = filter_full_reference_name(lctx.get_language("nunavut.lang.py"), test_subject)
    assert "uavcan.time.SynchronizedTimestamp_1_0" == full_reference_name


def test_python_filter_short_reference_name(gen_paths):  # type: ignore
    lctx = LanguageContextBuilder().create()

    type_map = read_namespace(str(gen_paths.dsdl_dir / pathlib.Path("uavcan")), [])

    from nunavut.lang.py import filter_short_reference_name

    test_subject = next(filter(lambda type: (type.short_name == "SynchronizedTimestamp"), type_map))
    full_reference_name = filter_short_reference_name(lctx.get_language("nunavut.lang.py"), test_subject)
    assert "SynchronizedTimestamp_1_0" == full_reference_name


def test_python_filter_imports(gen_paths):  # type: ignore
    lctx = LanguageContextBuilder().create()

    type_map = read_namespace(str(gen_paths.dsdl_dir / pathlib.Path("uavcan")), [])

    from nunavut.lang.py import filter_imports

    test_subject = next(filter(lambda type: (type.short_name == "bar"), type_map))
    imports = filter_imports(lctx.get_language("nunavut.lang.py"), test_subject)
    assert len(imports) == 1
    assert "uavcan.time" == imports[0]


@pytest.mark.parametrize("stropping,sort", [(True, False), (False, True)])
def test_python_filter_imports_for_service_type(gen_paths, stropping, sort):  # type: ignore
    lctx = (
        LanguageContextBuilder()
        .set_target_language("py")
        .set_target_language_configuration_override(Language.WKCV_ENABLE_STROPPING, stropping)
        .create()
    )
    lctx.config.set("nunavut.lang.py", "enable_stropping", str(stropping))
    assert stropping == lctx.config.get_config_value_as_bool("nunavut.lang.py", "enable_stropping")

    type_map = read_namespace(str(gen_paths.dsdl_dir / pathlib.Path("uavcan")), [])

    from nunavut.lang.py import filter_imports

    test_subject = next(filter(lambda type: (type.short_name == "bar_svc"), type_map))
    imports = filter_imports(lctx.get_language("nunavut.lang.py"), test_subject, sort=sort)
    assert len(imports) == 2
    if stropping:
        assert "uavcan.str_" == imports[0]
    else:
        assert "uavcan.str" == imports[0]
    assert "uavcan.time" == imports[1]


@pytest.mark.parametrize("stropping,sort", [(True, False), (False, True)])
def test_python_filter_imports_for_array_type(gen_paths, stropping, sort):  # type: ignore
    lctx = (
        LanguageContextBuilder()
        .set_target_language("py")
        .set_target_language_configuration_override(Language.WKCV_ENABLE_STROPPING, stropping)
        .create()
    )
    uavcan_dir = str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))
    type_map = read_namespace(str(gen_paths.dsdl_dir / pathlib.Path("new")), [uavcan_dir])

    assert len(type_map) == 2

    from nunavut.lang.py import filter_imports

    test_subject = next(filter(lambda type: (type.short_name == "hotness"), type_map))
    imports = filter_imports(lctx.get_language("nunavut.lang.py"), test_subject, sort=sort)
    assert len(imports) == 3
    assert "new" == imports[0]
    if stropping:
        assert "uavcan.str_" == imports[1]
    else:
        assert "uavcan.str" == imports[1]
    assert "uavcan.time" == imports[2]


@pytest.mark.parametrize("stropping,sort", [(True, False), (False, True)])
def test_cpp_filter_includes(gen_paths, stropping, sort):  # type: ignore
    """
    Test the include header generator for C++ jinja templates.
    """
    lctx = (
        LanguageContextBuilder(include_experimental_languages=True)
        .set_target_language("cpp")
        .set_target_language_configuration_override(Language.WKCV_ENABLE_STROPPING, stropping)
        .set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".h")
        .set_target_language_configuration_override(
            Language.WKCV_LANGUAGE_OPTIONS, {"omit_serialization_support": True}
        )
        .create()
    )

    uavcan_dir = (gen_paths.dsdl_dir / pathlib.Path("uavcan")).as_posix()
    type_map = read_namespace((gen_paths.dsdl_dir / pathlib.Path("new")).as_posix(), [uavcan_dir])
    from nunavut.lang.cpp import filter_includes  # pylint: disable=import-outside-toplevel

    test_subject = next(filter(lambda type: (type.short_name == "hotness"), type_map))
    imports = filter_includes(lctx.get_target_language(), test_subject, sort=sort)
    assert len(imports) == 6

    def assert_path_in_imports(path: str) -> None:
        nonlocal imports
        assert path in imports

    if stropping:
        if sort:
            assert [
                '"_new/malloc_1_0.h"',
                '"uavcan/str/bar_1_0.h"',
                '"uavcan/time/SynchronizedTimestamp_1_0.h"',
                "<array>",
                "<cstdint>",
                "<limits>",
            ] == imports
        else:

            map(
                assert_path_in_imports,
                (
                    '"uavcan/time/SynchronizedTimestamp_1_0.h"',
                    '"_new/malloc_1_0.h"',
                    '"uavcan/str/bar_1_0.h"',
                    "<array>",
                    "<cstdint>",
                    "<limits>",
                ),
            )
    elif sort:
        assert [
            '"new/malloc_1_0.h"',
            '"uavcan/str/bar_1_0.h"',
            '"uavcan/time/SynchronizedTimestamp_1_0.h"',
            "<array>",
            "<cstdint>",
            "<limits>",
        ] == imports
    else:
        map(
            assert_path_in_imports,
            (
                '"uavcan/time/SynchronizedTimestamp_1_0.h"',
                '"new/malloc_1_0.h"',
                '"uavcan/str/bar_1_0.h"',
                "<array>",
                "<cstdint>",
                "<limits>",
            ),
        )


def test_filter_includes_cpp_vla(gen_paths):  # type: ignore
    """
    Test the include header generator for C++ jinja templates when using the vla.
    """
    lctx = (
        LanguageContextBuilder(include_experimental_languages=True)
        .set_target_language("cpp")
        .set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".h")
        .create()
    )
    type_map = read_namespace((gen_paths.dsdl_dir / pathlib.Path("vla")).as_posix())
    from nunavut.lang.cpp import filter_includes # pylint: disable=import-outside-toplevel

    test_subject = next(filter(lambda type: (type.short_name == "uses_vla"), type_map))
    imports = filter_includes(lctx.get_target_language(), test_subject)
    assert "<vector>" in imports


@typing.no_type_check
@pytest.mark.parametrize("language_name,namespace_separator", [("c", "_"), ("cpp", "::")])
def test_filter_full_reference_name_via_template(gen_paths, language_name, namespace_separator):
    root_path = (gen_paths.dsdl_dir / Path("uavcan")).as_posix()
    output_path = (gen_paths.out_dir / Path("filter_and_test")).as_posix()
    compound_types = read_namespace(root_path, [])
    language_context = (
        LanguageContextBuilder(include_experimental_languages=True).set_target_language(language_name).create()
    )
    namespace = build_namespace_tree(compound_types, root_path, output_path, language_context)
    template_path = gen_paths.templates_dir / Path("full_reference_test")
    generator = DSDLCodeGenerator(namespace, templates_dir=template_path)

    generator.generate_all()
    outfile = gen_paths.find_outfile_in_namespace("uavcan.str.bar_svc", namespace)

    assert outfile is not None

    with open(str(outfile), "r", encoding="utf-8") as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob["parent"]["full_reference_name"] == "uavcan.str.bar_svc_1_0".replace(".", namespace_separator)
    assert json_blob["parent"]["short_reference_name"] == "bar_svc" if language_name == "cpp" else "bar_svc_1_0"
    assert json_blob["request"]["full_reference_name"] == "uavcan.str.bar_svc.Request_1_0".replace(
        ".", namespace_separator
    )
    assert json_blob["request"]["short_reference_name"] == "Request_1_0"
    assert json_blob["response"]["full_reference_name"] == "uavcan.str.bar_svc.Response_1_0".replace(
        ".", namespace_separator
    )
    assert json_blob["response"]["short_reference_name"] == "Response_1_0"


@typing.no_type_check
@pytest.mark.parametrize(
    "language_name,stropping,namespace_separator",
    [("c", False, "_"), ("c", True, "_"), ("cpp", False, "::"), ("cpp", True, "::")],
)
def test_filter_full_reference_name(language_name, stropping, namespace_separator):
    """
    Cover issue #153
    """
    lctx = (
        LanguageContextBuilder(include_experimental_languages=True)
        .set_target_language(language_name)
        .set_target_language_configuration_override(Language.WKCV_ENABLE_STROPPING, stropping)
        .create()
    )
    ln_package_name = LanguageClassLoader.to_language_module_name(language_name)
    ln = lctx.get_language(ln_package_name)

    # pylint: disable=import-outside-toplevel
    import importlib

    from pydsdl import ServiceType, StructureType, Version

    test_subject_module = importlib.import_module(ln_package_name)

    namespace_parts = ["register", "getting", "tired", "of"]
    stem = "Python"
    source_file = Path(*namespace_parts) / Path(f"{stem}_0_1").with_suffix(".dsdl")
    service_request_type = StructureType(
        name=f"{'.'.join(namespace_parts)}.{stem}.Request",
        version=Version(0, 1),
        attributes=[],
        deprecated=False,
        fixed_port_id=None,
        source_file_path=source_file,
        has_parent_service=True,
    )
    service_response_type = StructureType(
        name=f"{'.'.join(namespace_parts)}.{stem}.Response",
        version=Version(0, 1),
        attributes=[],
        deprecated=False,
        fixed_port_id=None,
        source_file_path=source_file,
        has_parent_service=True,
    )

    service_type = ServiceType(service_request_type, service_response_type, None)

    # C++ is special because namespaces are part of the language and therefore each namespace
    # name must be stropped
    top_level_name = "_register" if stropping and language_name == "cpp" else "register"
    result_format = f"{top_level_name}.getting.tired.of.Python{{}}_0_1".replace(".", namespace_separator)

    assert test_subject_module.filter_full_reference_name(ln, service_type) == result_format.format("")
    assert test_subject_module.filter_full_reference_name(ln, service_request_type) == result_format.format(
        ".Request".replace(".", namespace_separator)
    )
    assert test_subject_module.filter_full_reference_name(ln, service_response_type) == result_format.format(
        ".Response".replace(".", namespace_separator)
    )


@typing.no_type_check
def test_filter_to_template_unique(gen_paths):
    """
    Cover issue #88
    """
    root_path = str(gen_paths.dsdl_dir / Path("one"))
    output_path = gen_paths.out_dir / "to_unique"
    compound_types = read_namespace(root_path, [])
    language_context = LanguageContextBuilder(include_experimental_languages=True).set_target_language("c").create()
    namespace = build_namespace_tree(compound_types, root_path, output_path, language_context)
    template_path = gen_paths.templates_dir / Path("to_unique")
    generator = DSDLCodeGenerator(namespace, templates_dir=template_path)
    generator.generate_all()
    outfile = gen_paths.find_outfile_in_namespace("one.foo", namespace)

    assert outfile is not None

    expected = "_f0_\n_f1_\n_f2_\n_f3_\n\n_f4_\n_f5_\n_f6_\n_f7_\n\n_f8_\n_f9_\n_f10_\n_f11_\n"

    with open(str(outfile), "r", encoding="utf-8") as foo_file:
        actual = foo_file.read()

    assert expected == actual
