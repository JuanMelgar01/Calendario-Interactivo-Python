from __future__ import annotations

import argparse
import sys

from .data_loader import (
    ExcelReadError,
    JsonReadError,
    UnsupportedFormatError,
    load_events_from_file,
)
from .generator import render_calendar_html, write_output
from .processing import build_calendar_context, parse_and_validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generador de calendarios HTML interactivos desde JSON o Excel."
    )
    parser.add_argument("--input", "-i", required=True, help="Ruta al archivo .json o .xlsx")
    parser.add_argument("--sheet", help="Nombre de hoja en Excel. Si se omite, se usa la hoja activa.")
    parser.add_argument("--year", type=int, required=True, help="Ano de referencia del calendario")
    parser.add_argument(
        "--mode",
        choices=["month", "year"],
        default="year",
        help="Enfoque inicial del calendario: mes concreto o navegacion anual.",
    )
    parser.add_argument(
        "--month",
        type=int,
        help="Mes inicial a visualizar (1-12). Requerido si --mode=month.",
    )
    parser.add_argument("--templates", default="templates", help="Directorio de plantillas")
    parser.add_argument("--template", default="calendar.html.j2", help="Nombre de plantilla")
    parser.add_argument("--output", "-o", default="output/calendar.html", help="Ruta de salida HTML")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        raw_events = load_events_from_file(args.input, sheet_name=args.sheet)
    except (JsonReadError, ExcelReadError, UnsupportedFormatError) as exc:
        print(f"ERROR leyendo entrada: {exc}", file=sys.stderr)
        sys.exit(2)

    events, errors = parse_and_validate(raw_events)
    if errors:
        print("Se encontraron errores de validacion:", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        print("Se generara el calendario solo con eventos validos.\n", file=sys.stderr)

    initial_month = None
    if args.mode == "month":
        if args.month is None:
            print("ERROR: --month es requerido cuando --mode=month", file=sys.stderr)
            sys.exit(2)
        if not (1 <= args.month <= 12):
            print("ERROR: --month debe estar entre 1 y 12", file=sys.stderr)
            sys.exit(2)
        initial_month = args.month

    context = build_calendar_context(
        events,
        selected_year=args.year,
        initial_month=initial_month,
        initial_mode=args.mode,
    )

    html = render_calendar_html(context, args.templates, args.template)
    write_output(html, args.output)

    print(f"OK: generado {args.output} con {len(events)} eventos validos.")
    if errors:
        print(f"Nota: {len(errors)} eventos fueron descartados por errores.")


if __name__ == "__main__":
    main()
