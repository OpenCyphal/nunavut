#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2021  OpenCyphal Development Team  <opencyphal.org>
# This software is distributed under the terms of the MIT License.
#
"""
A small collection of common utilities.

.. note::

    Please don't use this as a dumping ground for things that belong in a dedicated package. Python being such a
    full-featured language, there should be very few truly generic utilities in Nunavut.

"""
import collections.abc
import copy
import enum
import logging
import pathlib
from typing import Generator, MutableMapping, cast, TypeVar

import importlib_resources

_logger = logging.getLogger(__name__)


TEMPLATE_SUFFIX = ".j2"  #: The suffix expected for nunavut templates.


@enum.unique
class YesNoDefault(enum.Enum):
    """
    Trinary type for decisions that allow a default behavior to be requested that can
    be different based on other contexts. For example:

    .. invisible-code-block: python

        from datetime import datetime
        from nunavut._utilities import YesNoDefault

    .. code-block:: python

        def should_we_order_pizza(answer: YesNoDefault) -> bool:
            if answer == YesNoDefault.YES or (
               answer == YesNoDefault.DEFAULT and
               datetime.today().isoweekday() == 5):
                # if yes or if we are taking the default action which is to
                # order pizza on Friday, and today is Friday, then we order pizza
                return True
            else:
                return False

    .. invisible-code-block: python

        assert should_we_order_pizza(YesNoDefault.YES)
        assert not should_we_order_pizza(YesNoDefault.NO)

    """

    @classmethod
    def test_truth(cls, ynd_value: "YesNoDefault", default_value: bool) -> bool:
        """
        Helper method to test a YesNoDefault value and return a default boolean value.

        .. invisible-code-block: python

            from nunavut._utilities import YesNoDefault

        .. code-block:: python

            '''
                let "is YES" be Y
                let "is DEFAULT" be D where:
                    if Y then not D and if D then not Y
                    and "is NO" is Y = D = 0
                let "is default_value true" be d

                Y | D | d | Y or (D and d)
                1   *   *    1
                0   1   0    0
                0   1   1    1
                0   0   *    0
            '''

            assert YesNoDefault.test_truth(YesNoDefault.YES, False)
            assert not YesNoDefault.test_truth(YesNoDefault.DEFAULT, False)
            assert YesNoDefault.test_truth(YesNoDefault.DEFAULT, True)
            assert not YesNoDefault.test_truth(YesNoDefault.NO, True)

        """
        if ynd_value == cls.DEFAULT:
            return default_value
        else:
            return ynd_value == cls.YES

    NO = 0
    YES = 1
    DEFAULT = 2


@enum.unique
class ResourceType(enum.Enum):
    """
    Common Nunavut classifications for Python package resources.
    """

    ANY = 0
    CONFIGURATION = 1
    SERIALIZATION_SUPPORT = 2
    TYPE_SUPPORT = 3


@enum.unique
class ResourceSearchPolicy(enum.Enum):
    """
    Generic policy type for controlling the behaviour of things that seach for resources.
    """

    FIND_ALL = 0
    FIND_FIRST = 1


def iter_package_resources(pkg_name: str, *suffix_filters: str) -> Generator[pathlib.Path, None, None]:
    """
    >>> from nunavut._utilities import iter_package_resources
    >>> rs = [x for x in iter_package_resources("nunavut.lang", ".py") if x.name == "__init__.py"]
    >>> len(rs)
    1
    >>> rs[0].name
    '__init__.py'

    """
    for resource in importlib_resources.files(pkg_name).iterdir():
        if resource.is_file() and isinstance(resource, pathlib.Path):
            # Not sure why this works but it's seemed to so far. importlib_resources.as_file(resource)
            # may be more correct but this can create temporary files which would disappear after the iterator
            # had copied their paths. If you are reading this because this method isn't working for some packaging
            # scheme then we may need to use importlib_resources.as_file(resource) to create a runtime cache of
            # temporary objects that live for a given nunavut session. This, of course, wouldn't help across sessions
            # which is a common use case when integrating Nunavut with build systems. So...here be dragons.
            file_resource = resource
            if any(suffix == file_resource.suffix for suffix in suffix_filters):
                yield file_resource


def empty_list_support_files() -> Generator[pathlib.Path, None, None]:
    """
    Helper for implementing the list_support_files method in language support packages. This provides an empty
    iterator with the correct type annotations.
    """
    # works in Python 3.3 and newer. Thanks https://stackoverflow.com/a/13243870
    yield from ()


DeepUpdateType = TypeVar("DeepUpdateType", bound=MutableMapping)


def deep_update(target: DeepUpdateType, source: DeepUpdateType) -> DeepUpdateType:
    """
    Helper method to do a recursive update of a map that may contain maps as values.

    .. invisible-code-block: python

        from nunavut._utilities import deep_update
        import collections.abc

    .. code-block:: python

        target_map   =  {
                            "a": { "one": 1, "two": 2 },
                            "b": "not a map"
                        }
        update_from  =  {
                            "a": { "two": { "i": "this value" }, "three": "that value"},
                            "c": "see"
                        }

        target_map   = deep_update(target_map, update_from)
        update_from["a"]["two"]["i"] = "whoops, this was supposed to be a copy"

        assert target_map["a"]["one"] == 1
        assert isinstance(target_map["a"]["two"], collections.abc.Mapping)
        assert target_map["a"]["two"]["i"] == "this value"
        assert target_map["a"]["three"] == "that value"
        assert target_map["b"] == "not a map"
        assert "c" in target_map
        assert target_map["c"] == "see"

    """
    if isinstance(target, collections.abc.Mapping):
        for key, value in source.items():
            if isinstance(value, collections.abc.Mapping):
                target[key] = deep_update(target.get(key, {}), cast(DeepUpdateType, value))
            else:
                target[key] = value
    else:
        target = copy.copy(source)
    return target
