"""In-memory fake of the Telegram Bot API (httpx.MockTransport) so tests never touch the network."""
from __future__ import annotations
import json, re
import httpx

class FakeTelegram:
    def __init__(self, token="123:TESTTOKEN", username="SalesStudioTestBot", fail_chats=(), offline=False):
        self.token, self.username, self.fail_chats, self.offline = token, username, set(fail_chats), offline
        self.updates, self.sent, self._uid = [], [], 0
    def press_start(self, code, chat_id, first_name="Budi"):
        self._uid += 1
        self.updates.append({"update_id": self._uid, "message": {"text": f"/start {code}", "chat": {"id": chat_id}, "from": {"first_name": first_name}}})
    @staticmethod
    def _multipart(req):
        ct = req.headers["content-type"]; b = ct.split("boundary=")[1].encode(); fields, files = {}, {}
        for part in req.content.split(b"--" + b)[1:-1]:
            head, _, body = part.partition(b"\r\n\r\n"); body = body.rsplit(b"\r\n", 1)[0]
            name = re.search(rb'name="([^"]+)"', head).group(1).decode()
            (files if b"filename=" in head else fields)[name] = body if b"filename=" in head else body.decode()
        return fields, files
    def handler(self, req: httpx.Request) -> httpx.Response:
        if self.offline: raise httpx.ConnectError("offline", request=req)
        m = re.match(r"/bot([^/]+)/(\w+)", req.url.path)
        if not m or m.group(1) != self.token: return httpx.Response(401, json={"ok": False, "error_code": 401, "description": "Unauthorized"})
        method = m.group(2)
        ct = req.headers.get("content-type", "")
        if "multipart" in ct: data, files = self._multipart(req)
        else: data, files = (json.loads(req.content) if req.content else {}), {}
        if method == "getMe": return httpx.Response(200, json={"ok": True, "result": {"id": 1, "is_bot": True, "first_name": "Sales Studio", "username": self.username}})
        if method == "getUpdates":
            off = int(data.get("offset", 0) or 0); out = [u for u in self.updates if u["update_id"] >= off]
            return httpx.Response(200, json={"ok": True, "result": out})
        if method in ("sendMessage", "sendPhoto", "sendMediaGroup"):
            chat = int(data["chat_id"])
            if chat in self.fail_chats: return httpx.Response(403, json={"ok": False, "error_code": 403, "description": "Forbidden: bot was blocked by the user"})
            self.sent.append(dict(method=method, chat_id=chat, text=data.get("text"), caption=data.get("caption"), files=files, data=data))
            return httpx.Response(200, json={"ok": True, "result": {"message_id": len(self.sent)}})
        return httpx.Response(404, json={"ok": False, "error_code": 404, "description": "Not Found"})
    def client(self): return httpx.Client(transport=httpx.MockTransport(self.handler))
