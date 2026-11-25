"""Auto-generated, editable action items (outlet, action, owner, due) from weakest outlets and anomalies."""
from __future__ import annotations
import datetime as dt
from .analytics import drivers, query, weakest, prep
from .fmt import month_label, pct, rp

ORDER = {"urgent": 0, "opportunity": 1, "watch": 2}

def _low(t: str) -> str: return t[0].lower() + t[1:] if t else t

def generate(df, today: dt.date | None = None, n_weakest: int = 5) -> list[dict]:
    today = today or dt.date.today(); due = (today + dt.timedelta(days=7)).isoformat()
    d = prep(df); months = sorted(d.month.unique())
    items: dict[str, dict] = {}
    def put(oid, name, branch, region, owner, action, reason, priority):
        if oid in items: return
        items[oid] = dict(id=f"a{len(items) + 1}", outlet_id=oid, outlet=name, branch=branch, region=region,
                          owner=owner or "Belum ditentukan", action=action, reason=reason, due=due, priority=priority, status="todo")
    # 1) biggest decline / growth drivers (anomalies) first so their reason is the specific one
    if len(months) >= 2 and "region" in d:
        a, b = months[-2], months[-1]
        rows = query(df, group_by="region", compare=[a, b])["rows"]
        names = d.drop_duplicates("outlet_id").set_index("outlet_id")
        sales = {o: s for o, s in d[d.salesman.notna() & (d.salesman != "Tidak diketahui")].groupby("outlet_id").salesman.agg(lambda s: s.value_counts().index[0]).items()} if "salesman" in d else {}
        def info(oid): r = names.loc[oid]; return str(r.outlet_name), str(r.get("branch", "")), str(r.get("region", ""))
        lo, hi = min(rows, key=lambda r: r["delta"]), max(rows, key=lambda r: r["delta"])
        for r, up in [(x, u) for x, u in ((lo, False), (hi, True)) if (x["delta"] > 0) == u and x["delta"] != 0]:   # a "decline" must really decline
            dr = drivers(df, "region", r["key"], a, b, top=1)
            if not dr or dr[0]["delta"] == 0: continue
            x = dr[0]; nm, br, rg = info(x["key"])
            if up:
                put(x["key"], nm, br, rg, sales.get(x["key"]), f"Pastikan stok dan layanan {nm} aman agar kenaikan bertahan",
                    f"Naik {rp(x['delta'])} ({month_label(a)} → {month_label(b)}), pendorong utama kenaikan {r['key']}.", "opportunity")
            else:
                put(x["key"], nm, br, rg, sales.get(x["key"]), f"Kunjungi {nm} ({br}) minggu ini dan cari tahu kenapa pesanan turun",
                    f"Turun {rp(abs(x['delta']))} ({month_label(a)} → {month_label(b)}), pendorong utama penurunan {r['key']}.", "urgent")
    # 2) weakest outlets relative to their type
    for w in weakest(df, n=n_weakest):
        put(w["outlet_id"], w["name"], w["branch"], w["region"], w["salesman"],
            f"Kunjungi {w['name']} ({w['branch']}) minggu ini; {_low(w['reasons'][0]['text'])}",
            f"Skor {w['score']:.0f}/100 dibanding sesama {w['type']}. " + "; ".join(r["text"] for r in w["reasons"]) + ".", "urgent")
    return sorted(items.values(), key=lambda x: ORDER[x["priority"]])
