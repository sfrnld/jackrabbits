import json, pytest
from fastapi.testclient import TestClient
from tests.fake_telegram import FakeTelegram
from app.main import app
from app import data_api, share, share_api

c = TestClient(app)

@pytest.fixture
def tg(tmp_path, monkeypatch):
    f = FakeTelegram()
    monkeypatch.setenv("SALES_STUDIO_STATE", str(tmp_path / "state")); monkeypatch.setenv("SALES_STUDIO_ENV", str(tmp_path / ".env"))
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", f.token); monkeypatch.setattr(share_api, "http_client", lambda: f.client())
    data_api.TEMPLATES = tmp_path / "tpl"; share.reset()
    return f

@pytest.fixture
def loaded(tg):
    data_api.S.clear()
    r = c.post("/api/data/sample").json()
    c.post("/api/data/mapping", json={"mapping": {k: v["column"] for k, v in r["mapping"].items()}}); c.post("/api/findings/apply-all")
    return tg

def pair(f, name, role, region, chat):
    inv = c.post("/api/telegram/invite", json={"name": name, "role": role, "region": region}).json()
    f.press_start(inv["code"], chat, name); st = c.get(f"/api/telegram/invite/{inv['code']}").json()
    assert st["status"] == "paired", st; return st["recipient"]["id"]

def test_status_variants(tg, monkeypatch):
    s = c.get("/api/telegram/status").json(); assert s["configured"] and s["online"] and s["bot"]["username"] == "SalesStudioTestBot"
    assert tg.token not in json.dumps(s)
    tg.offline = True; s = c.get("/api/telegram/status").json(); assert s["configured"] and not s["online"] and s["bot"] is None
    tg.offline = False; monkeypatch.delenv("TELEGRAM_BOT_TOKEN"); assert c.get("/api/telegram/status").json() == {"configured": False, "online": False, "bot": None}

def test_save_token_validates_then_writes_env(tg, monkeypatch, tmp_path):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN")
    bad = c.post("/api/telegram/token", json={"token": "0:WRONG"}); assert bad.status_code == 422 and "WRONG" not in bad.text
    ok = c.post("/api/telegram/token", json={"token": tg.token}).json(); assert ok["bot"]["username"] == "SalesStudioTestBot" and tg.token not in json.dumps(ok)
    assert tg.token in (tmp_path / ".env").read_text()

def test_invite_pair_flow_and_greeting(tg):
    inv = c.post("/api/telegram/invite", json={"name": "Budi", "role": "Head of Region", "region": "Jawa Timur"}).json()
    assert inv["link"] == f"https://t.me/SalesStudioTestBot?start={inv['code']}" and inv["qr"].startswith("data:image/png;base64,")
    assert c.get(f"/api/telegram/invite/{inv['code']}").json()["status"] == "waiting"
    tg.press_start(inv["code"], 111, "Budi")
    r = c.get(f"/api/telegram/invite/{inv['code']}").json(); assert r["status"] == "paired" and r["recipient"]["name"] == "Budi" and "chat_id" not in r["recipient"]
    assert "Budi" in tg.sent[-1]["text"] and tg.sent[-1]["chat_id"] == 111                        # bot greets on pairing
    assert c.get(f"/api/telegram/invite/{inv['code']}").json()["status"] == "paired"              # idempotent
    assert c.get("/api/telegram/invite/unknown").json()["status"] == "expired"
    assert [x["name"] for x in c.get("/api/recipients").json()["items"]] == ["Budi"]

def test_two_invites_in_one_poll_and_repair_dedupes(tg):
    a = c.post("/api/telegram/invite", json={"name": "A", "role": "Salesman", "region": ""}).json(); b = c.post("/api/telegram/invite", json={"name": "B", "role": "Salesman", "region": ""}).json()
    tg.press_start(a["code"], 1, "A"); tg.press_start(b["code"], 2, "B")
    assert c.get(f"/api/telegram/invite/{a['code']}").json()["status"] == "paired" and c.get(f"/api/telegram/invite/{b['code']}").json()["status"] == "paired"
    again = c.post("/api/telegram/invite", json={"name": "A2", "role": "Head of Sales", "region": ""}).json(); tg.press_start(again["code"], 1, "A")
    c.get(f"/api/telegram/invite/{again['code']}"); items = c.get("/api/recipients").json()["items"]
    assert len(items) == 2 and next(i for i in items if i["name"] == "A2")["role"] == "Head of Sales"

def test_delete_recipient(tg):
    rid = pair(tg, "Budi", "Salesman", "", 5); assert c.delete(f"/api/recipients/{rid}").status_code == 200 and c.get("/api/recipients").json()["items"] == []

def test_preview_is_what_recipient_gets(loaded):
    p = c.post("/api/share/preview", json={"filters": {}, "region": "Jawa Barat"}).json()
    assert p["scope_label"] == "Jawa Barat" and p["card"].startswith("data:image/png;base64,") and "13,9%" in p["summary"] and p["actions"]

def test_send_per_region_routes_each_scope(loaded):
    f = loaded
    ids = [pair(f, "Timur", "Head of Region", "Jawa Timur", 111), pair(f, "Barat", "Head of Region", "Jawa Barat", 222), pair(f, "Bos", "Head of Sales", "", 333)]
    r = c.post("/api/share/send", json={"recipient_ids": ids, "mode": "per_region", "filters": {}, "confirm": True}).json()
    assert [x["status"] for x in r["results"]] == ["sent"] * 3
    by = {}
    for m in f.sent:
        if m["chat_id"] in (111, 222, 333) and m["method"] != "sendMessage" or (m["text"] or "").startswith(("Jawa", "Semua", "Action")): by.setdefault(m["chat_id"], []).append(m)
    assert [m["method"] for m in by[111]] == ["sendPhoto", "sendMessage", "sendMessage"]          # card, summary, action items — in that order
    assert by[111][0]["files"]["photo"][:4] == b"\x89PNG" and len(by[111][0]["caption"]) <= 1024
    assert "Jawa Timur" in by[111][1]["text"] and "Jawa Barat" not in by[111][1]["text"] and "92,4%" in by[111][1]["text"]
    assert "Jawa Barat" in by[222][1]["text"] and "Jawa Timur" not in by[222][1]["text"]
    assert by[333][1]["text"].startswith("Semua wilayah") and by[111][0]["files"]["photo"] != by[222][0]["files"]["photo"]
    assert len(c.get("/api/share/history").json()["items"]) == 3

def test_send_same_view_to_everyone(loaded):
    f = loaded; ids = [pair(f, "A", "Salesman", "Jawa Timur", 1), pair(f, "B", "Salesman", "", 2)]
    c.post("/api/share/send", json={"recipient_ids": ids, "mode": "same", "filters": {"region": ["Jawa Tengah"]}, "confirm": True})
    texts = [m["text"] for m in f.sent if (m["text"] or "").startswith("Jawa Tengah")]; assert len(texts) == 2

def test_send_requires_confirmation_and_token(loaded, monkeypatch):
    rid = pair(loaded, "A", "Salesman", "", 1)
    assert c.post("/api/share/send", json={"recipient_ids": [rid], "mode": "same", "filters": {}}).status_code == 422
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN")
    assert c.post("/api/share/send", json={"recipient_ids": [rid], "mode": "same", "filters": {}, "confirm": True}).status_code == 409

def test_failure_is_reported_per_recipient_with_fallback(loaded):
    f = loaded; ok = pair(f, "Ok", "Salesman", "", 1); bad = pair(f, "Blocked", "Salesman", "", 2); f.fail_chats.add(2)
    r = c.post("/api/share/send", json={"recipient_ids": [ok, bad], "mode": "same", "filters": {}, "confirm": True}).json()
    assert [x["status"] for x in r["results"]] == ["sent", "failed"] and "blocked" in r["results"][1]["error"].lower()
    fb = r["fallbacks"][r["results"][1]["fallback"]]; assert fb["summary"] and fb["actions_text"] and fb["card"].startswith("data:image/png")
    assert f.token not in json.dumps(r) and f.token not in json.dumps(c.get("/api/share/history").json())
    assert [h["status"] for h in c.get("/api/share/history").json()["items"]] == ["failed", "sent"]      # newest first

def test_offline_marks_failed_and_offers_fallback(loaded):
    f = loaded; rid = pair(f, "A", "Salesman", "", 1); f.offline = True
    r = c.post("/api/share/send", json={"recipient_ids": [rid], "mode": "same", "filters": {}, "confirm": True}).json()
    assert r["results"][0]["status"] == "failed" and r["results"][0]["offline"] is True and r["fallbacks"]

def test_token_never_reaches_the_status_log(tg):
    from app.main import LOG
    c.get("/api/telegram/status"); c.post("/api/telegram/invite", json={"name": "A", "role": "Salesman", "region": ""})
    import logging; logging.getLogger("httpx").warning("POST https://api.telegram.org/bot%s/getMe", tg.token)      # even if something logs it
    assert tg.token not in " ".join(LOG) and tg.token not in c.get("/api/status").text

def test_per_owner_sends_each_person_only_their_own_actions(loaded):
    f = loaded
    items = c.get("/api/actions").json()["items"]
    items[0]["owner"] = "Gita"; items[1]["owner"] = "Gita"; items[2]["owner"] = "Bayu"
    for it in items[3:]: it["owner"] = "Orang Lain"
    items[1]["status"] = "done"; c.put("/api/actions", json={"items": items})
    gita = pair(f, "Gita", "Salesman", "", 11); bayu = pair(f, "Bayu", "Salesman", "", 12); nobody = pair(f, "Tanpa Aksi", "Salesman", "", 13)
    before = len(f.sent)
    r = c.post("/api/share/send", json={"recipient_ids": [gita, bayu, nobody], "mode": "per_owner", "confirm": True}).json()
    st = {x["name"]: x["status"] for x in r["results"]}
    assert st == {"Gita": "sent", "Bayu": "sent", "Tanpa Aksi": "skipped"}
    msgs = {m["chat_id"]: m["text"] for m in f.sent[before:]}
    assert items[0]["action"] in msgs[11] and items[1]["action"] not in msgs[11] and items[2]["action"] not in msgs[11]   # done item is not sent
    assert items[2]["action"] in msgs[12] and 13 not in msgs
    assert all(h["name"] != "Tanpa Aksi" for h in c.get("/api/share/history").json()["items"])
    pv = c.post("/api/share/preview-owner", json={"recipient_id": bayu}).json(); assert len(pv["actions"]) == 1 and "Bayu" in pv["text"]

def test_demo_me_sends_every_owners_message_to_one_chat(loaded):
    f = loaded
    items = c.get("/api/actions").json()["items"]
    for i, it in enumerate(items): it["owner"] = ["Gita", "Bayu"][i % 2]; it["status"] = "todo"
    c.put("/api/actions", json={"items": items})
    me = pair(f, "Saya", "Manajer", "", 21); before = len(f.sent)
    r = c.post("/api/share/send", json={"recipient_ids": [me], "mode": "demo_me", "confirm": True}).json()
    assert [x["status"] for x in r["results"]] == ["sent", "sent"]
    msgs = f.sent[before:]; assert {m["chat_id"] for m in msgs} == {21}
    texts = [m["text"] for m in msgs if m["method"] == "sendMessage"]
    assert any("sebagai <b>Gita</b>" in t for t in texts) and any("sebagai <b>Bayu</b>" in t for t in texts)
    assert sum(m["method"] == "sendPhoto" for m in msgs) == 2          # a data picture goes first, for each owner
    assert c.post("/api/share/send", json={"recipient_ids": [], "mode": "demo_me", "confirm": True}).status_code == 422

def test_preview_owner_works_for_an_owner_nobody_has_linked(loaded):
    items = c.get("/api/actions").json()["items"]; items[0]["owner"] = "Gita"; items[0]["status"] = "todo"; c.put("/api/actions", json={"items": items})
    pv = c.post("/api/share/preview-owner", json={"owner": "Gita"}).json()
    assert len(pv["actions"]) == 1 and "Gita" in pv["text"]


def test_owner_message_is_html_with_a_picture_first(loaded):
    f = loaded
    items = c.get("/api/actions").json()["items"]; items[0]["owner"] = "Gita"; items[0]["status"] = "todo"; c.put("/api/actions", json={"items": items})
    gita = pair(f, "Gita", "Salesman", "", 31); before = len(f.sent)
    c.post("/api/share/send", json={"recipient_ids": [gita], "mode": "per_owner", "confirm": True})
    msgs = f.sent[before:]; assert msgs[0]["method"] == "sendPhoto" and "Gita" in msgs[0]["caption"]
    body = "\n".join(m["text"] for m in msgs[1:])
    assert "<b>Kenapa</b>" in body and "<b>Yang perlu dilakukan</b>" in body and "<b>Yang perlu kamu jawab</b>" in body
    pv = c.post("/api/share/preview-owner", json={"owner": "Gita"}).json(); assert pv["card"].startswith("data:image/png")
