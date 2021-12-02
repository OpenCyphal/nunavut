#
# Copyright (C) 2021  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

import pathlib
import logging
from typing import Iterator, Optional, Any
from types import ModuleType

_logger = logging.getLogger(__name__)


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
    >>> from nunavut.utilities import iter_package_resources
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
    import importlib.resources
    import importlib
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
