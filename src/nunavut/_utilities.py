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
from typing import Iterator, Optional

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


class PackageResource:
    """
    Facade for accessing data files distributed within Python packages.
    See :func:`iter_package_resources` for details.
    """

    def make_path(self) -> pathlib.Path:
        """
        Ensures that this resource is mapped on the physical filesystem and returns its path.
        This may involve expensive data copying depending on the implementation of the package.
        """
        raise NotImplementedError

    @property
    def basename(self) -> str:
        raise NotImplementedError

    def read_text(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        raise NotImplementedError


def iter_package_resources(pkg_name: str) -> Iterator[PackageResource]:
    """
    >>> from nunavut._utilities import iter_package_resources
    >>> rs, = [x for x in iter_package_resources("nunavut.lang") if x.basename == "__init__.py"]
    >>> rs.basename
    '__init__.py'
    >>> p = rs.make_path()
    >>> p == rs.make_path()  # Returns same path.
    True
    >>> len(p.read_text()) > 0
    True
    >>> p.read_text() == rs.read_text()
    True

    """
    return _iter_package_resources_impl(pkg_name)


try:  # noqa: C901
    import importlib
    import importlib.resources
    import tempfile

    class PackageResourceImpl(PackageResource):
        def __init__(self, pkg_name: str, res_name: str) -> None:
            self._pkg_name = pkg_name
            self._res_name = res_name
            self._path = None  # type: Optional[pathlib.Path]

        def make_path(self) -> pathlib.Path:
            if not self._path:
                # Create a temporary directory to ensure that the basename is retained unchanged.
                # Normally we should return a context manager here, but the calling code does not support that,
                # it always expects a plain path. A mild refactoring is needed to fix that.
                parent = pathlib.Path(tempfile.mkdtemp())
                parent.mkdir(parents=True, exist_ok=True)
                path = parent / self.basename
                with open(path, "w") as f:
                    f.write(self.read_text())
                self._path = path
            _logger.debug("%r available on the filesystem as %r", self, str(self._path))
            assert self._path and self._path.is_file()
            return self._path

        @property
        def basename(self) -> str:
            return self._res_name

        def read_text(self) -> str:
            return importlib.resources.read_text(self._pkg_name, self._res_name)

        def __repr__(self) -> str:
            return type(self).__name__ + "(%r, %r)" % (self._pkg_name, self._res_name)

    def _iter_package_resources_impl(pkg_name: str) -> Iterator[PackageResource]:
        for r in importlib.resources.contents(pkg_name):
            _logger.debug("Found %r in %r", r, pkg_name)
            yield PackageResourceImpl(pkg_name, r)

except (ImportError, AttributeError):  # Compatibility with EOL versions of Python (v3.5, v3.6)
    import pkg_resources

    class PackageResourceImpl(PackageResource):  # type: ignore
        def __init__(self, pkg_name: str, res_name: str) -> None:
            self._pkg_name = pkg_name
            self._res_name = res_name

        def make_path(self) -> pathlib.Path:
            p = pathlib.Path(pkg_resources.resource_filename(self._pkg_name, str(self._res_name)))
            _logger.debug("%r available on the filesystem as %r", self, str(p))
            return p

        @property
        def basename(self) -> str:
            return self._res_name

        def read_text(self) -> str:
            with pkg_resources.resource_stream(self._pkg_name, self._res_name) as rs:
                return str(rs.read().decode(encoding="utf-8", errors="replace"))

        def __repr__(self) -> str:
            return type(self).__name__ + "(%r, %r)" % (self._pkg_name, self._res_name)

    def _iter_package_resources_impl(pkg_name: str) -> Iterator[PackageResource]:
        for r in pkg_resources.resource_listdir(pkg_name, "."):
            _logger.debug("Found %r in %r", r, pkg_name)
            yield PackageResourceImpl(pkg_name, r)
