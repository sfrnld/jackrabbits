import pandas as pd, pytest
from app.ingest import read_table
from app.mapping import guess_mapping, apply_mapping
from app.findings import detect, apply_decisions, recommended, summarize

@pytest.fixture(scope="module")
def canon():
    raw = read_table("data/sales.csv").df
    return apply_mapping(raw, {k: v["column"] for k, v in guess_mapping(raw).items()})

@pytest.fixture(scope="module")
def F(canon):
    return {f["id"]: f for f in detect(canon)}

def test_sample_has_exactly_the_five_findings(F):
    assert set(F) == {"region", "duplicates", "returns", "salesman", "outlet_names"}

def test_region_variants(F):
    f = F["region"]
    assert f["rows"] == 10 and f["impact_rows"] == 10
    groups = {g["canonical"]: set(g["variants"]) for g in f["groups"]}
    assert groups["Jawa Barat"] == {"Jabar", "JAWA BARAT"}
    assert groups["Jabodetabek"] == {"JABODETABEK"} and groups["Jawa Timur"] == {"JAWA TIMUR"}
    assert f["recommended"] == "merge_all"
    assert any("385" in o["preview"] and "393" in o["preview"] for o in f["options"])

def test_duplicates(F):
    f = F["duplicates"]
    assert f["rows"] == 3 and f["impact_rp"] == 2_070_900
    assert {e["invoice"] for e in f["examples"]} == {"INV500201", "INV500386", "INV500791"}
    assert f["recommended"] == "drop"

def test_return(F):
    f = F["returns"]
    assert f["rows"] == 1 and f["impact_rp"] == -528_000 and f["examples"][0]["invoice"] == "RTR900001"
    assert f["recommended"] == "deduct"

def test_missing_salesman(F):
    f = F["salesman"]
    assert f["rows"] == 5 and f["recommended"] == "label"

def test_outlet_names(F):
    f = F["outlet_names"]
    assert f["rows"] == 3 and {g["outlet_id"] for g in f["groups"]} == {"OUT1004", "OUT1005", "OUT1032"}

def test_recommended_decisions_give_acceptance_numbers(canon, F):
    out, trail = apply_decisions(canon, recommended(list(F.values())))
    assert out.net.sum() == 1_725_966_000 and len(out) == 1888
    assert out.region.nunique() == 6
    m = out.groupby(out.date.dt.month).net.sum()
    assert m[9] == 847_517_400 and m[10] == 878_448_600
    assert round(m[10] / m[9] - 1, 3) == 0.037 or round((m[10] / m[9] - 1) * 100, 1) == 3.6
    assert out.outlet_name.str.endswith(" ").sum() == 0
    assert (out.salesman == "Tidak diketahui").sum() == 5
    assert len(trail) == 5 and all("finding" in t and "option" in t for t in trail)

def test_no_decisions_leaves_data_untouched(canon):
    out, trail = apply_decisions(canon, {})
    assert out.net.sum() == 1_728_036_900 and len(out) == 1891 and trail == []

def test_each_option_changes_what_it_says(canon, F):
    keep, _ = apply_decisions(canon, {"duplicates": {"option": "keep"}})
    assert len(keep) == 1891
    flag, _ = apply_decisions(canon, {"duplicates": {"option": "flag"}})
    assert len(flag) == 1891 and flag.dq_duplicate.sum() == 3
    sep, _ = apply_decisions(canon, {"returns": {"option": "separate"}})
    assert sep.net.sum() == 1_728_036_900 + 528_000 and sep.return_amt.sum() == 528_000
    exc, _ = apply_decisions(canon, {"returns": {"option": "exclude"}})
    assert len(exc) == 1890
    fill, _ = apply_decisions(canon, {"salesman": {"option": "fill_dominant"}})
    assert fill.salesman.notna().all() and fill.salesman_guess.sum() == 5
    ren, _ = apply_decisions(canon, {"region": {"option": "rename", "params": {"map": {"Jabar": "Jawa Barat (Jabar)"}}}})
    assert "Jawa Barat (Jabar)" in set(ren.region)
    part, _ = apply_decisions(canon, {"region": {"option": "merge_groups", "params": {"groups": ["Jawa Barat"]}}})
    assert "JABODETABEK" in set(part.region) and "Jabar" not in set(part.region)

def test_undo_is_just_removing_the_decision(canon, F):
    rec = recommended(list(F.values()))
    rec.pop("duplicates")
    out, _ = apply_decisions(canon, rec)
    assert len(out) == 1891 and out.net.sum() == 1_725_966_000 + 2_070_900

def test_summary_before_after(canon, F):
    out, _ = apply_decisions(canon, recommended(list(F.values())))
    s = summarize(canon, out)
    assert s["before"]["rows"] == 1891 and s["after"]["rows"] == 1888
    assert s["before"]["regions"] == 10 and s["after"]["regions"] == 6
    assert s["after"]["net"] == 1_725_966_000

def test_generic_checks_fire_on_bad_data(canon):
    bad = canon.copy()
    bad.loc[bad.index[0], "gross"] += 5000                     # qty*price != gross
    bad.loc[bad.index[1], "date"] = pd.Timestamp("2030-01-01")  # out of range
    bad.loc[bad.index[2], "net"] = 90_000_000                   # extreme
    bad.loc[bad.index[3], "outlet_id"] = pd.NA                  # required empty
    kinds = {f["id"] for f in detect(bad)}
    assert {"calc_mismatch", "date_range", "extreme", "required_empty"} <= kinds

def test_duplicates_show_which_row_each_copy_duplicates(canon, F):
    f = F["duplicates"]; pairs = f["pairs"]
    assert len(pairs) == 3 and f["compared_columns"] == 15
    cols = [c for c in canon.columns if c != "src_row"]
    by_row = canon.set_index("src_row")
    for p in pairs:
        assert p["keep"]["row"] < p["drop"]["row"]                                   # the earlier row is kept, the later copy is dropped
        a, b = by_row.loc[p["keep"]["row"], cols], by_row.loc[p["drop"]["row"], cols]
        assert a.equals(b) or all((x == y) or (x != x and y != y) for x, y in zip(a, b))   # truly identical in every compared column
        assert p["keep"]["invoice"] == p["drop"]["invoice"] and p["drop"]["net"] > 0
        assert {"row", "invoice", "date", "outlet_id", "outlet_name", "brand", "sku", "qty", "net"} <= set(p["drop"])
    assert {p["drop"]["invoice"] for p in pairs} == {"INV500201", "INV500386", "INV500791"}

def test_involved_rows_drive_the_table(canon, F):
    inv = lambda k: F[k]["involved"]
    assert [(r["row"], r["role"], r["group"]) for r in inv("duplicates")] == [(493, "keep", 0), (495, "copy", 0), (912, "keep", 1), (913, "copy", 1), (1871, "keep", 2), (1873, "copy", 2)]
    ret = int(canon[canon.invoice == "RTR900001"].src_row.iloc[0])
    assert [(r["row"], r["role"], r["hi"]) for r in inv("returns")] == [(ret, "return", ["qty", "net"])]
    assert {r["row"] for r in inv("salesman")} == set(canon[canon.salesman.isna()].src_row) and all(r["hi"] == ["salesman"] for r in inv("salesman"))
    reg = canon[canon.region.isin(["Jabar", "JAWA BARAT", "JABODETABEK", "JAWA TIMUR"])]
    var = lambda k: [r for r in inv(k) if r["role"] == "variant"]
    assert {r["row"] for r in var("region")} == set(reg.src_row) and {r["label"] for r in var("region")} == {"Jawa Barat", "Jabodetabek", "Jawa Timur"}
    names = canon[canon.outlet_id.isin(["OUT1004", "OUT1005", "OUT1032"]) & canon.outlet_name.str.endswith(" ")]
    assert {r["row"] for r in var("outlet_names")} == set(names.src_row) and all(r["hi"] == ["outlet_name"] and r["label"] for r in var("outlet_names"))

def test_spelling_findings_show_a_reference_row_and_why(canon, F):
    f = F["outlet_names"]; inv = f["involved"]
    refs = [r for r in inv if r["role"] == "reference"]
    assert len(refs) == 3 and all(r["group_label"] for r in refs)
    by = canon.set_index("src_row")
    for r in refs: assert by.loc[r["row"], "outlet_name"] == by.loc[r["row"], "outlet_name"].strip()           # the reference uses the clean spelling
    assert all(r["why"] == "spasi di akhir" for r in inv if r["role"] == "variant")
    assert [r["role"] for r in inv[:2]] == ["reference", "variant"] and inv[0]["group"] == inv[1]["group"]      # each group: reference first, then its variants
    g = next(x for x in f["groups"] if x["outlet_id"] == "OUT1004")
    sp = {x["text"]: x for x in g["spellings"]}; assert sp["Grosir Berkah"]["issue"] is None and sp["Grosir Berkah "]["issue"] == "spasi di akhir"
    assert sp["Grosir Berkah"]["rows"] > sp["Grosir Berkah "]["rows"] and f["pin"] == ["outlet_id"]
    rg = F["region"]; assert [r["role"] for r in rg["involved"][:2]] == ["reference", "variant"] and {r["why"] for r in rg["involved"] if r["role"] == "variant"} == {"singkatan", "huruf besar/kecil beda"}
