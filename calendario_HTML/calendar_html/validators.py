from __future__ import annotations
from datetime import datetime, time
from typing import Any, Dict, Tuple, Optional
import re


ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$")


class ValidationError(Exception):
    pass


def _parse_iso(value: str) -> Tuple[datetime, bool]:
    """
    Devuelve (datetime, had_time).
    Acepta YYYY-MM-DD o YYYY-MM-DDTHH:MM[:SS]
    """
    value = value.strip()
    if ISO_DATE_RE.match(value):
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt, False
    if ISO_DATETIME_RE.match(value):
        # soporta con o sin segundos
        if len(value) == 16:
            dt = datetime.strptime(value, "%Y-%m-%dT%H:%M")
        else:
            dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        return dt, True
    raise ValidationError(f"Formato de fecha/hora inválido: '{value}'. Usa YYYY-MM-DD o YYYY-MM-DDTHH:MM")


def _ensure_required_str(data: Dict[str, Any], field: str) -> str:
    if field not in data or data[field] is None:
        raise ValidationError(f"Falta el campo requerido '{field}'.")
    if not isinstance(data[field], str) or not data[field].strip():
        raise ValidationError(f"El campo '{field}' debe ser un texto no vacío.")
    return data[field].strip()


def validate_event_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida y normaliza un dict de evento:
    - title, description, category obligatorios
    - start obligatorio
    - end opcional
    - start/end: ISO date o ISO datetime
    Normaliza:
    - si start/end son fecha (sin hora), se interpreta como 00:00 y end como 23:59:59 del mismo día (si es rango por fechas)
    """
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
            raise ValidationError("El campo 'end' debe ser texto ISO (o vacío).")
        end_dt, end_had_time = _parse_iso(end_raw)

    # Normalización para eventos por fecha (sin hora)
    # - Si start sin hora y end vacío: evento de todo el día (00:00 a 23:59:59)
    # - Si start sin hora y end sin hora: rango de días, end se lleva a 23:59:59
    if not start_had_time:
        start_dt = datetime.combine(start_dt.date(), time(0, 0, 0))
        if end_dt is None:
            end_dt = datetime.combine(start_dt.date(), time(23, 59, 59))
        else:
            if not end_had_time:
                end_dt = datetime.combine(end_dt.date(), time(23, 59, 59))

    # Si start con hora y end existe como fecha sin hora, lo llevamos al final del día
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
