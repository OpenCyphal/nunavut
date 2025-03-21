#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""
Objects that write debug/accounting information about code generation inputs, outputs, and configuration
to various outputs.
"""

import abc
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Type

from nunavut._utilities import DefaultValue


class ConfigJSONEncoder(json.JSONEncoder):
    """
    A JSON encoder that can handle Nunavut configuration and pydsdl objects.
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, Path):
            return str(o)
        if isinstance(o, DefaultValue):
            return o.value
        return super().default(o)


class Lister(abc.ABC):
    """
    Abstract base class for listers
    """

    DefaultEncoding = "utf-8"

    @classmethod
    def get_lister(cls, list_format: str, list_file: Optional[Path]) -> "Lister":
        """
        Get a lister object based on the given format and file.
        """
        if list_format in ("json", "json-pretty"):
            return JsonLister(list_file=list_file, pretty=list_format == "json-pretty")
        elif list_format in ("csv", "scsv"):
            return ValueSeparatedLister(separator=";" if list_format == "scsv" else ",", list_file=list_file)
        else:
            raise ValueError(f"Unsupported list format: {list_format}")  # pragma: no cover

    @abc.abstractmethod
    def list(self, list_object: Dict[str, Any]) -> None:
        """
        List the given object to the concrete lister's output(s).
        """


class JsonLister(Lister):
    """
    Dumps the given list object as JSON to stdout and optionally to a file.

    .. invisible-code-block: python

        import pathlib
        import json
        from nunavut.cli.listers import JsonLister

        list_file_path = gen_paths_for_module.out_dir / pathlib.Path("lister-test.json")
        list_data = {
            "inputs": ["input1", "input2"],
            "outputs": ["output1", "output2"]
        }

        JsonLister(list_file=list_file_path).list(list_data)

        with list_file_path.open("r", encoding=Lister.DefaultEncoding) as list_file:
            json_data = json.load(list_file)
            assert "inputs" in json_data
            assert "outputs" in json_data
            found_data = set(json_data["inputs"] + json_data["outputs"])

        assert "input1" in found_data
        assert "input2" in found_data
        assert "output1" in found_data
        assert "output2" in found_data

    """

    def __init__(
        self,
        json_encoder: Type[json.JSONEncoder] = ConfigJSONEncoder,
        pretty: bool = False,
        list_file: Optional[Path] = None,
    ):
        self._json_encoder = json_encoder
        self._list_file = list_file
        self._pretty = pretty

    def list(self, list_object: Dict[str, Any]) -> None:
        """
        List the given object to the JSON file and optionally to a file.
        """
        if self._pretty:
            indent = 2
        else:
            indent = None
        json.dump(list_object, sys.stdout, ensure_ascii=False, indent=indent, cls=self._json_encoder)
        if self._list_file is not None:
            with self._list_file.open("w", encoding=self.DefaultEncoding) as list_file:
                json.dump(list_object, list_file, ensure_ascii=False, indent=indent, cls=self._json_encoder)


class ValueSeparatedLister(Lister):
    """
    Dumps the given list object to stdout and optionally to a file with a given separator.

    .. invisible-code-block: python

        import pathlib
        import csv
        from nunavut.cli.listers import ValueSeparatedLister

        list_file_path = gen_paths_for_module.out_dir / pathlib.Path("lister-test.csv")
        list_data = {
            "inputs": ["input1", "input2"],
            "outputs": ["output1", "output2"]
        }

        ValueSeparatedLister(separator=",", list_file=list_file_path).list(list_data)

        found_data = set()

        with list_file_path.open("r", encoding=Lister.DefaultEncoding) as list_file:
            csv_reader = csv.reader(list_file, delimiter=',')
            for row in csv_reader:
                found_data.update(row)

        assert "input1" in found_data
        assert "input2" in found_data
        assert "output1" in found_data
        assert "output2" in found_data

    """

    def __init__(self, separator: str, list_file: Optional[Path] = None):
        self._list_file = list_file
        self._sep = separator

    def list(self, list_object: Dict[str, Any]) -> None:
        self.stdout_lister(list_object)

        if self._list_file is not None:
            with self._list_file.open("w", encoding=self.DefaultEncoding) as list_file:
                csv_writer = csv.writer(list_file, delimiter=self._sep)
                for key, value in list_object.items():
                    csv_writer.writerow([key] + value)

    def stdout_lister(self, list_object: Dict[str, Any]) -> None:
        """
        The output dialect to stdout is not supported by the CSV implementation in python. Use this instead.
        """

        def _write_row(row: Iterable[str], sep: str, end: str) -> None:
            first = True
            for cell in row:
                if first:
                    first = False
                else:
                    sys.stdout.write(sep)
                sys.stdout.write(cell)
            if not first:
                sys.stdout.write(end)

        had_inputs = False
        has_outputs = "outputs" in list_object and len(list_object["outputs"]) > 0
        if "inputs" in list_object and len(list_object["inputs"]) > 0:
            had_inputs = True
            _write_row(list_object["inputs"], sep=self._sep, end=(self._sep if has_outputs else ""))
        if has_outputs:
            if had_inputs:
                sys.stdout.write(self._sep)
            _write_row(list_object["outputs"], sep=self._sep, end="")
