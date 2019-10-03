#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

import pytest
import json
import typing

from pydsdl import read_namespace, CompositeType
from nunavut import Namespace, build_namespace_tree
from nunavut.lang import LanguageContext
from nunavut.jinja import Generator

from pathlib import Path


@pytest.fixture
def gen_paths():  # type: ignore
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


def gen_test_namespace(gen_paths: typing.Any, language_context: LanguageContext) -> \
        typing.Tuple[Namespace, str, typing.List[CompositeType]]:
    root_namespace_path = str(gen_paths.dsdl_dir / Path("scotec"))
    includes = [str(gen_paths.dsdl_dir / Path("uavcan"))]
    compound_types = read_namespace(root_namespace_path, includes, allow_unregulated_fixed_port_id=True)
    return build_namespace_tree(compound_types,
                                root_namespace_path,
                                gen_paths.out_dir,
                                language_context), root_namespace_path, compound_types


def test_namespace_eq(gen_paths):  # type: ignore
    """Verify the get_all_namespaces method in Namespace"""
    language_context = LanguageContext(extension='.json')
    namespace0, _, _ = gen_test_namespace(gen_paths, language_context)
    namespace1 = Namespace('', gen_paths.dsdl_dir, gen_paths.out_dir, language_context)
    assert namespace0 == namespace0
    assert namespace1 == namespace1
    assert namespace0 != namespace1
    assert "foo" != namespace0


def test_get_all_namespaces(gen_paths):  # type: ignore
    """Verify the get_all_namespaces method in Namespace"""
    namespace, _, _ = gen_test_namespace(gen_paths, LanguageContext(extension='.json'))
    index = dict()
    for ns, path in namespace.get_all_namespaces():
        index[path] = ns

    assert len(index) == 3


def test_get_all_types(gen_paths):  # type: ignore
    """Verify the get_all_namespaces method in Namespace"""
    namespace, _, _ = gen_test_namespace(gen_paths, LanguageContext(extension='.json'))
    index = dict()
    for ns, path in namespace.get_all_types():
        index[path] = ns

    assert len(index) == 5


def test_empty_namespace(gen_paths):  # type: ignore
    """Test a namespace object with no children."""
    namespace = Namespace('', gen_paths.dsdl_dir, gen_paths.out_dir, LanguageContext(extension='.txt'))
    assert namespace.full_name == ''
    assert namespace.output_folder == gen_paths.out_dir
    assert namespace.source_file_path == str(gen_paths.dsdl_dir)
    assert len(namespace.data_types) == 0
    assert (gen_paths.out_dir / Path('_')).with_suffix('.txt') == namespace.find_output_path_for_type(namespace)
    assert namespace == namespace
    assert hash(namespace) == hash(namespace)
    assert str(namespace) == str(namespace)
    from fixtures import DummyType
    with pytest.raises(KeyError):
        namespace.find_output_path_for_type(DummyType())


def parameterized_test_namespace_(gen_paths, templates_subdir):  # type: ignore
    language_context = LanguageContext(extension='.json')
    namespace, root_namespace_path, _ = gen_test_namespace(gen_paths, language_context)
    generator = Generator(namespace, False, language_context, gen_paths.templates_dir / Path(templates_subdir))
    generator.generate_all()
    assert namespace.source_file_path == root_namespace_path
    assert namespace.full_name == 'scotec'
    for nested_namespace in namespace.get_nested_namespaces():
        nested_namespace_path = Path(root_namespace_path) / Path(*nested_namespace.full_name.split('.')[1:])
        assert nested_namespace.source_file_path == str(nested_namespace_path)


def test_namespace_any_template(gen_paths):  # type: ignore
    """Basic test of a non-empty namespace using the Any.j2 template."""
    parameterized_test_namespace_(gen_paths, 'default')


def test_namespace_namespace_template(gen_paths):  # type: ignore
    """Basic test of a non-empty namespace using the Namespace.j2 template."""
    parameterized_test_namespace_(gen_paths, 'namespace')


def test_namespace_generation(gen_paths):  # type: ignore
    """Test actually generating a namepace file."""
    language_context = LanguageContext(extension='.json', namespace_output_stem='__module__')
    namespace, root_namespace_path, compound_types = gen_test_namespace(gen_paths, language_context)
    assert len(compound_types) == 2
    generator = Generator(namespace, True, language_context, gen_paths.templates_dir / Path('default'))
    generator.generate_all()
    for nested_namespace in namespace.get_nested_namespaces():
        nested_namespace_path = Path(root_namespace_path) / Path(*nested_namespace.full_name.split('.')[1:])
        assert nested_namespace.source_file_path == str(nested_namespace_path)

    outfile = gen_paths.find_outfile_in_namespace("scotec.mcu", namespace)

    assert (outfile is not None)

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob['scotec.mcu']['namespace'] == 'scotec.mcu'

    output_path_for_timer = namespace.find_output_path_for_type(compound_types[0])
    assert (gen_paths.out_dir / 'scotec' / 'mcu' / 'Timer_0_1').with_suffix('.json') == output_path_for_timer


def test_build_namespace_tree_from_nothing(gen_paths):  # type: ignore
    namespace = build_namespace_tree([], str(gen_paths.dsdl_dir), gen_paths.out_dir, LanguageContext('js'))
    assert namespace is not None
    assert namespace.full_name == ''


def test_namespace_stropping(gen_paths):  # type: ignore
    """Test generating a namespace that uses a reserved keyword for a given language."""
    language_context = LanguageContext('c')
    namespace, root_namespace_path, compound_types = gen_test_namespace(gen_paths, language_context)
    assert len(compound_types) == 2
    generator = Generator(namespace, True, language_context, gen_paths.templates_dir / Path('default'))
    generator.generate_all()

    outfile = gen_paths.find_outfile_in_namespace("scotec._typedef", namespace)

    assert (outfile is not None)

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None

    output_path_for_stropped = namespace.find_output_path_for_type(compound_types[1])
    assert (gen_paths.out_dir / 'scotec' / '_typedef' / 'ATOMIC_TYPE_0_1').with_suffix('.h') == output_path_for_stropped


def test_python35_resolve_behavior(gen_paths):  # type: ignore
    """Make sure Python3.5 and Python 3.6 throw the same exception here."""
    language_context = LanguageContext('c')
    with pytest.raises(FileNotFoundError):
        Namespace('foo.bar',
                  gen_paths.dsdl_dir / Path("scotec"),
                  gen_paths.out_dir,
                  language_context)
