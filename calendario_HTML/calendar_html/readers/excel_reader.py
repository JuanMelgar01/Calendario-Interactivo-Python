from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
from openpyxl import load_workbook


class ReadError(Exception):
    pass


REQUIRED_COLUMNS = ["title", "description", "category", "start", "end"]


def read_events_xlsx(path: str, sheet_name: str | None = None) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise ReadError(f"No existe el archivo Excel: {path}")

    try:
        wb = load_workbook(filename=str(p), data_only=True)
    except Exception as e:
        raise ReadError(f"No se pudo abrir el Excel: {e}") from e

    ws = wb[sheet_name] if sheet_name else wb.active

    # Cabecera en la primera fila
    header = []
    for cell in ws[1]:
        header.append(str(cell.value).strip().lower() if cell.value is not None else "")

    if not header or all(h == "" for h in header):
        raise ReadError("La primera fila del Excel debe contener encabezados.")

    col_index = {name: header.index(name) for name in header if name}
    missing = [c for c in REQUIRED_COLUMNS if c not in col_index]
    if missing:
        raise ReadError(f"Faltan columnas en Excel: {missing}. Esperadas: {REQUIRED_COLUMNS}")

    events: List[Dict[str, Any]] = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        # Ignorar filas vacías
        if row is None or all(v is None or str(v).strip() == "" for v in row):
            continue

        def get(col: str):
            idx = col_index[col]
            v = row[idx] if idx < len(row) else None
            return "" if v is None else str(v).strip()

        events.append({
            "title": get("title"),
            "description": get("description"),
            "category": get("category"),
            "start": get("start"),
            "end": get("end"),
        })

    return events
