from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from pypdf import PdfReader

PAGE_PLAIN = "size: A4; margin: 16mm 14mm;"


@dataclass(frozen=True)
class Template:
    id: str
    name: str
    description: str
    page: str
    membrete: Path

    def public(self) -> dict[str, str]:
        return {"id": self.id, "name": self.name, "description": self.description}


def load_templates(templates_dir: Path) -> dict[str, Template]:
    """Each subfolder: template.yaml + single-page letterhead PDF."""
    found: dict[str, Template] = {}
    for folder in sorted(p for p in templates_dir.iterdir() if p.is_dir()):
        cfg_path = folder / "template.yaml"
        if not cfg_path.is_file():
            raise RuntimeError(f"Plantilla sin template.yaml: {folder}")
        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        missing = [k for k in ("name", "page", "membrete") if not raw.get(k)]
        if missing:
            raise RuntimeError(f"{cfg_path} sin: {', '.join(missing)}")
        membrete = folder / str(raw["membrete"])
        if not membrete.is_file():
            raise RuntimeError(f"Falta membrete: {membrete}")
        pages = len(PdfReader(str(membrete)).pages)
        if pages != 1:
            raise RuntimeError(f"{membrete} debe tener 1 página (tiene {pages})")
        found[folder.name] = Template(
            id=folder.name,
            name=str(raw["name"]),
            description=str(raw.get("description") or ""),
            page=str(raw["page"]),
            membrete=membrete,
        )
    return found
