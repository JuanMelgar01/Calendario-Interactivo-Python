# Calendario HTML interactivo (Python)

Genera un calendario mensual en HTML (interactivo) a partir de eventos en JSON o Excel (.xlsx).

## Requisitos
- Python 3.10+
- Dependencias: `jinja2`, `openpyxl`

## Instalación
```bash
pip install -r requirements.txt


Ejecutar con json
python -m calendar_html.cli --mode year --input examples/events.json --year 2026 --output output/calendar.html

Ejecutar con excel
python -m calendar_html.cli --mode year --input examples/events.xlsx --year 2026 --output output/calendar.html

python -m PyInstaller --onefile --noconsole -n ActualizarCalendario --add-data "templates;templates" --add-data "assets;assets" calendar_html\app.py
