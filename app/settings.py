"""Tiny .env reader/writer. The Telegram token lives only in .env (gitignored) or the process environment."""
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def env_path() -> Path: return Path(os.environ.get("SALES_STUDIO_ENV", ROOT / ".env"))
def state_dir() -> Path: return Path(os.environ.get("SALES_STUDIO_STATE", ROOT / "state"))

def _parse(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1); out[k.strip()] = v.strip().strip('"').strip("'")
    return out

def get(name: str, default=None):
    if os.environ.get(name): return os.environ[name]
    p = env_path()
    return _parse(p.read_text()).get(name) or default if p.exists() else default

def set_value(name: str, value: str) -> None:
    p = env_path(); lines = p.read_text().splitlines() if p.exists() else []
    new = f"{name}={value}"; hit = False
    for i, l in enumerate(lines):
        if l.strip().startswith(name + "="): lines[i] = new; hit = True
    if not hit: lines.append(new)
    p.write_text("\n".join(lines) + "\n"); os.environ[name] = value
