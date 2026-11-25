from fastapi.testclient import TestClient
from app.main import app, find_free_port

c = TestClient(app)

def test_health():
    assert c.get("/api/health").json()["ok"] is True

def test_system_check_items():
    items = {i["id"]: i for i in c.get("/api/setup/check").json()["items"]}
    assert list(items) == ["engine", "storage", "writable", "sample", "port", "internet"]
    assert items["engine"]["status"] == "ok" and items["sample"]["status"] == "ok"      # data/sales.csv is bundled
    assert items["internet"]["status"] in {"ok", "warn"}                                 # offline is a warning, never an error
    for i in items.values():
        assert i["facts"] and all({"k", "v"} <= set(f) for f in i["facts"])             # every item says what it actually saw

def _facts(items, id_): return {f["k"]: f for f in next(i for i in items if i["id"] == id_)["facts"]}

def test_checks_report_real_values():
    items = c.get("/api/setup/check").json()["items"]
    e = _facts(items, "engine"); assert e["python"]["v"].startswith("3.") and e["python"]["min"] == "3.11" and "duckdb" in e and "pandas" in e
    s = _facts(items, "sample"); assert s["path"]["v"].endswith("data/sales.csv") and s["rows"]["v"] == "1.891" and s["columns"]["v"] == "15"
    p = _facts(items, "port"); assert p["address"]["v"].startswith("127.0.0.1") or p["address"]["v"].startswith("testserver")
    st = _facts(items, "storage"); assert st["free"]["v"].endswith("GB") and st["free"]["min"] and st["path"]["v"]

def test_storage_thresholds(monkeypatch):
    import shutil, collections
    U = collections.namedtuple("U", "total used free")
    for free_gb, want in [(50, "ok"), (0.5, "warn"), (0.05, "error")]:
        monkeypatch.setattr(shutil, "disk_usage", lambda p, f=free_gb: U(100 * 2**30, 0, int(f * 2**30)))
        assert next(i for i in c.get("/api/setup/check").json()["items"] if i["id"] == "storage")["status"] == want

def test_state_folder_must_be_writable(monkeypatch, tmp_path):
    ro = tmp_path / "ro"; ro.mkdir(); ro.chmod(0o500)
    monkeypatch.setenv("SALES_STUDIO_STATE", str(ro / "state"))
    w = next(i for i in c.get("/api/setup/check").json()["items"] if i["id"] == "writable")
    assert w["status"] == "error" and w["facts"][0]["k"] == "path"
    ro.chmod(0o700); monkeypatch.setenv("SALES_STUDIO_STATE", str(tmp_path / "ok"))
    assert next(i for i in c.get("/api/setup/check").json()["items"] if i["id"] == "writable")["status"] == "ok"

def test_internet_offline_and_slow(monkeypatch):
    from app import main
    monkeypatch.setattr(main, "_internet", lambda: (None, "tidak bisa terhubung"))
    i = next(i for i in c.get("/api/setup/check").json()["items"] if i["id"] == "internet")
    assert i["status"] == "warn" and _facts([i], "internet")["reason"]["v"] == "tidak bisa terhubung"
    monkeypatch.setattr(main, "_internet", lambda: (2400, None))
    assert next(i for i in c.get("/api/setup/check").json()["items"] if i["id"] == "internet")["status"] == "warn"      # reachable but too slow
    monkeypatch.setattr(main, "_internet", lambda: (80, None))
    assert next(i for i in c.get("/api/setup/check").json()["items"] if i["id"] == "internet")["status"] == "ok"

def test_free_port():
    assert 1024 < find_free_port() < 65536

def test_status_logs():
    assert isinstance(c.get("/api/status").json()["log"], list)

def test_data_flow_sample(tmp_path):
    from app import data_api
    data_api.TEMPLATES = tmp_path
    r = c.post("/api/data/sample").json()
    assert r["rows"] == 1891 and r["missing"] == [] and r["remembered"] is False
    m = {k: v["column"] for k, v in r["mapping"].items()}
    ok = c.post("/api/data/mapping", json={"mapping": m}).json()
    assert ok["rows"] == 1891 and ok["hidden"] == [] and ok["date_min"] == "2026-09-01" and ok["date_max"] == "2026-10-31"
    assert c.post("/api/data/sample").json()["remembered"] is True   # template remembered

def test_upload_missing_required_is_422(tmp_path):
    from app import data_api
    data_api.TEMPLATES = tmp_path
    r = c.post("/api/data/upload", files={"file": ("x.csv", b"foo,bar\n1,2\n")}).json()
    assert set(r["missing"]) == {"date", "outlet", "net"}
    assert c.post("/api/data/mapping", json={"mapping": {}}).status_code == 422

def test_findings_api_flow(tmp_path):
    from app import data_api
    data_api.TEMPLATES = tmp_path
    assert c.get("/api/findings").status_code == 409                       # before mapping
    r = c.post("/api/data/sample").json()
    c.post("/api/data/mapping", json={"mapping": {k: v["column"] for k, v in r["mapping"].items()}})
    st = c.get("/api/findings").json()
    assert {f["id"] for f in st["findings"]} == {"region", "duplicates", "returns", "salesman", "outlet_names"}
    assert len(st["pending"]) == 5 and st["summary"]["after"]["net"] == 1_728_036_900   # nothing silent
    st = c.put("/api/findings/duplicates", json={"option": "drop"}).json()
    assert st["summary"]["after"]["rows"] == 1888 and len(st["trail"]) == 1
    assert c.put("/api/findings/duplicates", json={"option": "nope"}).status_code == 422
    st = c.post("/api/findings/apply-all").json()
    assert st["summary"]["after"]["net"] == 1_725_966_000 and st["pending"] == []
    st = c.delete("/api/findings/duplicates").json()                          # undo one
    assert st["summary"]["after"]["rows"] == 1891 and "duplicates" in st["pending"]

def _load(tmp_path):
    from app import data_api
    data_api.TEMPLATES = tmp_path
    r = c.post("/api/data/sample").json()
    c.post("/api/data/mapping", json={"mapping": {k: v["column"] for k, v in r["mapping"].items()}})
    c.post("/api/findings/apply-all")

def test_analytics_and_assistant_api(tmp_path):
    from app import data_api
    data_api.TEMPLATES = tmp_path; data_api.S.clear()
    assert c.post("/api/analytics/query", json={}).status_code == 409
    _load(tmp_path)
    q = c.post("/api/analytics/query", json={"filters": {"region": ["Jawa Barat"], "month": ["2026-10"]}}).json()
    assert q["total"] == 143_882_800
    assert c.post("/api/analytics/query", json={"group_by": "nonsense"}).status_code == 422
    cmp_ = c.post("/api/analytics/query", json={"group_by": "region", "compare": ["2026-09", "2026-10"]}).json()
    assert round({r["key"]: r["pct"] for r in cmp_["rows"]}["Jawa Timur"], 1) == 92.4
    assert c.get("/api/analytics/options").json()["month"] == ["2026-09", "2026-10"]
    ins = c.post("/api/analytics/insights", json={}).json()["insights"]
    assert any("92,4%" in i["text"] for i in ins)
    assert len(c.post("/api/analytics/weakest", json={"n": 5}).json()) == 5
    d = c.post("/api/analytics/drivers", json={"group_dim": "region", "key": "Jawa Timur", "a": "2026-09", "b": "2026-10"}).json()
    assert d[0]["key"] == "OUT1036"
    r = c.post("/api/assistant", json={"text": "jabar", "filters": {}}).json()
    assert r["filters"] == {"region": ["Jawa Barat"]} and r["undo"] is True and r["previous"] == {}
    r2 = c.post("/api/assistant", json={"text": "top 10 outlet", "filters": r["filters"]}).json()
    assert len(r2["result"]) == 8 and all(x["region"] == "Jawa Barat" for x in r2["result"])
    tl = c.get("/api/timeline").json()["items"]
    assert [t["who"] for t in tl][:2] == ["user", "assistant"] and len(tl) == 4


def test_reset_clears_everything_but_the_token(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app import data_api, main, settings
    env = tmp_path / ".env"; env.write_text("TELEGRAM_BOT_TOKEN=123:FAKE\n")
    monkeypatch.setenv("SALES_STUDIO_ENV", str(env)); monkeypatch.setenv("SALES_STUDIO_STATE", str(tmp_path / "st"))
    (tmp_path / "st" / "templates").mkdir(parents=True); (tmp_path / "st" / "share.json").write_text("{}")
    data_api.S["raw"] = 1
    r = TestClient(main.app).post("/api/reset"); assert r.json() == {"ok": True}
    assert not data_api.S and not (tmp_path / "st" / "share.json").exists() and not (tmp_path / "st" / "templates").exists()
    assert "123:FAKE" in env.read_text()

def test_filter_options_follow_the_cleaning_decisions(tmp_path):
    """After cleaning, the Region filter lists the merged names (Jabar → Jawa Barat), not the raw spellings."""
    from app import data_api
    data_api.TEMPLATES = tmp_path; data_api.S.clear()
    r = c.post("/api/data/sample").json()
    c.post("/api/data/mapping", json={"mapping": {k: v["column"] for k, v in r["mapping"].items()}})
    before = c.get("/api/analytics/options").json()["region"]
    c.post("/api/findings/apply-all")
    after = c.get("/api/analytics/options").json()["region"]
    assert len(after) == 6 and "Jabar" not in after and "JAWA BARAT" not in after and "Jawa Barat" in after
    assert len(before) > len(after)

def test_missing_sample_file_is_handled_gracefully(tmp_path, monkeypatch):
    """data/sales.csv may not be in the repo: the app must say so and keep working (uploading still works)."""
    import app.main as m
    monkeypatch.setattr(m, "SAMPLE", tmp_path / "nope.csv")
    assert c.get("/api/data/sample").json() == {"available": False}
    r = c.post("/api/data/sample"); assert r.status_code == 404 and "tidak ditemukan" in r.json()["detail"]
    item = next(i for i in c.get("/api/setup/check").json()["items"] if i["id"] == "sample")
    assert item["status"] == "warn"                                    # not an error: the sample is optional
    up = c.post("/api/data/upload", files={"file": ("x.csv", "date,outlet,net\n2026-09-01,A,100\n", "text/csv")}); assert up.status_code == 200
