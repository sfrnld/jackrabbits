"""Persistent recipients + send history (state/share.json) and in-memory pairing state."""
from __future__ import annotations
import json, threading, uuid, time
from pathlib import Path
from . import settings

LOCK = threading.Lock()
PENDING: dict[str, dict] = {}     # invite code -> draft recipient
PAIRED: dict[str, dict] = {}      # invite code -> recipient (so repeated polls are idempotent)
STATE = {"offset": 0}
ROLES = ["Admin", "Head of Sales", "Head of Region", "Salesman"]

def reset():
    PENDING.clear(); PAIRED.clear(); STATE["offset"] = 0

def _path() -> Path: return settings.state_dir() / "share.json"

def load() -> dict:
    p = _path()
    return json.loads(p.read_text()) if p.exists() else {"recipients": [], "history": []}

def save(d: dict) -> None:
    p = _path(); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(d, ensure_ascii=False, indent=1))

def public(r: dict) -> dict:           # never expose chat ids to the browser
    return {k: v for k, v in r.items() if k != "chat_id"}

def upsert_recipient(draft: dict, chat_id: int, first_name: str) -> dict:
    with LOCK:
        d = load(); ex = next((r for r in d["recipients"] if r["chat_id"] == chat_id), None)
        rec = ex or {"id": uuid.uuid4().hex[:8], "chat_id": chat_id}
        rec.update(name=draft.get("name") or first_name, role=draft.get("role", "Salesman"), region=draft.get("region", ""), owner=draft.get("owner", ""), first_name=first_name, paired_at=time.strftime("%Y-%m-%d %H:%M"))
        if not ex: d["recipients"].append(rec)
        save(d); return rec

def add_history(entries: list[dict]) -> None:
    with LOCK:
        d = load(); d["history"] = (entries[::-1] + d["history"])[:200]; save(d)

def owner_key(r: dict) -> str:
    """The name this recipient answers to in the data's owner column (defaults to their own name)."""
    return (r.get("owner") or r.get("name") or "").strip().casefold()
