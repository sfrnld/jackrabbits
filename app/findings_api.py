from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .data_api import S
import pandas as pd
from .findings import apply_decisions, detect, recommended, summarize
from .mapping import NUMERIC

router = APIRouter(prefix="/api/findings")

def build_table(f: dict, raw: pd.DataFrame, mapping: dict, header_row: int, limit: int = 20, clean: pd.DataFrame | None = None, decided: bool = False) -> dict:
    """Spreadsheet-style view of the rows a finding involves: original headers, raw values, and the line number as the user sees it."""
    inv = f["involved"]; shown = inv[:limit]; cols = list(raw.columns)
    numeric = [mapping[r] for r in NUMERIC if mapping.get(r) in cols]
    cell = lambda v: None if (v is None or (isinstance(v, float) and v != v) or v is pd.NA) else str(v)
    after = clean.set_index("src_row", drop=False) if (decided and clean is not None) else None
    def show(v):                                    # cleaned canonical value -> the way a spreadsheet would show it
        if v is None or v is pd.NA or (isinstance(v, float) and v != v): return None
        if hasattr(v, "strftime"): return v.strftime("%Y-%m-%d")
        if isinstance(v, float) and v.is_integer(): return str(int(v))
        return str(v)
    rows = []
    for r in shown:
        src = raw.iloc[r["row"] - 1]; row = dict(row=r["row"], line=r["row"] + header_row + 1, role=r["role"], label=r["label"], group=r["group"], why=r.get("why"), group_label=r.get("group_label"),
                         hi=[mapping[x] for x in r["hi"] if x in mapping], cells={c: cell(src[c]) for c in cols}, removed=False)
        if after is not None:
            if r["row"] not in after.index: row["removed"] = True
            else: row["after"] = {mapping[x]: show(after.loc[r["row"], x]) for x in r["hi"] if x in mapping and x in after.columns}
        rows.append(row)
    pinned = [mapping[x] for x in f.get("pin", []) if x in mapping]
    return dict(columns=cols, numeric=numeric, pinned=pinned, rows=rows, total=len(inv), hidden=max(0, len(inv) - len(shown)))

class Decision(BaseModel):
    option: str
    params: dict | None = None

def _state():
    if "canon" not in S: raise HTTPException(409, "Konfirmasi pemetaan kolom dulu")
    if "findings" not in S: S["findings"] = detect(S["canon"]); S["decisions"] = {}
    S["clean"], trail = apply_decisions(S["canon"], S["decisions"])
    hdr = S["table"].header_row if "table" in S else 0
    out = []
    for f in S["findings"]:
        f["decision"] = S["decisions"].get(f["id"])
        out.append({**{k: v for k, v in f.items() if k != "involved"},
                    "table": build_table(f, S["raw"], S.get("mapping", {}), hdr, clean=S["clean"], decided=f["decision"] is not None)})
    return {"findings": out, "decisions": S["decisions"], "trail": trail,
            "summary": summarize(S["canon"], S["clean"]),
            "pending": [f["id"] for f in S["findings"] if f["id"] not in S["decisions"]]}

@router.get("")
def get(): return _state()

@router.put("/{fid}")
def decide(fid: str, body: Decision):
    st = _state(); f = next((x for x in st["findings"] if x["id"] == fid), None)
    if not f: raise HTTPException(404, "Temuan tidak ada")
    if body.option not in {o["id"] for o in f["options"]}: raise HTTPException(422, "Opsi tidak dikenal")
    S["decisions"][fid] = body.model_dump(); return _state()

@router.delete("/{fid}")
def undo(fid: str):
    _state(); S["decisions"].pop(fid, None); return _state()

@router.post("/apply-all")
def apply_all():
    _state(); S["decisions"] = recommended(S["findings"]); return _state()
