#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
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
import sys
from typing import Any, Callable, Generator, Generic, MutableMapping, Optional, TypeVar, cast

if sys.version_info < (3, 9):
    import importlib_resources
else:
    from importlib import resources as importlib_resources

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
class QuaternaryLogic(enum.Enum):
    """
    A quaternary logic value.

    .. invisible-code-block: python

        from nunavut._utilities import QuaternaryLogic
        from pytest import raises

        assert QuaternaryLogic.from_en_us(str(False)) == QuaternaryLogic.ALWAYS_FALSE
        assert QuaternaryLogic.from_en_us(int(False)) == QuaternaryLogic.ALWAYS_FALSE
        assert QuaternaryLogic.from_en_us(None) == QuaternaryLogic.TRUE_IF
        assert QuaternaryLogic.from_en_us("") == QuaternaryLogic.TRUE_IF
        assert QuaternaryLogic.from_en_us("default") == QuaternaryLogic.TRUE_IF
        assert QuaternaryLogic.from_en_us(str(None)) == QuaternaryLogic.TRUE_IF
        assert QuaternaryLogic.from_en_us(str(True)) == QuaternaryLogic.TRUE_IF
        assert QuaternaryLogic.from_en_us(int(True)) == QuaternaryLogic.TRUE_IF

        assert QuaternaryLogic.from_en_us("always_false") == QuaternaryLogic.ALWAYS_FALSE
        assert QuaternaryLogic.from_en_us("always-false") == QuaternaryLogic.ALWAYS_FALSE
        assert QuaternaryLogic.from_en_us("never") == QuaternaryLogic.ALWAYS_FALSE
        assert QuaternaryLogic.from_en_us("No") == QuaternaryLogic.ALWAYS_FALSE

        assert QuaternaryLogic.from_en_us("true_if") == QuaternaryLogic.TRUE_IF
        assert QuaternaryLogic.from_en_us("true-if") == QuaternaryLogic.TRUE_IF
        assert QuaternaryLogic.from_en_us("as-needed") == QuaternaryLogic.TRUE_IF
        assert QuaternaryLogic.from_en_us("if-needed") == QuaternaryLogic.TRUE_IF
        assert QuaternaryLogic.from_en_us("yes") == QuaternaryLogic.TRUE_IF

        assert QuaternaryLogic.from_en_us("true_unless") == QuaternaryLogic.TRUE_UNLESS
        assert QuaternaryLogic.from_en_us("true-unless") == QuaternaryLogic.TRUE_UNLESS
        assert QuaternaryLogic.from_en_us("only") == QuaternaryLogic.TRUE_UNLESS

        assert QuaternaryLogic.from_en_us("always_true") == QuaternaryLogic.ALWAYS_TRUE
        assert QuaternaryLogic.from_en_us("always-true") == QuaternaryLogic.ALWAYS_TRUE
        assert QuaternaryLogic.from_en_us("always") == QuaternaryLogic.ALWAYS_TRUE

        with raises(ValueError):
            QuaternaryLogic.from_en_us("not_a_value")

    Example usage:

    .. code-block:: python

        def should_we_order_pizza(answer: QuaternaryLogic, is_today_friday: bool) -> bool:
            if answer == QuaternaryLogic.TRUE_IF:
                # order pizza on Friday!
                return is_today_friday
            elif answer == QuaternaryLogic.TRUE_UNLESS:
                # only order pizza if it's not Friday
                return not is_today_friday
            elif answer == QuaternaryLogic.ALWAYS_TRUE:
                # always order pizza
                return True
            elif answer == QuaternaryLogic.ALWAYS_FALSE:
                # never order pizza
                return False
            else:
                raise ValueError("Unknown value")

    """

    @classmethod
    def from_en_us(cls, en_us_word: Any) -> "QuaternaryLogic":
        """
        Convert an English words for "always false, always true, true if, and true unless" to a quaternary logic
        value.

        :param en_us_word: The English word to convert.
        :return: The input as a quaternary logic value.
        :raises ValueError: If the word is not recognized.

        """

        if en_us_word is None:
            return cls.TRUE_IF

        lcw = str(en_us_word).lower()
        if lcw in ("always_false", "always-false", "never", "no", "false", "0"):
            return cls.ALWAYS_FALSE
        if lcw in ("true_if", "true-if", "as-needed", "if-needed", "yes", "", "default", "none", "true", "1"):
            return cls.TRUE_IF
        if lcw in ("true_unless", "true-unless", "only"):
            return cls.TRUE_UNLESS
        if lcw in ("always_true", "always-true", "always"):
            return cls.ALWAYS_TRUE
        raise ValueError(f"Unknown value '{en_us_word}'")

    ALWAYS_FALSE = 0
    """
    Always false.
    """

    ALWAYS_TRUE = 1
    """
    Always true.
    """

    TRUE_IF = 2
    """
    True if a condition is met. (1 AND condition)
    """

    TRUE_UNLESS = 3
    """
    True unless a condition is met. (1 XOR condition)
    """


@enum.unique
class ResourceType(enum.Enum):
    """
    Standard Nunavut classifications for Python package resources.
    """

    NONE = 0
    """ No resources specified."""
    SERIALIZATION_SUPPORT = 0x1
    """Serialization support files."""
    TYPE_SUPPORT = 0x2
    """Type support files."""
    ONLY = 0x80000000
    """Only the specified resources."""
    ANY = 0x3
    """Any resources."""


@enum.unique
class ResourceSearchPolicy(enum.Enum):
    """
    Generic policy type for controlling the behaviour of things that search for resources.
    """

    FIND_ALL = 0
    FIND_FIRST = 1


def iter_package_resources(pkg_name: str, *suffix_filters: str) -> Generator[pathlib.Path, None, None]:
    """
    A generator that yields all the resources in a package that match a given suffix filter.

    Example usage:

    .. invisible-code-block: python

        from nunavut._utilities import iter_package_resources

    .. code-block:: python

        for x in iter_package_resources("nunavut.lang", ".py"):
            print(x)

    .. invisible-code-block: python

        rs = [x for x in iter_package_resources("nunavut.lang", ".py") if x.name == "__init__.py"]
        assert 1 == len(rs)
        assert rs[0].name == '__init__.py'

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


class DefaultValue:
    """
    Represents a default value in the language configuration. Use this to differentiate between explicit values and
    default values when merging configuration. For example, given the following configuration:

    .. invisible-code-block: python

        from nunavut import DefaultValue

    .. code-block:: python

        collection = {
            'a': DefaultValue(1),
            'b': 2
        }

        overrides = [
            {
                'a': 3,
                'b': DefaultValue(4)
            },
            {
                'a': DefaultValue(5),
                'b': 6
            }
        ]

    Then the merged configuration should be:

    .. code-block:: python

        merged = {
            'a': 3,
            'b': 6
        }

    .. invisible-code-block: python

        # let's try it
        for override in overrides:
            collection = deep_update(collection, override)

        assert collection['a'] == merged['a']
        assert collection['b'] == merged['b']

    Other properties of DefaultValue:

    .. code-block:: python

        assert DefaultValue(1) == 1
        assert DefaultValue(1) != 2
        assert DefaultValue(1) == DefaultValue(1)
        assert DefaultValue(1) != DefaultValue(2)
        assert eval(repr(DefaultValue(1))) == DefaultValue(1)
        assert hash(DefaultValue(1)) == hash(1)
        assert bool(DefaultValue(1))
        assert not bool(DefaultValue(None))
        repred = eval(repr(DefaultValue(8)))
        assert repred.value == 8

    """

    @classmethod
    def assign_to_if_not_default(cls, target: MutableMapping[str, Any], key: str, value: Any) -> Any:
        """
        Assigns a value to a key in a dictionary unless the key already has a value and the value is not a
        `DefaultValue`. The one exception to this is if the value is a `DefaultValue` and the value for the key is
        already a `DefaultValue`. In this case the new `DefaultValue` value will be assigned to the key.

        :param target: The dictionary to assign to.
        :param key: The key to assign to.
        :param value: The value to test and assign.
        :return: The value assigned to the key. This is the value of the `value` parameter if it was assigned or the
                    value of the key in the target dictionary if it was not assigned.
        """
        try:
            if isinstance(value, DefaultValue) and not isinstance(target[key], DefaultValue):
                return target[key]
        except KeyError:
            pass
        target[key] = value
        return value

    def __init__(self, value: Any) -> None:
        self._value = value

    @property
    def value(self) -> Any:
        """
        The default value.
        """
        return self._value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, DefaultValue):
            return bool(self._value == other.value)
        return bool(self._value == other)

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return f"DefaultValue({self.value})"

    def __str__(self) -> str:
        return f"DefaultValue({self.value})"

    def __hash__(self) -> int:
        return hash(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)


def no_default_value(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to convert a function that may return `DefaultValue`s to a function that returns the value of the any
    `DefaultValue`s found. For example:

    .. invisible-code-block: python

        from nunavut._utilities import DefaultValue, no_default_value

    .. code-block:: python

        @no_default_value
        def some_function() -> DefaultValue:
            return DefaultValue(1)

        assert some_function() == 1
        assert not isinstance(some_function(), DefaultValue)
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)
        if isinstance(result, DefaultValue):
            return result.value
        return result

    return wrapper


DeepUpdateT = TypeVar("DeepUpdateT", bound=MutableMapping)


def deep_update(target: DeepUpdateT, source: DeepUpdateT) -> DeepUpdateT:
    """
    Helper method to do a recursive update of a map that may contain maps as values.

    .. invisible-code-block: python

        from nunavut._utilities import deep_update

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

    Note that this method is `DefaultValue` aware. If a value in the target map is a `DefaultValue` then it will not
    overwrite the value in the target map. If the value in the source map is a `DefaultValue` then it will not be
    used to update existing values of any type in the target map but will be used to update the target map if the
    target map does not have a value for the given key. In such cases the `DefaultValue` will be inserted into the
    target map.

    .. code-block:: python

        from nunavut import DefaultValue
        target_map   =  {
                            "a": { "one": 1, "two": DefaultValue(2) },
                            "b": "not a default",
                            "c": DefaultValue("one default...")
                        }
        update_from  =  {
                            "a": { "two": { "i": "this value" }, "three": DefaultValue("that value")},
                            "b": DefaultValue("see"),
                            "c": DefaultValue("...deserves another."),
                            "d": DefaultValue("This happened.")
                        }

        target_map   = deep_update(target_map, update_from)

        assert target_map["a"]["one"] == 1
        assert target_map["a"]["two"]["i"] == "this value"
        assert target_map["a"]["three"] == "that value"
        assert target_map["b"] == "not a default"
        assert target_map["c"] == "...deserves another."
        assert target_map["d"] == "This happened."

    """
    if isinstance(target, collections.abc.Mapping):
        for key, value in source.items():
            if isinstance(value, collections.abc.Mapping):
                target[key] = deep_update(target.get(key, {}), cast(DeepUpdateT, value))
            else:
                DefaultValue.assign_to_if_not_default(target, key, value)
    else:
        target = copy.copy(source)
    return target


PropertyT = TypeVar("PropertyT")


class cached_property(Generic[PropertyT]):
    """
    Based on `functools.cached_property` (Python Foundation License 2.0, SPDX: PSF-2.0) implementation in Python 3.11,
    this is both a backport for older Python versions and a version that omits the problematic lock as documented for
    Python 3.12. As such, this version is not thread safe.

    :param func: The function to be wrapped by this decorator.

    .. invisible-code-block: python

        from nunavut._utilities import cached_property
        from pytest import raises

        class Test:

            @classmethod
            @cached_property
            def cls_test(cls) -> int:
                return 1

            def __init__(self) -> None:
                self.calls = 0

            @cached_property
            def test(self) -> int:
                self.calls += 1
                return self.calls

        t = Test()
        assert t.test == 1
        assert t.test == 1
        assert t.test == 1

    """

    _NOT_FOUND = object()

    def __init__(self, func: Callable[..., PropertyT]):
        self._func = func
        self._attr_name: Optional[str] = None
        self.__doc__ = func.__doc__

    def __set_name__(self, owner: Any, name: str) -> None:
        self._attr_name = name

    def __get__(self, instance: Any, owner: Optional[Any] = None) -> PropertyT:
        if self._attr_name is None:  # pragma: no cover
            raise TypeError("Cannot use cached_property instance without calling __set_name__ on it.")
        cache = instance.__dict__
        val = cast(PropertyT, cache.get(self._attr_name, self._NOT_FOUND))
        if val is self._NOT_FOUND:
            val = self._func(instance)
            cache[self._attr_name] = val
        return val
