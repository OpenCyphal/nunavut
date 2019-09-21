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
import re

import pydsdl
import nunavut
import nunavut.jinja
import nunavut.postprocessors
import fixtures

from nunavut.lang import LanguageContext


@pytest.fixture
def gen_paths():  # type: ignore
    from fixtures import GenTestPaths
    return GenTestPaths(__file__)


def _test_common_namespace(gen_paths):  # type: ignore
    root_namespace_dir = gen_paths.dsdl_dir / pathlib.Path("uavcan")
    root_namespace = str(root_namespace_dir)
    return nunavut.build_namespace_tree(pydsdl.read_namespace(root_namespace, ''),
                                        root_namespace_dir,
                                        gen_paths.out_dir,
                                        '.json',
                                        '_',
                                        LanguageContext())


def _test_common_post_condition(gen_paths, namespace):  # type: ignore
    # Now read back in and verify
    outfile = gen_paths.find_outfile_in_namespace("uavcan.test.TestType", namespace)
    assert outfile is not None

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob['name0'] == 'uavcan.test.TestType.0.2'

    return outfile


def test_abs():  # type: ignore
    """ Require that PostProcessor and intermediate types are abstract.
    """
    with pytest.raises(TypeError):
        nunavut.postprocessors.PostProcessor()  # type: ignore
    with pytest.raises(TypeError):
        nunavut.postprocessors.FilePostProcessor()  # type: ignore
    with pytest.raises(TypeError):
        nunavut.postprocessors.LinePostProcessor()  # type: ignore


def test_unknown_intermediate(gen_paths):  # type: ignore
    """ Verifies that a ValueError is raised if something other than
    LinePostProcessor or FilePostProcessor is provided to the jinja2 generator.
    """

    class InvalidType(nunavut.postprocessors.PostProcessor):
        def __init__(self):  # type: ignore
            pass

        def __call__(self, generated: pathlib.Path) -> pathlib.Path:
            return generated

    namespace = _test_common_namespace(gen_paths)
    generator = nunavut.jinja.Generator(namespace, False, LanguageContext(), gen_paths.templates_dir)
    with pytest.raises(ValueError):
        generator.generate_all(False, True, [InvalidType()])


def test_empty_pp_array(gen_paths):  # type: ignore
    """ Verifies the behavior of a zero length post_processors argument.
    """
    namespace = _test_common_namespace(gen_paths)
    generator = nunavut.jinja.Generator(namespace, False, LanguageContext(), gen_paths.templates_dir)
    generator.generate_all(False, True, [])

    _test_common_post_condition(gen_paths, namespace)


def test_chmod(gen_paths):  # type: ignore
    """ Generates a file using a SetFileMode post-processor.
    """
    namespace = _test_common_namespace(gen_paths)
    generator = nunavut.jinja.Generator(namespace, False, LanguageContext(), gen_paths.templates_dir)
    generator.generate_all(False, True, [nunavut.postprocessors.SetFileMode(0o444)])

    outfile = _test_common_post_condition(gen_paths, namespace)

    assert pathlib.Path(outfile).stat().st_mode & 0o777 == 0o444


def test_overwrite(gen_paths):  # type: ignore
    """ Verifies the allow_overwrite flag contracts.
    """
    namespace = _test_common_namespace(gen_paths)
    generator = nunavut.jinja.Generator(namespace, False, LanguageContext(), gen_paths.templates_dir)
    generator.generate_all(False, True, [nunavut.postprocessors.SetFileMode(0o444)])

    with pytest.raises(PermissionError):
        generator.generate_all(False, False)

    generator.generate_all(False, True)

    _test_common_post_condition(gen_paths, namespace)


def test_overwrite_dryrun(gen_paths):  # type: ignore
    """ Verifies the allow_overwrite flag contracts.
    """
    namespace = _test_common_namespace(gen_paths)
    generator = nunavut.jinja.Generator(namespace, False, LanguageContext(), gen_paths.templates_dir)
    generator.generate_all(False, True, [nunavut.postprocessors.SetFileMode(0o444)])

    with pytest.raises(PermissionError):
        generator.generate_all(False, False)

    generator.generate_all(True, False)


def test_no_overwrite_arg(gen_paths):  # type: ignore
    """ Verifies the --no-overwrite argument of nnvg.
    """
    nnvg_cmd = ['--templates', str(gen_paths.templates_dir),
                '-O', str(gen_paths.out_dir),
                '-e', '.json',
                str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    fixtures.run_nnvg(gen_paths, nnvg_cmd)

    nnvg_cmd.append('--no-overwrite')

    with pytest.raises(subprocess.CalledProcessError):
        fixtures.run_nnvg(gen_paths, nnvg_cmd)


def test_file_mode(gen_paths):  # type: ignore
    """ Verify the --file-mode argument of nnvg.
    """

    file_mode = 0o774
    nnvg_cmd = ['--templates', str(gen_paths.templates_dir),
                '-O', str(gen_paths.out_dir),
                '-e', '.json',
                '--file-mode', oct(file_mode),
                str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    fixtures.run_nnvg(gen_paths, nnvg_cmd)

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

    class Mover(nunavut.postprocessors.FilePostProcessor):
        def __init__(self, move_to: pathlib.Path):
            self.target_path = move_to
            self.generated_path = pathlib.Path()
            self.called = False

        def __call__(self, generated: pathlib.Path) -> pathlib.Path:
            self.called = True
            self.generated_path = generated
            return self.target_path

    class Verifier(nunavut.postprocessors.FilePostProcessor):
        def __init__(self):  # type: ignore
            self.generated_path = pathlib.Path()

        def __call__(self, generated: pathlib.Path) -> pathlib.Path:
            self.generated_path = generated
            return generated

    mover = Mover(gen_paths.out_dir / pathlib.Path('moved').with_suffix('.json'))
    verifier = Verifier()

    namespace = _test_common_namespace(gen_paths)
    generator = nunavut.jinja.Generator(namespace, False, LanguageContext(), gen_paths.templates_dir)
    generator.generate_all(False, True, [mover, verifier])

    assert mover.called
    assert mover.generated_path != mover.target_path
    assert verifier.generated_path == mover.target_path


def test_line_pp(gen_paths):  # type: ignore
    """
    Exercises the LinePostProcessor type.
    """

    class TestLinePostProcessor0(nunavut.postprocessors.LinePostProcessor):

        def __call__(self, line_and_lineend: typing.Tuple[str, str]) -> typing.Tuple[str, str]:
            if len(line_and_lineend[0]) == 0:
                return ('', '')
            else:
                return line_and_lineend

    class TestLinePostProcessor1(nunavut.postprocessors.LinePostProcessor):
        def __init__(self):  # type: ignore
            self._lines = []  # type: typing.List[str]

        def __call__(self, line_and_lineend: typing.Tuple[str, str]) -> typing.Tuple[str, str]:
            self._lines.append(line_and_lineend[0])
            return line_and_lineend

    line_pp0 = TestLinePostProcessor0()
    line_pp1 = TestLinePostProcessor1()
    namespace = _test_common_namespace(gen_paths)
    generator = nunavut.jinja.Generator(namespace, False, LanguageContext(), gen_paths.templates_dir)
    generator.generate_all(False, True, [line_pp0, line_pp1])
    assert len(line_pp1._lines) > 0
    _test_common_post_condition(gen_paths, namespace)


def test_line_pp_returns_none(gen_paths):  # type: ignore
    class TestBadLinePostProcessor(nunavut.postprocessors.LinePostProcessor):

        def __call__(self, line_and_lineend: typing.Tuple[str, str]) -> typing.Tuple[str, str]:
            return None  # type: ignore

    namespace = _test_common_namespace(gen_paths)
    generator = nunavut.jinja.Generator(namespace, False, LanguageContext(), gen_paths.templates_dir)
    with pytest.raises(ValueError):
        generator.generate_all(False, True, [TestBadLinePostProcessor()])


def test_trim_trailing_ws(gen_paths):  # type: ignore
    namespace = _test_common_namespace(gen_paths)
    generator = nunavut.jinja.Generator(namespace, False, LanguageContext(), gen_paths.templates_dir)
    generator.generate_all(False, True, [nunavut.postprocessors.TrimTrailingWhitespace()])
    outfile = _test_common_post_condition(gen_paths, namespace)

    with open(str(outfile), 'r') as json_file:
        for line in json_file:
            assert re.search(r' +$', line) is None


def test_limit_empty_lines(gen_paths):  # type: ignore
    namespace = _test_common_namespace(gen_paths)
    generator = nunavut.jinja.Generator(namespace, False, LanguageContext(), gen_paths.templates_dir)
    generator.generate_all(False, True, [nunavut.postprocessors.LimitEmptyLines(0)])
    outfile = _test_common_post_condition(gen_paths, namespace)

    with open(str(outfile), 'r') as json_file:
        for line in json_file:
            line_end_match = re.search(r'\n|\r\n', line)
            if line_end_match is not None:
                assert len(line) > line_end_match.end() - line_end_match.start()
            else:
                assert len(line) > 0


def test_pp_trim_trailing_whitespace(gen_paths):  # type: ignore
    """ Verify the --pp-trim-trailing-whitespace argument of nnvg.
    """
    outfile = gen_paths.out_dir /\
        pathlib.Path('uavcan') /\
        pathlib.Path('test') /\
        pathlib.Path('TestType_0_2').with_suffix('.json')

    nnvg_cmd_0 = ['--templates', str(gen_paths.templates_dir),
                  '-O', str(gen_paths.out_dir),
                  '-e', '.json',
                  str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    fixtures.run_nnvg(gen_paths, nnvg_cmd_0)

    lines_w_trailing = 0
    with open(str(outfile), 'r') as json_file:
        for line in json_file:
            if re.search(r' +$', line) is not None:
                lines_w_trailing += 1

    assert lines_w_trailing > 0

    nnvg_cmd_1 = ['--templates', str(gen_paths.templates_dir),
                  '-O', str(gen_paths.out_dir),
                  '-e', '.json',
                  '--pp-trim-trailing-whitespace',
                  str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    fixtures.run_nnvg(gen_paths, nnvg_cmd_1)

    with open(str(outfile), 'r') as json_file:
        for line in json_file:
            assert re.search(r' +$', line) is None


def test_pp_max_emptylines(gen_paths):  # type: ignore
    """ Verify the --pp-max-emptylines argument of nnvg.
    """
    outfile = gen_paths.out_dir /\
        pathlib.Path('uavcan') /\
        pathlib.Path('test') /\
        pathlib.Path('TestType_0_2').with_suffix('.json')

    nnvg_cmd_0 = ['--templates', str(gen_paths.templates_dir),
                  '-O', str(gen_paths.out_dir),
                  '-e', '.json',
                  str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    fixtures.run_nnvg(gen_paths, nnvg_cmd_0)

    found_empty_line = False
    with open(str(outfile), 'r') as json_file:
        for line in json_file:
            line_end_match = re.search(r'\n|\r\n', line)
            if line_end_match is not None and len(line) == line_end_match.end() - line_end_match.start():
                found_empty_line = True
                break
            elif len(line) == 0:
                found_empty_line = True
                break

    assert found_empty_line

    nnvg_cmd_1 = ['--templates', str(gen_paths.templates_dir),
                  '-O', str(gen_paths.out_dir),
                  '-e', '.json',
                  '--pp-max-emptylines', '0',
                  str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    fixtures.run_nnvg(gen_paths, nnvg_cmd_1)

    with open(str(outfile), 'r') as json_file:
        for line in json_file:
            for line in json_file:
                line_end_match = re.search(r'\n|\r\n', line)
                if line_end_match is not None:
                    assert len(line) > line_end_match.end() - line_end_match.start()
                else:
                    assert len(line) > 0


def test_external_edit_in_place(gen_paths):  # type: ignore
    """
    Test that ExternalProgramEditInPlace is invoked as expected
    """
    namespace = _test_common_namespace(gen_paths)
    generator = nunavut.jinja.Generator(namespace, False, LanguageContext(), gen_paths.templates_dir)
    ext_program = gen_paths.test_dir / pathlib.Path('ext_program.py')
    edit_in_place = nunavut.postprocessors.ExternalProgramEditInPlace([str(ext_program)])
    generator.generate_all(False, True, [edit_in_place])

    outfile = gen_paths.find_outfile_in_namespace("uavcan.test.TestType", namespace)
    assert outfile is not None

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob['ext'] == 'changed'


def test_external_edit_in_place_fail(gen_paths):  # type: ignore
    """
    Test that ExternalProgramEditInPlace handles error as expected.
    """
    namespace = _test_common_namespace(gen_paths)
    generator = nunavut.jinja.Generator(namespace, False, LanguageContext(), gen_paths.templates_dir)
    ext_program = gen_paths.test_dir / pathlib.Path('ext_program.py')
    simulated_error_args = [str(ext_program), '--simulate-error']
    edit_in_place_checking = nunavut.postprocessors.ExternalProgramEditInPlace(simulated_error_args)
    with pytest.raises(subprocess.CalledProcessError):
        generator.generate_all(False, True, [edit_in_place_checking])
    edit_in_place_not_checking = nunavut.postprocessors.ExternalProgramEditInPlace(simulated_error_args, check=False)
    generator.generate_all(False, True, [edit_in_place_not_checking])


def test_pp_run_program(gen_paths):  # type: ignore
    outfile = gen_paths.out_dir /\
        pathlib.Path('uavcan') /\
        pathlib.Path('test') /\
        pathlib.Path('TestType_0_2').with_suffix('.json')

    ext_program = gen_paths.test_dir / pathlib.Path('ext_program.py')

    nnvg_args0 = ['--templates', str(gen_paths.templates_dir),
                  '-O', str(gen_paths.out_dir),
                  '-e', '.json',
                  '--pp-run-program', str(ext_program),
                  str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    fixtures.run_nnvg(gen_paths, nnvg_args0)

    with open(str(outfile), 'r') as json_file:
        json_blob = json.load(json_file)

    assert json_blob is not None
    assert json_blob['ext'] == 'changed'

    assert pathlib.Path(outfile).stat().st_mode & 0o777 == 0o444


def test_pp_run_program_w_arg(gen_paths):  # type: ignore
    ext_program = gen_paths.test_dir / pathlib.Path('ext_program.py')

    nnvg_args0 = ['--templates', str(gen_paths.templates_dir),
                  '-O', str(gen_paths.out_dir),
                  '-e', '.json',
                  '--pp-run-program', str(ext_program),
                  '--pp-run-program-arg=--simulate-error',
                  str(gen_paths.dsdl_dir / pathlib.Path("uavcan"))]

    with pytest.raises(subprocess.CalledProcessError):
        fixtures.run_nnvg(gen_paths, nnvg_args0)
