#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

from pathlib import Path

import pytest

from typing import Dict

from pydsdl import read_namespace
from pydsdlgen import build_namespace_tree
from pydsdlgen.jinja import Generator
from pydsdlgen.jinja.lang import c


@pytest.fixture
def gen_paths():  # type: ignore
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


def test_lang_c(gen_paths):  # type: ignore
    """ Generates and verifies JSON with values filtered using the c language support module.
    """

    root_namespace_dir = gen_paths.dsdl_dir / Path("langtest")
    root_namespace = str(root_namespace_dir)
    compound_types = read_namespace(root_namespace, '', allow_unregulated_fixed_port_id=True)
    namespace = build_namespace_tree(compound_types,
                                     root_namespace_dir,
                                     gen_paths.out_dir,
                                     '.py',
                                     '_')
    generator = Generator(namespace, False, gen_paths.templates_dir)
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


def test_lang_cpp(gen_paths):  # type: ignore
    """Generates and verifies JSON with values filtered using the cpp language module.
    """

    root_namespace_dir = gen_paths.dsdl_dir / Path("langtest")
    root_namespace = str(root_namespace_dir)
    compound_types = read_namespace(root_namespace, '', allow_unregulated_fixed_port_id=True)
    namespace = build_namespace_tree(compound_types,
                                     root_namespace_dir,
                                     gen_paths.out_dir,
                                     '.py',
                                     '_')
    generator = Generator(namespace, False, gen_paths.templates_dir)
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


def test_c_to_snake_case():  # type: ignore
    assert "scotec_mcu_timer" == c.filter_to_snake_case("scotec.mcu.Timer")
    assert "scotec_mcu_timer_helper" == c.filter_to_snake_case("scotec.mcu.TimerHelper")
    assert "aa_bb_c_cc_aaa_a_aa_aaa_aa_aaa_a_a" == c.filter_to_snake_case(" aa bb. cCcAAa_aAa_AAaAa_AAaA_a ")
