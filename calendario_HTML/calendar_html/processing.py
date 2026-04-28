from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Tuple
import uuid

from .models import Event
from .validators import ValidationError, validate_event_dict


class ProcessingError(Exception):
    pass


def _days_between(start: date, end: date) -> List[date]:
    current = start
    values: List[date] = []
    while current <= end:
        values.append(current)
        current += timedelta(days=1)
    return values


def _event_to_payload(event: Event) -> Dict[str, Any]:
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "category": event.category,
        "start": event.start.isoformat(timespec="minutes"),
        "end": (event.end.isoformat(timespec="minutes") if event.end else None),
        "is_range": event.is_range,
    }


def _collect_categories(events: List[Event]) -> List[str]:
    return sorted({event.category for event in events})


def _collect_available_years(events: List[Event], selected_year: int) -> List[int]:
    years = {selected_year}
    for event in events:
        years.add(event.start.year)
        years.add((event.end or event.start).year)

    # Dejamos un ano de margen a cada lado para que la navegacion semanal
    # no empuje la interfaz a un ano sin rejilla mensual disponible.
    start_year = min(years) - 1
    end_year = max(years) + 1
    return list(range(start_year, end_year + 1))


def _guess_initial_month(events: List[Event], selected_year: int) -> int:
    candidate_months = sorted(
        {
            event.start.month
            for event in events
            if event.start.year == selected_year
        }
    )
    if candidate_months:
        return candidate_months[0]

    today = date.today()
    if today.year == selected_year:
        return today.month

    return 1


def parse_and_validate(raw_events: List[Dict[str, Any]]) -> Tuple[List[Event], List[str]]:
    events: List[Event] = []
    errors: List[str] = []

    for index, raw_event in enumerate(raw_events, start=1):
        try:
            normalized = validate_event_dict(raw_event)
            events.append(
                Event(
                    id=str(uuid.uuid4())[:8],
                    title=normalized["title"],
                    description=normalized["description"],
                    category=normalized["category"],
                    start=normalized["start"],
                    end=normalized["end"],
                )
            )
        except ValidationError as exc:
            errors.append(f"Evento #{index}: {exc}")
        except Exception as exc:
            errors.append(f"Evento #{index}: error inesperado: {exc}")

    return events, errors


def build_month_view(events: List[Event], year: int, month: int) -> Dict[str, Any]:
    first_day = date(year, month, 1)
    start_weekday = first_day.weekday()
    grid_start = first_day - timedelta(days=start_weekday)

    days = [grid_start + timedelta(days=offset) for offset in range(42)]
    grid_end = days[-1]
    events_by_day: Dict[date, List[Dict[str, Any]]] = {day: [] for day in days}

    for event in events:
        start_day = event.start.date()
        end_day = (event.end.date() if event.end else event.start.date())
        visible_start = max(start_day, grid_start)
        visible_end = min(end_day, grid_end)

        for current_day in _days_between(visible_start, visible_end):
            if current_day in events_by_day:
                events_by_day[current_day].append(_event_to_payload(event))

    for current_day in events_by_day:
        events_by_day[current_day].sort(key=lambda item: item["start"])

    weeks = []
    for week_index in range(6):
        week_days = []
        for day_index in range(7):
            current_day = days[week_index * 7 + day_index]
            week_days.append(
                {
                    "date": current_day.isoformat(),
                    "day": current_day.day,
                    "in_month": current_day.month == month,
                    "events": events_by_day[current_day],
                }
            )
        weeks.append(week_days)

    return {
        "year": year,
        "month": month,
        "weeks": weeks,
    }


def build_year_view(events: List[Event], year: int) -> Dict[str, Any]:
    return {
        "year": year,
        "months": [build_month_view(events, year, month) for month in range(1, 13)],
    }


def build_calendar_context(
    events: List[Event],
    selected_year: int,
    initial_month: int | None = None,
    initial_mode: str = "year",
) -> Dict[str, Any]:
    resolved_initial_month = initial_month or _guess_initial_month(events, selected_year)
    available_years = _collect_available_years(events, selected_year)
    categories = _collect_categories(events)
    years = [build_year_view(events, year) for year in available_years]

    return {
        "selected_year": selected_year,
        "initial_month": resolved_initial_month,
        "initial_mode": initial_mode,
        "available_years": available_years,
        "categories": categories,
        "years": years,
        "all_events": [event.to_dict() for event in events],
    }
