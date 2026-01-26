from __future__ import annotations

import os
import sys
import traceback
import webbrowser
from pathlib import Path
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

from calendar_html.readers.excel_reader import read_events_xlsx, ReadError as ExcelReadError
from calendar_html.processing import parse_and_validate, build_period_view
from calendar_html.generator import render_calendar_html, write_output


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / relative


MONTHS = [
    ("Enero", 1), ("Febrero", 2), ("Marzo", 3), ("Abril", 4),
    ("Mayo", 5), ("Junio", 6), ("Julio", 7), ("Agosto", 8),
    ("Septiembre", 9), ("Octubre", 10), ("Noviembre", 11), ("Diciembre", 12)
]


def month_name_to_num(name: str) -> int:
    for n, v in MONTHS:
        if n == name:
            return v
    raise ValueError("Mes inválido")


def generate_from_excel(excel_path: Path, sy: int, sm: int, ey: int, em: int, output_html: Path) -> tuple[int, list[str]]:
    raw = read_events_xlsx(str(excel_path), sheet_name=None)
    events, errors = parse_and_validate(raw)

    context = build_period_view(events, sy, sm, ey, em)

    templates_dir = resource_path("templates")
    html = render_calendar_html(context, str(templates_dir), "calendar.html.j2")
    write_output(html, str(output_html))
    return len(events), errors


class App(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.master = master

        self.master.title("Actualizar Calendario")
        self.master.geometry("820x460")
        self.master.minsize(760, 430)

        # Tema y estilos
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        self.bg = "#0f172a"       # azul oscuro
        self.card = "#111c33"     # panel
        self.text = "#e5e7eb"     # casi blanco
        self.muted = "#a3a3a3"    # gris
        self.accent = "#3b82f6"   # azul

        self.master.configure(bg=self.bg)
        style.configure("TFrame", background=self.bg)
        style.configure("Card.TFrame", background=self.card)
        style.configure("TLabel", background=self.bg, foreground=self.text, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=self.bg, foreground=self.muted)
        style.configure("Title.TLabel", background=self.bg, foreground=self.text, font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", background=self.bg, foreground=self.muted, font=("Segoe UI", 10))

        style.configure("CardTitle.TLabel", background=self.card, foreground=self.text, font=("Segoe UI", 11, "bold"))
        style.configure("CardText.TLabel", background=self.card, foreground=self.muted)

        style.configure("TButton", font=("Segoe UI", 10), padding=10)
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=12)
        style.map("Accent.TButton",
                  background=[("active", self.accent), ("!active", self.accent)],
                  foreground=[("active", "white"), ("!active", "white")])

        style.configure("TCombobox", padding=6)
        style.configure("TEntry", padding=6)

        # Variables
        self.excel_path = tk.StringVar(value=str(Path.cwd() / "events.xlsx"))

        now = datetime.now()
        # default: periodo lectivo sep->jun
        if now.month < 9:
            sy, sm = now.year - 1, 9
            ey, em = now.year, 6
        else:
            sy, sm = now.year, 9
            ey, em = now.year + 1, 6

        self.start_month = tk.StringVar(value=[n for n, v in MONTHS if v == sm][0])
        self.start_year = tk.IntVar(value=sy)
        self.end_month = tk.StringVar(value=[n for n, v in MONTHS if v == em][0])
        self.end_year = tk.IntVar(value=ey)

        self.status = tk.StringVar(value="Listo. Selecciona el Excel y el periodo, y pulsa “Actualizar calendario”.")
        self.last_html: Path | None = None

        # Años en dropdown
        self.years = list(range(now.year - 5, now.year + 8))

        self._build_ui()
        self._bind_preview_updates()
        self._update_preview()

    def _build_ui(self):
        # Header
        header = ttk.Frame(self.master)
        header.pack(fill="x", padx=18, pady=(16, 8))

        ttk.Label(header, text="Actualizar calendario", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Genera un calendario HTML desde un Excel, sin tocar código.",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))

        # Main: two columns
        main = ttk.Frame(self.master)
        main.pack(fill="both", expand=True, padx=18, pady=12)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        right = ttk.Frame(main)
        right.pack(side="right", fill="both", expand=True, padx=(14, 0))

        # Card 1: Excel
        card_excel = ttk.Frame(left, style="Card.TFrame")
        card_excel.pack(fill="x", pady=(0, 14))

        ttk.Label(card_excel, text="1) Archivo Excel", style="CardTitle.TLabel").pack(anchor="w", padx=14, pady=(12, 2))
        ttk.Label(card_excel, text="Selecciona el archivo .xlsx con tus eventos.",
                  style="CardText.TLabel").pack(anchor="w", padx=14, pady=(0, 10))

        row = ttk.Frame(card_excel, style="Card.TFrame")
        row.pack(fill="x", padx=14, pady=(0, 12))

        path_entry = ttk.Entry(row, textvariable=self.excel_path)
        path_entry.pack(side="left", fill="x", expand=True)

        ttk.Button(row, text="Examinar…", command=self._pick_excel).pack(side="left", padx=(10, 0))

        # Card 2: Period
        card_period = ttk.Frame(left, style="Card.TFrame")
        card_period.pack(fill="x")

        ttk.Label(card_period, text="2) Periodo a exportar", style="CardTitle.TLabel").pack(anchor="w", padx=14, pady=(12, 2))
        ttk.Label(card_period, text="Puedes elegir un año lectivo (por ejemplo Sep 2026 → Jun 2027).",
                  style="CardText.TLabel").pack(anchor="w", padx=14, pady=(0, 10))

        grid = ttk.Frame(card_period, style="Card.TFrame")
        grid.pack(fill="x", padx=14, pady=(0, 12))

        ttk.Label(grid, text="Inicio", style="CardText.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Label(grid, text="Fin", style="CardText.TLabel").grid(row=0, column=3, sticky="w", pady=(0, 6))

        start_m = ttk.Combobox(grid, state="readonly", width=16,
                               values=[n for n, _ in MONTHS], textvariable=self.start_month)
        start_y = ttk.Combobox(grid, state="readonly", width=8,
                               values=self.years, textvariable=self.start_year)

        end_m = ttk.Combobox(grid, state="readonly", width=16,
                             values=[n for n, _ in MONTHS], textvariable=self.end_month)
        end_y = ttk.Combobox(grid, state="readonly", width=8,
                             values=self.years, textvariable=self.end_year)

        start_m.grid(row=1, column=0, sticky="w", padx=(0, 10))
        start_y.grid(row=1, column=1, sticky="w")

        ttk.Label(grid, text="→", style="CardText.TLabel").grid(row=1, column=2, padx=12)

        end_m.grid(row=1, column=3, sticky="w", padx=(0, 10))
        end_y.grid(row=1, column=4, sticky="w")

        self.preview_label = ttk.Label(card_period, text="", style="CardText.TLabel")
        self.preview_label.pack(anchor="w", padx=14, pady=(0, 12))

        # Right column: Actions + Status (like console)
        card_actions = ttk.Frame(right, style="Card.TFrame")
        card_actions.pack(fill="x", pady=(0, 14))

        ttk.Label(card_actions, text="3) Generar", style="CardTitle.TLabel").pack(anchor="w", padx=14, pady=(12, 8))

        buttons = ttk.Frame(card_actions, style="Card.TFrame")
        buttons.pack(fill="x", padx=14, pady=(0, 12))

        ttk.Button(buttons, text="Actualizar calendario", style="Accent.TButton",
                   command=self._update_calendar).pack(fill="x")

        small = ttk.Frame(card_actions, style="Card.TFrame")
        small.pack(fill="x", padx=14, pady=(0, 12))

        ttk.Button(small, text="Abrir carpeta", command=self._open_folder).pack(side="left")
        ttk.Button(small, text="Abrir calendario", command=self._open_calendar).pack(side="left", padx=10)
        ttk.Button(small, text="Salir", command=self.master.destroy).pack(side="right")

        card_status = ttk.Frame(right, style="Card.TFrame")
        card_status.pack(fill="both", expand=True)

        ttk.Label(card_status, text="Estado", style="CardTitle.TLabel").pack(anchor="w", padx=14, pady=(12, 8))

        # status box
        box = tk.Text(card_status, height=12, wrap="word", bg="#0b1224", fg="#e5e7eb",
                      insertbackground="#e5e7eb", relief="flat", font=("Consolas", 10))
        box.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        box.insert("1.0", self.status.get())
        box.configure(state="disabled")
        self.status_box = box

        # Footer hint
        footer = ttk.Frame(self.master)
        footer.pack(fill="x", padx=18, pady=(0, 14))
        ttk.Label(footer, text="Tip: edita el Excel, guarda, pulsa “Actualizar calendario”.",
                  style="Muted.TLabel").pack(anchor="w")

    def _bind_preview_updates(self):
        # Actualiza vista previa al cambiar combos
        for var in (self.start_month, self.start_year, self.end_month, self.end_year):
            var.trace_add("write", lambda *_: self._update_preview())

    def _update_preview(self):
        try:
            sm = month_name_to_num(self.start_month.get())
            sy = int(self.start_year.get())
            em = month_name_to_num(self.end_month.get())
            ey = int(self.end_year.get())
            ok = (ey, em) >= (sy, sm)
            msg = f"Periodo seleccionado: {self.start_month.get()} {sy}  →  {self.end_month.get()} {ey}"
            if not ok:
                msg += "   (⚠ fin anterior al inicio)"
            self.preview_label.configure(text=msg)
        except Exception:
            self.preview_label.configure(text="Periodo seleccionado: (incompleto)")

    def _pick_excel(self):
        p = filedialog.askopenfilename(title="Selecciona el Excel", filetypes=[("Excel", "*.xlsx")])
        if p:
            self.excel_path.set(p)

    def _log(self, text: str):
        self.status_box.configure(state="normal")
        self.status_box.delete("1.0", "end")
        self.status_box.insert("1.0", text)
        self.status_box.configure(state="disabled")

    def _open_folder(self):
        p = Path(self.excel_path.get()).resolve()
        folder = p.parent if p.exists() else Path.cwd()
        try:
            os.startfile(str(folder))
        except Exception:
            pass

    def _open_calendar(self):
        if self.last_html and self.last_html.exists():
            webbrowser.open(self.last_html.as_uri())
        else:
            messagebox.showinfo("Calendario", "Aún no se ha generado ningún calendario.")

    def _update_calendar(self):
        try:
            excel = Path(self.excel_path.get()).resolve()
            if not excel.exists():
                messagebox.showerror("Error", f"No existe el Excel:\n{excel}")
                return

            sm = month_name_to_num(self.start_month.get())
            sy = int(self.start_year.get())
            em = month_name_to_num(self.end_month.get())
            ey = int(self.end_year.get())

            if (ey, em) < (sy, sm):
                messagebox.showerror("Periodo inválido", "La fecha de FIN no puede ser anterior al INICIO.")
                return

            out_html = excel.parent / "calendar.html"
            self._log("Generando calendario…\n")

            count_ok, errors = generate_from_excel(excel, sy, sm, ey, em, out_html)
            self.last_html = out_html

            msg = (
                "✅ Calendario actualizado\n"
                f"Archivo: {out_html}\n"
                f"Periodo: {self.start_month.get()} {sy} → {self.end_month.get()} {ey}\n"
                f"Eventos válidos: {count_ok}\n"
            )

            if errors:
                msg += f"\n⚠ Eventos ignorados por errores ({len(errors)}):\n- " + "\n- ".join(errors[:10])
                if len(errors) > 10:
                    msg += f"\n... y {len(errors)-10} más."

            self._log(msg)
            webbrowser.open(out_html.as_uri())

        except ExcelReadError as e:
            messagebox.showerror("Error leyendo Excel", str(e))
        except Exception:
            messagebox.showerror("Error inesperado", traceback.format_exc())


def main():
    root = tk.Tk()
    App(root).pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
