from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class ReadError(Exception):
    pass


def read_events_json(path: str) -> List[Dict[str, Any]]:
    json_path = Path(path)
    if not json_path.exists():
        raise ReadError(f"No existe el archivo JSON: {path}")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ReadError(f"No se pudo leer o parsear el JSON: {exc}") from exc

    if not isinstance(data, list):
        raise ReadError("El JSON debe ser una lista de eventos.")
    if any(not isinstance(item, dict) for item in data):
        raise ReadError("Todos los elementos del JSON deben ser objetos de evento.")

    return data
