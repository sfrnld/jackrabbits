from __future__ import annotations
import base64, io, logging, secrets, time
import httpx, qrcode
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from . import settings, share
from .actions import generate
from .analytics_api import _df
from .data_api import S
from .narrative import compose, owned, owner_html, owner_text
from .render import render_owner_card
from .telegram import Telegram, TelegramError, split_text

router = APIRouter(prefix="/api")
BOT: dict = {}                       # cached getMe result for the current token

def http_client() -> httpx.Client: return httpx.Client(timeout=10)   # tests swap this for a fake transport
def _token() -> str | None: return settings.get("TELEGRAM_BOT_TOKEN")
def _tg() -> Telegram:
    t = _token()
    if not t: raise HTTPException(409, "Telegram belum tersambung. Tempel token bot dulu.")
    return Telegram(t, client=http_client())
def _bot(tg: Telegram) -> dict:
    if BOT.get("token") != tg.token: BOT.clear(); BOT.update(token=tg.token, info=tg.get_me())
    return BOT["info"]
def _err(e: TelegramError): raise HTTPException(503 if e.offline else 422, {"message": str(e), "offline": e.offline})
def _png_url(b: bytes) -> str: return "data:image/png;base64," + base64.b64encode(b).decode()

@router.get("/telegram/status")
def status():
    if not _token(): return {"configured": False, "online": False, "bot": None}
    try:
        tg = _tg(); b = tg.get_me(); BOT.clear(); BOT.update(token=tg.token, info=b)      # live check, not the cache
        return {"configured": True, "online": True, "bot": {"username": b["username"], "name": b.get("first_name")}}
    except TelegramError as e:
        return {"configured": True, "online": False, "bot": None, "error": str(e)}

class Tok(BaseModel): token: str

@router.post("/telegram/token")
def save_token(b: Tok):
    tok = b.token.strip()
    try: info = Telegram(tok, client=http_client()).get_me()
    except TelegramError as e: _err(e)
    settings.set_value("TELEGRAM_BOT_TOKEN", tok); BOT.clear(); BOT.update(token=tok, info=info)
    return {"configured": True, "bot": {"username": info["username"], "name": info.get("first_name")}}

class Invite(BaseModel):
    name: str = ""; role: str = "Salesman"; region: str = ""; owner: str = ""

@router.post("/telegram/invite")
def invite(b: Invite):
    tg = _tg()
    try: user = _bot(tg)["username"]
    except TelegramError as e: _err(e)
    code = secrets.token_urlsafe(6); share.PENDING[code] = {**b.model_dump(), "t": time.time()}
    link = f"https://t.me/{user}?start={code}"
    img = qrcode.make(link); buf = io.BytesIO(); img.save(buf, format="PNG")
    return {"code": code, "link": link, "qr": _png_url(buf.getvalue())}

@router.get("/telegram/invite/{code}")
def poll(code: str):
    if code in share.PAIRED: return {"status": "paired", "recipient": share.public(share.PAIRED[code])}
    if code not in share.PENDING: return {"status": "expired"}
    tg = _tg()
    try:
        with share.LOCK:
            ups = tg.get_updates(share.STATE["offset"])
            for u in ups:
                share.STATE["offset"] = max(share.STATE["offset"], u["update_id"] + 1)
        for u in ups:
            m = u.get("message") or {}; parts = (m.get("text") or "").split()
            if len(parts) == 2 and parts[0] == "/start" and parts[1] in share.PENDING:
                draft = share.PENDING.pop(parts[1]); name = (m.get("from") or {}).get("first_name", "")
                rec = share.upsert_recipient(draft, m["chat"]["id"], name); share.PAIRED[parts[1]] = rec
                try: tg.send_message(rec["chat_id"], f"Halo {name or rec['name']}! Sales Studio terhubung. Mulai sekarang laporan penjualan akan masuk ke chat ini.")
                except TelegramError: pass
    except TelegramError as e: _err(e)
    if code in share.PAIRED: return {"status": "paired", "recipient": share.public(share.PAIRED[code])}
    return {"status": "waiting"}

@router.get("/recipients")
def recipients(): return {"items": [share.public(r) for r in share.load()["recipients"]], "roles": share.ROLES}

@router.delete("/recipients/{rid}")
def delete_recipient(rid: str):
    with share.LOCK:
        d = share.load(); d["recipients"] = [r for r in d["recipients"] if r["id"] != rid]; share.save(d)
    return {"ok": True}

# ---------------- preview & send ----------------
def _actions(df):
    if "actions" not in S: S["actions"] = generate(df)
    return S["actions"]

class Prev(BaseModel):
    filters: dict = Field(default_factory=dict); region: str | None = None

def _scope(filters: dict, region: str | None) -> dict:
    if not region: return filters
    f = {k: v for k, v in filters.items() if k not in ("region", "branch", "outlet_id", "invoice")}; f["region"] = [region]; return f

def _public_compose(c: dict) -> dict:
    return {"scope_label": c["scope_label"], "period": c["period"], "caption": c["caption"], "summary": c["summary"],
            "actions": c["actions"], "actions_text": c["actions_text"], "card": _png_url(c["png"])}

@router.post("/share/preview")
def preview(b: Prev):
    df = _df(); return _public_compose(compose(df, _scope(b.filters, b.region), _actions(df)))

class OwnerPrev(BaseModel): recipient_id: str = ""; owner: str = ""      # by recipient, or by an owner name nobody has linked yet

@router.post("/share/preview-owner")
def preview_owner(b: OwnerPrev):
    """What one person receives when every action goes to its named owner."""
    df = _df(); r = next((x for x in share.load()["recipients"] if x["id"] == b.recipient_id), None)
    if not r and b.owner: r = {"name": b.owner, "owner": b.owner}
    if not r: raise HTTPException(404, "Penerima tidak ditemukan.")
    items = owned(_actions(df), share.owner_key(r))
    return {"scope_label": f"Aksi untuk {r['name']}", "actions": items, "text": owner_text(r["name"], items) if items else "", "card": (lambda png: _png_url(png) if png else None)(render_owner_card(df, r["name"], items)) if items else None}

def _send_owner(tg, chat_id, name: str, items: list[dict], df, demo: bool = False) -> str | None:
    """Picture first (their outlets' numbers), then the easy-to-read message. Returns the picture as a data URL for the offline fallback."""
    png = render_owner_card(df, name, items)
    if png: tg.send_photo(chat_id, png, ("🧪 DEMO · " if demo else "") + f"📊 Data untuk {name}")
    for part in split_text(owner_html(name, items, demo=demo)): tg.send_message(chat_id, part, parse_mode="HTML")
    return _png_url(png) if png else None

class Send(BaseModel):
    recipient_ids: list[str]; mode: str = "per_region"; filters: dict = Field(default_factory=dict); confirm: bool = False

@router.post("/share/send")
def send(b: Send):
    if not b.confirm: raise HTTPException(422, "Konfirmasi pengiriman dulu.")
    tg = _tg(); df = _df(); acts = _actions(df)
    recs = {r["id"]: r for r in share.load()["recipients"]}
    cache: dict[str, dict] = {}; results, fallbacks, hist = [], {}, []
    if b.mode == "demo_me":          # every owner's message, all to ONE chat (yours), so the flow works without inviting anyone
        me = recs.get(b.recipient_ids[0]) if b.recipient_ids else None
        if not me: raise HTTPException(422, "Pilih satu penerima (kamu sendiri) untuk demo.")
        by: dict[str, list[dict]] = {}
        for a in acts:
            o = (a.get("owner") or "").strip()
            if a.get("status") != "done" and o and o != "Belum ditentukan": by.setdefault(o, []).append(a)
        sent_n = failed = 0
        for o, items in by.items():
            txt = "DEMO (kamu menerima ini sebagai " + o + ")\n\n" + owner_text(o, items)
            entry = {"recipient_id": me["id"], "name": me["name"], "role": me["role"], "scope": f"demo: {o}, {len(items)} aksi"}
            try:
                _send_owner(tg, me["chat_id"], o, items, df, demo=True)
                entry["status"] = "sent"
            except TelegramError as e:
                entry.update(status="failed", error=str(e), offline=e.offline, fallback="owner:" + o)
                fallbacks["owner:" + o] = {"scope_label": entry["scope"], "summary": "", "actions_text": txt, "card": None, "actions": items}
            results.append(entry); hist.append({**{k: v for k, v in entry.items() if k != "fallback"}, "t": time.strftime("%Y-%m-%d %H:%M:%S")})
        share.add_history(hist)
        return {"results": results, "fallbacks": fallbacks}
    for rid in b.recipient_ids:
        r = recs.get(rid)
        if not r: continue
        if b.mode == "per_owner":                      # each action goes only to the person it is assigned to
            items = owned(acts, share.owner_key(r)); entry = {"recipient_id": rid, "name": r["name"], "role": r["role"], "scope": f"{len(items)} aksi"}
            if not items:
                results.append({**entry, "status": "skipped", "scope": "tidak ada aksi untuknya"}); continue
            txt = owner_text(r["name"], items)
            try:
                _send_owner(tg, r["chat_id"], r["name"], items, df)
                entry["status"] = "sent"
            except TelegramError as e:
                entry.update(status="failed", error=str(e), offline=e.offline, fallback="owner:" + rid)
                fallbacks["owner:" + rid] = {"scope_label": entry["scope"], "summary": "", "actions_text": txt, "card": None, "actions": items}
            results.append(entry); hist.append({**{k: v for k, v in entry.items() if k != "fallback"}, "t": time.strftime("%Y-%m-%d %H:%M:%S")})
            continue
        f = _scope(b.filters, r["region"]) if b.mode == "per_region" and r.get("region") else b.filters
        key = (f.get("region") or ["*"])[0] if b.mode == "per_region" or f.get("region") else "*" + str(sorted(f.items()))
        c = cache.setdefault(key, compose(df, f, acts))
        entry = {"recipient_id": rid, "name": r["name"], "role": r["role"], "scope": c["scope_label"]}
        try:
            tg.send_photo(r["chat_id"], c["png"], c["caption"])
            for part in split_text(c["summary"]) + split_text(c["actions_text"]): tg.send_message(r["chat_id"], part)
            entry["status"] = "sent"
        except TelegramError as e:
            entry.update(status="failed", error=str(e), offline=e.offline, fallback=key)
            fallbacks[key] = {k: v for k, v in _public_compose(c).items()}
        results.append(entry); hist.append({**{k: v for k, v in entry.items() if k != "fallback"}, "t": time.strftime("%Y-%m-%d %H:%M:%S")})
    share.add_history(hist)
    logging.info("Kirim laporan: %d terkirim, %d gagal", sum(h['status'] == 'sent' for h in hist), sum(h['status'] == 'failed' for h in hist))
    return {"results": results, "fallbacks": fallbacks}

@router.get("/share/history")
def history(): return {"items": share.load()["history"]}
