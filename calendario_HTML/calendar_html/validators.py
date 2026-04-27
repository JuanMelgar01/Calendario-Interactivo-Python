from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, Optional, Tuple
import re


ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$")


class ValidationError(Exception):
    pass


def _parse_iso(value: str) -> Tuple[datetime, bool]:
    trimmed = value.strip()
    if ISO_DATE_RE.match(trimmed):
        return datetime.strptime(trimmed, "%Y-%m-%d"), False
    if ISO_DATETIME_RE.match(trimmed):
        if len(trimmed) == 16:
            return datetime.strptime(trimmed, "%Y-%m-%dT%H:%M"), True
        return datetime.strptime(trimmed, "%Y-%m-%dT%H:%M:%S"), True

    raise ValidationError(
        f"Formato de fecha/hora invalido: '{value}'. "
        "Usa YYYY-MM-DD o YYYY-MM-DDTHH:MM[:SS]."
    )


def _ensure_required_str(data: Dict[str, Any], field: str) -> str:
    if field not in data or data[field] is None:
        raise ValidationError(f"Falta el campo requerido '{field}'.")
    if not isinstance(data[field], str) or not data[field].strip():
        raise ValidationError(f"El campo '{field}' debe ser un texto no vacio.")
    return data[field].strip()


def validate_event_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValidationError("Cada evento debe ser un objeto/diccionario.")

    title = _ensure_required_str(data, "title")
    description = _ensure_required_str(data, "description")
    category = _ensure_required_str(data, "category")

    if "start" not in data or data["start"] is None:
        raise ValidationError("Falta el campo requerido 'start'.")
    if not isinstance(data["start"], str):
        raise ValidationError("El campo 'start' debe ser texto ISO.")

    start_dt, start_had_time = _parse_iso(data["start"])

    end_raw = data.get("end")
    end_dt: Optional[datetime] = None
    end_had_time = False
    if end_raw is not None and str(end_raw).strip() != "":
        if not isinstance(end_raw, str):
            raise ValidationError("El campo 'end' debe ser texto ISO o vacio.")
        end_dt, end_had_time = _parse_iso(end_raw)

    if not start_had_time:
        start_dt = datetime.combine(start_dt.date(), time(0, 0, 0))
        if end_dt is None:
            end_dt = datetime.combine(start_dt.date(), time(23, 59, 59))
        elif not end_had_time:
            end_dt = datetime.combine(end_dt.date(), time(23, 59, 59))

    if start_had_time and end_dt is not None and not end_had_time:
        end_dt = datetime.combine(end_dt.date(), time(23, 59, 59))

    if end_dt is not None and end_dt < start_dt:
        raise ValidationError("El campo 'end' no puede ser anterior a 'start'.")

    return {
        "title": title,
        "description": description,
        "category": category,
        "start": start_dt,
        "end": end_dt,
    }
