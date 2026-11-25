"""Dev-only fake Telegram Bot API for end-to-end demos:  uv run python tests/fake_telegram_server.py
Point the app at it with TELEGRAM_API_BASE=http://127.0.0.1:8799 and TELEGRAM_BOT_TOKEN=123:FAKE."""
import json, os, sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Request

app = FastAPI(); OUT = Path(os.environ.get("FAKE_TG_OUT", "/tmp/fake_tg")); OUT.mkdir(parents=True, exist_ok=True)
UPDATES, SENT = [], []

@app.get("/_sim/start")
def sim(code: str, chat: int, name: str = "Budi"):
    UPDATES.append({"update_id": len(UPDATES) + 1, "message": {"text": f"/start {code}", "chat": {"id": chat}, "from": {"first_name": name}}}); return {"ok": True}

@app.get("/_sent")
def sent(): return SENT

@app.post("/bot{token}/{method}")
async def api(token: str, method: str, request: Request):
    if token != "123:FAKE": return {"ok": False, "error_code": 401, "description": "Unauthorized"}
    ct = request.headers.get("content-type", "")
    if "multipart" in ct:
        form = await request.form(); data = {k: v for k, v in form.items() if isinstance(v, str)}
        files = {k: v for k, v in form.items() if not isinstance(v, str)}
    else: data, files = (await request.json()) if (await request.body()) else {}, {}
    if method == "getMe": return {"ok": True, "result": {"id": 1, "is_bot": True, "first_name": "Sales Studio Demo", "username": "SalesStudioDemoBot"}}
    if method == "getUpdates": return {"ok": True, "result": [u for u in UPDATES if u["update_id"] >= int(data.get("offset", 0) or 0)]}
    if method in ("sendMessage", "sendPhoto"):
        rec = {"method": method, "chat_id": data.get("chat_id"), "text": data.get("text"), "caption": data.get("caption")}
        if method == "sendPhoto":
            f = OUT / f"card_{len(SENT) + 1}_{data.get('chat_id')}.png"; f.write_bytes(await files["photo"].read()); rec["file"] = str(f)
        SENT.append(rec); return {"ok": True, "result": {"message_id": len(SENT)}}
    return {"ok": False, "error_code": 404, "description": "Not Found"}

if __name__ == "__main__": uvicorn.run(app, host="127.0.0.1", port=8799, log_level="warning")
