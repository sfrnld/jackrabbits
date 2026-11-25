import datetime as dt
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.ingest import read_table
from app.mapping import guess_mapping, apply_mapping
from app.findings import detect, apply_decisions, recommended
from app.actions import generate

TODAY = dt.date(2026, 11, 25)

@pytest.fixture(scope="module")
def df():
    raw = read_table("data/sales.csv").df
    c = apply_mapping(raw, {k: v["column"] for k, v in guess_mapping(raw).items()})
    return apply_decisions(c, recommended(detect(c)))[0]

def test_actions_cover_weakest_and_movers(df):
    a = generate(df, today=TODAY)
    ids = [x["outlet_id"] for x in a]
    assert len(ids) == len(set(ids))                                   # one action per outlet
    assert {"OUT1045", "OUT1048", "OUT1001"} <= set(ids)               # weakest outlets (within-type score)
    dec = next(x for x in a if x["outlet_id"] == "OUT1014")            # biggest decline driver
    assert dec["priority"] == "urgent" and "turun" in dec["reason"].lower() or "−" in dec["reason"]
    gain = next(x for x in a if x["outlet_id"] == "OUT1036")           # biggest growth driver
    assert gain["priority"] == "opportunity"

def test_action_fields(df):
    for x in generate(df, today=TODAY):
        assert x["id"] and x["action"] and x["reason"] and x["owner"] and x["due"] == "2026-12-02"
        assert x["priority"] in {"urgent", "opportunity", "watch"}
    a = generate(df, today=TODAY)
    assert [x["priority"] for x in a] == sorted([x["priority"] for x in a], key={"urgent": 0, "opportunity": 1, "watch": 2}.get)

def test_actions_and_session_api(tmp_path):
    from app import data_api
    c = TestClient(app); data_api.TEMPLATES = tmp_path; data_api.S.clear()
    assert c.get("/api/session").json() == {"loaded": False, "confirmed": False}
    assert c.get("/api/actions").status_code == 409
    r = c.post("/api/data/sample").json()
    assert c.get("/api/session").json()["loaded"] is True and c.get("/api/session").json()["confirmed"] is False
    c.post("/api/data/mapping", json={"mapping": {k: v["column"] for k, v in r["mapping"].items()}})
    s = c.get("/api/session").json(); assert s["confirmed"] is True and s["rows"] == 1891
    c.post("/api/findings/apply-all")
    items = c.get("/api/actions").json()["items"]; assert len(items) >= 5
    items[0]["owner"] = "Budi"; items[0]["action"] = "Edited"
    items.append(dict(id="x1", outlet_id="", outlet="", owner="Citra", action="Manual", reason="", due="2026-12-01", priority="watch"))
    assert c.put("/api/actions", json={"items": items}).json()["items"][0]["owner"] == "Budi"
    again = c.get("/api/actions").json()["items"]; assert again[0]["action"] == "Edited" and again[-1]["action"] == "Manual"
    regen = c.post("/api/actions/regenerate").json()["items"]; assert regen[0]["action"] != "Edited"

def test_no_fake_decline_action_when_every_region_grew(df):
    up = df.copy(); up.loc[up.date >= "2026-10-01", "net"] *= 3          # every region now grows
    a = generate(up, today=TODAY)
    assert not any(x["reason"].startswith("Turun Rp") for x in a)         # nothing is labelled a decline
    assert any(x["priority"] == "opportunity" for x in a)                 # the biggest gainer is still an opportunity
