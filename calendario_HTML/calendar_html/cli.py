from __future__ import annotations
import argparse
import sys

from .readers.json_reader import read_events_json, ReadError as JsonReadError
from .readers.excel_reader import read_events_xlsx, ReadError as ExcelReadError
from .processing import parse_and_validate, build_month_view, build_year_view
from .generator import render_calendar_html, write_output


def main():
    parser = argparse.ArgumentParser(
        description="Generador de calendarios HTML interactivos desde JSON o Excel."
    )
    parser.add_argument("--input", "-i", required=True, help="Ruta al archivo .json o .xlsx")
    parser.add_argument("--sheet", help="Nombre de hoja (solo Excel). Si se omite, usa la activa.")
    parser.add_argument("--year", type=int, required=True, help="Año a visualizar")

    parser.add_argument(
        "--mode",
        choices=["month", "year"],
        default="month",
        help="Genera un mes (month) o el año completo (year) en un solo HTML."
    )
    parser.add_argument("--month", type=int, help="Mes a visualizar (1-12). Requerido si mode=month")

    parser.add_argument("--templates", default="templates", help="Directorio de plantillas")
    parser.add_argument("--template", default="calendar.html.j2", help="Nombre de plantilla")
    parser.add_argument("--output", "-o", default="output/calendar.html", help="Ruta de salida HTML")

    args = parser.parse_args()

    in_path = args.input.lower()
    try:
        if in_path.endswith(".json"):
            raw = read_events_json(args.input)
        elif in_path.endswith(".xlsx"):
            raw = read_events_xlsx(args.input, sheet_name=args.sheet)
        else:
            print("ERROR: El archivo de entrada debe ser .json o .xlsx", file=sys.stderr)
            sys.exit(2)
    except (JsonReadError, ExcelReadError) as e:
        print(f"ERROR leyendo entrada: {e}", file=sys.stderr)
        sys.exit(2)

    events, errors = parse_and_validate(raw)
    if errors:
        print("Se encontraron errores de validación:", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        print("Se generará el calendario SOLO con eventos válidos.\n", file=sys.stderr)

    if args.mode == "month":
        if args.month is None:
            print("ERROR: --month es requerido cuando --mode=month", file=sys.stderr)
            sys.exit(2)
        if not (1 <= args.month <= 12):
            print("ERROR: month debe estar entre 1 y 12", file=sys.stderr)
            sys.exit(2)
        context = build_month_view(events, args.year, args.month)
    else:
        context = build_year_view(events, args.year)

    context["all_events"] = [e.to_dict() for e in events]

    html = render_calendar_html(context, args.templates, args.template)
    write_output(html, args.output)

    print(f"OK: generado {args.output} con {len(events)} eventos válidos.")
    if errors:
        print(f"Nota: {len(errors)} eventos fueron descartados por errores.")


if __name__ == "__main__":
    main()
