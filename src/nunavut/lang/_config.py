#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2020  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""Logic for parsing language configuration.

"""
import re
import types
import typing

from yaml import Loader as YamlLoader
from yaml import load as yaml_loader


class LanguageConfig:
    """
    Configuration storage encapsulating parsers and other configuration format details. For any configuration type used
    the concept of "sections" must be maintained which requires that the top-level configuration be structured as
    key/value pairs with the keys using the form "nunavut.lang.[language name]". For example, yaml configuration must
    have a top-level structure like this:

    .. code-block:: python

        example_yaml = '''
            nunavut.lang.a:
                key_one: value_one
                key_two: value_two
            nunavut.lang.b:
                key_one: value_one
                key_two: value_two
            nunavut.lang.c:
                key_one: value_one
                key_two: value_two
        '''

    .. invisible-code-block: python
        from nunavut.lang import LanguageConfig

        config = LanguageConfig()
        config.read_string(example_yaml)

        data = config.sections()
        assert len(data) == 3
        assert data['nunavut.lang.b']['key_two'] == 'value_two'

    .. note::
        The "language name" part of the section identifier must not start with a number and can contain only
        alphanumeric characters. That is, the section identifier must match this pattern:

            nunavut\\.lang\\.[a-zA-Z]{1}\\w*

    The values of the section data can be anything:

    .. code-block:: python

        example_yaml = '''
            nunavut.lang.d:
                key_one:
                    - is
                    - a
                    - list:
                        where: index2
                        is: a_dictionary
        '''

    .. invisible-code-block: python

        config.read_string(example_yaml)
        assert 'a_dictionary' == config.sections()['nunavut.lang.d']['key_one'][2]['list']['is']

    """

    def __init__(self):  # type: ignore
        self._section_name_pattern = re.compile(r"^nunavut\.lang\.([a-zA-Z]{1}\w*)$")
        self._sections = dict()  # type: typing.Dict[str, typing.Dict[str, typing.Any]]

    def update(self, configuration: typing.Any) -> None:
        """
        Add configuration data to this configuration from a string.

        Unlike add_section, this method will update section data with existing keys.

        For example, the first update is to an empty configuration so it will act as a simple insert operation:

        .. invisible-code-block: python
            from nunavut.lang import LanguageConfig

        .. code-block: python

            initial_data = {
                'nunavut.lang.a':
                    {
                        'key_one': 'value_one',
                        'key_two': 'value_two'
                    },
                'nunavut.lang.b':
                    {
                        'key_one':
                            [
                                'item_0',
                                {
                                    'item_1_value_0': 0,
                                    'item_1_value_1': 1
                                },
                                'item_2'
                            ],
                        'key_two': 'value_two'
                    }
            }

            config = LanguageConfig()
            config.update(initial_data)

            assert config.sections()['nunavut.lang.a']['key_one'] == 'value_one'
            assert config.sections()['nunavut.lang.b']['key_one'][1]['item_1_value_1'] == 1
            assert config.sections()['nunavut.lang.b']['key_two'] == 'value_two'

        ...but updating this data is now possible where sections can be added and updated:

        .. code-block: python

            updated_data = '''
                nunavut.lang.b:
                    key_one: simple
                    key_three: value_three
                nunavut.lang.c:
                    key_one: new_language_key
            '''

            updated_data = {
                'nunavut.lang.b':
                    {
                        'key_one': 'simple',
                        'key_three': 'value_three'
                    },
                'nunavut.lang.c':
                    {
                        'key_one': 'new_language_key'
                    },
            }

            config.update(updated_data)

            assert config.sections()['nunavut.lang.a']['key_one'] == 'value_one'
            assert config.sections()['nunavut.lang.b']['key_one'] == 'simple'
            assert config.sections()['nunavut.lang.b']['key_two'] == 'value_two'
            assert config.sections()['nunavut.lang.b']['key_three'] == 'value_three'
            assert config.sections()['nunavut.lang.c']['key_one'] == 'new_language_key'

        .. invisible-code-block: python

            tests = [
                (
                    {
                        'did_not_start.with.nunavut':
                            {
                                'key_one': 'value_one'
                            }
                    },
                    ValueError()
                ),
                (
                    {
                        'nunavut.lang.0c':
                            {
                                'key_one': 'value_one'
                            }
                    },
                    ValueError()
                ),
                (
                    {
                        1:
                            {
                                'key_one': 'value_one'
                            }
                    },
                    TypeError()
                ),
                (
                    {
                        'nunavut.lang.c.iso':
                            {
                                'key_one': 'value_one'
                            }
                    },
                    ValueError()
                )
            ]

            for test_tuple in tests:
                try:
                    config.update(test_tuple[0])
                    assert False
                except BaseException as e:
                    assert isinstance(e, type(test_tuple[1]))
                    pass

        """

        # validate the (very loose) configuration schema.
        for section_name, section_data in configuration.items():
            if not isinstance(section_name, str):
                raise TypeError("section names must be strings")
            if not self._section_name_pattern.match(section_name):
                raise ValueError(
                    'Section name "{}" is invalid. See LanguageConfig documentation for rules.'.format(section_name)
                )
            try:
                section = self._sections[section_name]
            except KeyError:
                self._sections[section_name] = dict()
                section = self._sections[section_name]
            section.update(section_data)

    def sections(self) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
        return self._sections

    def read_string(self, string: str, context: typing.Optional[str] = None) -> None:
        configuration = yaml_loader(string, Loader=YamlLoader)
        self.update(configuration)

    def read_file(self, f: typing.TextIO, context: typing.Optional[str] = None) -> None:
        configuration = yaml_loader(f, Loader=YamlLoader)
        self.update(configuration)

    def set(self, section: str, option: str, value: typing.Any) -> None:
        self._sections[section][option] = value

    def add_section(self, section_name: str) -> None:
        if not isinstance(section_name, str):
            raise TypeError("section names must be strings")
        if not self._section_name_pattern.match(section_name):
            raise ValueError(
                'Section name "{}" is invalid. See LanguageConfig documentation for rules.'.format(section_name)
            )
        if section_name in self._sections:
            raise ValueError("Section {} is already defined.".format(section_name))
        self._sections[section_name] = dict()

    _UNSET = object()  # Used internally to allow "None" as a default value.

    def _get_config_value_raw(self, section_name: str, key: str, default_value: typing.Any) -> typing.Any:
        """
        .. invisible-code-block: python
            from nunavut.lang import LanguageConfig

        .. code-block: python

            test_data = {
                'nunavut.lang.a':
                    {
                        'key_one': 'value_one'
                    },
                'nunavut.lang.b':
                    {
                        'key_one': 'value_one'
                    }
            }

            config = LanguageConfig()
            config.update(initial_data)

            try:
                config.get_config_value('nunavut.lang.c', 'foo')
                assert False
            except KeyError:
                pass

            assert 'bar' == config.get_config_value('nunavut.lang.c', 'foo', 'bar')

            try:
                config.get_config_value('nunavut.lang.a', 'foo')
                assert False
            except KeyError:
                pass

            assert 'bar' == config.get_config_value('nunavut.lang.a', 'foo', 'bar')

            assert 'value_one' == config.get_config_value('nunavut.lang.a', 'key_one')
            assert 'value_one' == config.get_config_value('nunavut.lang.a', 'key_one', 'bar')
        """
        try:
            section_data = self._sections[section_name]
        except KeyError:
            if default_value is not self._UNSET:
                return default_value
            else:
                raise
        try:
            return section_data[key]
        except KeyError:
            if default_value is not self._UNSET:
                return default_value
            else:
                raise

    def get_config_value(self, section_name: str, key: str, default_value: typing.Optional[str] = None) -> str:
        """
        Get an optional language property from the language configuration.

        :param section_name : The name of the section to get the value from.
        :param str key      : The config value to retrieve.
        :param default_value: The value to return if the key was not in the configuration. If provided
            this method will not raise.
        :type default_value : typing.Optional[str]
        :return: Either the value from the config or the default_value if provided.
        :rtype: str
        :raises: KeyError if the section or the key in the section does not exist and a default_value was not provided.

         .. invisible-code-block: python
            from nunavut.lang import LanguageConfig

        .. code-block: python

            test_data = {
                'nunavut.lang.a':
                    {
                        'key_one': [
                            1,
                            2
                        ]
                    },
                'nunavut.lang.b':
                    {
                        'key_one': 'value_one'
                    }
            }

            config = LanguageConfig()
            config.update(test_data)

            assert 'value_one' == config.get_config_value('nunavut.lang.b', 'key_one')
            assert 'value_one' == config.get_config_value('nunavut.lang.b', 'key_one', 'bar')
            assert 'bar' == config.get_config_value('nunavut.lang.b', 'key_two', 'bar')
            try:
                config.get_config_value('nunavut.lang.b', 'key_two')
                assert False # supposed to throw without a default value.
            except KeyError:
                pass
        """
        optional_result = self._get_config_value_raw(
            section_name, key, (self._UNSET if default_value is None else default_value)
        )

        # when we've retrieved a None result the str() cast will return "None" which isn't our intent.
        # Instead, if we get None and the _get_config_value_raw didn't throw a KeyError then what we really
        # meant is that we wanted an empty string if the value existed but was None.
        return str(optional_result) if optional_result is not None else ""

    def get_config_value_as_bool(self, section_name: str, key: str, default_value: bool = False) -> bool:
        """
        Get an optional language property from the language configuration returning a boolean. The rules
        for boolean conversion are as follows:

        .. invisible-code-block: python

            from nunavut.lang import LanguageConfig

            config = LanguageConfig()
            config.add_section('nunavut.lang.cpp')

        .. code-block:: python

            # "Any string" = True
            config.set('nunavut.lang.cpp', 'v', 'Any string')
            assert config.get_config_value_as_bool('nunavut.lang.cpp', 'v')

            # "true" = True
            config.set('nunavut.lang.cpp', 'v', 'true')
            assert config.get_config_value_as_bool('nunavut.lang.cpp', 'v')

            # "TrUe" = True
            config.set('nunavut.lang.cpp', 'v', 'TrUe')
            assert config.get_config_value_as_bool('nunavut.lang.cpp', 'v')

            # "1" = True
            config.set('nunavut.lang.cpp', 'v', '1')
            assert config.get_config_value_as_bool('nunavut.lang.cpp', 'v')

            # "false" = False
            config.set('nunavut.lang.cpp', 'v', 'false')
            assert not config.get_config_value_as_bool('nunavut.lang.cpp', 'v')

            # "FaLse" = False
            config.set('nunavut.lang.cpp', 'v', 'FaLse')
            assert not config.get_config_value_as_bool('nunavut.lang.cpp', 'v')

            # "0" = False
            config.set('nunavut.lang.cpp', 'v', '0')
            assert not config.get_config_value_as_bool('nunavut.lang.cpp', 'v')

            # "" = False
            config.set('nunavut.lang.cpp', 'v', '')
            assert not config.get_config_value_as_bool('nunavut.lang.cpp', 'v')

            # False if not defined
            assert not config.get_config_value_as_bool('nunavut.lang.cpp', 'not_a_key')

            # True if not defined but default_value is True
            assert not config.get_config_value_as_bool('nunavut.lang.cpp', 'not_a_key')

        :param section_name         : The name of the section to get the value from.
        :param str key              : The config value to retrieve.
        :param bool default_value   : The value to use if no value existed.
        :return                     : The config value as either True or False.
        :rtype                      : bool
        """
        result = self.get_config_value(section_name, key, default_value="false" if not default_value else "true")
        if result.lower() == "false" or result == "0":
            return False
        else:
            return bool(result)

    def get_config_value_as_dict(
        self, section_name: str, key: str, default_value: typing.Optional[typing.Dict] = None
    ) -> typing.Dict[str, typing.Any]:
        """
        Get a language property parsing it as a map with string keys.

        Example:

        .. invisible-code-block: python

            from nunavut.lang import LanguageConfig

            config = LanguageConfig()
            config.add_section('nunavut.lang.a')

        .. code-block: python

            config.set('nunavut.lang.a', 'foo', {'one': 1})

            assert config.get_config_value_as_dict('nunavut.lang.a', 'foo')['one'] == 1

        .. invisible-code-block: python

            try:
                config.get_config_value_as_dict('nunavut.lang.b', 'foo')
                assert False
            except KeyError:
                pass

            assert config.get_config_value_as_dict('nunavut.lang.b', 'foo', {'one': 2})['one'] == 2

            try:
                config.get_config_value_as_dict('nunavut.lang.a', 'bar')
                assert False
            except KeyError:
                pass

            assert config.get_config_value_as_dict('nunavut.lang.a', 'bar', {'one': 2})['one'] == 2

            config.set('nunavut.lang.a', 'bar', 1)

            try:
                config.get_config_value_as_dict('nunavut.lang.a', 'bar')
                assert False
            except TypeError:
                pass

            assert config.get_config_value_as_dict('nunavut.lang.a', 'bar', {'one': 2})['one'] == 2

        :param str section_name : The name of the section to get the key from.
        :param str key          : The config value to retrieve.
        :param default_value    : The value to return if the key was not in the configuration. If provided this method
            will not raise a KeyError nor a TypeError.
        :type default_value     : typing.Optional[typing.Mapping[str, typing.Any]]
        :return                 : Either the value from the config or the default_value if provided.
        :rtype                  : typing.Mapping[str, typing.Any]
        :raises                 : KeyError if the key does not exist and a default_value was not provided.
        :raises                 : TypeError if the value exists but is not a dict and a default_value was not provided.

        """
        raw_value = self._get_config_value_raw(
            section_name, key, default_value=(self._UNSET if default_value is None else default_value)
        )
        if isinstance(raw_value, dict):
            return raw_value

        if default_value is None:
            raise TypeError("{}.{} exists but is not a dict. (is type {})".format(section_name, key, type(raw_value)))

        return default_value

    def get_config_value_as_list(
        self, section_name: str, key: str, default_value: typing.Optional[typing.List] = None
    ) -> typing.List[typing.Any]:
        """
        Get a language property parsing it as a map with string keys.

        Example:

        .. invisible-code-block: python

            from nunavut.lang import LanguageConfig

            config = LanguageConfig()
            config.add_section('nunavut.lang.a')

        .. code-block: python

            config.set('nunavut.lang.a', 'foo', [1, 2, 3])

            assert config.get_config_value_as_list('nunavut.lang.a', 'foo')[1] == 2

        .. invisible-code-block: python

            try:
                config.get_config_value_as_list('nunavut.lang.b', 'foo')
                assert False
            except KeyError:
                pass

            assert config.get_config_value_as_list('nunavut.lang.b', 'foo', [2, 3, 4])[1] == 3

            try:
                config.get_config_value_as_list('nunavut.lang.a', 'bar')
                assert False
            except KeyError:
                pass

            assert config.get_config_value_as_list('nunavut.lang.a', 'bar', [3, 4, 5])[1] == 4

            config.set('nunavut.lang.a', 'bar', 1)

            try:
                config.get_config_value_as_list('nunavut.lang.a', 'bar')
                assert False
            except TypeError:
                pass

            assert config.get_config_value_as_list('nunavut.lang.a', 'bar', [4, 5, 6])[1] == 5

        :param str section_name : The name of the section to get the key from.
        :param str key          : The config value to retrieve.
        :param default_value    : The value to return if the key was not in the configuration. If provided this method
            will not raise a KeyError nor a TypeError.
        :type default_value     : typing.Optional[typing.List[typing.Any]]
        :return                 : Either the value from the config or the default_value if provided.
        :rtype                  : typing.List[typing.Any]
        :raises                 : KeyError if the key does not exist and a default_value was not provided.
        :raises                 : TypeError if the value exists but is not a dict and a default_value was not provided.

        """
        raw_value = self._get_config_value_raw(
            section_name, key, default_value=(self._UNSET if default_value is None else default_value)
        )
        if isinstance(raw_value, list):
            return raw_value

        if default_value is None:
            raise TypeError("{}.{} exists but is not a list. (is type {})".format(section_name, key, type(raw_value)))

        return default_value


# +-------------------------------------------------------------------------------------------------------------------+
# | VersionReader
# +-------------------------------------------------------------------------------------------------------------------+


class VersionReader:
    """
    Helper to read an "x.y.z" semantic version from python modules as a module variable
    "__version__"
    """

    MODULE_VERSION_ATTRIBUTE_NAME = "__version__"

    @classmethod
    def parse_version(cls, version_string: str) -> typing.Optional[typing.Tuple[int, int, int]]:
        version_array = [int(x) for x in version_string.split(".")]
        if len(version_array) != 3:
            return None
        else:
            return (version_array[0], version_array[1], version_array[2])

    @classmethod
    def read_version(cls, module: "types.ModuleType") -> typing.Tuple[int, int, int]:
        version = getattr(module, cls.MODULE_VERSION_ATTRIBUTE_NAME, "0.0.0")  # type: str

        version_tuple = cls.parse_version(version)
        if version_tuple is None:
            raise RuntimeError(
                'Invalid {} "{}" for module {} (expected "x.y.z")'.format(
                    cls.MODULE_VERSION_ATTRIBUTE_NAME, version, module.__name__
                )
            )
        return version_tuple

    def __init__(self, module_name: str):
        self._module_name = module_name
        self._cached = None  # type: typing.Optional[typing.Tuple[int, int, int]]

    @property
    def version(self) -> typing.Tuple[int, int, int]:
        if self._cached is None:
            self._cached = self._get_version()
        return self._cached

    def _get_version(self) -> typing.Tuple[int, int, int]:
        import importlib

        try:
            return self.read_version(importlib.import_module(self._module_name))
        except (ImportError, ValueError):
            return (0, 0, 0)
