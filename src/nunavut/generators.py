#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
Module containing types and utilities for building generator objects.
Generators abstract the code generation technology used to transform
pydsdl AST into source code.
"""

import abc
import os
import pathlib
import typing

import nunavut


class AbstractGenerator(metaclass=abc.ABCMeta):
    """
        Abstract base class for classes that generate source file output
        from a given pydsdl parser result.

        :param nunavut.Namespace namespace:  The top-level namespace to
            generates types at and from.
        :param nunavut.YesNoDefault generate_namespace_types:  Set to YES
            to force generation files for namespaces and NO to suppress.
            DEFAULT will generate namespace files based on the language
            preference.
    """

    def __init__(self,
                 namespace: nunavut.Namespace,
                 generate_namespace_types: nunavut.YesNoDefault = nunavut.YesNoDefault.DEFAULT):
        self._namespace = namespace
        if generate_namespace_types == nunavut.YesNoDefault.YES:
            self._generate_namespace_types = True
        elif generate_namespace_types == nunavut.YesNoDefault.NO:
            self._generate_namespace_types = False
        else:
            target_language = self._namespace.get_language_context().get_target_language()
            if target_language is not None and target_language.has_standard_namespace_files:
                self._generate_namespace_types = True
            else:
                self._generate_namespace_types = False

    @property
    def namespace(self) -> nunavut.Namespace:
        """
        The root :class:`nunavut.Namespace` for this generator.
        """
        return self._namespace

    @property
    def generate_namespace_types(self) -> bool:
        """
        If true then the generator is set to emit files for :class:`nunavut.Namespace`
        in addition to the pydsdl datatypes. If false then only files for pydsdl datatypes
        will be generated.
        """
        return self._generate_namespace_types

    @abc.abstractmethod
    def get_templates(self) -> typing.Iterable[pathlib.Path]:
        """
        Enumerate all templates found in the templates path.
        :returns: A list of paths to all templates found by this Generator object.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def generate_all(self,
                     is_dryrun: bool = False,
                     allow_overwrite: bool = True) \
            -> typing.Iterable[pathlib.Path]:
        """
        Generates all output for a given :class:`nunavut.Namespace` and using
        the templates found by this object.

        :param bool is_dryrun: If True then no output files will actually be
                               written but all other operations will be performed.
        :param bool allow_overwrite: If True then the generator will attempt to overwrite any existing files
                                it encounters. If False then the generator will raise an error if the
                                output file exists and the generation is not a dry-run.
        :return: 0 for success. Non-zero for errors.
        :raises: PermissionError if :attr:`allow_overwrite` is False and the file exists.
        """
        raise NotImplementedError()


class CopyFromPackageGenerator(AbstractGenerator):
    """
    Generates output files by copying them from within the Nunavut package itself.
    This allows us to embed things in Nunavut that are copied without going through
    a template engine. This generator always copies files from those returned by
    the ``file_iterator`` to locations under :func:`nunavut.Namespace.get_support_output_folder()`

    .. invisible-code-block: python

        import pathlib
        import pytest
        from unittest.mock import NonCallableMagicMock, MagicMock
        from nunavut.generators import CopyFromPackageGenerator

        fake_support_output_folder = pathlib.PurePath('tmp')

        namespace = NonCallableMagicMock()
        namespace.get_support_output_folder = MagicMock(return_value=fake_support_output_folder)

        fake_source_files = [
            pathlib.Path("foo/bar.a"),
            pathlib.Path("foo/bar.b")
        ]

    .. code-block:: python

        def source_file_iterator():
            # we generate from a list of two fake paths to
            # demonstrate how the CopyFromPackageGenerator
            # uses its file_iterator parameter.
            for source_file in fake_source_files:
                yield source_file

        generator = CopyFromPackageGenerator(namespace, source_file_iterator(), pathlib.Path('my_subfolder'))
        assert len(generator.get_templates()) == 2
        assert len(generator.generate_all(is_dryrun=True)) == 2

        # The generator will copy from the "templates" (i.e. the files within this package to copy) to a
        # folder under the subfolder provided to its constructor.
        assert 'my_subfolder' == generator.generate_all(is_dryrun=True)[0].parent.name

        # Note that the sub-folder must be a relative path since the generator will place it under
        # the path returned by Namespace.get_support_output_folder()

        with pytest.raises(ValueError):
            _ = CopyFromPackageGenerator(namespace, source_file_iterator(), pathlib.Path('/').resolve())

    .. invisible-code-block: python

        for template in generator.get_templates():
            print('copy from fake input: ' + str(template))

        for copy_to in generator.generate_all(is_dryrun=True):
            print('copy to fake output : ' + str(copy_to))

    :param nunavut.Namespace namespace:  The top-level namespace to generates types at and from.
    :param typing.Generator[pathlib.Path] file_iterator: Provides files within the Nunavut distribution to
        copy from. All files returned by this iterator will be copied.
    :param pathlib.Path sub_folders: Folders to create under :func:`nunavut.Namespace.get_support_output_folder()`
        within which all of the package files will be copied to.
    """

    def __init__(self,
                 namespace: nunavut.Namespace,
                 file_iterator: typing.Generator[pathlib.Path, None, None],
                 sub_folders: pathlib.Path):
        super().__init__(namespace)
        self._file_iterator = file_iterator
        self._support_resources = None  # type: typing.Optional[typing.Iterable[pathlib.Path]]
        if sub_folders.is_absolute():
            raise ValueError('subfolders argument must be a relative path.')
        self._sub_folders = sub_folders

    def get_templates(self) -> typing.Iterable[pathlib.Path]:
        files = []
        resources = self._list_support_resources()
        for resource in resources:
            files.append(resource)
        return files

    def generate_all(self,
                     is_dryrun: bool = False,
                     allow_overwrite: bool = True) \
            -> typing.Iterable[pathlib.Path]:

        target_path = pathlib.Path(self.namespace.get_support_output_folder()) / self._sub_folders

        if not is_dryrun:
            import shutil
            os.makedirs(str(target_path), exist_ok=True)

        copied = []  # type: typing.List[pathlib.Path]
        for resource in self.get_templates():
            target = target_path / resource.name
            if not is_dryrun:
                if not allow_overwrite and target.exists():
                    raise PermissionError('{} exists. Refusing to overwrite.'.format(str(target)))
                shutil.copy(str(resource), str(target_path))
            copied.append(target)
        return copied

    def _list_support_resources(self) -> typing.Iterable[pathlib.Path]:
        """
        Cache all files returned from the file iterator in this object.
        """
        if self._support_resources is None:
            self._support_resources = []
            for support_file in self._file_iterator:
                self._support_resources.append(support_file)
        return self._support_resources


def create_support_generator(namespace: nunavut.Namespace) -> 'AbstractGenerator':
    """
    Create a new :class:`Generator <nunavut.generators.AbstractGenerator>` that uses embedded support
    headers, libraries, and other types needed to use generated serialization code for the
    :func:`target language <nunavut.lang.LanguageContext.get_target_language>`. If no target language
    is set or if serialization support has been turned off a no-op generator will be returned instead.
    """
    class _NoOpSupportGenerator(AbstractGenerator):
        def get_templates(self) -> typing.Iterable[pathlib.Path]:
            return []

        def generate_all(self,
                         is_dryrun: bool = False,
                         allow_overwrite: bool = True) \
                -> typing.Iterable[pathlib.Path]:
            return []

    target_language = namespace.get_language_context().get_target_language()

    if target_language is None or target_language.omit_serialization_support:
        return _NoOpSupportGenerator(namespace, nunavut.YesNoDefault.DEFAULT)
    else:

        #  Create the sub-folder to copy-to based on the support namespace.
        sub_folders = pathlib.Path('')

        for namespace_part in target_language.support_namespace:
            sub_folders = sub_folders / pathlib.Path(namespace_part)

        return CopyFromPackageGenerator(namespace,
                                        target_language.support_files,
                                        sub_folders)


def create_generators(namespace: nunavut.Namespace, **kwargs: typing.Any) -> \
        typing.Tuple['AbstractGenerator', 'AbstractGenerator']:
    """
    Create the two generators used by Nunavut; a code-generator and a support-library generator.
    :param  nunavut.Namespace namespace:  The namespace to generate code within.
    :param  kwargs: A list of arguments that are forwarded to the generator constructors.
    :return: Tuple with the first item being the code-generator and the second the support-library
        generator.
    """
    from nunavut.jinja import Generator
    return (Generator(namespace, **kwargs), create_support_generator(namespace))
