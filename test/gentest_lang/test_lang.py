#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

from pathlib import Path

import pytest

from typing import Dict

from pydsdl import read_namespace
from nunavut import build_namespace_tree, lang
from nunavut.jinja import Generator

from nunavut.jinja.jinja2 import Environment


@pytest.fixture
def gen_paths():  # type: ignore
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


class Dummy:

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

# +---------------------------------------------------------------------------+
# | PARAMETERIZED TESTS
# +---------------------------------------------------------------------------+

def ptest_lang_c(gen_paths, implicit):  # type: ignore
    """ Generates and verifies JSON with values filtered using the c language support module.
    """

    root_namespace_dir = gen_paths.dsdl_dir / Path("langtest")
    if implicit:
        templates_dirs = [gen_paths.templates_dir / Path("implicit") / Path("c")]
    else:
        templates_dirs = [gen_paths.templates_dir / Path("explicit")]

    templates_dirs.append(gen_paths.templates_dir / Path("common"))

    root_namespace = str(root_namespace_dir)
    compound_types = read_namespace(root_namespace, '', allow_unregulated_fixed_port_id=True)
    namespace = build_namespace_tree(compound_types,
                                     root_namespace_dir,
                                     gen_paths.out_dir,
                                     '.py',
                                     '_')
    generator = Generator(namespace,
                          False,
                          templates_dirs,
                          implicit_language_support=('c' if implicit else None))
    generator.generate_all(False)

    # Now read back in and verify
    outfile = gen_paths.find_outfile_in_namespace("langtest.c.TestType", namespace)

    assert (outfile is not None)

    generated_values = {}  # type: Dict
    with open(str(outfile), 'r') as python_file:
        exec(python_file.read(), generated_values)

    assert len(generated_values) > 0

    lang_c_output = generated_values["tests"]["lang_c"]
    assert lang_c_output["namespace"] == "langtest.c"
    assert lang_c_output["namespace_macrofy"] == "LANGTEST_C"

    assert lang_c_output["ctype_std truncated uint8"] == "uint8_t"
    assert lang_c_output["ctype_std saturated int8"] == "int8_t"
    assert lang_c_output["ctype_std truncated uint9"] == "uint16_t"
    assert lang_c_output["ctype_std saturated int9"] == "int16_t"

    assert lang_c_output["ctype truncated uint8"] == "unsigned char"
    assert lang_c_output["ctype saturated int8"] == "char"
    assert lang_c_output["ctype truncated uint9"] == "unsigned int"
    assert lang_c_output["ctype saturated int9"] == "int"

    assert lang_c_output["ctype_std truncated uint32"] == "uint32_t"
    assert lang_c_output["ctype_std saturated int32"] == "int32_t"
    assert lang_c_output["ctype_std truncated uint64"] == "uint64_t"
    assert lang_c_output["ctype_std saturated int64"] == "int64_t"

    assert lang_c_output["ctype truncated uint32"] == "unsigned long"
    assert lang_c_output["ctype saturated int32"] == "long"
    assert lang_c_output["ctype truncated uint64"] == "unsigned long long"
    assert lang_c_output["ctype saturated int64"] == "long long"

    assert lang_c_output["ctype saturated bool"] == "BOOL"
    assert lang_c_output["ctype_std saturated bool"] == "bool"

    assert "_nAME0_" == lang_c_output["unique_name_0"]
    assert "_nAME1_" == lang_c_output["unique_name_1"]
    assert "_naME0_" == lang_c_output["unique_name_2"]
    assert "_0_" == lang_c_output["unique_name_3"]
    return generated_values


def ptest_lang_cpp(gen_paths, implicit):  # type: ignore
    """Generates and verifies JSON with values filtered using the cpp language module.
    """

    root_namespace_dir = gen_paths.dsdl_dir / Path("langtest")
    root_namespace = str(root_namespace_dir)
    compound_types = read_namespace(root_namespace, '', allow_unregulated_fixed_port_id=True)
    if implicit:
        templates_dirs = [gen_paths.templates_dir / Path("implicit") / Path("cpp")]
    else:
        templates_dirs = [gen_paths.templates_dir / Path("explicit")]

    templates_dirs.append(gen_paths.templates_dir / Path("common"))

    namespace = build_namespace_tree(compound_types,
                                     root_namespace_dir,
                                     gen_paths.out_dir,
                                     '.py',
                                     '_')

    generator = Generator(namespace,
                          False,
                          templates_dirs,
                          implicit_language_support=('cpp' if implicit else None))

    generator.generate_all(False)

    # Now read back in and verify
    outfile = gen_paths.find_outfile_in_namespace("langtest.cpp.ns.TestType", namespace)

    assert (outfile is not None)

    generated_values = {}  # type: Dict
    with open(str(outfile), 'r') as python_file:
        exec(python_file.read(), generated_values)

    assert len(generated_values)

    lang_cpp_output = generated_values["tests"]["lang_cpp"]
    assert lang_cpp_output["namespace"] == "langtest.cpp.ns"
    assert lang_cpp_output["namespace_open"] == r'''namespace langtest
{
namespace cpp
{
namespace ns
{
'''
    assert lang_cpp_output["namespace_open_wo_nl"] == r'''namespace langtest {
namespace cpp {
namespace ns {
'''
    assert lang_cpp_output["namespace_close"] == r'''}
}
}
'''
    assert lang_cpp_output["namespace_close_w_comments"] == r'''} // ns
} // cpp
} // langtest
'''
    return generated_values


def ptest_lang_py(gen_paths, implicit):  # type: ignore
    """ Generates and verifies JSON with values filtered using the python language support module.
    """

    root_namespace_dir = gen_paths.dsdl_dir / Path("langtest")
    root_namespace = str(root_namespace_dir)
    if implicit:
        templates_dirs = [gen_paths.templates_dir / Path("implicit") / Path("py")]
    else:
        templates_dirs = [gen_paths.templates_dir / Path("explicit")]

    templates_dirs.append(gen_paths.templates_dir / Path("common"))

    compound_types = read_namespace(root_namespace, '', allow_unregulated_fixed_port_id=True)
    namespace = build_namespace_tree(compound_types,
                                     root_namespace_dir,
                                     gen_paths.out_dir,
                                     '.py',
                                     '_')
    generator = Generator(namespace,
                          False,
                          templates_dirs,
                          implicit_language_support=('py' if implicit else None))

    generator.generate_all(False)

    # Now read back in and verify
    outfile = gen_paths.find_outfile_in_namespace("langtest.py.TestType", namespace)

    assert (outfile is not None)

    generated_values = {}  # type: Dict
    with open(str(outfile), 'r') as python_file:
        exec(python_file.read(), generated_values)

    assert len(generated_values) > 0

    lang_py_output = generated_values["tests"]["lang_py"]
    assert "_NAME0_" == lang_py_output["unique_name_0"]
    assert "_NAME1_" == lang_py_output["unique_name_1"]
    assert "_name0_" == lang_py_output["unique_name_2"]
    assert "identifier_zero" == lang_py_output["id_0"]
    return generated_values

# +---------------------------------------------------------------------------+
# | TESTS
# +---------------------------------------------------------------------------+


def test_lang_c(gen_paths):  # type: ignore
    """ Generates and verifies JSON with values filtered using the c language support module.
    """
    generated_values = ptest_lang_c(gen_paths, True)
    lang_any = generated_values["tests"]["lang_any"]
    assert lang_any['id_0'] == '_123_class__for_u2___ZX0028ZX002Aother_stuffZX002DZX0026ZX002DsuchZX0029'
    assert lang_any['id_1'] == '_reserved'
    assert lang_any['id_2'] == '_ZX005Falso_reserved'
    assert lang_any['id_3'] == '_register'
    assert lang_any['id_4'] == 'False'
    assert lang_any['id_5'] == '_return'
    assert lang_any['id_6'] == ':poop:return'
    assert lang_any['id_7'] == 'I_ZX2764_UAVCAN'
    assert lang_any['id_8'] == 'I_0x2764_UAVCAN'

    assert lang_any['id_9'] == 'str'
    assert lang_any['id_A'] == '_strr'
    assert lang_any['id_B'] == '_uINT_FOO_MIN'
    assert lang_any['id_C'] == '_iNT_C'
    assert lang_any['id_D'] == '_lC_Is_reserved'
    assert lang_any['id_E'] == 'NOT_ATOMIC_YO'
    assert lang_any['id_F'] == '_aTOMIC_YO'

    assert '_flight__time' == lang.c.filter_id(Dummy('_Flight__time'))


def test_lang_c_explicit(gen_paths):  # type: ignore
    """
    Generates and verifies JSON with values filtered using the c language support module using
    explicit language feature names.
    """
    ptest_lang_c(gen_paths, False)


def test_lang_cpp(gen_paths):  # type: ignore
    """
    Generates and verifies JSON with values filtered using the cpp language module.
    """

    generated_values = ptest_lang_cpp(gen_paths, True)
    lang_any = generated_values["tests"]["lang_any"]
    assert lang_any['id_0'] == '_123_class_ZX005Ffor_u2_ZX005F_ZX0028ZX002Aother_stuffZX002DZX0026ZX002DsuchZX0029'
    assert lang_any['id_1'] == '_reserved'
    assert lang_any['id_2'] == '_ZX005Falso_reserved'
    assert lang_any['id_3'] == '_register'
    assert lang_any['id_4'] == 'False'
    assert lang_any['id_5'] == '_return'
    assert lang_any['id_6'] == ':poop:return'
    assert lang_any['id_7'] == 'I_ZX2764_UAVCAN'
    assert lang_any['id_8'] == 'I_0x2764_UAVCAN'
    assert lang_any['id_9'] == 'str'
    assert lang_any['id_A'] == '_strr'
    assert lang_any['id_B'] == '_uINT_FOO_MIN'
    assert lang_any['id_C'] == '_iNT_C'
    assert lang_any['id_D'] == '_lC_Is_reserved'
    assert lang_any['id_E'] == 'NOT_ATOMIC_YO'
    assert lang_any['id_F'] == '_aTOMIC_YO'

    with pytest.raises(RuntimeError):
        lang.cpp.filter_id('foo', '_', '__')

    assert '_flight_ZX005Ftime' == lang.cpp.filter_id(Dummy('_Flight__time'))


def test_lang_cpp_explicit(gen_paths):  # type: ignore
    """
    Generates and verifies JSON with values filtered using the cpp language module using
    explicit language feature names.
    """

    ptest_lang_cpp(gen_paths, False)


def test_c_to_snake_case():  # type: ignore
    assert "scotec_mcu_timer" == lang.c.filter_to_snake_case("scotec.mcu.Timer")
    assert "scotec_mcu_timer_helper" == lang.c.filter_to_snake_case("scotec.mcu.TimerHelper")
    assert "aa_bb_c_cc_aaa_a_aa_aaa_aa_aaa_a_a" == lang.c.filter_to_snake_case(" aa bb. cCcAAa_aAa_AAaAa_AAaA_a ")


def test_lang_py(gen_paths):  # type: ignore
    """ Generates and verifies JSON with values filtered using the python language support module.
    """

    generated_values = ptest_lang_py(gen_paths, True)
    lang_any = generated_values["tests"]["lang_any"]
    assert lang_any['id_0'] == '_123_class__for_u2___ZX0028ZX002Aother_stuffZX002DZX0026ZX002DsuchZX0029'
    assert lang_any['id_1'] == '_Reserved'
    assert lang_any['id_2'] == '__also_reserved'
    assert lang_any['id_3'] == 'register'
    assert lang_any['id_4'] == 'False_'
    assert lang_any['id_5'] == 'return_'
    assert lang_any['id_6'] == 'return:poop:'
    assert lang_any['id_7'] == 'I_ZX2764_UAVCAN'
    assert lang_any['id_8'] == 'I_0x2764_UAVCAN'
    assert lang_any['id_9'] == 'str_'
    assert lang_any['id_A'] == 'strr'
    assert lang_any['id_B'] == 'UINT_FOO_MIN'
    assert lang_any['id_C'] == 'INT_C'
    assert lang_any['id_D'] == 'LC_Is_reserved'
    assert lang_any['id_E'] == 'NOT_ATOMIC_YO'
    assert lang_any['id_F'] == 'ATOMIC_YO'

    assert '_Flight__time' == lang.py.filter_id(Dummy('_Flight__time'))


def test_lang_py_explicit(gen_paths):  # type: ignore
    """ 
    Generates and verifies JSON with values filtered using the python language support module using
    explicit language feature names.
    """

    ptest_lang_py(gen_paths, False)


def test_multiple_implicit_languages(gen_paths):  # type: ignore
    """
    Verifies that any dsdl type will resolve to an ``Any`` template.
    """
    dummy_env = Environment()
    lang.add_language_support('c', dummy_env, True)
    lang.add_language_support('c', dummy_env, True)
    with pytest.raises(RuntimeError):
        lang.add_language_support('cpp', dummy_env, True)
