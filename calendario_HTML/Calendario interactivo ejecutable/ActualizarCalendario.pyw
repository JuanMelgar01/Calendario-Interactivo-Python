from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from calendar_html.data_loader import (  # noqa: E402
    ExcelReadError,
    JsonReadError,
    UnsupportedFormatError,
    load_events_from_file,
)
from calendar_html.generator import render_calendar_html, write_output  # noqa: E402
from calendar_html.processing import build_calendar_context, parse_and_validate  # noqa: E402


class CalendarLauncher:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Actualizar calendario")
        self.root.resizable(False, False)

        default_input = APP_DIR / "events.xlsx"
        default_output = APP_DIR / "calendar.html"
        today = date.today()

        self.input_var = tk.StringVar(value=str(default_input if default_input.exists() else ""))
        self.sheet_var = tk.StringVar()
        self.year_var = tk.StringVar(value=str(today.year))
        self.mode_var = tk.StringVar(value="year")
        self.month_var = tk.StringVar(value=str(today.month))
        self.output_var = tk.StringVar(value=str(default_output))
        self.status_var = tk.StringVar(value="Listo para generar.")

        self._build_ui()
        self._bind_events()
        self._refresh_mode_state()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.grid(sticky="nsew")

        ttk.Label(frame, text="Archivo de entrada").grid(row=0, column=0, sticky="w", pady=(0, 6))
        input_entry = ttk.Entry(frame, textvariable=self.input_var, width=52)
        input_entry.grid(row=1, column=0, sticky="we", padx=(0, 8))
        ttk.Button(frame, text="Examinar", command=self._choose_input).grid(row=1, column=1, sticky="we")

        ttk.Label(frame, text="Hoja de Excel (opcional)").grid(row=2, column=0, sticky="w", pady=(12, 6))
        ttk.Entry(frame, textvariable=self.sheet_var, width=52).grid(row=3, column=0, columnspan=2, sticky="we")

        options = ttk.Frame(frame)
        options.grid(row=4, column=0, columnspan=2, sticky="we", pady=(12, 0))
        options.columnconfigure(1, weight=1)
        options.columnconfigure(3, weight=1)

        ttk.Label(options, text="Ano").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(options, textvariable=self.year_var, width=10).grid(row=0, column=1, sticky="we", padx=(0, 16))

        ttk.Label(options, text="Vista inicial").grid(row=0, column=2, sticky="w", padx=(0, 8))
        mode_combo = ttk.Combobox(
            options,
            textvariable=self.mode_var,
            values=("year", "month"),
            state="readonly",
            width=10,
        )
        mode_combo.grid(row=0, column=3, sticky="we")

        ttk.Label(options, text="Mes inicial").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(12, 0))
        self.month_combo = ttk.Combobox(
            options,
            textvariable=self.month_var,
            values=tuple(str(value) for value in range(1, 13)),
            state="readonly",
            width=10,
        )
        self.month_combo.grid(row=1, column=1, sticky="we", padx=(0, 16), pady=(12, 0))

        ttk.Label(frame, text="Salida HTML").grid(row=5, column=0, sticky="w", pady=(12, 6))
        output_entry = ttk.Entry(frame, textvariable=self.output_var, width=52)
        output_entry.grid(row=6, column=0, sticky="we", padx=(0, 8))
        ttk.Button(frame, text="Guardar como", command=self._choose_output).grid(row=6, column=1, sticky="we")

        actions = ttk.Frame(frame)
        actions.grid(row=7, column=0, columnspan=2, sticky="we", pady=(16, 0))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        ttk.Button(actions, text="Generar calendario", command=self._generate).grid(row=0, column=0, sticky="we", padx=(0, 8))
        ttk.Button(actions, text="Abrir HTML", command=self._open_output).grid(row=0, column=1, sticky="we")

        status = ttk.Label(frame, textvariable=self.status_var, wraplength=460, justify="left")
        status.grid(row=8, column=0, columnspan=2, sticky="we", pady=(14, 0))

    def _bind_events(self) -> None:
        self.mode_var.trace_add("write", lambda *_: self._refresh_mode_state())

    def _refresh_mode_state(self) -> None:
        if self.mode_var.get() == "month":
            self.month_combo.configure(state="readonly")
        else:
            self.month_combo.configure(state="disabled")

    def _choose_input(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self.root,
            title="Selecciona un archivo de eventos",
            filetypes=(
                ("Archivos compatibles", "*.xlsx *.json"),
                ("Excel", "*.xlsx"),
                ("JSON", "*.json"),
                ("Todos los archivos", "*.*"),
            ),
            initialdir=str(APP_DIR),
        )
        if selected:
            self.input_var.set(selected)

    def _choose_output(self) -> None:
        current_output = Path(self.output_var.get()).expanduser() if self.output_var.get().strip() else APP_DIR / "calendar.html"
        selected = filedialog.asksaveasfilename(
            parent=self.root,
            title="Guardar calendario HTML",
            defaultextension=".html",
            initialdir=str(current_output.parent),
            initialfile=current_output.name,
            filetypes=(("HTML", "*.html"), ("Todos los archivos", "*.*")),
        )
        if selected:
            self.output_var.set(selected)

    def _generate(self) -> None:
        input_path = self.input_var.get().strip()
        output_path = self.output_var.get().strip()
        mode = self.mode_var.get().strip()
        sheet_name = self.sheet_var.get().strip() or None

        if not input_path:
            messagebox.showerror("Falta el archivo", "Selecciona un archivo .xlsx o .json.")
            return
        if not output_path:
            messagebox.showerror("Falta la salida", "Indica la ruta del HTML de salida.")
            return

        try:
            year = int(self.year_var.get().strip())
        except ValueError:
            messagebox.showerror("Ano invalido", "El ano debe ser un numero entero.")
            return

        initial_month: int | None = None
        if mode == "month":
            try:
                initial_month = int(self.month_var.get().strip())
            except ValueError:
                messagebox.showerror("Mes invalido", "El mes inicial debe estar entre 1 y 12.")
                return
            if not (1 <= initial_month <= 12):
                messagebox.showerror("Mes invalido", "El mes inicial debe estar entre 1 y 12.")
                return

        try:
            raw_events = load_events_from_file(input_path, sheet_name=sheet_name)
        except (JsonReadError, ExcelReadError, UnsupportedFormatError) as exc:
            messagebox.showerror("Error leyendo entrada", str(exc))
            self.status_var.set(f"Error: {exc}")
            return

        events, errors = parse_and_validate(raw_events)
        context = build_calendar_context(
            events,
            selected_year=year,
            initial_month=initial_month,
            initial_mode=mode,
        )
        context["assets_href"] = "./assets/style.css"

        try:
            html = render_calendar_html(context, str(PROJECT_DIR / "templates"), "calendar.html.j2")
            write_output(html, output_path)
        except Exception as exc:
            messagebox.showerror("Error generando HTML", str(exc))
            self.status_var.set(f"Error: {exc}")
            return

        summary = f"Calendario generado en {output_path} con {len(events)} eventos validos."
        if errors:
            summary += f" Se descartaron {len(errors)} eventos."
            messagebox.showwarning("Calendario generado con avisos", summary + "\n\nRevisa los datos de entrada.")
        else:
            messagebox.showinfo("Calendario generado", summary)

        self.status_var.set(summary)

    def _open_output(self) -> None:
        output_path = Path(self.output_var.get().strip()).expanduser()
        if not output_path.exists():
            messagebox.showerror("HTML no encontrado", "Genera primero el archivo HTML.")
            return
        webbrowser.open(output_path.resolve().as_uri())


def main() -> None:
    root = tk.Tk()
    CalendarLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
