#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2021  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""
A small collection of common utilities.

.. note::

    Please don't use this as a dumping ground for things that belong in a dedicated package. Python being such a
    full-featured language, there should be very few truly generic utilities in Nunavut.

"""
import enum
import logging
import pathlib
from typing import Generator

import importlib_resources

_logger = logging.getLogger(__name__)


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
        if any(suffix == resource.suffix for suffix in suffix_filters):
            yield resource
