import pytest
from app.ingest import read_table
from app.mapping import guess_mapping, apply_mapping
from app.findings import detect, apply_decisions, recommended
from app.assistant import parse

@pytest.fixture(scope="module")
def df():
    raw = read_table("data/sales.csv").df
    c = apply_mapping(raw, {k: v["column"] for k, v in guess_mapping(raw).items()})
    return apply_decisions(c, recommended(detect(c)))[0]

def test_jabar_sets_region_filter(df):
    r = parse("jabar", df, {})
    assert r["intent"] == "filter" and r["filters"] == {"region": ["Jawa Barat"]}
    assert "Region = Jawa Barat" in r["message"] and r["previous"] == {}

def test_brand_sukro(df):
    assert parse("brand sukro", df, {})["filters"] == {"brand": ["Sukro"]}
    assert parse("sukroo", df, {})["filters"] == {"brand": ["Sukro"]}          # typo tolerant

def test_combined_filters_and_months(df):
    r = parse("grosir oktober", df, {})
    assert r["filters"] == {"outlet_type": ["Grosir"], "month": ["2026-10"]}

def test_filter_replaces_same_dimension_and_keeps_others(df):
    cur = {"region": ["Jawa Barat"], "brand": ["Sukro"]}
    r = parse("tampilkan jatim saja", df, cur)
    assert r["filters"] == {"region": ["Jawa Timur"], "brand": ["Sukro"]} and r["previous"] == cur

def test_top_and_weakest(df):
    r = parse("top 10 outlet", df, {}); assert r["intent"] == "top" and r["n"] == 10 and len(r["result"]) == 10
    r = parse("5 outlet terlemah", df, {}); assert r["intent"] == "weakest" and r["n"] == 5 and len(r["result"]) == 5
    assert parse("outlet terlemah di jabar", df, {})["filters"] == {"region": ["Jawa Barat"]}

def test_compare(df):
    r = parse("bandingkan sep vs okt", df, {})
    assert r["intent"] == "compare" and r["periods"] == ["2026-09", "2026-10"]

def test_why_outlet(df):
    r = parse("kenapa OUT1014 turun?", df, {})
    assert r["intent"] == "why" and r["outlet_id"] == "OUT1014" and r["result"]["delta"] < 0

def test_why_without_outlet_offers_chips(df):
    r = parse("kenapa outlet ini lemah?", df, {})
    assert r["intent"] == "clarify" and len(r["chips"]) >= 3

def test_ambiguous_word_asks(df):
    r = parse("jawa", df, {})
    assert r["intent"] == "clarify" and {"Jawa Barat", "Jawa Timur", "Jawa Tengah"} <= {c["label"].replace("Tampilkan ", "").replace(" saja", "") for c in r["chips"]}

def test_send_intent_needs_confirmation(df):
    r = parse("kirim ke tim jatim", df, {})
    assert r["intent"] == "send" and r["filters"] == {"region": ["Jawa Timur"]} and r["needs_confirm"] is True

def test_reset(df):
    assert parse("reset", df, {"region": ["Jawa Barat"]})["filters"] == {}

def test_unknown_is_chips_not_error(df):
    r = parse("blabla xyz qwerty", df, {"brand": ["Sukro"]})
    assert r["intent"] == "unknown" and r["chips"] and r["filters"] == {"brand": ["Sukro"]} and "message" in r

def test_english_and_empty(df):
    assert parse("show jabar", df, {})["filters"] == {"region": ["Jawa Barat"]}
    assert parse("   ", df, {})["intent"] == "unknown"
