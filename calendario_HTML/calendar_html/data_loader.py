from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .readers.excel_reader import ReadError as ExcelReadError
from .readers.excel_reader import read_events_xlsx
from .readers.json_reader import ReadError as JsonReadError
from .readers.json_reader import read_events_json


class UnsupportedFormatError(Exception):
    pass


def load_events_from_file(path: str, sheet_name: str | None = None) -> List[Dict[str, Any]]:
    suffix = Path(path).suffix.lower()

    if suffix == ".json":
        return read_events_json(path)
    if suffix == ".xlsx":
        return read_events_xlsx(path, sheet_name=sheet_name)

    raise UnsupportedFormatError(
        f"Formato de archivo no soportado: '{suffix or '(sin extension)'}'. "
        "Usa un archivo .json o .xlsx."
    )


__all__ = [
    "ExcelReadError",
    "JsonReadError",
    "UnsupportedFormatError",
    "load_events_from_file",
]
