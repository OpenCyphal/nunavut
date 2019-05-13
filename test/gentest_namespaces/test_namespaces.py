#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

import pytest
import json

from pydsdl import read_namespace
from nunavut import Namespace, build_namespace_tree
from nunavut.jinja import Generator

from pathlib import Path


@pytest.fixture
def gen_paths():  # type: ignore
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


def gen_test_namespace(gen_paths, namespace_output_stem):  # type: ignore
    root_namespace_path = str(gen_paths.dsdl_dir / Path("scotec"))
    includes = [str(gen_paths.dsdl_dir / Path("uavcan"))]
    compound_types = read_namespace(root_namespace_path, includes, allow_unregulated_fixed_port_id=True)
    return build_namespace_tree(compound_types,
                                root_namespace_path,
                                gen_paths.out_dir,
                                '.json',
                                namespace_output_stem), root_namespace_path, compound_types


def test_namespace_eq(gen_paths):  # type: ignore
    """Verify the get_all_namespaces method in Namespace"""
    namespace0, _, _ = gen_test_namespace(gen_paths, '_')
    namespace1 = Namespace('', gen_paths.dsdl_dir, gen_paths.out_dir, '.txt', '_')
    assert namespace0 == namespace0
    assert namespace1 == namespace1
    assert namespace0 != namespace1
    assert "foo" != namespace0


def test_get_all_namespaces(gen_paths):  # type: ignore
    """Verify the get_all_namespaces method in Namespace"""
    namespace, _, _ = gen_test_namespace(gen_paths, '_')
    index = dict()
    for ns, path in namespace.get_all_namespaces():
        index[path] = ns

    assert len(index) == 2


def test_get_all_types(gen_paths):  # type: ignore
    """Verify the get_all_namespaces method in Namespace"""
    namespace, _, _ = gen_test_namespace(gen_paths, '_')
    index = dict()
    for ns, path in namespace.get_all_types():
        index[path] = ns

    assert len(index) == 3


def test_empty_namespace(gen_paths):  # type: ignore
    """Test a namespace object with no children."""
    namespace = Namespace('', gen_paths.dsdl_dir, gen_paths.out_dir, '.txt', '_')
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
    namespace, root_namespace_path, _ = gen_test_namespace(gen_paths, '_')
    generator = Generator(namespace, False, gen_paths.templates_dir / Path(templates_subdir))
    generator.generate_all()
    assert namespace.source_file_path == root_namespace_path
    assert namespace.full_name == 'scotec'
    for nested_namespace in namespace.get_nested_namespaces():
        assert nested_namespace.source_file_path == str(Path(root_namespace_path) / Path(*nested_namespace.full_name.split('.')[1:]))


def test_namespace_any_template(gen_paths):  # type: ignore
    """Basic test of a non-empty namespace using the Any.j2 template."""
    parameterized_test_namespace_(gen_paths, 'default')


def test_namespace_namespace_template(gen_paths):  # type: ignore
    """Basic test of a non-empty namespace using the Namespace.j2 template."""
    parameterized_test_namespace_(gen_paths, 'namespace')


def test_namespace_generation(gen_paths):  # type: ignore
    """Test actually generating a namepace file."""
    namespace, root_namespace_path, compound_types = gen_test_namespace(gen_paths, '__module__')
    assert len(compound_types) == 1
    generator = Generator(namespace, True, gen_paths.templates_dir / Path('default'))
    generator.generate_all()
    for nested_namespace in namespace.get_nested_namespaces():
        assert nested_namespace.source_file_path == str(Path(root_namespace_path) / Path(*nested_namespace.full_name.split('.')[1:]))

    outfile = gen_paths.find_outfile_in_namespace("scotec.mcu", namespace)

    assert (outfile is not None)

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob['scotec.mcu']['namespace'] == 'scotec.mcu'

    output_path_for_timer = namespace.find_output_path_for_type(compound_types[0])
    assert (gen_paths.out_dir / 'scotec' / 'mcu' / 'Timer_0_1').with_suffix('.json') == output_path_for_timer


def test_build_namespace_tree_from_nothing(gen_paths):  # type: ignore
    namespace = build_namespace_tree([], str(gen_paths.dsdl_dir), gen_paths.out_dir, '.json', '_')
    assert namespace is not None
    assert namespace.full_name == ''
