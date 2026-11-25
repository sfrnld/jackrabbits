"""Report card PNG (1080x1350 portrait, readable on a phone). Colours come from web/src/tokens.css
so the card matches the app. Rendered offline with matplotlib."""
from __future__ import annotations
import io, re, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from . import settings
from .analytics import query, weakest
from .fmt import month_label, pct, rp as _rp
from .narrative import scope_label

def tokens() -> dict:
    d = dict(ink="#0A0A0A", paper="#FFFFFF", grey200="#E4E4E7", grey400="#A1A1AA", grey600="#52525B", red="#D4183D", green="#15803D")
    f = settings.ROOT / "web" / "src" / "tokens.css"
    if f.exists():
        css = f.read_text()
        for k, v in {"ink": "--ink", "paper": "--paper", "grey200": "--grey-200", "grey400": "--grey-400", "grey600": "--grey-600", "red": "--alert-red", "green": "--ok-green"}.items():
            m = re.search(re.escape(v) + r":\s*(#[0-9A-Fa-f]{6})", css)
            if m: d[k] = m.group(1)
    return d

def _short(x: float) -> str:
    s, a = ("−" if x < 0 else ""), abs(x)
    f = lambda v, n=1: (f"{v:.{n}f}".replace(".", ",")).removesuffix(",0")
    return s + (f"{f(a / 1e9)} M" if a >= 1e9 else f"{f(a / 1e6, 0 if a >= 1e7 else 1)} jt" if a >= 1e6 else f"{f(a / 1e3, 0)} rb" if a >= 1e3 else f"{a:.0f}")

def render_card(df, filters: dict | None = None) -> bytes:
    from .analytics import apply_filters, prep
    filters = filters or {}; T = tokens()
    d = apply_filters(prep(df), {k: v for k, v in filters.items() if k != "month"})
    ms = sorted(d.month.unique()); cmp = ms[-2:] if len(ms) >= 2 else None
    fig = plt.figure(figsize=(10.8, 13.5), dpi=100, facecolor=T["paper"])
    def txt(x, y, s, **k): fig.text(x, y, s, color=k.pop("color", T["ink"]), **k)
    # ---- header: scope + the big number ----
    txt(0.08, 0.955, "Laporan penjualan", fontsize=17, color=T["grey600"])
    txt(0.08, 0.925, scope_label(filters), fontsize=30, fontweight="bold")
    if cmp:
        t = query(df, filters, compare=cmp)["total"]
        txt(0.08, 0.862, _rp(t["b"]), fontsize=46, fontweight="bold")
        up = t["delta"] >= 0; col = T["green"] if up else T["red"]
        txt(0.08, 0.826, f"{'▲' if up else '▼'} {'+' if up else '−'}{pct(t['pct'])}  ({'+' if up else ''}{_rp(t['delta'])})", fontsize=22, color=col, fontweight="bold")
        txt(0.08, 0.800, f"{month_label(cmp[1])} dibanding {month_label(cmp[0]).split()[0]}", fontsize=16, color=T["grey600"])
        by = "branch" if filters.get("region") and "branch" in d else "region"
        rows = query(df, filters, group_by=by, compare=cmp)["rows"] if by in d else []
        # ---- middle: bridge chart (totals black, changes green/red) ----
        ax = fig.add_axes([0.27, 0.43, 0.62, 0.335]); ax.set_facecolor(T["paper"])
        items = [("total", month_label(cmp[0]).split()[0], t["a"])] + [("d", r["key"], r["delta"]) for r in rows] + [("total", month_label(cmp[1]).split()[0], t["b"])]
        cum, ys, labels = 0.0, list(range(len(items)))[::-1], []
        for (kind, lab, v), y in zip(items, ys):
            a0, a1 = (0, v) if kind == "total" else (cum, cum + v); cum = a1
            color = T["ink"] if kind == "total" else (T["green"] if v >= 0 else T["red"])
            ax.barh(y, abs(a1 - a0), left=min(a0, a1), height=0.56, color=color)
            tx = max(a0, a1) + t["b"] * 0.015
            ax.text(tx, y, (_short(v) if kind == "total" else f"{'▲' if v >= 0 else '▼'} {_short(v)}"), va="center", fontsize=14, color=T["ink"])
            labels.append(lab)
        ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=15, color=T["ink"]); ax.set_xlim(0, max(t["a"], t["b"], cum) * 1.22)
        ax.xaxis.set_visible(False)
        for s in ("top", "right", "bottom"): ax.spines[s].set_visible(False)
        ax.spines["left"].set_color(T["grey200"]); ax.tick_params(axis="y", length=0)
        txt(0.08, 0.775, "Perubahan per " + ("cabang" if by == "branch" else "wilayah"), fontsize=15, color=T["grey600"], fontweight="bold")
    else:
        t = query(df, filters)["total"]; txt(0.08, 0.862, _rp(t), fontsize=46, fontweight="bold")
    # ---- bottom: 5 weakest outlets (relative to their type), numbered ----
    txt(0.08, 0.395, "5 outlet terlemah dibanding sesama tipenya", fontsize=19, fontweight="bold")
    y = 0.355
    for i, w in enumerate(weakest(df, filters, 5), 1):
        fig.patches.append(plt.Circle((0.098, y + 0.004), 0.0125, transform=fig.transFigure, color=T["red"], figure=fig))
        txt(0.098, y - 0.0005, str(i), fontsize=14, color="#FFFFFF", fontweight="bold", ha="center", va="center")
        txt(0.13, y + 0.008, w["name"], fontsize=17, fontweight="bold", va="center")
        txt(0.92, y + 0.008, f"skor {w['score']:.0f}", fontsize=15, color=T["red"], ha="right", va="center", fontweight="bold")
        lines = textwrap.wrap(f"{w['branch']} · {w['type']} · " + "; ".join(x["text"] if k == 0 else x["text"][0].lower() + x["text"][1:] for k, x in enumerate(w["reasons"][:2])), 86)[:2]
        for j, ln in enumerate(lines): txt(0.13, y - 0.014 - j * 0.0165, ln, fontsize=12.5, color=T["grey600"], va="center")
        y -= 0.068
    txt(0.08, 0.025, "Sales Studio · angka dihitung dari data yang sudah dibersihkan", fontsize=11.5, color=T["grey400"])
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=100, facecolor=T["paper"]); plt.close(fig)
    return buf.getvalue()


def render_owner_card(df, owner: str, items: list[dict], limit: int = 4) -> bytes | None:
    """One picture for one salesperson: for each of their outlets, Sep vs Oct sales and the four marks behind its score."""
    from .analytics import outlet_scores, prep
    d = prep(df); sc = outlet_scores(df)
    rows = [a for a in items if a.get("outlet_id") in sc.index][:limit]
    if not rows: return None
    T = tokens(); ms = sorted(d.month.unique())[-2:]; H = 1.7 + 3.4 * len(rows)
    fig = plt.figure(figsize=(10.8, H), dpi=100, facecolor=T["paper"])
    fig.text(0.06, 1 - 0.55 / H, f"Data untuk {owner}", fontsize=26, fontweight="bold", color=T["ink"], va="center")
    fig.text(0.06, 1 - 1.05 / H, f"{len(items)} hal perlu ditangani · bar hijau naik, merah turun", fontsize=15, color=T["grey600"], va="center")
    names = ["Uang masuk", "Naik/turun", "Frekuensi pemesanan", "Terakhir memesan"]
    for i, a in enumerate(rows):
        oid = a["outlet_id"]; r = sc.loc[oid]; top = H - 1.7 - 3.4 * i
        pr = a.get("priority"); pc = T["red"] if pr == "urgent" else T["green"] if pr == "opportunity" else T["grey600"]
        fig.text(0.06, (top + 0.15) / H, str(a.get("outlet") or oid), fontsize=22, fontweight="bold", color=T["ink"], va="center")
        fig.text(0.94, (top + 0.15) / H, f"skor {r.score:.0f}/100", fontsize=20, fontweight="bold", color=pc, va="center", ha="right")
        net = [float(d[(d.outlet_id == oid) & (d.month == m)].net.sum()) for m in ms]
        ax = fig.add_axes([0.14, (top - 2.65) / H, 0.30, 2.1 / H]); ax.set_facecolor(T["paper"])
        cols = [T["ink"]] + ([T["green"] if net[1] >= net[0] else T["red"]] if len(net) > 1 else [])
        ax.bar(range(len(net)), net, color=cols, width=0.55)
        for x, v in enumerate(net): ax.text(x, v, _short(v), ha="center", va="bottom", fontsize=13, color=T["ink"])
        ax.set_xticks(range(len(net))); ax.set_xticklabels([month_label(m).split()[0] for m in ms], fontsize=14)
        ax.set_ylim(0, max(max(net), 1) * 1.25); ax.yaxis.set_visible(False)
        for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
        ax.set_title("Penjualan bersih", fontsize=13, color=T["grey600"], loc="left")
        ax2 = fig.add_axes([0.62, (top - 2.65) / H, 0.32, 2.1 / H]); ax2.set_facecolor(T["paper"])
        marks = [float(r.c_value) * 100, float(r.c_trend) * 100, float(r.c_freq) * 100, float(r.c_recency) * 100]
        ys = list(range(4))[::-1]
        ax2.barh(ys, [100] * 4, color=T["grey200"], height=0.5)
        ax2.barh(ys, marks, color=[T["red"] if m < 35 else T["green"] if m >= 65 else T["grey600"] for m in marks], height=0.5)
        for y, m in zip(ys, marks): ax2.text(101.5, y, f"{m:.0f}", va="center", fontsize=13, color=T["ink"])
        ax2.set_yticks(ys); ax2.set_yticklabels(names, fontsize=13); ax2.set_xlim(0, 112); ax2.xaxis.set_visible(False)
        for sp in ("top", "right", "bottom", "left"): ax2.spines[sp].set_visible(False)
        ax2.tick_params(length=0); ax2.set_title("Nilai 0–100 (makin kecil makin lemah)", fontsize=13, color=T["grey600"], loc="left")
    buf = io.BytesIO(); fig.savefig(buf, format="png", facecolor=T["paper"]); plt.close(fig); return buf.getvalue()
