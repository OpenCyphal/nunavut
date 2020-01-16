#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

import json
import pathlib
from pathlib import Path, PurePath

import pytest
from pydsdl import read_namespace

from nunavut import Namespace, build_namespace_tree
from nunavut.jinja import Generator
from nunavut.jinja.jinja2.exceptions import TemplateAssertionError
from nunavut.lang import LanguageContext


def test_template_assert(gen_paths):  # type: ignore
    """
    Tests our template assertion extension.
    """
    root_path = str(gen_paths.dsdl_dir / Path("uavcan"))
    output_path = gen_paths.out_dir / 'assert'
    compound_types = read_namespace(root_path, [])
    language_context = LanguageContext(extension='.json')
    namespace = build_namespace_tree(compound_types,
                                     root_path,
                                     output_path,
                                     language_context)
    template_path = gen_paths.templates_dir / Path('assert')
    generator = Generator(namespace, templates_dir=template_path)
    try:
        generator.generate_all()
        assert False
    except TemplateAssertionError as e:
        e.filename == str(template_path / "Any.j2")
        e.filename == 2
        e.message == 'Template assertion failed.'


def test_type_to_include(gen_paths):  # type: ignore
    """Test the type_to_include filter."""
    root_path = str(gen_paths.dsdl_dir / Path("uavcan"))
    output_path = gen_paths.out_dir / 'type_to_include'
    compound_types = read_namespace(root_path, [])
    language_context = LanguageContext(extension='.json')
    namespace = build_namespace_tree(compound_types,
                                     root_path,
                                     output_path,
                                     language_context)
    template_path = gen_paths.templates_dir / Path('type_to_include')
    generator = Generator(namespace, templates_dir=template_path)
    generator.generate_all()
    outfile = gen_paths.find_outfile_in_namespace("uavcan.time.SynchronizedTimestamp", namespace)

    assert (outfile is not None)

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob['include'] == "uavcan/time/SynchronizedTimestamp_1_0.json"


def test_custom_filter_and_test(gen_paths):  # type: ignore
    root_path = str(gen_paths.dsdl_dir / Path("uavcan"))
    output_path = gen_paths.out_dir / 'filter_and_test'
    compound_types = read_namespace(root_path, [])
    language_context = LanguageContext(extension='.json')
    namespace = build_namespace_tree(compound_types,
                                     root_path,
                                     output_path,
                                     language_context)
    template_path = gen_paths.templates_dir / Path('custom_filter_and_test')
    generator = Generator(namespace,
                          templates_dir=template_path,
                          additional_filters={'custom_filter': lambda T: 'hi mum'},
                          additional_tests={'custom_test': lambda T: True})

    generator.generate_all()
    outfile = gen_paths.find_outfile_in_namespace("uavcan.time.SynchronizedTimestamp", namespace)

    assert (outfile is not None)

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob['filter_result'] == 'hi mum'
    assert json_blob['test_result'] == 'yes'


def test_custom_filter_and_test_redefinition(gen_paths):  # type: ignore
    language_context = LanguageContext(extension='.json')
    namespace = Namespace('', Path(), PurePath(), language_context)

    with pytest.raises(RuntimeError):
        Generator(namespace,
                  additional_filters={'type_to_include_path': lambda T: ''},
                  additional_tests={'custom_test': lambda T: False})

    with pytest.raises(RuntimeError):
        Generator(namespace,
                  additional_filters={'custom_filter': lambda T: ''},
                  additional_tests={'primitive': lambda T: False})


def test_python_filter_full_reference_name(gen_paths):  # type: ignore
    lctx = LanguageContext()
    type_map = read_namespace(str(gen_paths.dsdl_dir / pathlib.Path('uavcan')), [])

    from nunavut.lang.py import filter_full_reference_name

    test_subject = next(filter(lambda type: (type.short_name == 'SynchronizedTimestamp'), type_map))

    full_reference_name = filter_full_reference_name(lctx.get_language('nunavut.lang.py'), test_subject)
    assert "uavcan.time.SynchronizedTimestamp_1_0" == full_reference_name


def test_python_filter_short_reference_name(gen_paths):  # type: ignore
    lctx = LanguageContext()

    type_map = read_namespace(str(gen_paths.dsdl_dir / pathlib.Path('uavcan')), [])

    from nunavut.lang.py import filter_short_reference_name

    test_subject = next(filter(lambda type: (type.short_name == 'SynchronizedTimestamp'), type_map))
    full_reference_name = filter_short_reference_name(lctx.get_language('nunavut.lang.py'), test_subject)
    assert "SynchronizedTimestamp_1_0" == full_reference_name


def test_python_filter_alignment_prefix(gen_paths):  # type: ignore
    from nunavut.lang.py import filter_alignment_prefix
    from pydsdl import BitLengthSet

    subject = BitLengthSet(64)
    assert 'aligned' == filter_alignment_prefix(subject)
    subject.increment(1)
    assert 'unaligned' == filter_alignment_prefix(subject)

    with pytest.raises(TypeError):
        filter_alignment_prefix('wrong type')


def test_python_filter_imports(gen_paths):  # type: ignore
    lctx = LanguageContext()

    type_map = read_namespace(str(gen_paths.dsdl_dir / pathlib.Path('uavcan')), [])

    from nunavut.lang.py import filter_imports

    test_subject = next(filter(lambda type: (type.short_name == 'bar'), type_map))
    imports = filter_imports(lctx.get_language('nunavut.lang.py'), test_subject)
    assert len(imports) == 1
    assert 'uavcan.time' == imports[0]


@pytest.mark.parametrize('stropping,sort', [(True, False), (False, True)])
def test_python_filter_imports_for_service_type(gen_paths, stropping, sort):  # type: ignore
    lctx = LanguageContext()
    lctx.config.set('nunavut.lang.py', 'enable_stropping', str(stropping))
    assert stropping == lctx.config.getboolean('nunavut.lang.py', 'enable_stropping')

    type_map = read_namespace(str(gen_paths.dsdl_dir / pathlib.Path('uavcan')), [])

    from nunavut.lang.py import filter_imports

    lctx.get_language('nunavut.lang.py').get_reserved_identifiers()
    test_subject = next(filter(lambda type: (type.short_name == 'bar_svc'), type_map))
    imports = filter_imports(lctx.get_language('nunavut.lang.py'), test_subject, sort=sort)
    assert len(imports) == 2
    if stropping:
        assert 'uavcan.str_' == imports[0]
    else:
        assert 'uavcan.str' == imports[0]
    assert 'uavcan.time' == imports[1]


@pytest.mark.parametrize('stropping,sort', [(True, False), (False, True)])
def test_python_filter_imports_for_array_type(gen_paths, stropping, sort):  # type: ignore
    lctx = LanguageContext()
    lctx.config.set('nunavut.lang.py', 'enable_stropping', str(stropping))

    uavcan_dir = str(gen_paths.dsdl_dir / pathlib.Path('uavcan'))
    type_map = read_namespace(str(gen_paths.dsdl_dir / pathlib.Path('new')), [uavcan_dir])

    assert len(type_map) == 2

    from nunavut.lang.py import filter_imports

    test_subject = next(filter(lambda type: (type.short_name == 'hotness'), type_map))
    imports = filter_imports(lctx.get_language('nunavut.lang.py'), test_subject, sort=sort)
    assert len(imports) == 3
    assert 'new' == imports[0]
    if stropping:
        assert 'uavcan.str_' == imports[1]
    else:
        assert 'uavcan.str' == imports[1]
    assert 'uavcan.time' == imports[2]


@pytest.mark.parametrize('stropping,sort', [(True, False), (False, True)])
def test_python_filter_includes(gen_paths, stropping, sort):  # type: ignore
    lctx = LanguageContext(target_language='cpp', extension='.h')
    lctx.config.set('nunavut.lang.cpp', 'enable_stropping', str(stropping))

    uavcan_dir = str(gen_paths.dsdl_dir / pathlib.Path('uavcan'))
    type_map = read_namespace(str(gen_paths.dsdl_dir / pathlib.Path('new')), [uavcan_dir])
    from nunavut.lang.cpp import filter_includes

    test_subject = next(filter(lambda type: (type.short_name == 'hotness'), type_map))
    imports = filter_includes(lctx.get_language('nunavut.lang.cpp'), test_subject, sort=sort)
    assert len(imports) == 5

    def assert_path_in_imports(path: str) -> None:
        nonlocal imports
        assert path in imports

    if stropping:
        if sort:
            assert ['<array>',
                    '<cstdint>',
                    '"_new/malloc_1_0.h"',
                    '"uavcan/str/bar_1_0.h"',
                    '"uavcan/time/SynchronizedTimestamp_1_0.h"'
                    ] == imports
        else:

            map(assert_path_in_imports, ('<array>',
                                         '<cstdint>',
                                         '"uavcan/time/SynchronizedTimestamp_1_0.h"',
                                         '"_new/malloc_1_0.h"',
                                         '"uavcan/str/bar_1_0.h"'))
    elif sort:
        assert ['<array>',
                '<cstdint>',
                '"new/malloc_1_0.h"',
                '"uavcan/str/bar_1_0.h"',
                '"uavcan/time/SynchronizedTimestamp_1_0.h"'
                ] == imports
    else:
        map(assert_path_in_imports, ('<array>',
                                     '<cstdint>',
                                     '"uavcan/time/SynchronizedTimestamp_1_0.h"',
                                     '"new/malloc_1_0.h"',
                                     '"uavcan/str/bar_1_0.h"'))
