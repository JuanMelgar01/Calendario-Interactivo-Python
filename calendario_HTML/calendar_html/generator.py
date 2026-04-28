from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape


class GenerationError(Exception):
    pass


def build_template_environment(templates_dir: str) -> Environment:
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )


def render_calendar_html(context: Dict[str, Any], templates_dir: str, template_name: str) -> str:
    try:
        environment = build_template_environment(templates_dir)
        template = environment.get_template(template_name)
        return template.render(**context)
    except Exception as exc:
        raise GenerationError(f"Error generando HTML: {exc}") from exc


def write_output(html: str, out_path: str) -> None:
    output_path = Path(out_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
