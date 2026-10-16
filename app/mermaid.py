from __future__ import annotations

import functools
import json
import subprocess
import tempfile
from pathlib import Path

from .config import settings

MERMAID_CONFIG = {
    "theme": "neutral",
    "securityLevel": "strict",
    "htmlLabels": False,
    "flowchart": {"htmlLabels": False, "useMaxWidth": False},
    "class": {"htmlLabels": False, "useMaxWidth": False},
    "sequence": {"useMaxWidth": False},
    "state": {"useMaxWidth": False},
    "er": {"useMaxWidth": False},
    "gantt": {"useMaxWidth": False},
    "pie": {"useMaxWidth": False},
    "gitGraph": {"useMaxWidth": False},
    "journey": {"useMaxWidth": False},
}

PUPPETEER_CONFIG = {"args": ["--no-sandbox", "--disable-dev-shm-usage"]}


class MermaidError(Exception):
    """mmdc no pudo renderizar el diagrama (input inválido o entorno)."""


def _detail(stderr: str, stdout: str, limit: int = 400) -> str:
    lines = [ln.strip() for ln in (stderr or stdout).splitlines() if ln.strip()]
    for line in lines:
        low = line.lower()
        if "error" in low or "parse" in low or "expecting" in low:
            return line[:limit]
    return " | ".join(lines[-4:])[-limit:] or "sin detalle"


@functools.lru_cache(maxsize=64)
def render_svg(code: str) -> str:
    """Render a ```mermaid source block to a standalone SVG string via mmdc."""
    with tempfile.TemporaryDirectory(prefix="pdfgen-mermaid-") as tmp:
        tmp_path = Path(tmp)
        src = tmp_path / "diagram.mmd"
        out = tmp_path / "diagram.svg"
        src.write_text(code, encoding="utf-8")
        (tmp_path / "mermaid.json").write_text(
            json.dumps(MERMAID_CONFIG), encoding="utf-8"
        )
        (tmp_path / "puppeteer.json").write_text(
            json.dumps(PUPPETEER_CONFIG), encoding="utf-8"
        )
        cmd = [
            settings.mermaid_cmd,
            "-i", str(src),
            "-o", str(out),
            "-c", str(tmp_path / "mermaid.json"),
            "-p", str(tmp_path / "puppeteer.json"),
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.mermaid_timeout,
                cwd=tmp,
            )
        except FileNotFoundError as exc:
            raise MermaidError(
                f"no se encontró el ejecutable Mermaid ({settings.mermaid_cmd!r}); "
                "instala mermaid-cli o configura MERMAID_CMD"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise MermaidError(
                f"el diagrama superó {settings.mermaid_timeout}s de render"
            ) from exc
        if proc.returncode != 0 or not out.is_file():
            raise MermaidError(
                f"mmdc falló ({proc.returncode}): {_detail(proc.stderr, proc.stdout)}"
            )
        svg = out.read_text(encoding="utf-8").lstrip("\ufeff").lstrip()
        if not svg.startswith("<svg"):
            raise MermaidError("mmdc no produjo un SVG válido")
        return svg
