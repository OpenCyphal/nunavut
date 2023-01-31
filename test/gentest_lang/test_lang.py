#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#

from pathlib import Path
from typing import Any, Callable, Dict, List
from unittest.mock import MagicMock

import pytest
from nunavut import build_namespace_tree
from nunavut.jinja import DSDLCodeGenerator
from nunavut._dependencies import Dependencies
from nunavut.lang import Language, LanguageContext, LanguageClassLoader, LanguageContextBuilder
from nunavut.lang.c import filter_id as c_filter_id
from nunavut.lang.cpp import filter_id as cpp_filter_id
from nunavut.lang.py import filter_id as py_filter_id
from nunavut._utilities import YesNoDefault
from pydsdl import read_namespace


class Dummy:
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name


# +---------------------------------------------------------------------------+
# | PARAMETERIZED TESTS
# +---------------------------------------------------------------------------+


def ptest_lang_c(
    gen_paths: Any,
    implicit: bool,
    unique_name_evaluator: Any,
    use_standard_types: bool,
) -> Dict:
    """Generates and verifies JSON with values filtered using the c language support module."""

    root_namespace_dir = gen_paths.dsdl_dir / Path("langtest")
    if implicit:
        templates_dirs = [gen_paths.templates_dir / Path("implicit") / Path("c")]
    else:
        templates_dirs = [gen_paths.templates_dir / Path("explicit")]

    templates_dirs.append(gen_paths.templates_dir / Path("common"))

    root_namespace = str(root_namespace_dir)
    compound_types = read_namespace(root_namespace, [], allow_unregulated_fixed_port_id=True)

    builder = LanguageContextBuilder(include_experimental_languages=True).set_target_language_configuration_override(
        "use_standard_types", use_standard_types
    )
    if implicit:
        builder.set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".h")
    else:
        builder.set_target_language("c")

    language_context = builder.create()
    namespace = build_namespace_tree(compound_types, root_namespace_dir, gen_paths.out_dir, language_context)
    generator = DSDLCodeGenerator(namespace, templates_dir=templates_dirs)
    generator.generate_all()

    # Now read back in and verify
    outfile = gen_paths.find_outfile_in_namespace("langtest.c.TestType", namespace)

    assert outfile is not None

    generated_values = {}  # type: Dict
    with open(str(outfile), "r") as python_file:
        exec(python_file.read(), generated_values)

    assert len(generated_values) > 0

    lang_c_output = generated_values["tests"]["lang_c"]
    assert lang_c_output["namespace"] == "langtest.c"
    assert lang_c_output["namespace_macrofy"] == "LANGTEST_C"

    if use_standard_types:
        assert lang_c_output["ctype truncated uint8"] == "uint8_t"
        assert lang_c_output["ctype saturated int8"] == "int8_t"
        assert lang_c_output["ctype truncated uint9"] == "uint16_t"
        assert lang_c_output["ctype saturated int9"] == "int16_t"
    else:
        assert lang_c_output["ctype truncated uint8"] == "unsigned char"
        assert lang_c_output["ctype saturated int8"] == "char"
        assert lang_c_output["ctype truncated uint9"] == "unsigned int"
        assert lang_c_output["ctype saturated int9"] == "int"

    if use_standard_types:
        assert lang_c_output["ctype truncated uint32"] == "uint32_t"
        assert lang_c_output["ctype saturated int32"] == "int32_t"
        assert lang_c_output["ctype truncated uint64"] == "uint64_t"
        assert lang_c_output["ctype saturated int64"] == "int64_t"
    else:
        assert lang_c_output["ctype truncated uint32"] == "unsigned long"
        assert lang_c_output["ctype saturated int32"] == "long"
        assert lang_c_output["ctype truncated uint64"] == "unsigned long long"
        assert lang_c_output["ctype saturated int64"] == "long long"

    assert lang_c_output["ctype saturated bool"] == "bool"

    unique_name_evaluator(r"_nAME\d+_", lang_c_output["unique_name_0"])
    unique_name_evaluator(r"_nAME\d+_", lang_c_output["unique_name_1"])
    unique_name_evaluator(r"_naME\d+_", lang_c_output["unique_name_2"])
    unique_name_evaluator(r"_\d+_", lang_c_output["unique_name_3"])

    return generated_values


def ptest_lang_cpp(gen_paths, implicit):  # type: ignore
    """Generates and verifies JSON with values filtered using the cpp language module."""

    root_namespace_dir = gen_paths.dsdl_dir / Path("langtest")
    root_namespace = str(root_namespace_dir)
    compound_types = read_namespace(root_namespace, [], allow_unregulated_fixed_port_id=True)
    if implicit:
        templates_dirs = [gen_paths.templates_dir / Path("implicit") / Path("cpp")]
    else:
        templates_dirs = [gen_paths.templates_dir / Path("explicit")]

    templates_dirs.append(gen_paths.templates_dir / Path("common"))

    builder = LanguageContextBuilder(include_experimental_languages=True)
    if implicit:
        builder.set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".hpp")
    else:
        builder.set_target_language("cpp")

    language_context = builder.create()

    namespace = build_namespace_tree(compound_types, root_namespace_dir, gen_paths.out_dir, language_context)

    generator = DSDLCodeGenerator(namespace, templates_dir=templates_dirs)

    generator.generate_all(False)

    # Now read back in and verify
    outfile = gen_paths.find_outfile_in_namespace("langtest.cpp.ns.TestType", namespace)

    assert outfile is not None

    generated_values = {}  # type: Dict
    with open(str(outfile), "r") as python_file:
        exec(python_file.read(), generated_values)

    assert len(generated_values)

    lang_cpp_output = generated_values["tests"]["lang_cpp"]
    assert lang_cpp_output["namespace"] == "langtest.cpp.ns"
    assert (
        lang_cpp_output["namespace_open"]
        == r"""namespace langtest
{
namespace cpp
{
namespace ns
{"""
    )
    assert (
        lang_cpp_output["namespace_open_wo_nl"]
        == r"""namespace langtest {
namespace cpp {
namespace ns {"""
    )
    assert (
        lang_cpp_output["namespace_close"]
        == r"""}
}
}"""
    )
    assert (
        lang_cpp_output["namespace_close_w_comments"]
        == r"""} // namespace ns
} // namespace cpp
} // namespace langtest"""
    )
    return generated_values


def ptest_lang_py(gen_paths, implicit, unique_name_evaluator):  # type: ignore
    """Generates and verifies JSON with values filtered using the python language support module."""

    root_namespace_dir = gen_paths.dsdl_dir / Path("langtest")
    root_namespace = str(root_namespace_dir)
    if implicit:
        templates_dirs = [gen_paths.templates_dir / Path("implicit") / Path("py")]
    else:
        templates_dirs = [gen_paths.templates_dir / Path("explicit")]

    templates_dirs.append(gen_paths.templates_dir / Path("common"))

    compound_types = read_namespace(root_namespace, [], allow_unregulated_fixed_port_id=True)

    builder = LanguageContextBuilder(include_experimental_languages=True)
    if implicit:
        builder.set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".py")
    else:
        builder.set_target_language("py")

    language_context = builder.create()

    namespace = build_namespace_tree(compound_types, root_namespace_dir, gen_paths.out_dir, language_context)
    generator = DSDLCodeGenerator(namespace, generate_namespace_types=YesNoDefault.NO, templates_dir=templates_dirs)

    generator.generate_all(False)

    # Now read back in and verify
    outfile = gen_paths.find_outfile_in_namespace("langtest.py.TestType", namespace)

    assert outfile is not None

    generated_values = {}  # type: Dict
    with open(str(outfile), "r") as python_file:
        exec(python_file.read(), generated_values)

    assert len(generated_values) > 0

    lang_py_output = generated_values["tests"]["lang_py"]
    unique_name_evaluator(r"_NAME\d+_", lang_py_output["unique_name_0"])
    unique_name_evaluator(r"_NAME\d+_", lang_py_output["unique_name_1"])
    unique_name_evaluator(r"_name\d+_", lang_py_output["unique_name_2"])
    assert "identifier_zero" == lang_py_output["id_0"]

    many_unique_names = lang_py_output.get("many_unique_names")
    if many_unique_names is not None:
        for name in many_unique_names:
            unique_name_evaluator(r"_f\d+_", name)

    return generated_values


# +---------------------------------------------------------------------------+
# | TESTS
# +---------------------------------------------------------------------------+


@pytest.mark.parametrize("implicit,use_standard_types", [(True, True), (True, False), (False, True), (False, False)])
def test_lang_c(gen_paths: Any, unique_name_evaluator: Any, implicit: bool, use_standard_types: bool) -> None:
    """
    Generates and verifies JSON with values filtered using the c language support module.
    """
    generated_values = ptest_lang_c(gen_paths, implicit, unique_name_evaluator, use_standard_types)
    if implicit:
        lang_any = generated_values["tests"]["lang_any"]

        assert lang_any["id_0"] == "zX003123_class__for_u2___zX0028zX002Aother_stuffzX002DzX0026zX002DsuchzX0029"
        assert lang_any["id_1"] == "_reserved"
        assert lang_any["id_2"] == "_also_reserved"
        assert lang_any["id_3"] == "_register"
        assert lang_any["id_4"] == "False"
        assert lang_any["id_5"] == "_return"
        assert lang_any["id_7"] == "I_zX2764_Cyphal"
        assert lang_any["id_8"] == "zX0031_zX2764_Cyphal"

        assert lang_any["id_9"] == "str"
        assert lang_any["id_A"] == "_strr"
        assert lang_any["id_B"] == "_uINT_FOO_MIN"
        assert lang_any["id_C"] == "_iNT_C"
        assert lang_any["id_D"] == "LC_Is_reserved"
        assert lang_any["id_E"] == "NOT_ATOMIC_YO"
        assert lang_any["id_F"] == "_aTOMIC_YO"
        assert lang_any["id_G"] == "_memory_order_yo"

    lctx = LanguageContextBuilder().set_target_language("c").create()
    assert "_flight__time" == c_filter_id(lctx.get_target_language(), Dummy("_Flight__time"))


def test_lang_cpp(gen_paths):  # type: ignore
    """
    Generates and verifies JSON with values filtered using the cpp language module.
    """
    generated_values = ptest_lang_cpp(gen_paths, True)
    lang_any = generated_values["tests"]["lang_any"]

    assert lang_any["id_0"] == "_123_class_for_u2_zX0028zX002Aother_stuffzX002DzX0026zX002DsuchzX0029"
    assert lang_any["id_1"] == "_reserved"
    assert lang_any["id_2"] == "zX005FzX005Falso_reserved"
    assert lang_any["id_3"] == "_register"
    assert lang_any["id_4"] == "False"
    assert lang_any["id_5"] == "_return"
    assert lang_any["id_7"] == "I_zX2764_Cyphal"
    assert lang_any["id_8"] == "_1_zX2764_Cyphal"
    assert lang_any["id_9"] == "str"
    assert lang_any["id_A"] == "strr"
    assert lang_any["id_B"] == "UINT_FOO_MIN"
    assert lang_any["id_C"] == "INT_C"
    assert lang_any["id_D"] == "LC_Is_reserved"
    assert lang_any["id_E"] == "NOT_ATOMIC_YO"
    assert lang_any["id_F"] == "ATOMIC_YO"
    assert lang_any["id_G"] == "memory_order_yo"

    lang_cpp = (
        LanguageContextBuilder(include_experimental_languages=True)
        .set_target_language("cpp")
        .create()
        .get_target_language()
    )

    assert "_flight_time" == cpp_filter_id(lang_cpp, Dummy("_Flight_time"))


def test_lang_cpp_explicit(gen_paths):  # type: ignore
    """
    Generates and verifies JSON with values filtered using the cpp language module using
    explicit language feature names.
    """

    ptest_lang_cpp(gen_paths, False)


def test_lang_py_implicit(gen_paths, unique_name_evaluator):  # type: ignore
    """Generates and verifies JSON with values filtered using the python language support module."""

    generated_values = ptest_lang_py(gen_paths, True, unique_name_evaluator)
    lang_any = generated_values["tests"]["lang_any"]

    assert lang_any["id_0"] == "zX003123_class__for_u2___zX0028zX002Aother_stuffzX002DzX0026zX002DsuchzX0029"
    assert lang_any["id_1"] == "_Reserved"
    assert lang_any["id_2"] == "__also_reserved"
    assert lang_any["id_3"] == "register"
    assert lang_any["id_4"] == "False_"
    assert lang_any["id_5"] == "return_"
    assert lang_any["id_7"] == "I_zX2764_Cyphal"
    assert lang_any["id_8"] == "zX0031_zX2764_Cyphal"
    assert lang_any["id_9"] == "str_"
    assert lang_any["id_A"] == "strr"
    assert lang_any["id_B"] == "UINT_FOO_MIN"
    assert lang_any["id_C"] == "INT_C"
    assert lang_any["id_D"] == "LC_Is_reserved"
    assert lang_any["id_E"] == "NOT_ATOMIC_YO"
    assert lang_any["id_F"] == "ATOMIC_YO"

    lctx = LanguageContextBuilder().set_target_language("py").create()

    assert "_Flight__time" == py_filter_id(lctx.get_target_language(), Dummy("_Flight__time"))


def test_lang_py_explicit(gen_paths, unique_name_evaluator):  # type: ignore
    """
    Generates and verifies JSON with values filtered using the python language support module using
    explicit language feature names.
    """

    ptest_lang_py(gen_paths, False, unique_name_evaluator)


def test_language_object() -> None:
    """
    Verify that the Language module object works as required.
    """
    mock_config = MagicMock()

    class TestLang(Language):
        def get_includes(self, deps: Dependencies) -> List[str]:
            return []

    language = TestLang(LanguageClassLoader.to_language_module_name("c"), mock_config)

    assert "c" == language.name

    assert language.stable_support


def test_language_context() -> None:
    """
    Verify that the LanguageContext objects works as required.
    """

    context_w_no_target = (
        LanguageContextBuilder(include_experimental_languages=True)
        .create()
    )

    assert None is not context_w_no_target.get_target_language()
    assert "c" in context_w_no_target.get_supported_languages()
    assert "cpp" in context_w_no_target.get_supported_languages()
    assert "py" in context_w_no_target.get_supported_languages()

    assert "foo" == context_w_no_target.filter_id_for_target("foo", "")

    context_w_target = (
        LanguageContextBuilder(include_experimental_languages=True)
        .set_target_language("c")
        .create()
    )

    assert context_w_target.get_target_language() is not None

    target_language = context_w_target.get_target_language()
    assert target_language is not None
    target_named_types = target_language.named_types
    assert "byte" in target_named_types


def test_either_target_or_extension() -> None:
    """
    LanguageContext requires either a target or an extension or both but not
    neither.
    """

    assert "py" == (
        LanguageContextBuilder()
        .set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".py")
        .create()
        .get_target_language()
        .name
    )
    assert "py" == (
        LanguageContextBuilder()
        .set_target_language("py")
        .create()
        .get_target_language()
        .name
    )
    assert "py" == (
        LanguageContextBuilder()
        .set_target_language("py")
        .set_target_language_configuration_override(Language.WKCV_DEFINITION_FILE_EXTENSION, ".py")
        .create()
        .get_target_language()
        .name
    )
    assert LanguageContextBuilder.DEFAULT_TARGET_LANGUAGE == (
        LanguageContextBuilder()
        .create()
        .get_target_language()
        .name
    )

def test_lang_cpp_use_vector(gen_paths) -> None:
    """
    Test override of the built-in variable-length array type.
    """
