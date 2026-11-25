import pandas as pd, pytest
from app.ingest import read_table
from app.mapping import guess_mapping, apply_mapping
from app.findings import detect, apply_decisions, recommended
from app.analytics import query, drivers, outlet_scores, weakest, insights, options
from app.fmt import rp, pct

@pytest.fixture(scope="module")
def df():
    raw = read_table("data/sales.csv").df
    c = apply_mapping(raw, {k: v["column"] for k, v in guess_mapping(raw).items()})
    return apply_decisions(c, recommended(detect(c)))[0]

def test_acceptance_query_jabar_oct(df):
    r = query(df, filters={"region": ["Jawa Barat"], "month": ["2026-10"]})
    assert r["total"] == 143_882_800

def test_total_and_months(df):
    assert query(df)["total"] == 1_725_966_000
    rows = {x["key"]: x["value"] for x in query(df, group_by="month")["rows"]}
    assert rows == {"2026-09": 847_517_400, "2026-10": 878_448_600}

def test_compare_regions(df):
    r = query(df, group_by="region", compare=["2026-09", "2026-10"])
    by = {x["key"]: x for x in r["rows"]}
    assert round(by["Jawa Timur"]["pct"], 1) == 92.4 and round(by["Jawa Barat"]["pct"], 1) == -13.9
    assert r["total"]["b"] == 878_448_600 and round(r["total"]["pct"], 1) == 3.6

def test_metrics_and_dims(df):
    assert query(df, metric="invoices")["total"] > 0
    assert 0 < query(df, metric="discount_ratio")["total"] < 1
    assert query(df, group_by="week")["rows"] and query(df, group_by="brand", top=3)["rows"].__len__() == 3
    assert query(df, filters={"date_from": "2026-10-01"})["total"] == 878_448_600
    multi = query(df, filters={"region": ["Jawa Barat"], "outlet_type": ["Grosir"]})["total"]
    assert 0 < multi < query(df, filters={"region": ["Jawa Barat"]})["total"]
    with pytest.raises(ValueError): query(df, group_by="nonsense")

def test_drivers_jatim_is_one_outlet(df):
    d = drivers(df, "region", "Jawa Timur", "2026-09", "2026-10")
    assert d[0]["key"] == "OUT1036" and round(d[0]["delta"]) == 47_666_200 and d[0]["share"] > 0.6

def test_drivers_jabar_driver_exceeds_region_decline(df):
    d = drivers(df, "region", "Jawa Barat", "2026-09", "2026-10")
    assert d[0]["key"] == "OUT1014" and round(d[0]["delta"]) == -31_632_900 and d[0]["exceeds_total"] is True

def test_insights_tell_the_story(df):
    txt = " ".join(i["text"] for i in insights(df, {}))
    assert "Jawa Timur" in txt and "92,4%" in txt and "Grosir Lancar Jaya" in txt and "hampir semuanya" in txt
    assert "Jawa Barat" in txt and "13,9%" in txt and "Grosir Sentosa" in txt
    assert 1 <= len(insights(df, {})) <= 3

def test_insights_drill_when_region_filtered(df):
    ins = insights(df, {"region": ["Jawa Barat"]})
    assert ins and all("Jawa Barat" not in i["text"] or "Bandung" in i["text"] or "Grosir" in i["text"] for i in ins)

def test_score_is_relative_to_outlet_type():
    rows = []
    def add(oid, typ, m1, m2, n=6):
        for m, v in (("2026-09", m1), ("2026-10", m2)):
            for k in range(n):
                rows.append(dict(date=pd.Timestamp(f"{m}-{10+k}"), invoice=f"{oid}{m}{k}", outlet_id=oid, outlet_name=oid,
                                 outlet_type=typ, region="R", branch="B", salesman="S", net=v / n))
    for i in range(6): add(f"W{i}", "Warung", 14e6 + i * 1e5, 14e6 + i * 1e5)       # steady small warungs
    for i in range(5): add(f"G{i}", "Grosir", 135e6 + i * 1e6, 135e6 + i * 1e6)     # steady big grosir
    add("GWEAK", "Grosir", 60e6, 20e6)                                               # 40M total: > any warung, weak for a grosir
    d = pd.DataFrame(rows); d["gross"] = d.net; d["discount"] = 0.0; d["qty"] = 1.0
    w = weakest(d, n=1)[0]
    assert w["outlet_id"] == "GWEAK"                       # NOT a warung, despite the smaller absolute totals
    smallest = set(d.groupby("outlet_id").net.sum().nsmallest(5).index)
    assert smallest <= {f"W{i}" for i in range(6)}          # the naive ranking would be all warung

def test_scores_on_sample(df):
    s = outlet_scores(df)
    assert len(s) == 52 and s.score.between(0, 100).all()
    w = weakest(df, n=5)
    assert len(w) == 5 and all(x["reasons"] for x in w)
    naive = set(df.groupby("outlet_id").net.sum().nsmallest(5).index)
    assert {x["outlet_id"] for x in w} != naive
    assert w[0]["score"] <= w[-1]["score"]

def test_weakest_respects_scope(df):
    w = weakest(df, filters={"region": ["Jawa Barat"]}, n=5)
    ids = set(df[df.region == "Jawa Barat"].outlet_id)
    assert len(w) == 5 and {x["outlet_id"] for x in w} <= ids

def test_options_lists_values(df):
    o = options(df)
    assert "Jawa Barat" in o["region"] and "Sukro" in o["brand"] and o["month"] == ["2026-09", "2026-10"]

def test_formatting():
    assert rp(31_632_900) == "Rp 31,6 juta" and rp(-23_181_700) == "−Rp 23,2 juta"
    assert rp(1_725_966_000) == "Rp 1,7 miliar" and rp(528_000) == "Rp 528 ribu"
    assert pct(92.37) == "92,4%" and pct(-13.9) == "13,9%"

def test_series_for_small_multiples(df):
    from app.analytics import series
    s = series(df, split_by="brand", x="week")
    assert s["x"] == sorted(s["x"]) and len(s["series"]) == 8
    assert abs(sum(sum(r["values"]) for r in s["series"]) - 1_725_966_000) < 1
    assert s["series"][0]["total"] >= s["series"][-1]["total"] and all(len(r["values"]) == len(s["x"]) for r in s["series"])
    one = series(df, filters={"region": ["Jawa Barat"]}, split_by="brand", x="month")
    assert one["x"] == ["2026-09", "2026-10"]

def test_outlet_rows_for_scatter(df):
    from app.analytics import outlet_rows
    r = outlet_rows(df); assert len(r) == 52 and {"outlet_id", "total", "invoices", "score"} <= set(r[0])
    assert len(outlet_rows(df, {"region": ["Jawa Barat"]})) == 8
