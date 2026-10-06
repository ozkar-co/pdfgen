---
title: pdfgen — diseño
date: 2026-10-06
tags: [pdfgen, pdf, weasyprint, fastapi]
status: active
---

# pdfgen — diseño

Servicio que convierte Markdown o HTML en PDF, con plantillas de
membrete. Lo consumen Laura (informes) y la UI web.

Principios: KISS, fail-fast. Un motor (WeasyPrint); sin
fallbacks.

## API `[PDF-API]`

| Método | Ruta | Notas |
|--------|------|-------|
| GET | `/` | UI |
| GET | `/health` | `ok` + ids de plantillas |
| GET | `/api/templates` | `{"templates": [{id, name, description}]}` |
| POST | `/api/pdf` | JSON → `application/pdf` |

`POST /api/pdf`:

```json
{
  "content": "# Título\n\nTexto…",
  "format": "md",
  "template": "forja",
  "title": "opcional",
  "filename": "opcional"
}
```

| Campo | Regla |
|-------|-------|
| `content` | Obligatorio; tope `max_input_kb` (413) |
| `format` | `md` o `html` |
| `template` | `null` = A4 sin membrete; id desconocido → 404 |
| `title` | Metadato del PDF; si falta, `title` del frontmatter |
| `filename` | Nombre sugerido en `Content-Disposition` |

Errores de contenido (Mermaid, HTML sin `<head>`) → 422 con el
motivo.

## Render `[PDF-RENDER]`

- **Markdown:** frontmatter fuera; extensiones `tables` y
  `fenced_code`. Los saltos de línea simples se unen: un
  párrafo cortado a 80 columnas ocupa todo el ancho.
- **HTML fragmento:** se envuelve con el CSS base.
- **HTML completo:** el CSS base entra al inicio de `<head>`;
  el CSS del documento lo sobrescribe.
- **Saltos de página:** los títulos no quedan solos al final de
  una página; título + párrafo + tabla saltan juntos; las filas
  de tabla y los bloques de código no se parten; el encabezado
  de tabla se repite en cada página.
- **Recursos:** solo `data:` URIs. Imágenes remotas o locales se
  ignoran (el servicio es público y no hace peticiones de red).
- **Mermaid:** no soportado; un bloque `mermaid` devuelve 422.

## Plantillas `[PDF-TPL]`

`templates/<id>/`:

```text
template.yaml   # name, description, page (regla @page), membrete
membrete.pdf    # una página: logos, borde, marca de agua
```

El contenido se renderiza con los márgenes de `page` y cada
página se estampa sobre el membrete.

| Id | Hoja | Margen |
|----|------|--------|
| `forja` | carta | 22 / 19 / 36 / 19 mm (pie y logo abajo) |
| `pritopia` | A4 | 20 mm (dentro del borde ornamental) |

Nueva plantilla: crear la carpeta y reiniciar. Al arrancar, una
plantilla incompleta o con membrete de más de una página detiene
el servicio.

## Config `[PDF-CFG]`

`config.yaml`: `host`, `port` (3009), `max_input_kb`,
`templates_dir`. Env: `PORT`, `MAX_INPUT_KB`.

Sin autenticación (como el resto de la familia en OzNet).
