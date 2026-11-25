"""Minimal Telegram Bot API client. Errors never contain the token."""
from __future__ import annotations
import json
import httpx
from . import settings

class TelegramError(Exception):
    def __init__(self, message: str, code: int | None = None, offline: bool = False):
        super().__init__(message); self.code, self.offline = code, offline

def api_base() -> str: return settings.get("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")

def split_text(text: str, limit: int = 4000) -> list[str]:
    """Split on line boundaries so no message exceeds Telegram's 4096-char cap."""
    lines, parts, cur = [], [], None
    for line in text.split("\n"):
        while len(line) > limit: lines.append(line[:limit]); line = line[limit:]
        lines.append(line)
    for line in lines:
        if cur is None: cur = line
        elif len(cur) + 1 + len(line) <= limit: cur += "\n" + line
        else: parts.append(cur); cur = line
    parts.append(cur or ""); return parts

class Telegram:
    def __init__(self, token: str, client: httpx.Client | None = None):
        self.token = token; self.http = client or httpx.Client(timeout=15)

    def _call(self, method: str, *, json_body: dict | None = None, data: dict | None = None, files: dict | None = None):
        url = f"{api_base()}/bot{self.token}/{method}"
        try:
            r = self.http.post(url, json=json_body) if json_body is not None else self.http.post(url, data=data, files=files)
        except httpx.HTTPError:
            raise TelegramError("Tidak bisa terhubung ke Telegram (cek internet)", offline=True) from None
        try: j = r.json()
        except ValueError: raise TelegramError(f"Respons Telegram tidak valid (HTTP {r.status_code})", r.status_code) from None
        if not j.get("ok"): raise TelegramError(str(j.get("description", "Error")).replace(self.token, "***"), j.get("error_code", r.status_code))
        return j["result"]

    def get_me(self): return self._call("getMe", json_body={})
    def get_updates(self, offset: int = 0): return self._call("getUpdates", json_body={"offset": offset, "timeout": 0, "allowed_updates": ["message"]})
    def send_message(self, chat_id, text: str, parse_mode: str | None = None):
        body = {"chat_id": chat_id, "text": text, **({"parse_mode": parse_mode, "disable_web_page_preview": True} if parse_mode else {})}
        return self._call("sendMessage", json_body=body)
    def send_photo(self, chat_id, png: bytes, caption: str = ""):
        return self._call("sendPhoto", data={"chat_id": str(chat_id), "caption": caption[:1024]}, files={"photo": ("laporan.png", png, "image/png")})
    def send_media_group(self, chat_id, pngs: list[bytes], caption: str = ""):
        media = [{"type": "photo", "media": f"attach://p{i}", **({"caption": caption[:1024]} if i == 0 else {})} for i in range(len(pngs))]
        return self._call("sendMediaGroup", data={"chat_id": str(chat_id), "media": json.dumps(media)},
                          files={f"p{i}": (f"p{i}.png", b, "image/png") for i, b in enumerate(pngs)})
