from __future__ import annotations

import asyncio
import logging
import re
import time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import settings
from .render import RenderError, render_pdf
from .templates import load_templates

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
log = logging.getLogger("pdfgen")

TEMPLATES = load_templates(settings.templates_dir)
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

app = FastAPI(title="pdfgen")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parents[1] / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class PdfRequest(BaseModel):
    content: str
    format: Literal["md", "html"]
    template: str | None = None
    title: str | None = None
    filename: str | None = None


def _filename(raw: str | None) -> str:
    stem = SAFE_NAME_RE.sub("-", (raw or "documento").strip()).strip("-.") or "documento"
    return stem if stem.lower().endswith(".pdf") else f"{stem}.pdf"


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "templates": sorted(TEMPLATES)}


@app.get("/api/templates")
async def templates() -> dict[str, object]:
    return {"templates": [t.public() for t in TEMPLATES.values()]}


@app.post("/api/pdf")
async def pdf(req: PdfRequest) -> Response:
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="content vacío")
    if len(req.content.encode("utf-8")) > settings.max_input_kb * 1024:
        raise HTTPException(
            status_code=413, detail=f"content supera {settings.max_input_kb} KB"
        )
    template = None
    if req.template:
        template = TEMPLATES.get(req.template)
        if template is None:
            raise HTTPException(
                status_code=404,
                detail=f"plantilla desconocida: {req.template} "
                f"(disponibles: {', '.join(sorted(TEMPLATES))})",
            )

    started = time.perf_counter()
    try:
        data = await asyncio.to_thread(
            render_pdf, req.content, req.format, template, req.title
        )
    except RenderError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    log.info(
        "pdf %s template=%s %d bytes %.2fs",
        req.format, req.template or "-", len(data), time.perf_counter() - started,
    )
    name = _filename(req.filename or req.title)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{name}"'},
    )
