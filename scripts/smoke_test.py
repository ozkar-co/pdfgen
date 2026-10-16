#!/usr/bin/env python3
"""Smoke contra un pdfgen corriendo: health, plantillas y un PDF por plantilla."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3009"
OUT = Path(__file__).resolve().parents[1] / "tmp"

SAMPLE = """---
title: Prueba pdfgen
---

# Prueba pdfgen

Párrafo con líneas cortadas a ochenta columnas como en los
documentos de Laura: deben unirse en un solo párrafo a todo el
ancho de la página.

## Tabla

| Clave | Valor |
|-------|-------|
| uno | 1 |
| dos | 2 |

```bash
make run
```
"""


def get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=10) as res:
        return json.load(res)


def post_pdf(template: str | None) -> bytes:
    body = json.dumps(
        {"content": SAMPLE, "format": "md", "template": template}
    ).encode()
    req = urllib.request.Request(
        BASE + "/api/pdf", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        return res.read()


def main() -> int:
    print("health:", get("/health"))
    templates = [t["id"] for t in get("/api/templates")["templates"]]
    print("plantillas:", templates)
    OUT.mkdir(exist_ok=True)
    for template in [None, *templates]:
        data = post_pdf(template)
        if not data.startswith(b"%PDF"):
            print(f"FALLO {template}: no es PDF", file=sys.stderr)
            return 1
        path = OUT / f"smoke-{template or 'plain'}.pdf"
        path.write_bytes(data)
        print(f"ok {template or 'plain'}: {len(data)} bytes → {path}")
    mermaid = "```mermaid\nflowchart LR\n  A[uno] --> B[dos]\n```\n"
    req = urllib.request.Request(
        BASE + "/api/pdf",
        data=json.dumps({"content": mermaid, "format": "md"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        data = res.read()
    if not data.startswith(b"%PDF"):
        print("FALLO mermaid: no es PDF", file=sys.stderr)
        return 1
    print(f"ok mermaid: {len(data)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
