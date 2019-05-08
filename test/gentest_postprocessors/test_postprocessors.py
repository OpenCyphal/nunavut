#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
import json
import pathlib
import subprocess
import typing
import pytest

import pydsdl
import pydsdlgen
import pydsdlgen.jinja
import pydsdlgen.postprocessors


@pytest.fixture
def gen_paths():  # type: ignore
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


def _test_common_namespace(gen_paths):  # type: ignore
    root_namespace_dir = gen_paths.dsdl_dir / pathlib.Path("uavcan")
    root_namespace = str(root_namespace_dir)
    return pydsdlgen.build_namespace_tree(pydsdl.read_namespace(root_namespace, ''),
                                          root_namespace_dir,
                                          gen_paths.out_dir,
                                          '.json',
                                          '_')


def _test_common_post_condition(gen_paths, namespace):  # type: ignore
    # Now read back in and verify
    outfile = gen_paths.find_outfile_in_namespace("uavcan.test.TestType", namespace)
    assert outfile is not None

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob['name'] == 'uavcan.test.TestType.0.2'

    return outfile


def test_abs():  # type: ignore
    """ Require that PostProcessor and intermediate types are abstract.
    """
    with pytest.raises(TypeError):
        pydsdlgen.postprocessors.PostProcessor()  # type: ignore
    with pytest.raises(TypeError):
        pydsdlgen.postprocessors.FilePostProcessor()  # type: ignore
    with pytest.raises(TypeError):
        pydsdlgen.postprocessors.LinePostProcessor()  # type: ignore


def test_unknown_intermediate(gen_paths):  # type: ignore
    """ Verifies that a ValueError is raised if something other than
    LinePostProcessor or FilePostProcessor is provided to the jinja2 generator.
    """

    class InvalidType(pydsdlgen.postprocessors.PostProcessor):
        def __init__(self):  # type: ignore
            pass

        def __call__(self, generated: pathlib.Path) -> pathlib.Path:
            return generated

    namespace = _test_common_namespace(gen_paths)
    generator = pydsdlgen.jinja.Generator(namespace, False, gen_paths.templates_dir)
    with pytest.raises(ValueError):
        generator.generate_all(False, True, [InvalidType()])


def test_empty_pp_array(gen_paths):  # type: ignore
    """ Verifies the behavior of a zero length post_processors argument.
    """
    namespace = _test_common_namespace(gen_paths)
    generator = pydsdlgen.jinja.Generator(namespace, False, gen_paths.templates_dir)
    generator.generate_all(False, True, [])

    _test_common_post_condition(gen_paths, namespace)


def test_chmod(gen_paths):  # type: ignore
    """ Generates a file using a SetFileMode post-processor.
    """
    namespace = _test_common_namespace(gen_paths)
    generator = pydsdlgen.jinja.Generator(namespace, False, gen_paths.templates_dir)
    generator.generate_all(False, True, [pydsdlgen.postprocessors.SetFileMode(0o444)])

    outfile = _test_common_post_condition(gen_paths, namespace)

    assert pathlib.Path(outfile).stat().st_mode & 0o777 == 0o444


def test_overwrite(gen_paths):  # type: ignore
    """ Verifies the allow_overwrite flag contracts.
    """
    namespace = _test_common_namespace(gen_paths)
    generator = pydsdlgen.jinja.Generator(namespace, False, gen_paths.templates_dir)
    generator.generate_all(False, True, [pydsdlgen.postprocessors.SetFileMode(0o444)])

    with pytest.raises(PermissionError):
        generator.generate_all(False, False)

    generator.generate_all(False, True)

    _test_common_post_condition(gen_paths, namespace)


def test_overwrite_dryrun(gen_paths):  # type: ignore
    """ Verifies the allow_overwrite flag contracts.
    """
    namespace = _test_common_namespace(gen_paths)
    generator = pydsdlgen.jinja.Generator(namespace, False, gen_paths.templates_dir)
    generator.generate_all(False, True, [pydsdlgen.postprocessors.SetFileMode(0o444)])

    with pytest.raises(PermissionError):
        generator.generate_all(False, False)

    generator.generate_all(True, False)


def test_no_overwrite_arg(gen_paths):  # type: ignore
    """ Verifies the --no-overwrite argument of dsdlgenj.
    """
    dsdlgenj_cmd = ['dsdlgenj',
                    '--templates', str(gen_paths.templates_dir),
                    '-O', str(gen_paths.out_dir),
                    '-e', str('.json'),
                    str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    subprocess.run(dsdlgenj_cmd, check=True)

    dsdlgenj_cmd.append('--no-overwrite')

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(dsdlgenj_cmd, check=True)


def test_file_mode(gen_paths):  # type: ignore
    """ Verify the --file-mode argument of dsdlgenj.
    """

    file_mode = 0o774
    dsdlgenj_cmd = ['dsdlgenj',
                    '--templates', str(gen_paths.templates_dir),
                    '-O', str(gen_paths.out_dir),
                    '-e', str('.json'),
                    '--file-mode', oct(file_mode),
                    str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    subprocess.run(dsdlgenj_cmd, check=True)

    outfile = gen_paths.out_dir /\
        pathlib.Path('uavcan') /\
        pathlib.Path('test') /\
        pathlib.Path('TestType_0_2').with_suffix('.json')

    assert pathlib.Path(outfile).stat().st_mode & 0o777 == file_mode


def test_move_file(gen_paths):  # type: ignore
    """
    Verifies that one post-processor can move the generated file and the
    next will find the new path.
    """

    class Mover(pydsdlgen.postprocessors.FilePostProcessor):
        def __init__(self, move_to: pathlib.Path):
            self.target_path = move_to
            self.generated_path = pathlib.Path()
            self.called = False

        def __call__(self, generated: pathlib.Path) -> pathlib.Path:
            self.called = True
            self.generated_path = generated
            return self.target_path

    class Verifier(pydsdlgen.postprocessors.FilePostProcessor):
        def __init__(self):  # type: ignore
            self.generated_path = pathlib.Path()

        def __call__(self, generated: pathlib.Path) -> pathlib.Path:
            self.generated_path = generated
            return generated

    mover = Mover(gen_paths.out_dir / pathlib.Path('moved').with_suffix('.json'))
    verifier = Verifier()

    namespace = _test_common_namespace(gen_paths)
    generator = pydsdlgen.jinja.Generator(namespace, False, gen_paths.templates_dir)
    generator.generate_all(False, True, [mover, verifier])

    assert mover.called
    assert mover.generated_path != mover.target_path
    assert verifier.generated_path == mover.target_path


def test_line_pp(gen_paths):  # type: ignore
    """
    Exercises the LinePostProcessor type.
    """

    class TestLinePostProcessor0(pydsdlgen.postprocessors.LinePostProcessor):

        def __call__(self, line_and_lineend: typing.Tuple[str, str]) -> typing.Tuple[str, str]:
            if len(line_and_lineend[0]) == 0:
                return ('', '')
            else:
                return line_and_lineend

    class TestLinePostProcessor1(pydsdlgen.postprocessors.LinePostProcessor):
        def __init__(self):  # type: ignore
            self._lines = []  # type: typing.List[str]

        def __call__(self, line_and_lineend: typing.Tuple[str, str]) -> typing.Tuple[str, str]:
            self._lines.append(line_and_lineend[0])
            return line_and_lineend

    line_pp0 = TestLinePostProcessor0()
    line_pp1 = TestLinePostProcessor1()
    namespace = _test_common_namespace(gen_paths)
    generator = pydsdlgen.jinja.Generator(namespace, False, gen_paths.templates_dir)
    generator.generate_all(False, True, [line_pp0, line_pp1])
    assert len(line_pp1._lines) > 0
    _test_common_post_condition(gen_paths, namespace)


def test_line_pp_returns_none(gen_paths):  # type: ignore
    class TestBadLinePostProcessor(pydsdlgen.postprocessors.LinePostProcessor):

        def __call__(self, line_and_lineend: typing.Tuple[str, str]) -> typing.Tuple[str, str]:
            return None  # type: ignore

    namespace = _test_common_namespace(gen_paths)
    generator = pydsdlgen.jinja.Generator(namespace, False, gen_paths.templates_dir)
    with pytest.raises(ValueError):
        generator.generate_all(False, True, [TestBadLinePostProcessor()])
