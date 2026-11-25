"""Data-quality findings: detect, let the user decide per finding, apply, summarize.
Nothing is changed silently: apply_decisions() only acts on explicit decisions."""
from __future__ import annotations
import difflib, re
import pandas as pd

ABBR = {"jabar": "jawa barat", "jateng": "jawa tengah", "jatim": "jawa timur", "dki": "dki jakarta",
        "sumut": "sumatera utara", "sumsel": "sumatera selatan", "sumbar": "sumatera barat",
        "kalsel": "kalimantan selatan", "kaltim": "kalimantan timur", "kalbar": "kalimantan barat",
        "diy": "di yogyakarta", "jogja": "di yogyakarta", "yogya": "di yogyakarta"}
UNKNOWN = "Tidak diketahui"
ORDER = ["required_empty", "duplicates", "returns", "region", "outlet_names", "salesman",
         "calc_mismatch", "date_range", "extreme"]

def _norm(s) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(s).lower())).strip()

def _key(s) -> str:
    n = _norm(s); return ABBR.get(n, n)

def _opt(id_, label, preview, rec=False):
    return {"id": id_, "label": label, "preview": preview, "recommended": rec}

def _ex(df, mask, n=5):
    cols = [c for c in ("src_row", "invoice", "date", "outlet_id", "outlet_name", "salesman", "qty", "net") if c in df]
    e = df.loc[mask, cols].head(n).copy()
    if "date" in e: e["date"] = e["date"].dt.strftime("%Y-%m-%d")
    return e.astype(object).where(e.notna(), None).to_dict("records")

def _inv(d, idx, role, hi=(), label=None, group=None, why=None, group_label=None) -> list[dict]:
    """Rows involved in a finding, for the spreadsheet-style table: src_row, role, highlighted roles, optional label/group/why."""
    out = []
    ev = lambda f, i: f(i) if callable(f) else f
    for i in idx:
        lab, w, gl = ev(label, i), ev(why, i), ev(group_label, i)
        out.append(dict(row=int(d.src_row[i]), role=role, hi=[h for h in hi if h in d.columns], label=None if lab is None else str(lab),
                        group=ev(group, i), why=w, group_label=gl))
    return out

def _why_name(n: str, canon: str) -> str:
    """Why does spelling n differ from the canonical spelling?"""
    if n == canon: return ""
    if n.strip() == canon:
        lead, tail = n != n.lstrip(), n != n.rstrip()
        return "spasi di awal dan akhir" if lead and tail else "spasi di awal" if lead else "spasi di akhir"
    if re.sub(r"\s+", " ", n).strip() == canon: return "spasi ganda"
    if n.lower() == canon.lower(): return "huruf besar/kecil beda"
    return "ejaan lain"

def _why_region(v: str, canon: str) -> str:
    if v.lower() == canon.lower(): return "huruf besar/kecil beda"
    return "singkatan" if _norm(v) in ABBR else "ejaan lain"

def _rp(x) -> int: return int(round(float(x)))

# ---------- detectors: each returns (finding, payload) or None ----------
def _d_required_empty(d):
    m = d.date.isna() | d.outlet_id.isna() | d.net.isna()
    if not m.any(): return None
    n = int(m.sum())
    return dict(id="required_empty", title="Kolom wajib kosong", rows=n, impact_rows=n, impact_rp=_rp(d.loc[m, "net"].sum()),
                examples=_ex(d, m), involved=[dict(r, hi=[c for c in ("date", "outlet_id", "net") if pd.isna(d.loc[i, c])]) for i, r in zip(d.index[m], _inv(d, d.index[m], "issue"))],
                recommended="exclude", options=[
        _opt("exclude", "Keluarkan baris ini", f"{len(d)} → {len(d) - n} baris", True),
        _opt("keep", "Biarkan", "Tidak ada perubahan")]), m

def _d_duplicates(d):
    cols = [c for c in d.columns if c != "src_row"]
    m = d.duplicated(cols, keep="first")
    if not m.any(): return None
    n = int(m.sum()); rp = _rp(d.loc[m, "net"].sum())
    obj = d[cols].astype(object); key = pd.Series(list(map(tuple, obj.where(obj.notna(), None).values)), index=d.index)   # identical in every compared column
    first = d.assign(_k=key)[~m].set_index("_k").src_row.to_dict()         # key -> row that is kept
    def side(r):
        o = {"row": int(r.src_row), "invoice": r.get("invoice"), "date": r.date.strftime("%Y-%m-%d"), "outlet_id": r.outlet_id,
             "outlet_name": r.get("outlet_name"), "brand": r.get("brand"), "sku": r.get("sku"), "qty": r.get("qty"), "net": r.net}
        return {k: (None if (v is pd.NA or v != v) else (v.item() if hasattr(v, "item") else v)) for k, v in o.items()}
    by_row = d.set_index("src_row", drop=False)
    pairs = [dict(keep=side(by_row.loc[first[key[i]]]), drop=side(d.loc[i])) for i in d.index[m]]
    involved = [dict(row=p[w]["row"], role=r, hi=[], label=None, group=g) for g, p in enumerate(pairs) for w, r in (("keep", "keep"), ("drop", "copy"))]
    return dict(id="duplicates", title="Baris duplikat persis", rows=n, impact_rows=n, impact_rp=rp, pairs=pairs, compared_columns=len(cols), involved=involved,
                examples=_ex(d, m), recommended="drop", options=[
        _opt("drop", "Hapus duplikat", f"{len(d)} → {len(d) - n} baris · net −Rp {rp:,}".replace(",", "."), True),
        _opt("keep", "Simpan semua", "Tidak ada perubahan"),
        _opt("flag", "Tandai saja", f"{n} baris ditandai, angka tidak berubah")]), m

def _d_returns(d):
    m = (d.get("qty", pd.Series(0, index=d.index)) < 0) | (d.net < 0)
    if not m.any(): return None
    n = int(m.sum()); rp = _rp(d.loc[m, "net"].sum())
    return dict(id="returns", title="Retur (qty negatif)", rows=n, impact_rows=n, impact_rp=rp,
                examples=_ex(d, m), involved=_inv(d, d.index[m], "return", ("qty", "net")), recommended="deduct", options=[
        _opt("deduct", "Kurangi dari penjualan", f"Net tetap menyertakan Rp {rp:,}".replace(",", "."), True),
        _opt("separate", "Pisahkan sebagai metrik retur", "Net naik, retur dihitung terpisah"),
        _opt("exclude", "Keluarkan dari analisis", f"{len(d)} → {len(d) - n} baris")]), m

def _d_region(d):
    if "region" not in d: return None
    vc = d.region.dropna().value_counts()
    vals = list(vc.index)
    parent = {v: v for v in vals}
    def find(x):
        while parent[x] != x: x = parent[x]
        return x
    for i, a in enumerate(vals):
        for b in vals[i + 1:]:
            ka, kb = _key(a), _key(b)
            if ka == kb or difflib.SequenceMatcher(None, ka, kb).ratio() >= 0.88:
                parent[find(b)] = find(a)
    clusters: dict[str, list[str]] = {}
    for v in vals: clusters.setdefault(find(v), []).append(v)
    branches: dict[str, set] = {}
    if "branch" in d:
        for r, b in d[["region", "branch"]].dropna().itertuples(index=False): branches.setdefault(str(r), set()).add(str(b))
    groups = []
    for members in clusters.values():
        if len(members) < 2: continue
        # canonical = most frequent; ties prefer not-all-caps
        canon = sorted(members, key=lambda v: (-vc[v], v.isupper(), v))[0]
        variants = [v for v in members if v != canon
                    and (not branches or branches.get(v, set()) <= branches.get(canon, set()))]  # branch cross-check
        if not variants: continue
        groups.append(dict(canonical=canon, variants=variants, counts={v: int(vc[v]) for v in variants},
                           canonical_rows=int(vc[canon]), rows=int(sum(vc[v] for v in variants))))
    if not groups: return None
    n = sum(g["rows"] for g in groups)
    allv = [v for g in groups for v in g["variants"]]
    m = d.region.isin(allv)
    regions_after = d.region.nunique() - len(allv)
    to = {v: g["canonical"] for g in groups for v in g["variants"]}
    involved = []
    for gi, g in enumerate(groups):
        ref = d.index[d.region == g["canonical"]][:1]
        gl = f"{g['canonical']} · ejaan baku ({g['canonical_rows']} baris) dan variannya"
        involved += _inv(d, ref, "reference", ("region",), label=g["canonical"], group=gi, group_label=gl)
        involved += _inv(d, d.index[d.region.isin(g["variants"])], "variant", ("region",), label=g["canonical"], group=gi,
                         why=lambda i, g=g: _why_region(d.region[i], g["canonical"]), group_label=gl)
    prev = " · ".join(f"{g['canonical']}: {g['canonical_rows']} → {g['canonical_rows'] + g['rows']} baris" for g in groups)
    return dict(id="region", title="Nama region mirip", rows=n, impact_rows=n, impact_rp=_rp(d.loc[m, "net"].sum()),
                groups=groups, examples=_ex(d, m), involved=involved, pin=["branch"], recommended="merge_all", options=[
        _opt("merge_all", "Gabungkan semua ke nama baku", prev, True),
        _opt("merge_groups", "Gabungkan per grup", "Pilih grup yang digabung (params.groups)"),
        _opt("rename", "Ganti nama manual", "Pemetaan nama sendiri (params.map)"),
        _opt("keep", "Biarkan terpisah", f"{d.region.nunique()} region tetap")]), (groups, regions_after)

def _d_outlet_names(d):
    if "outlet_name" not in d: return None
    g = d.dropna(subset=["outlet_id", "outlet_name"]).groupby("outlet_id").outlet_name
    groups, involved, bad = [], [], pd.Series(False, index=d.index)
    for oid, names in g:
        if names.nunique() < 2: continue
        clean = names.map(lambda s: re.sub(r"\s+", " ", s).strip())
        canon = clean.value_counts().index[0]
        counts = names.value_counts()
        spell = [dict(text=n, rows=int(counts[n]), issue=_why_name(n, canon) or None) for n in counts.index]
        groups.append(dict(outlet_id=oid, canonical=canon, variants=sorted(set(names) - {canon}), spellings=spell))
        mask = (d.outlet_id == oid) & (d.outlet_name != canon); bad |= mask
        gi = len(groups) - 1; gl = f"{oid} · ejaan baku “{canon}”"
        involved += _inv(d, d.index[(d.outlet_id == oid) & (d.outlet_name == canon)][:1], "reference", ("outlet_name",), label=canon, group=gi, group_label=gl)
        involved += _inv(d, d.index[mask], "variant", ("outlet_name",), label=canon, group=gi, why=lambda i, c=canon: _why_name(d.outlet_name[i], c), group_label=gl)
    if not groups: return None
    return dict(id="outlet_names", title="Satu outlet ID, beberapa ejaan nama", rows=len(groups), impact_rows=int(bad.sum()),
                impact_rp=0, groups=groups, examples=_ex(d, bad), involved=involved, pin=["outlet_id"], recommended="unify", options=[
        _opt("unify", "Satukan berdasarkan outlet ID", f"{len(groups)} outlet dirapikan, {int(bad.sum())} baris", True),
        _opt("keep", "Biarkan apa adanya", "Tidak ada perubahan")]), {x["outlet_id"]: x["canonical"] for x in groups}

def _dominant(d):
    """Per outlet: salesman with most rows (ties -> most net, then name)."""
    s = d.dropna(subset=["salesman"]).groupby(["outlet_id", "salesman"]).agg(n=("net", "size"), v=("net", "sum")).reset_index()
    s = s.sort_values(["outlet_id", "n", "v", "salesman"], ascending=[True, False, False, True])
    return s.drop_duplicates("outlet_id").set_index("outlet_id").salesman.to_dict()

def _d_salesman(d):
    if "salesman" not in d: return None
    m = d.salesman.isna() | (d.salesman.str.strip() == "")
    if not m.any(): return None
    n = int(m.sum()); dom = _dominant(d)
    ex = _ex(d, m)
    for e in ex: e["guess"] = dom.get(e["outlet_id"])
    return dict(id="salesman", title="Salesman kosong", rows=n, impact_rows=n, impact_rp=_rp(d.loc[m, "net"].sum()),
                examples=ex, involved=_inv(d, d.index[m], "missing", ("salesman",)), recommended="label", options=[
        _opt("label", f"Label “{UNKNOWN}”", f"{n} baris diberi label", True),
        _opt("fill_dominant", "Isi dengan salesman dominan outlet (prediksi)", "Ditandai sebagai prediksi: " + ", ".join(sorted({str(e['guess']) for e in ex if e['guess']}))),
        _opt("keep", "Biarkan kosong", "Tidak ada perubahan")]), (m, dom)

def _generic(id_, title, d, m, label_flag="Tandai saja", hi=()):
    if not m.any(): return None
    n = int(m.sum())
    return dict(id=id_, title=title, rows=n, impact_rows=n, impact_rp=_rp(d.loc[m, "net"].sum()), examples=_ex(d, m),
                involved=_inv(d, d.index[m], "issue", hi), recommended="flag", options=[
        _opt("flag", label_flag, f"{n} baris ditandai, angka tidak berubah", True),
        _opt("exclude", "Keluarkan dari analisis", f"{len(d)} → {len(d) - n} baris"),
        _opt("keep", "Biarkan", "Tidak ada perubahan")]), m

def _d_calc(d):
    m = pd.Series(False, index=d.index)
    if {"qty", "price", "gross"} <= set(d): m |= ((d.qty * d.price - d.gross).abs() > 1).fillna(False)
    if {"gross", "discount", "net"} <= set(d): m |= ((d.gross - d.discount - d.net).abs() > 1).fillna(False)
    return _generic("calc_mismatch", "Total tidak cocok (qty × harga ≠ bruto)", d, m, hi=("qty", "price", "gross", "discount", "net"))

def _d_date(d):
    ok = d.date.dropna()
    if ok.empty: return None
    med = ok.median(); m = d.date.isna() | ((d.date - med).abs() > pd.Timedelta(days=366))
    return _generic("date_range", "Tanggal di luar rentang", d, m.fillna(True), hi=("date",))

def _d_extreme(d):
    m = pd.Series(False, index=d.index)
    for _, g in (d.groupby("outlet_type") if "outlet_type" in d else [(None, d)]):
        if len(g) < 20: continue
        q1, q3 = g.net.quantile([.25, .75]); m.loc[g.index] = g.net > q3 + 6 * (q3 - q1)
    return _generic("extreme", "Nilai ekstrem", d, m, hi=("net",))

_DETECTORS = dict(required_empty=_d_required_empty, duplicates=_d_duplicates, returns=_d_returns, region=_d_region,
                  outlet_names=_d_outlet_names, salesman=_d_salesman, calc_mismatch=_d_calc, date_range=_d_date, extreme=_d_extreme)

def _run(d):
    out = {}
    for fid in ORDER:
        r = _DETECTORS[fid](d)
        if r: out[fid] = r
    return out

def detect(canon: pd.DataFrame) -> list[dict]:
    return [f for f, _ in _run(canon).values()]

def recommended(findings: list[dict]) -> dict:
    return {f["id"]: {"option": f["recommended"]} for f in findings}

# ---------- apply ----------
def apply_decisions(canon: pd.DataFrame, decisions: dict):
    found = _run(canon)
    d = canon.copy(); trail = []
    drop = pd.Series(False, index=d.index)
    def log(fid, opt, label, changed, **kw):
        trail.append(dict(finding=fid, title=found[fid][0]["title"], option=opt, label=label, rows_changed=int(changed), **kw))
    for fid in ORDER:
        if fid not in found or fid not in decisions: continue
        f, pay = found[fid]; dec = decisions[fid]; opt = dec["option"]; params = dec.get("params") or {}
        label = next((o["label"] for o in f["options"] if o["id"] == opt), opt)
        if opt == "keep": log(fid, opt, label, 0); continue
        if fid in ("required_empty", "duplicates", "returns", "calc_mismatch", "date_range", "extreme"):
            m = pay
            if opt in ("exclude", "drop"): drop |= m; log(fid, opt, label, m.sum())
            elif opt == "flag":
                d[{"duplicates": "dq_duplicate"}.get(fid, f"dq_{fid}")] = m; log(fid, opt, label, m.sum())
            elif opt == "separate":
                d["return_amt"] = (-d.net).where(m, 0.0); d.loc[m, "net"] = 0.0; log(fid, opt, label, m.sum())
            elif opt == "deduct": log(fid, opt, label, 0)
        elif fid == "region":
            groups, _ = pay
            if opt == "merge_all": mp = {v: g["canonical"] for g in groups for v in g["variants"]}
            elif opt == "merge_groups":
                sel = set(params.get("groups", [])); mp = {v: g["canonical"] for g in groups if g["canonical"] in sel for v in g["variants"]}
            elif opt == "rename": mp = dict(params.get("map", {}))
            else: mp = {}
            ch = d.region.isin(list(mp)); d["region"] = d.region.replace(mp); log(fid, opt, label, ch.sum(), mapping=mp)
        elif fid == "outlet_names":
            ch = d.outlet_id.map(pay).fillna(d.outlet_name) != d.outlet_name
            d["outlet_name"] = d.outlet_id.map(pay).fillna(d.outlet_name).str.replace(r"\s+", " ", regex=True).str.strip()
            log(fid, opt, label, ch.sum())
        elif fid == "salesman":
            m, dom = pay
            if opt == "label": d.loc[m, "salesman"] = UNKNOWN
            elif opt == "fill_dominant":
                guess = d.outlet_id.map(dom); d["salesman_guess"] = m & guess.notna()
                d.loc[m, "salesman"] = guess[m].fillna(UNKNOWN)
            log(fid, opt, label, m.sum())
    d = d[~drop].copy()
    d.attrs["available"] = canon.attrs.get("available", [])
    return d, trail

def summarize(before: pd.DataFrame, after: pd.DataFrame) -> dict:
    def s(x): return dict(rows=len(x), net=_rp(x.net.sum()), regions=int(x.region.nunique()) if "region" in x else 0,
                          outlets=int(x.outlet_id.nunique()))
    return dict(before=s(before), after=s(after))
