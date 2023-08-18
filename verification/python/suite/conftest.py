# Copyright (c) 2019 OpenCyphal
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@opencyphal.org>

from __future__ import annotations
import os
from typing import Sequence, Any
import dataclasses
import logging
import pytest
import pydsdl


_logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class GeneratedPackageInfo:
    models: Sequence[pydsdl.CompositeType]
    """
    List of PyDSDL objects describing the source DSDL definitions.
    This can be used for arbitrarily complex introspection and reflection.
    """


@pytest.fixture(scope="session")
def compiled() -> list[GeneratedPackageInfo]:
    """
    Obtains the list of DSDL-generated Python packages with metadata.
    This is used to guide the automatic testing process.
    """
    out: list[GeneratedPackageInfo] = []
    ns_dirs = os.environ["NUNAVUT_VERIFICATION_DSDL_PATH"].split(os.pathsep)
    for nsd in ns_dirs:
        _logger.info("Reading DSDL namespace %s", nsd)
        composite_types = pydsdl.read_namespace(root_namespace_directory=nsd, lookup_directories=ns_dirs)
        if not composite_types:  # pragma: no cover
            _logger.warning("Empty DSDL namespace: %s", nsd)
            continue
        out.append(GeneratedPackageInfo(models=composite_types))
    return out


def pytest_configure(config: Any) -> None:
    """
    See https://docs.pytest.org/en/6.2.x/reference.html#initialization-hooks
    """
    del config
    logging.getLogger("pydsdl").setLevel(logging.INFO)
