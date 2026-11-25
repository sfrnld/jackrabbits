import io, pytest
from PIL import Image
from app.ingest import read_table
from app.mapping import guess_mapping, apply_mapping
from app.findings import detect, apply_decisions, recommended
from app.actions import generate
from app.narrative import compose, summary_text, actions_text
from app.render import render_card
import datetime as dt

TODAY = dt.date(2026, 11, 25)

@pytest.fixture(scope="module")
def df():
    raw = read_table("data/sales.csv").df
    c = apply_mapping(raw, {k: v["column"] for k, v in guess_mapping(raw).items()})
    return apply_decisions(c, recommended(detect(c)))[0]

@pytest.fixture(scope="module")
def acts(df): return generate(df, today=TODAY)

def test_summary_follows_number_then_anomalies_then_action(df, acts):
    s = summary_text(df, {}, acts)
    assert "Oktober 2026" in s and "naik 3,6%" in s and "Rp 878,4 juta" in s
    assert s.index("Rp 878,4 juta") < s.index("Jawa Timur") < s.index("Minggu ini:")
    assert "92,4%" in s and "Grosir Lancar Jaya" in s and "13,9%" in s and "Grosir Sentosa" in s
    assert "\n" not in s                                      # one paragraph
    assert s == summary_text(df, {}, acts)                    # deterministic

def test_region_scope_only_talks_about_that_region(df, acts):
    s = summary_text(df, {"region": ["Jawa Barat"]}, acts)
    assert "Jawa Barat" in s and "turun 13,9%" in s and "Bandung" in s and "Jawa Timur" not in s
    assert "Minggu ini:" in s

def test_actions_text_is_scoped_numbered_and_dated(df, acts):
    allt = actions_text({}, acts); assert allt.startswith("Action items minggu ini") and "1. " in allt and "2 Des 2026" in allt and "PJ:" in allt
    jb = actions_text({"region": ["Jawa Barat"]}, acts)
    assert "Grosir Sentosa" in jb and "Grosir Lancar Jaya" not in jb
    assert "Belum ada" in actions_text({"region": ["Nowhere"]}, acts)

def test_card_png_is_1080x1350_and_uses_status_colours(df):
    png = render_card(df, {})
    im = Image.open(io.BytesIO(png)).convert("RGB"); assert im.size == (1080, 1350)
    px = list(im.getdata())
    near = lambda c, t: all(abs(a - b) < 40 for a, b in zip(c, t))
    assert any(near(p, (212, 24, 61)) for p in px[::7])       # --alert-red present (declines / weak outlets)
    assert any(near(p, (21, 128, 61)) for p in px[::7])       # --ok-green present (growth)
    assert sum(1 for p in px[::50] if p == (255, 255, 255)) > len(px[::50]) * 0.5   # mostly white paper
    r = Image.open(io.BytesIO(render_card(df, {"region": ["Jawa Barat"]}))); assert r.size == (1080, 1350)

def test_compose_bundles_everything(df, acts):
    c = compose(df, {"region": ["Jawa Timur"]}, acts)
    assert c["scope_label"] == "Jawa Timur" and len(c["caption"]) <= 1024 and c["png"][:8] == b"\x89PNG\r\n\x1a\n"
    assert "Jawa Timur" in c["summary"] and c["actions_text"]

def test_no_fake_decline_when_everything_grew(df, acts):
    s = summary_text(df, {"region": ["Jawa Timur"]}, acts)       # both Jawa Timur branches grew
    assert "turun" not in s.split("Minggu ini:")[0].split("dibanding September.")[1] and s.count("hampir semuanya") == 1

def test_owner_message_says_why_what_when_and_the_question(acts):
    from app.narrative import owner_text
    a = dict(acts[0]); a["owner"] = "Gita"; t = owner_text("Gita", [a])
    assert t.startswith("Halo Gita") and "Kenapa:" in t and "Yang perlu dilakukan:" in t and "Tenggat:" in t and "Yang perlu kamu jawab:" in t
    assert a["reason"] in t and a["action"] in t
