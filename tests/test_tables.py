from fastapi.testclient import TestClient
from app.main import app
from app import data_api

c = TestClient(app)

def load(tmp_path):
    data_api.TEMPLATES = tmp_path; data_api.S.clear()
    r = c.post("/api/data/sample").json()
    c.post("/api/data/mapping", json={"mapping": {k: v["column"] for k, v in r["mapping"].items()}})
    return {f["id"]: f for f in c.get("/api/findings").json()["findings"]}

def test_every_finding_has_a_table_of_the_original_file(tmp_path):
    F = load(tmp_path); raw = data_api.S["raw"]
    for f in F.values():
        t = f["table"]
        assert t["columns"] == list(raw.columns)                                  # the user's own headers, in file order
        assert t["rows"] and all(set(r["cells"]) == set(raw.columns) for r in t["rows"])
        assert {"qty_carton", "net_sales_idr"} <= set(t["numeric"])

def test_line_numbers_match_the_spreadsheet(tmp_path):
    t = load(tmp_path)["duplicates"]["table"]
    assert [(r["line"], r["role"], r["group"]) for r in t["rows"]] == [(494, "keep", 0), (496, "copy", 0), (913, "keep", 1), (914, "copy", 1), (1872, "keep", 2), (1874, "copy", 2)]
    for a, b in zip(t["rows"][::2], t["rows"][1::2]): assert a["cells"] == b["cells"]       # a pair really is identical
    assert t["rows"][0]["cells"]["invoice_no"] == "INV500201" and t["rows"][0]["cells"]["net_sales_idr"] == "1024300"

def test_highlighted_cells_use_the_original_column_names(tmp_path):
    F = load(tmp_path)
    s = F["salesman"]["table"]; assert len(s["rows"]) == 5 and all(r["hi"] == ["salesman"] and r["cells"]["salesman"] is None for r in s["rows"])
    r = F["returns"]["table"]["rows"][0]; assert r["cells"]["invoice_no"] == "RTR900001" and r["hi"] == ["qty_carton", "net_sales_idr"] and r["cells"]["qty_carton"] == "-2"
    g = [x for x in F["region"]["table"]["rows"] if x["role"] == "variant"]; assert len(g) == 10 and all(x["hi"] == ["region"] and x["label"] for x in g)

def test_big_findings_are_capped_but_counted(tmp_path):
    from app import findings_api
    load(tmp_path)
    t = findings_api.build_table({"involved": [{"row": i + 1, "role": "issue", "hi": [], "label": None, "group": None} for i in range(50)]}, data_api.S["raw"], {}, 0, limit=20)
    assert len(t["rows"]) == 20 and t["total"] == 50 and t["hidden"] == 30

def test_undecided_findings_have_no_after_values(tmp_path):
    F = load(tmp_path)
    assert all("after" not in r and r["removed"] is False for f in F.values() for r in f["table"]["rows"])

def test_decided_findings_report_what_happened_to_each_row(tmp_path):
    load(tmp_path); F = {f["id"]: f for f in c.post("/api/findings/apply-all").json()["findings"]}
    dup = F["duplicates"]["table"]["rows"]
    assert [(r["role"], r["removed"]) for r in dup] == [("keep", False), ("copy", True)] * 3          # copies are gone, originals stay
    var = [r for r in F["region"]["table"]["rows"] if r["role"] == "variant"]
    assert {r["after"]["region"] for r in var} == {"Jawa Barat", "Jabodetabek", "Jawa Timur"}
    assert all(r["cells"]["region"] != r["after"]["region"] for r in var)                            # before differs from after
    assert {r["after"]["salesman"] for r in F["salesman"]["table"]["rows"]} == {"Tidak diketahui"}
    names = [r for r in F["outlet_names"]["table"]["rows"] if r["role"] == "variant"]; assert all(r["after"]["outlet_name"] == r["cells"]["outlet_name"].strip() for r in names)
    ret = F["returns"]["table"]["rows"][0]; assert ret["removed"] is False and ret["after"] == {"qty_carton": "-2", "net_sales_idr": "-528000"}   # deducted: values stay

def test_undo_removes_the_after_values(tmp_path):
    load(tmp_path); c.post("/api/findings/apply-all")
    F = {f["id"]: f for f in c.delete("/api/findings/duplicates").json()["findings"]}
    assert all("after" not in r and r["removed"] is False for r in F["duplicates"]["table"]["rows"])


def test_table_carries_reference_rows_groups_and_pinned_context(tmp_path):
    t = load(tmp_path)["outlet_names"]["table"]
    assert t["pinned"] == ["outlet_id"] and t["rows"][0]["role"] == "reference" and t["rows"][0]["group_label"].startswith("OUT")
    assert t["rows"][1]["role"] == "variant" and t["rows"][1]["why"] == "spasi di akhir"
    assert t["rows"][0]["cells"]["outlet_id"] == t["rows"][1]["cells"]["outlet_id"]                   # same outlet ID...
    assert t["rows"][0]["cells"]["outlet_name"] + " " == t["rows"][1]["cells"]["outlet_name"]         # ...names differ only by the trailing space

def test_the_ui_contract_for_deciding_is_put_not_post(tmp_path):
    """Regression: the UI once POSTed a decision and silently got 405, so card choices never reached the server."""
    load(tmp_path)
    assert c.post("/api/findings/duplicates", json={"option": "drop"}).status_code == 405
    st = c.put("/api/findings/duplicates", json={"option": "drop"}).json()
    assert st["decisions"]["duplicates"]["option"] == "drop" and st["summary"]["after"]["rows"] == 1888
