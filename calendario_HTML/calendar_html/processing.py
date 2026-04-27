from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Tuple
import uuid

from .models import Event
from .validators import validate_event_dict, ValidationError


class ProcessingError(Exception):
    pass


def _days_between(start: date, end: date) -> List[date]:
    cur = start
    out = []
    while cur <= end:
        out.append(cur)
        cur += timedelta(days=1)
    return out


def parse_and_validate(raw_events: List[Dict[str, Any]]) -> Tuple[List[Event], List[str]]:
    """
    Devuelve (eventos_ok, errores)
    """
    events: List[Event] = []
    errors: List[str] = []

    for i, raw in enumerate(raw_events, start=1):
        try:
            normalized = validate_event_dict(raw)
            e = Event(
                id=str(uuid.uuid4())[:8],
                title=normalized["title"],
                description=normalized["description"],
                category=normalized["category"],
                start=normalized["start"],
                end=normalized["end"],
            )
            events.append(e)
        except ValidationError as ve:
            errors.append(f"Evento #{i}: {ve}")
        except Exception as e:
            errors.append(f"Evento #{i}: error inesperado: {e}")

    return events, errors


def build_month_view(events: List[Event], year: int, month: int) -> Dict[str, Any]:
    """
    Construye estructura para plantilla:
    - semanas: lista de semanas, cada semana lista de 7 días
    - cada día tiene: date, in_month, events (lista)
    """
    first = date(year, month, 1)
    # weekday: lunes=0 ... domingo=6
    start_weekday = first.weekday()
    grid_start = first - timedelta(days=start_weekday)

    # 6 semanas * 7 días (vista típica)
    days = [grid_start + timedelta(days=i) for i in range(42)]
    last = days[-1]

    # Expandir eventos por día para pintarlos
    events_by_day: Dict[date, List[Dict[str, Any]]] = {d: [] for d in days}
    categories = sorted({e.category for e in events})

    for e in events:
        e_start_date = e.start.date()
        e_end_date = (e.end.date() if e.end else e.start.date())
        for d in _days_between(max(e_start_date, grid_start), min(e_end_date, last)):
            if d in events_by_day:
                events_by_day[d].append({
                    "id": e.id,
                    "title": e.title,
                    "description": e.description,
                    "category": e.category,
                    "start": e.start.isoformat(timespec="minutes"),
                    "end": (e.end.isoformat(timespec="minutes") if e.end else None),
                    "is_range": e.is_range,
                })

    # Orden simple: por hora de inicio
    for d in events_by_day:
        events_by_day[d].sort(key=lambda x: x["start"])

    weeks = []
    for w in range(6):
        week_days = []
        for i in range(7):
            d = days[w * 7 + i]
            week_days.append({
                "date": d.isoformat(),
                "day": d.day,
                "in_month": d.month == month,
                "events": events_by_day[d],
            })
        weeks.append(week_days)

    return {
        "year": year,
        "month": month,
        "weeks": weeks,
        "categories": categories,
    }

def build_year_view(events: List["Event"], year: int) -> Dict[str, Any]:
    """
    Genera contexto para un año completo:
    - months: lista con 12 contextos mensuales
    - categories: categorías globales del año (para filtro)
    """
    months = []
    categories = sorted({e.category for e in events})

    for m in range(1, 13):
        month_ctx = build_month_view(events, year, m)
        # Reutilizamos categories globales para que el filtro no cambie por mes
        month_ctx["categories"] = categories
        months.append(month_ctx)

    return {
        "year": year,
        "months": months,
        "categories": categories,
    }
