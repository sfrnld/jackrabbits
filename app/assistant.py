"""Rule-based assistant: keywords -> actions. No LLM, so every answer is deterministic and numerically correct.
parse(text, df, current_filters) never raises; unknown input yields suggestion chips, not an error."""
from __future__ import annotations
import difflib, re
from .analytics import options, query, strongest, weakest, outlet_scores, prep, _reasons
from .findings import ABBR, _norm
from .fmt import month_label, pct, rp

FILTER_DIMS = ["region", "branch", "brand", "outlet_type", "salesman", "sku", "month"]
DIM_LABEL = dict(region="Region", branch="Cabang", brand="Brand", outlet_type="Tipe outlet", salesman="Salesman", sku="SKU", month="Bulan")
MONTH_ALIASES = {1: "januari january jan", 2: "februari february feb", 3: "maret march mar", 4: "april apr", 5: "mei may",
                 6: "juni june jun", 7: "juli july jul", 8: "agustus august agu agt aug", 9: "september sep sept",
                 10: "oktober october okt oct", 11: "november nov", 12: "desember december des dec"}
SHORT = "Jan Feb Mar Apr Mei Jun Jul Agu Sep Okt Nov Des".split()
INTENT_WORDS = {
    "reset": {"reset", "clear"}, "send": {"kirim", "send", "bagikan", "share"}, "why": {"kenapa", "mengapa", "why", "penyebab"},
    "compare": {"bandingkan", "banding", "compare", "vs", "versus", "dibanding", "dibandingkan"},
    "weakest": {"terlemah", "lemah", "weakest", "worst", "terburuk"}, "top": {"top", "teratas", "terbesar", "terbaik", "best", "biggest"}}
FILLER = {"tampilkan", "tampil", "saja", "show", "only", "filter", "brand", "region", "wilayah", "bulan", "tipe", "cabang", "di", "ke", "dan",
          "yang", "dari", "untuk", "pasang", "lihat", "data", "tim", "team", "outlet", "ini", "itu", "turun", "naik", "salesman", "the", "in", "of", "for", "hapus", "semua", "sku"}
SKIP = FILLER | {w for s in INTENT_WORDS.values() for w in s}

def _chip(text, label=None): return dict(label=label or text, text=text)

def _vocab(df):
    o = options(df); cands = []
    months = o.get("month", [])
    for dim in FILTER_DIMS:
        if dim == "month":
            for ym in months:
                for alias in MONTH_ALIASES[int(ym[5:])].split(): cands.append((dim, ym, [alias]))
            continue
        for v in o.get(dim, []):
            cands.append((dim, v, _norm(v).split()))
            if dim == "region":
                cands += [(dim, v, [k]) for k, exp in ABBR.items() if exp == _norm(v)]
    return [c for c in cands if c[2]]

def _find(toks, phrase, used):
    n = len(phrase)
    for i in range(len(toks) - n + 1):
        if toks[i:i + n] == phrase and not any(j in used for j in range(i, i + n)): return i
    return None

def _match(text, df):
    toks = _norm(text).split(); used: set[int] = set(); hits = []; ambiguous = {}
    cands = _vocab(df)
    for dim, val, ph in sorted(cands, key=lambda c: -len(c[2])):
        i = _find(toks, ph, used)
        if i is not None: used.update(range(i, i + len(ph))); hits.append(dict(dim=dim, value=val, pos=i))
    for i, t in enumerate(toks):
        if i in used or t in SKIP or len(t) < 4 or t.isdigit() or re.fullmatch(r"out\d+", t): continue
        pref = {(d, v) for d, v, ph in cands if len(ph) > 1 and ph[0] == t}
        if len(pref) == 1: d, v = next(iter(pref)); hits.append(dict(dim=d, value=v, pos=i)); used.add(i); continue
        if len(pref) > 1: ambiguous[t] = sorted(pref); used.add(i); continue
        singles = {ph[0]: (d, v) for d, v, ph in cands if len(ph) == 1 and d != "month"}
        m = difflib.get_close_matches(t, list(singles), n=1, cutoff=0.84)
        if m: d, v = singles[m[0]]; hits.append(dict(dim=d, value=v, pos=i)); used.add(i)
    leftover = [t for i, t in enumerate(toks) if i not in used and t not in SKIP and not t.isdigit()]
    return toks, sorted(hits, key=lambda h: h["pos"]), ambiguous, leftover

def _label(dim, v): return month_label(v) if dim == "month" else v

def suggest(df, filters) -> list[dict]:
    o = options(df); ms = o.get("month", []); chips = []
    if len(ms) >= 2: chips.append(_chip(f"Bandingkan {SHORT[int(ms[0][5:]) - 1]} vs {SHORT[int(ms[-1][5:]) - 1]}"))
    reg = (filters.get("region") or [None])[0]
    chips.append(_chip(f"5 outlet terlemah" + (f" di {reg}" if reg else "")))
    chips.append(_chip("Top 10 outlet"))
    if reg: chips.append(_chip(f"Kirim ke tim {reg}"))
    elif o.get("region"):
        d = prep(df); top = d.groupby("region").net.sum().idxmax(); chips.append(_chip(f"Tampilkan {top} saja"))
    if filters: chips.append(_chip("Reset filter"))
    return chips[:4]

def _num(toks, default):
    return next((int(t) for t in toks if t.isdigit() and 0 < int(t) <= 100), default)

def _out(intent, message, filters, previous, df, **kw):
    return dict(intent=intent, message=message, filters=filters, previous=previous, undo=filters != previous,
                chips=kw.pop("chips", None) or suggest(df, filters), **kw)

def parse(text: str, df, current: dict | None = None) -> dict:
    current = {k: list(v) for k, v in (current or {}).items()}
    try:
        return _parse(text or "", df, current)
    except Exception as e:                                   # never surface a stack trace to a sales manager
        return _out("unknown", "Maaf, aku belum bisa memproses itu. Coba salah satu saran di bawah.", current, current, df, error=str(e))

def _parse(text, df, current):
    toks, hits, amb, leftover = _match(text, df); tset = set(toks)
    def has(k): return bool(tset & INTENT_WORDS[k]) or (k == "reset" and "hapus" in tset and "filter" in tset)
    new = {}
    for h in hits: new.setdefault(h["dim"], []).append(h["value"])
    def with_new(skip=()):
        m = {k: list(v) for k, v in current.items()}
        for d, vals in new.items():
            if d not in skip: m[d] = vals
        return m
    if not toks: return _out("unknown", "Tulis perintah singkat, misalnya “jabar” atau “top 10 outlet”.", current, current, df)
    if has("reset"): return _out("filter", "Semua filter dihapus.", {}, current, df)
    if amb:
        t, vals = next(iter(amb.items()))
        chips = [_chip(f"Tampilkan {v} saja") for _, v in vals][:6]
        return _out("clarify", f"“{t}” bisa berarti beberapa hal. Maksudnya yang mana?", current, current, df, chips=chips)
    if has("send"):
        f = with_new(skip=("month",))
        who = ", ".join(f"{_label(d, v)}" for d, vs in f.items() for v in vs if d == "region") or "semua penerima"
        return _out("send", f"Aku siapkan laporan untuk {who}. Cek pratinjau di langkah Bagikan, lalu konfirmasi pengiriman.", f, current, df, needs_confirm=True)
    if has("why"):
        d = prep(df); oid = next((t for t in toks if re.fullmatch(r"out\d+", t)), None)
        names = d.drop_duplicates("outlet_id").set_index("outlet_id").outlet_name.astype(str)
        if oid: oid = next((i for i in names.index if str(i).lower() == oid), None)
        if not oid:
            nm = _norm(text)
            oid = next((i for i, n in names.items() if _norm(n) in nm), None)
        if not oid:
            chips = [_chip(f"Kenapa {w['outlet_id']} lemah?", f"Kenapa {w['name']} lemah?") for w in weakest(df, with_new(), 5)]
            return _out("clarify", "Outlet mana yang ingin kamu lihat? Sebut nama atau kodenya, atau pilih:", current, current, df, chips=chips)
        f = with_new(); s = outlet_scores(df, {}); r = s.loc[oid]
        a, b = r._prev, r._last
        res = dict(outlet_id=oid, name=r["name"], type=r["type"], a=float(r.prev_m), b=float(r.last_m), delta=float(r.last_m - r.prev_m),
                   pct=None if not r.prev_m else float((r.last_m - r.prev_m) / r.prev_m * 100), periods=[a, b], score=float(r.score), reasons=_reasons(r))
        dirn = "turun" if res["delta"] < 0 else "naik"
        msg = f"{r['name']} {dirn} {pct(res['pct']) if res['pct'] is not None else ''} ({rp(res['delta'])}): {month_label(a)} {rp(res['a'])} → {month_label(b)} {rp(res['b'])}."
        return _out("why", msg.replace("  ", " "), current, current, df, outlet_id=oid, result=res)
    if has("compare"):
        ms = [h["value"] for h in hits if h["dim"] == "month"]; allm = options(df).get("month", [])
        per = (ms[:2] if len(ms) >= 2 else ([allm[0], allm[-1]] if len(allm) >= 2 else None))
        if not per: return _out("unknown", "Data hanya punya satu bulan, jadi belum bisa dibandingkan.", current, current, df)
        f = with_new(skip=("month",)); f.pop("month", None)
        gb = "branch" if f.get("region") else "region"
        res = query(df, f, group_by=gb, compare=per)
        t = res["total"]
        return _out("compare", f"Membandingkan {month_label(per[0])} dengan {month_label(per[1])}: total {'naik' if t['delta'] >= 0 else 'turun'} {pct(t['pct']) if t['pct'] is not None else '-'} ({rp(t['delta'])}).",
                    f, current, df, periods=per, group_by=gb, result=res)
    if has("weakest") or has("top"):
        f = with_new(); n = _num(toks, 5 if has("weakest") else 10)
        scope = (" di " + ", ".join(_label(d, v) for d, vs in f.items() for v in vs)) if f else ""
        if has("weakest"):
            return _out("weakest", f"Ini {n} outlet terlemah dibanding sesama tipenya{scope}.", f, current, df, n=n, result=weakest(df, f, n))
        return _out("top", f"Ini {n} outlet teratas berdasarkan net sales{scope}.", f, current, df, n=n, result=strongest(df, f, n))
    if new:
        f = with_new()
        desc = ", ".join(f"{DIM_LABEL[d]} = {', '.join(_label(d, v) for v in vs)}" for d, vs in new.items())
        return _out("filter", f"Aku pasang filter {desc}.", f, current, df)
    return _out("unknown", f"Aku belum paham “{text.strip()}”. Coba salah satu ini:", current, current, df)
