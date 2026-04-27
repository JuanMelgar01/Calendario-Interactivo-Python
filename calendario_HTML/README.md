# Calendario HTML interactivo con Python

Proyecto en Python para leer eventos desde archivos JSON o Excel, validarlos y generar automaticamente un calendario HTML interactivo.

## Caracteristicas

- Lectura de eventos desde `JSON` y `Excel (.xlsx)`.
- Validacion de campos requeridos: `title`, `description`, `category` y `start`.
- Soporte para eventos puntuales y eventos de varios dias.
- Generacion automatica de un archivo HTML interactivo.
- Vista mensual con navegacion por meses y anos.
- Vista semanal complementaria.
- Panel lateral al hacer clic en un evento.
- Tooltip al pasar el cursor por encima de un evento.
- Filtro por categoria.
- Boton de impresion con estilos especificos para papel.
- Personalizacion visual mediante `assets/style.css`.
- Estructura modular separando lectura, validacion, procesamiento y generacion.

## Librerias usadas

- `json`
- `openpyxl`
- `jinja2`

## Estructura

```text
calendario_HTML/
├─ assets/
│  └─ style.css
├─ calendar_html/
│  ├─ cli.py
│  ├─ data_loader.py
│  ├─ generator.py
│  ├─ models.py
│  ├─ processing.py
│  ├─ validators.py
│  └─ readers/
│     ├─ excel_reader.py
│     └─ json_reader.py
├─ examples/
│  ├─ events.json
│  ├─ events.js
│  ├─ events.xlsx
│  └─ events_template.xlsx
├─ output/
│  └─ calendar.html
└─ templates/
   └─ calendar.html.j2
```

## Formato esperado de los eventos

### JSON

El archivo debe ser una lista de objetos:

```json
[
  {
    "title": "Reunion con equipo",
    "description": "Revisar tareas y objetivos.",
    "category": "Trabajo",
    "start": "2026-01-08T10:30",
    "end": "2026-01-08T11:15"
  },
  {
    "title": "Semana de examenes",
    "description": "Repasar temario y hacer simulacros.",
    "category": "Estudio",
    "start": "2026-01-07",
    "end": "2026-01-12"
  }
]
```

### Excel

Columnas requeridas:

- `title`
- `description`
- `category`
- `start`

Columna opcional:

- `end`

En `examples/events_template.xlsx` tienes una plantilla base para introducir datos.

## Instalacion

```bash
pip install -r requirements.txt
```

## Uso

### Generar calendario desde JSON

```bash
python -m calendar_html.cli --mode year --input examples/events.json --year 2026 --output output/calendar.html
```

### Generar calendario desde Excel

```bash
python -m calendar_html.cli --mode year --input examples/events.xlsx --year 2026 --output output/calendar.html
```

### Abrir un mes concreto como vista inicial

```bash
python -m calendar_html.cli --mode month --month 2 --input examples/events.xlsx --year 2026 --output output/calendar.html
```

## Validaciones y errores

El programa muestra mensajes claros cuando:

- el archivo no existe o no se puede leer;
- el formato no es `json` o `xlsx`;
- faltan columnas requeridas en Excel;
- el JSON no contiene una lista de eventos;
- faltan campos obligatorios;
- el formato de fecha no es valido;
- la fecha `end` es anterior a `start`.

Si algunos eventos son invalidos, el calendario se sigue generando con los eventos correctos y se informa por consola de los descartados.

## Personalizacion visual

Puedes cambiar colores, tipografias, separaciones y modo de impresion editando:

- `assets/style.css`

La plantilla HTML base se encuentra en:

- `templates/calendar.html.j2`
