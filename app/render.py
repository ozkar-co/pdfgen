from __future__ import annotations

import base64
import html as html_lib
import io
import re

import markdown
import yaml
from pypdf import PdfReader, PdfWriter
from weasyprint import HTML, default_url_fetcher

from .mermaid import MermaidError, render_svg
from .templates import PAGE_PLAIN, Template

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
MERMAID_FENCE_RE = re.compile(
    r"^[ \t]{0,3}```mermaid[ \t]*\r?\n(.*?)^[ \t]{0,3}```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)
MERMAID_HTML_RE = re.compile(
    r"<(?P<tag>pre|div|code)\b(?=[^>]*\bclass=[\"'][^\"']*\bmermaid\b)[^>]*>"
    r"(?P<body>.*?)</(?P=tag)>",
    re.IGNORECASE | re.DOTALL,
)
HTML_DOC_RE = re.compile(r"<html[\s>]", re.IGNORECASE)
HEAD_OPEN_RE = re.compile(r"<head[^>]*>", re.IGNORECASE)
KEEP_BLOCK_RE = re.compile(
    r"(<h[1-4][^>]*>.*?</h[1-4]>)"
    r"((?:\s*<p\b[^>]*>.*?</p>)?)"
    r"(\s*<table\b[\s\S]*?</table>)",
    re.IGNORECASE,
)

CSS = """
body {
  font-family: "DejaVu Sans", "Liberation Sans", sans-serif;
  font-size: 11pt;
  line-height: 1.35;
  color: #1a1a1a;
}
h1, h2, h3, h4 { break-after: avoid; page-break-after: avoid; }
h1 { font-size: 18pt; margin: 0 0 0.5em; }
h2 { font-size: 14pt; margin: 1em 0 0.35em; }
h3 { font-size: 12pt; margin: 0.8em 0 0.3em; }
h4 { font-size: 11pt; margin: 0.8em 0 0.3em; }
p, li { orphans: 2; widows: 2; }
code, pre {
  font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
  font-size: 9pt;
}
pre {
  background: rgba(0, 0, 0, 0.05);
  padding: 0.6em 0.8em;
  white-space: pre-wrap;
  word-break: break-word;
  break-inside: avoid;
}
table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0 1em;
  font-size: 9pt;
}
thead { display: table-header-group; }
tr { break-inside: avoid; page-break-inside: avoid; }
th, td {
  border: 1px solid #bbb;
  padding: 0.28em 0.35em;
  text-align: left;
  vertical-align: top;
}
th { background: rgba(0, 0, 0, 0.06); }
img { max-width: 100%; height: auto; break-inside: avoid; }
.mermaid-figure {
  margin: 0.6em 0 1em;
  text-align: center;
  break-inside: avoid;
  page-break-inside: avoid;
}
.mermaid-figure img { max-width: 100%; height: auto; }
blockquote { margin: 0.6em 0; padding-left: 0.8em; border-left: 3px solid #bbb; }
hr { border: 0; border-top: 1px solid #bbb; margin: 1em 0; }
.keep { break-inside: avoid; page-break-inside: avoid; }
"""


class RenderError(Exception):
    """Input the service refuses to render (client error)."""


def _no_network_fetcher(url: str, *args, **kwargs):
    if url.startswith("data:"):
        return default_url_fetcher(url, *args, **kwargs)
    raise ValueError(f"recurso externo no permitido: {url}")


def _strip_frontmatter(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    return (meta if isinstance(meta, dict) else {}), text[m.end():]


def _mermaid_img(code: str) -> str:
    try:
        svg = render_svg(code)
    except MermaidError as exc:
        raise RenderError(f"Mermaid: {exc}") from exc
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (
        '<figure class="mermaid-figure">'
        f'<img src="data:image/svg+xml;base64,{b64}" alt="diagrama Mermaid" />'
        "</figure>"
    )


def _replace_markdown_mermaid(body: str) -> str:
    return MERMAID_FENCE_RE.sub(
        lambda m: f"\n\n{_mermaid_img(m.group(1))}\n\n", body
    )


def _replace_html_mermaid(fragment: str) -> str:
    return MERMAID_HTML_RE.sub(
        lambda m: _mermaid_img(html_lib.unescape(m.group("body"))), fragment
    )


def _keep_blocks_together(fragment: str) -> str:
    """Heading (+ one intro paragraph) jumps page together with its table."""
    return KEEP_BLOCK_RE.sub(
        lambda m: f'<div class="keep">{m.group(1)}{m.group(2)}{m.group(3)}</div>',
        fragment,
    )


def _style(template: Template | None) -> str:
    page = template.page if template else PAGE_PLAIN
    return f"<style>@page {{ {page} }}{CSS}</style>"


def _wrap(fragment: str, title: str, template: Template | None) -> str:
    return (
        '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8" />'
        f"<title>{html_lib.escape(title)}</title>{_style(template)}</head>"
        f"<body>{fragment}</body></html>"
    )


def build_html(
    content: str, fmt: str, template: Template | None, title: str | None
) -> str:
    if fmt == "md":
        meta, body = _strip_frontmatter(content)
        body = _replace_markdown_mermaid(body)
        fragment = markdown.markdown(body, extensions=["tables", "fenced_code"])
        doc_title = title or str(meta.get("title") or "Documento")
        return _wrap(_keep_blocks_together(fragment), doc_title, template)

    if fmt == "html":
        content = _replace_html_mermaid(content)
        if not HTML_DOC_RE.search(content):
            return _wrap(_keep_blocks_together(content), title or "Documento", template)
        # Documento completo: nuestro CSS va primero; el del documento manda.
        head = HEAD_OPEN_RE.search(content)
        if not head:
            raise RenderError("HTML completo sin <head>")
        return content[: head.end()] + _style(template) + content[head.end():]

    raise RenderError(f"format debe ser md o html, recibido {fmt!r}")


def _stamp(content_pdf: bytes, membrete) -> bytes:
    writer = PdfWriter()
    for page in PdfReader(io.BytesIO(content_pdf)).pages:
        base = PdfReader(str(membrete)).pages[0]
        base.merge_page(page)
        writer.add_page(base)
    writer.compress_identical_objects()
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def render_pdf(
    content: str, fmt: str, template: Template | None, title: str | None
) -> bytes:
    document = build_html(content, fmt, template, title)
    pdf = HTML(string=document, url_fetcher=_no_network_fetcher).write_pdf()
    if template is None:
        return pdf
    return _stamp(pdf, template.membrete)
