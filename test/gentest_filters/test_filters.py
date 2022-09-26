#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

import json
import pathlib
import typing
from pathlib import Path, PurePath

import pytest
from nunavut import Namespace, build_namespace_tree
from nunavut.jinja import DSDLCodeGenerator
from nunavut.jinja.jinja2.exceptions import TemplateAssertionError
from nunavut.lang import LanguageContext
from pydsdl import read_namespace


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
    generator = DSDLCodeGenerator(namespace, templates_dir=template_path)
    try:
        generator.generate_all()
        assert False
    except TemplateAssertionError as e:
        e.filename == str(template_path / "Any.j2")
        e.filename == 2
        e.message == 'Template assertion failed.'


def test_type_to_include(gen_paths):  # type: ignore
    """Test the type_to_include filter."""
    root_path = (gen_paths.dsdl_dir / Path("uavcan")).as_posix()
    output_path = gen_paths.out_dir / 'type_to_include'
    compound_types = read_namespace(root_path, [])
    language_context = LanguageContext(extension='.json')
    namespace = build_namespace_tree(compound_types,
                                     root_path,
                                     output_path,
                                     language_context)
    template_path = gen_paths.templates_dir / Path('type_to_include')
    generator = DSDLCodeGenerator(namespace, templates_dir=template_path)
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
    generator = DSDLCodeGenerator(namespace,
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
        DSDLCodeGenerator(namespace,
                          additional_filters={'type_to_include_path': lambda T: ''},
                          additional_tests={'custom_test': lambda T: False})

    with pytest.raises(RuntimeError):
        DSDLCodeGenerator(namespace,
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
    assert stropping == lctx.config.get_config_value_as_bool('nunavut.lang.py', 'enable_stropping')

    type_map = read_namespace(str(gen_paths.dsdl_dir / pathlib.Path('uavcan')), [])

    from nunavut.lang.py import filter_imports

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

    uavcan_dir = (gen_paths.dsdl_dir / pathlib.Path('uavcan')).as_posix()
    type_map = read_namespace((gen_paths.dsdl_dir / pathlib.Path('new')).as_posix(), [uavcan_dir])
    from nunavut.lang.cpp import filter_includes

    test_subject = next(filter(lambda type: (type.short_name == 'hotness'), type_map))
    imports = filter_includes(lctx.get_language('nunavut.lang.cpp'), test_subject, sort=sort)
    assert len(imports) == 5

    def assert_path_in_imports(path: str) -> None:
        nonlocal imports
        assert path in imports

    if stropping:
        if sort:
            assert ['"_new/malloc_1_0.h"',
                    '"uavcan/str/bar_1_0.h"',
                    '"uavcan/time/SynchronizedTimestamp_1_0.h"',
                    '<array>',
                    '<cstdint>'
                    ] == imports
        else:

            map(assert_path_in_imports, ('"uavcan/time/SynchronizedTimestamp_1_0.h"',
                                         '"_new/malloc_1_0.h"',
                                         '"uavcan/str/bar_1_0.h"',
                                         '<array>',
                                         '<cstdint>'))
    elif sort:
        assert ['"new/malloc_1_0.h"',
                '"uavcan/str/bar_1_0.h"',
                '"uavcan/time/SynchronizedTimestamp_1_0.h"',
                '<array>',
                '<cstdint>'
                ] == imports
    else:
        map(assert_path_in_imports, ('"uavcan/time/SynchronizedTimestamp_1_0.h"',
                                     '"new/malloc_1_0.h"',
                                     '"uavcan/str/bar_1_0.h"',
                                     '<array>',
                                     '<cstdint>'))


def test_filter_includes_cpp_vla(gen_paths):  # type: ignore
    lctx = LanguageContext(target_language='cpp', extension='.h')
    type_map = read_namespace((gen_paths.dsdl_dir / pathlib.Path('vla')).as_posix())
    from nunavut.lang.cpp import filter_includes

    test_subject = next(filter(lambda type: (type.short_name == 'uses_vla'), type_map))
    imports = filter_includes(lctx.get_language('nunavut.lang.cpp'), test_subject)
    assert '"nunavut/support/variable_length_array.h"' in imports


@typing.no_type_check
@pytest.mark.parametrize('language_name,namespace_separator', [('c', '_'), ('cpp', '::')])
def test_filter_full_reference_name_via_template(gen_paths, language_name, namespace_separator):
    root_path = (gen_paths.dsdl_dir / Path("uavcan")).as_posix()
    output_path = (gen_paths.out_dir / Path("filter_and_test")).as_posix()
    compound_types = read_namespace(root_path, [])
    language_context = LanguageContext(target_language=language_name)
    namespace = build_namespace_tree(compound_types,
                                     root_path,
                                     output_path,
                                     language_context)
    template_path = gen_paths.templates_dir / Path('full_reference_test')
    generator = DSDLCodeGenerator(namespace,
                                  templates_dir=template_path)

    generator.generate_all()
    outfile = gen_paths.find_outfile_in_namespace("uavcan.str.bar_svc", namespace)

    assert (outfile is not None)

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob['parent']['full_reference_name'] == 'uavcan.str.bar_svc_1_0'.replace('.', namespace_separator)
    assert json_blob['parent']['short_reference_name'] == 'bar_svc' if language_name == 'cpp' else 'bar_svc_1_0'
    assert json_blob['request']['full_reference_name'] == 'uavcan.str.bar_svc.Request_1_0'.replace(
        '.', namespace_separator)
    assert json_blob['request']['short_reference_name'] == 'Request_1_0'
    assert json_blob['response']['full_reference_name'] == 'uavcan.str.bar_svc.Response_1_0'.replace(
        '.', namespace_separator)
    assert json_blob['response']['short_reference_name'] == 'Response_1_0'


@typing.no_type_check
@pytest.mark.parametrize(
    'language_name,stropping,namespace_separator',
    [('c', False, '_'),
     ('c', True, '_'),
     ('cpp', False, '::'),
     ('cpp', True, '::')])
def test_filter_full_reference_name(gen_paths, language_name, stropping, namespace_separator):
    """
    Cover issue #153
    """
    lctx = LanguageContext()
    ln_package_name = 'nunavut.lang.{}'.format(language_name)
    lctx.config.set(ln_package_name, 'enable_stropping', str(stropping))
    ln = lctx.get_language(ln_package_name)

    import importlib

    from pydsdl import ServiceType, StructureType, Version

    test_subject_module = importlib.import_module(ln_package_name)

    service_request_type = StructureType(name='register.getting.tired.of.Python',
                                         version=Version(0, 1),
                                         attributes=[],
                                         deprecated=False,
                                         fixed_port_id=None,
                                         source_file_path=Path(),
                                         has_parent_service=True)
    service_response_type = StructureType(name='register.getting.tired.of.Python',
                                          version=Version(0, 1),
                                          attributes=[],
                                          deprecated=False,
                                          fixed_port_id=None,
                                          source_file_path=Path(),
                                          has_parent_service=True)

    service_type = ServiceType(service_request_type,
                               service_response_type,
                               None)

    # C++ is special because namespaces are part of the language and therefore each namespace
    # name must be stropped
    top_level_name = ('_register' if stropping and language_name == 'cpp' else 'register')

    assert test_subject_module.filter_full_reference_name(
        ln, service_type) == '{}.getting.tired.of_0_1'.format(top_level_name).replace('.', namespace_separator)
    assert test_subject_module.filter_full_reference_name(
        ln, service_request_type) == '{}.getting.tired.of.Python_0_1'.format(top_level_name)\
        .replace('.', namespace_separator)
    assert test_subject_module.filter_full_reference_name(
        ln, service_response_type) == '{}.getting.tired.of.Python_0_1'.format(top_level_name)\
        .replace('.', namespace_separator)


@typing.no_type_check
def test_filter_to_template_unique(gen_paths):
    """
    Cover issue #88
    """
    root_path = str(gen_paths.dsdl_dir / Path("one"))
    output_path = gen_paths.out_dir / 'to_unique'
    compound_types = read_namespace(root_path, [])
    language_context = LanguageContext(target_language='c')
    namespace = build_namespace_tree(compound_types,
                                     root_path,
                                     output_path,
                                     language_context)
    template_path = gen_paths.templates_dir / Path('to_unique')
    generator = DSDLCodeGenerator(namespace, templates_dir=template_path)
    generator.generate_all()
    outfile = gen_paths.find_outfile_in_namespace("one.foo", namespace)

    assert (outfile is not None)

    expected = '_f0_\n_f1_\n_f2_\n_f3_\n\n_f4_\n_f5_\n_f6_\n_f7_\n\n_f8_\n_f9_\n_f10_\n_f11_\n'

    with open(str(outfile), 'r') as foo_file:
        actual = foo_file.read()

    assert expected == actual
