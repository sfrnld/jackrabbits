"""Report text for Telegram: a one-paragraph summary (headline number -> 1-2 anomalies -> concrete action)
and numbered action items. Templates filled with analytics results, so no LLM is involved."""
from __future__ import annotations
import datetime as dt
from .analytics import apply_filters, insights, options, prep, query
from .fmt import month_label, pct, rp

MON = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

def scope_label(filters: dict) -> str:
    f = {k: v for k, v in (filters or {}).items() if v}
    if f.get("region"): return ", ".join(f["region"])
    return "Tampilan terfilter" if f else "Semua wilayah"

def _in_scope(items: list[dict], filters: dict) -> list[dict]:
    regs = (filters or {}).get("region")
    # finished items are not worth sending; everything else in scope goes out
    return [a for a in items if a.get("status") != "done" and (not regs or a.get("region") in regs)]

def _periods(df, filters):
    d = apply_filters(prep(df), {k: v for k, v in (filters or {}).items() if k != "month"})
    ms = sorted(d.month.unique()); return ms

def summary_text(df, filters, actions) -> str:
    ms = _periods(df, filters); label = scope_label(filters)
    if len(ms) >= 2:
        a, b = ms[-2], ms[-1]; t = query(df, filters, compare=[a, b])["total"]
        head = f"{label}: net {month_label(b)} {rp(t['b'])}, {'naik' if t['delta'] >= 0 else 'turun'} {pct(t['pct']) if t['pct'] is not None else '-'} dibanding {month_label(a).split()[0]}."
        movers = [i["text"] for i in insights(df, filters, limit=3) if i["kind"] == "mover"][:2]
    else:
        t = query(df, filters)["total"]; head = f"{label}: net total {rp(t)}."; movers = []
    todo = _in_scope(actions, filters)
    step = f"Minggu ini: {todo[0]['action'][0].lower() + todo[0]['action'][1:]}." if todo else "Minggu ini: pertahankan ritme kunjungan ke outlet utama."
    return " ".join([head, *movers, step.replace("..", ".")])

def _due(s: str) -> str:
    try: d = dt.date.fromisoformat(s); return f"{d.day} {MON[d.month - 1]} {d.year}"
    except ValueError: return s

def actions_text(filters, actions, limit: int = 10) -> str:
    todo = _in_scope(actions, filters)[:limit]
    if not todo: return "Belum ada action item untuk wilayah ini."
    lines = ["Action items minggu ini:"]
    for i, a in enumerate(todo, 1):
        lines.append(f"{i}. {a['action']} (PJ: {a['owner']}, tenggat {_due(a['due'])})")
        if a.get("reason"): lines.append(f"   Kenapa: {a['reason']}")
    return "\n".join(lines)

def owned(actions: list[dict], key: str) -> list[dict]:
    """Open action items whose owner matches `key` (case-insensitive)."""
    return [a for a in actions if a.get("status") != "done" and key and (a.get("owner") or "").strip().casefold() == key]

_PRIO = {"urgent": "MENDESAK", "opportunity": "Peluang", "watch": "Pantau"}

def _question(a: dict) -> str:
    o = a.get("outlet") or "outlet ini"
    return {"urgent": f"Kenapa pesanan {o} turun, dan apa yang bisa dilakukan minggu ini?",
            "opportunity": f"Apa yang membuat {o} naik, dan bagaimana menjaganya tetap naik?"}.get(a.get("priority"), f"Adakah hal yang perlu diwaspadai di {o}?")

def owner_text(name: str, items: list[dict], limit: int = 10) -> str:
    """One person's message: for every action WHY it exists, WHAT to do, by WHEN, and the QUESTION to answer back."""
    n = len(items)
    lines = [f"Halo {name}, ada {n} hal yang perlu kamu tangani." if n > 1 else f"Halo {name}, ada 1 hal yang perlu kamu tangani.", ""]
    for i, a in enumerate(items[:limit], 1):
        where = f" ({a['branch']}, {a['region']})" if a.get("branch") and a.get("region") else (f" ({a['region']})" if a.get("region") else "")
        lines.append(f"{i}. {a.get('outlet') or 'Aksi'}{where} · {_PRIO.get(a.get('priority'), '')}".rstrip(" ·"))
        if a.get("reason"): lines.append(f"   Kenapa: {a['reason']}")
        lines.append(f"   Yang perlu dilakukan: {a['action']}")
        lines.append(f"   Tenggat: {_due(a['due'])}")
        lines.append(f"   Yang perlu kamu jawab: {_question(a)}")
        lines.append("")
    if n > limit: lines.append(f"…dan {n - limit} lainnya, lihat di Sales Studio.")
    lines.append("Setelah selesai, balas pesan ini dengan jawabanmu dan apa yang kamu temukan.")
    return "\n".join(lines).strip()

_ICON = {"urgent": ("🔴", "MENDESAK", "📉"), "opportunity": ("🟢", "PELUANG", "📈"), "watch": ("🟡", "PANTAU", "🔎")}

def owner_html(name: str, items: list[dict], limit: int = 10, demo: bool = False) -> str:
    """The same message as owner_text, laid out for Telegram (HTML): bold labels, icons, one idea per line."""
    from html import escape as e
    n = len(items)
    out = []
    if demo: out += [f"🧪 <b>DEMO</b> · kamu menerima ini sebagai <b>{e(name)}</b>", ""]
    out += [f"👋 <b>Halo {e(name)}!</b>", f"Ada <b>{n}</b> hal yang perlu kamu tangani:", ""]
    for i, a in enumerate(items[:limit], 1):
        dot, label, ric = _ICON.get(a.get("priority"), ("⚪", "", "🔎"))
        where = ", ".join(x for x in (a.get("branch"), a.get("region")) if x)
        out.append(f"<b>{i}. {e(a.get('outlet') or 'Aksi')}</b>" + (f" · {e(where)}" if where else ""))
        out.append(f"{dot} <b>{label}</b>")
        out.append("")
        if a.get("reason"): out += [f"{ric} <b>Kenapa</b>", e(a["reason"]), ""]
        out += ["✅ <b>Yang perlu dilakukan</b>", e(a["action"]), "", f"📅 <b>Tenggat:</b> {e(_due(a['due']))}", "",
                "❓ <b>Yang perlu kamu jawab</b>", e(_question(a)), "", "──────────", ""]
    if n > limit: out += [f"…dan {n - limit} lainnya, lihat di Sales Studio.", ""]
    out.append("💬 Setelah selesai, balas pesan ini dengan jawabanmu dan apa yang kamu temukan.")
    return "\n".join(out)

def compose(df, filters, actions) -> dict:
    from .render import render_card
    ms = _periods(df, filters); period = month_label(ms[-1]) if ms else ""
    label = scope_label(filters)
    return dict(scope_label=label, period=period, caption=f"Laporan penjualan · {label} · {period}"[:1024],
                summary=summary_text(df, filters, actions), actions_text=actions_text(filters, actions),
                actions=_in_scope(actions, filters), png=render_card(df, filters))
