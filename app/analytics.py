"""Slice-and-dice engine, period comparison, drivers, outlet score, proactive insights.
Pure functions over the cleaned canonical DataFrame: every number is deterministic."""
from __future__ import annotations
import pandas as pd
from .fmt import pct, rp

DIMS = ["region", "branch", "brand", "sku", "outlet_type", "salesman", "outlet_id", "outlet_name", "invoice", "month", "week", "day"]
METRICS = ["net", "gross", "qty", "invoices", "discount", "discount_ratio"]
DRILL = ["region", "branch", "outlet_id", "invoice"]

def prep(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["month"] = d.date.dt.strftime("%Y-%m")
    d["week"] = (d.date - pd.to_timedelta(d.date.dt.weekday, unit="D")).dt.strftime("%Y-%m-%d")
    d["day"] = d.date.dt.strftime("%Y-%m-%d")
    return d

def available_dims(df): return [c for c in DIMS if c in prep(df.head(1)).columns]

def apply_filters(d: pd.DataFrame, filters: dict | None) -> pd.DataFrame:
    for k, v in (filters or {}).items():
        if k == "date_from": d = d[d.date >= pd.Timestamp(v)]
        elif k == "date_to": d = d[d.date <= pd.Timestamp(v)]
        elif k in d.columns: d = d[d[k].astype(str).isin([str(x) for x in v])]
        else: raise ValueError(f"Dimensi tidak tersedia: {k}")
    return d

def _period(d, p: str):
    if ".." in p:
        a, b = p.split(".."); return d[(d.date >= pd.Timestamp(a)) & (d.date <= pd.Timestamp(b))]
    return d[d.month == p]

def _val(d, metric, by=None):
    if metric not in METRICS: raise ValueError(f"Metrik tidak dikenal: {metric}")
    if metric == "invoices":
        return d.groupby(by, dropna=False).invoice.nunique() if by else d.invoice.nunique()
    if metric == "discount_ratio":
        if by:
            g = d.groupby(by, dropna=False)[["discount", "gross"]].sum(); return g.discount / g.gross
        return d.discount.sum() / d.gross.sum() if d.gross.sum() else 0.0
    col = {"net": "net", "gross": "gross", "qty": "qty", "discount": "discount"}[metric]
    if col not in d.columns: raise ValueError(f"Kolom tidak tersedia: {col}")
    return d.groupby(by, dropna=False)[col].sum() if by else d[col].sum()

def _f(x): return None if pd.isna(x) else float(x)
def _pct(a, b): return None if not a else (b - a) / abs(a) * 100

def query(df, filters=None, group_by=None, metric="net", compare=None, top=None, ascending=False):
    d = prep(df)
    if group_by and group_by not in d.columns: raise ValueError(f"Dimensi tidak tersedia: {group_by}")
    if compare:
        f = {k: v for k, v in (filters or {}).items() if k != "month"}
        base = apply_filters(d, f)
        a, b = (_val(_period(base, p), metric, group_by) for p in compare)
        if group_by:
            t = pd.DataFrame({"a": a, "b": b}).fillna(0.0)
            t["delta"] = t.b - t.a
            rows = [dict(key=str(k), a=float(r.a), b=float(r.b), delta=float(r.delta), pct=_pct(r.a, r.b)) for k, r in t.iterrows()]
            rows.sort(key=lambda r: r["delta"], reverse=not ascending)
        else: rows = []
        ta, tb = (float(_val(_period(base, p), metric)) for p in compare)
        total = dict(a=ta, b=tb, delta=tb - ta, pct=_pct(ta, tb))
        return dict(metric=metric, group_by=group_by, compare=list(compare), rows=rows[:top] if top else rows, total=total)
    d = apply_filters(d, filters)
    if not group_by:
        return dict(metric=metric, group_by=None, rows=[], total=_f(_val(d, metric)) if len(d) else 0.0)
    s = _val(d, metric, group_by).sort_values(ascending=ascending)
    if top: s = s.head(top)
    return dict(metric=metric, group_by=group_by, rows=[dict(key=str(k), value=float(v)) for k, v in s.items()],
                total=_f(_val(d, metric)) if len(d) else 0.0, next_dim=_next(group_by))

def _next(dim):
    return DRILL[DRILL.index(dim) + 1] if dim in DRILL[:-1] else None

def _names(d):
    return d.drop_duplicates("outlet_id").set_index("outlet_id").outlet_name.astype(str).to_dict()

def drivers(df, group_dim, key, a, b, filters=None, child_dim="outlet_id", top=3):
    d = apply_filters(prep(df), {k: v for k, v in (filters or {}).items() if k != "month"})
    d = d[d[group_dim].astype(str) == key]
    ca, cb = (_period(d, p).groupby(child_dim).net.sum() for p in (a, b))
    t = pd.DataFrame({"a": ca, "b": cb}).fillna(0.0); t["delta"] = t.b - t.a
    total = float(t.delta.sum()); names = _names(d); out = []
    for k, r in t.reindex(t.delta.abs().sort_values(ascending=False).index).head(top).iterrows():
        same = (r.delta > 0) == (total > 0)
        out.append(dict(key=str(k), name=names.get(k, str(k)), a=float(r.a), b=float(r.b), delta=float(r.delta),
                        share=float(r.delta / total) if total else None,
                        exceeds_total=bool(same and abs(r.delta) > abs(total))))
    return out

# ---------------- outlet score (relative to outlet type) ----------------
W = dict(value=0.35, trend=0.30, freq=0.20, recency=0.15)

def outlet_scores(df, filters=None) -> pd.DataFrame:
    d = apply_filters(prep(df), filters)
    months = sorted(d.month.unique()); last, prev = months[-1], (months[-2] if len(months) > 1 else None)
    end = d.date.max()
    g = d.groupby("outlet_id")
    o = pd.DataFrame({"name": g.outlet_name.first().astype(str), "type": g.outlet_type.first().astype(str) if "outlet_type" in d else "Semua",
                      "region": g.region.first().astype(str) if "region" in d else "", "branch": g.branch.first().astype(str) if "branch" in d else "",
                      "total": g.net.sum(), "invoices": g.invoice.nunique(), "last_date": g.date.max()})
    o["last_m"] = d[d.month == last].groupby("outlet_id").net.sum().reindex(o.index).fillna(0.0)
    o["prev_m"] = d[d.month == prev].groupby("outlet_id").net.sum().reindex(o.index).fillna(0.0) if prev else float("nan")
    o["trend"] = ((o.last_m - o.prev_m) / o.prev_m.where(o.prev_m > 0)) if prev else float("nan")
    o["days"] = (end - o.last_date).dt.days
    if "salesman" in d:
        sm = d[d.salesman.notna() & (d.salesman != "Tidak diketahui")].groupby("outlet_id").salesman.agg(lambda s: s.value_counts().index[0])
        o["salesman"] = sm.reindex(o.index)
    size = o.groupby("type").type.transform("size")
    def rank(col, sign=1):
        within = (sign * o[col]).groupby(o.type).rank(pct=True)
        overall = (sign * o[col]).rank(pct=True)
        return within.where(size >= 3, overall)
    o["c_value"], o["c_trend"], o["c_freq"], o["c_recency"] = rank("total"), rank("trend").fillna(0.5), rank("invoices"), rank("days", -1)
    o["score"] = (100 * (W["value"] * o.c_value + W["trend"] * o.c_trend + W["freq"] * o.c_freq + W["recency"] * o.c_recency)).round(1)
    o["_peers"] = o.groupby("type").total.transform("mean"); o["_peer_inv"] = o.groupby("type").invoices.transform("mean")
    o["_last"], o["_prev"] = last, prev
    return o.sort_values(["score", "total"])

def _reasons(r) -> list[dict]:
    out = []
    if r.c_value <= 0.25: out.append(dict(kind="value", text=f"Total {rp(r.total)} termasuk yang terendah di antara {r.type} (rata-rata {rp(r._peers)})"))
    if r.c_trend <= 0.25 and r.trend == r.trend: out.append(dict(kind="trend", text=f"{'Turun' if r.trend < 0 else 'Naik'} {pct(r.trend * 100)} dibanding bulan lalu ({rp(r.prev_m)} → {rp(r.last_m)})"))
    if r.c_freq <= 0.25: out.append(dict(kind="frequency", text=f"Hanya {int(r.invoices)} invoice (rata-rata {r.type}: {r._peer_inv:.0f})"))
    if r.c_recency <= 0.25: out.append(dict(kind="recency", text=f"Terakhir beli {int(r.days)} hari lalu"))
    if not out:
        k = min(("value", r.c_value), ("trend", r.c_trend), ("frequency", r.c_freq), ("recency", r.c_recency), key=lambda x: x[1])[0]
        lab = dict(value="nilai penjualan", trend="tren", frequency="frekuensi pesanan", recency="kebaruan pesanan")[k]
        out.append(dict(kind=k, text=f"Nilai terendahnya ada di {lab} dibanding sesama {r.type}"))
    return out

def _row(oid, r):
    return dict(outlet_id=oid, name=r["name"], type=r["type"], region=r["region"], branch=r["branch"],
                salesman=(None if pd.isna(r.get("salesman")) else r.get("salesman")), total=float(r.total), score=float(r.score),
                invoices=int(r.invoices), days_since=int(r.days), trend=None if pd.isna(r.trend) else float(r.trend),
                components={"value": float(r.c_value), "trend": float(r.c_trend), "frequency": float(r.c_freq), "recency": float(r.c_recency)},
                reasons=_reasons(r))

def weakest(df, filters=None, n=5):
    s = outlet_scores(df, filters)
    return [_row(i, r) for i, r in s.head(n).iterrows()]

def strongest(df, filters=None, n=10):
    d = apply_filters(prep(df), filters); s = outlet_scores(df, filters)
    top = d.groupby("outlet_id").net.sum().nlargest(n).index
    return [_row(i, s.loc[i]) for i in top]

# ---------------- proactive insights ----------------
def options(df) -> dict:
    d = prep(df); out = {c: sorted(d[c].dropna().astype(str).unique()) for c in DIMS if c in d.columns and c not in ("invoice", "day", "week", "outlet_name")}
    out["month"] = sorted(d.month.unique()); return out

def insights(df, filters=None, limit=3) -> list[dict]:
    d = apply_filters(prep(df), {k: v for k, v in (filters or {}).items() if k != "month"})
    months = sorted(d.month.unique())
    if len(months) < 2 or d.empty: return []
    a, b = months[-2], months[-1]
    regs = d.region.nunique() if "region" in d else 0
    level, child = ("region", "outlet_id") if regs > 1 else (("branch", "outlet_id") if "branch" in d and d.branch.nunique() > 1 else (None, None))
    out = []
    if level:
        t = query(d, group_by=level, compare=[a, b])["rows"]
        up_, dn_ = max(t, key=lambda r: r["delta"]), min(t, key=lambda r: r["delta"])
        picks = [r for r in (up_, dn_) if (r is up_ and r["delta"] > 0) or (r is dn_ and r["delta"] < 0)]   # a "decliner" must really decline
        for r in picks:
            if any(o["entity"] == r["key"] for o in out): continue
            up = r["delta"] > 0
            dr = drivers(d, level, r["key"], a, b, child_dim=child, top=1)
            head = f"{r['key']} {'naik' if up else 'turun'} {pct(r['pct']) if r['pct'] is not None else ''} ({'+' if up else ''}{rp(r['delta'])})".replace("  ", " ")
            if dr and dr[0]["share"] is not None and (dr[0]["exceeds_total"] or abs(dr[0]["share"]) >= 0.6):
                x = dr[0]; extra = ", lebih besar dari total perubahan" if x["exceeds_total"] else ""
                lead = "hampir semuanya dari satu outlet" if (up and not x["exceeds_total"]) else "terutama karena"
                head += f", {lead}: {x['name']} ({'+' if x['delta'] > 0 else ''}{rp(x['delta'])}{extra})" if lead.startswith("hampir") \
                    else f", {lead} {x['name']} ({'+' if x['delta'] > 0 else ''}{rp(x['delta'])}{extra})"
            out.append(dict(kind="mover", entity=r["key"], delta=r["delta"], pct=r["pct"], text=head + "."))
    w = weakest(d, n=2)
    if w:
        out.append(dict(kind="weakest", entity=w[0]["outlet_id"], text=f"Outlet paling lemah dibanding sesama tipenya: {w[0]['name']} ({w[0]['branch']}, skor {w[0]['score']:.0f}) — {w[0]['reasons'][0]['text'][0].lower() + w[0]['reasons'][0]['text'][1:]}."))
    return out[:limit]

def series(df, filters=None, split_by="brand", x="week", metric="net"):
    d = apply_filters(prep(df), filters)
    for c in (split_by, x):
        if c not in d.columns: raise ValueError(f"Dimensi tidak tersedia: {c}")
    v = _val(d, metric, [x, split_by]).unstack(split_by).fillna(0.0).sort_index()
    out = [dict(key=str(k), values=[float(i) for i in v[k]], total=float(v[k].sum())) for k in v.columns]
    return dict(x=[str(i) for i in v.index], series=sorted(out, key=lambda r: -r["total"]), metric=metric)

def outlet_rows(df, filters=None):
    return [_row(i, r) for i, r in outlet_scores(df, filters).iterrows()]
