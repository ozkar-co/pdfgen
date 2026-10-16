from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            os.environ.setdefault(key, value)


def _positive_int(name: str, value: object) -> int:
    try:
        number = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{name} debe ser un entero, recibido {value!r}") from exc
    if number <= 0:
        raise RuntimeError(f"{name} debe ser > 0")
    return number


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    max_input_kb: int
    templates_dir: Path
    mermaid_cmd: str
    mermaid_timeout: int


def load_settings() -> Settings:
    _load_dotenv()
    cfg_path = ROOT / "config.yaml"
    if not cfg_path.is_file():
        raise RuntimeError(f"Falta {cfg_path}")
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise RuntimeError("config.yaml inválido")
    missing = [k for k in ("port", "max_input_kb", "templates_dir") if not raw.get(k)]
    if missing:
        raise RuntimeError(f"config.yaml sin: {', '.join(missing)}")

    templates_dir = (ROOT / str(raw["templates_dir"])).resolve()
    if not templates_dir.is_dir():
        raise RuntimeError(f"No existe templates_dir: {templates_dir}")

    return Settings(
        host=str(raw.get("host") or "0.0.0.0"),
        port=_positive_int("PORT", os.getenv("PORT") or raw["port"]),
        max_input_kb=_positive_int(
            "MAX_INPUT_KB", os.getenv("MAX_INPUT_KB") or raw["max_input_kb"]
        ),
        templates_dir=templates_dir,
        mermaid_cmd=str(
            os.getenv("MERMAID_CMD") or raw.get("mermaid_cmd") or "mmdc"
        ),
        mermaid_timeout=_positive_int(
            "MERMAID_TIMEOUT",
            os.getenv("MERMAID_TIMEOUT") or raw.get("mermaid_timeout") or 30,
        ),
    )


settings = load_settings()
