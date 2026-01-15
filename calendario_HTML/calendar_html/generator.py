from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, Any


class GenerationError(Exception):
    pass


def render_calendar_html(context: Dict[str, Any], templates_dir: str, template_name: str) -> str:
    try:
        env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
        tmpl = env.get_template(template_name)
        return tmpl.render(**context)
    except Exception as e:
        raise GenerationError(f"Error generando HTML: {e}") from e


def write_output(html: str, out_path: str) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
