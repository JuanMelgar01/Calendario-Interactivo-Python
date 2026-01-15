from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any


class ReadError(Exception):
    pass


def read_events_json(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise ReadError(f"No existe el archivo JSON: {path}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise ReadError(f"No se pudo leer/parsear JSON: {e}") from e

    if not isinstance(data, list):
        raise ReadError("El JSON debe ser una lista de eventos (array).")

    return data
