from __future__ import annotations
import io, logging
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from .ingest import read_table
from .mapping import (ROLES, MappingError, apply_mapping, guess_mapping, load_template,
                      missing_required, save_template)

router = APIRouter(prefix="/api/data")
TEMPLATES = None  # set by main (ROOT/state/templates)
S: dict = {}      # single-user local session

def _load(table, source: str, name: str):
    df = table.df
    S.clear(); S.update(raw=df, table=table, source=source, name=name)
    tpl = load_template(df.columns, TEMPLATES)
    if tpl:
        m = {r: {"column": c, "confidence": 1.0} for r, c in tpl.items() if c in df.columns}
        remembered = True
    else:
        m, remembered = guess_mapping(df), False
    S["guess"] = m
    logging.info("Data dibaca: %s (%d baris, %d kolom)", name, len(df), len(df.columns))
    return {"source": source, "name": name, "rows": len(df), "columns": list(df.columns),
            "sheets": table.sheets, "header_row": table.header_row, "remembered": remembered,
            "mapping": m, "missing": missing_required({r: v["column"] for r, v in m.items()}),
            "preview": df.head(5).fillna("").astype(str).to_dict("records")}

@router.get("/sample")
def sample_available():
    """Is the bundled sample file there? (It may be left out of a repo; uploading your own data always works.)"""
    from .main import SAMPLE
    return {"available": SAMPLE.is_file()}

@router.post("/sample")
def sample():
    from .main import SAMPLE
    if not SAMPLE.is_file():
        raise HTTPException(404, "File data contoh (data/sales.csv) tidak ditemukan di folder aplikasi. Unggah file penjualanmu sendiri.")
    try: return _load(read_table(SAMPLE), "sample", SAMPLE.name)
    except Exception as e: raise HTTPException(422, f"Data contoh tidak bisa dibaca: {e}")

@router.post("/upload")
async def upload(file: UploadFile = File(...), sheet: str | None = None):
    data = await file.read()
    try:
        t = read_table(io.BytesIO(data), name=file.filename, sheet=sheet)
    except Exception as e:
        raise HTTPException(422, f"Tidak bisa membaca file: {e}")
    if t.df.empty: raise HTTPException(422, "File kosong")
    return _load(t, "upload", file.filename or "upload")

class Confirm(BaseModel):
    mapping: dict[str, str]

@router.post("/mapping")
def confirm(body: Confirm):
    if "raw" not in S: raise HTTPException(409, "Pilih data dulu")
    try:
        clean_in = apply_mapping(S["raw"], body.mapping)
    except MappingError as e:
        raise HTTPException(422, {"missing": e.missing})
    S["mapping"] = dict(body.mapping); S["canon"] = clean_in; S.pop("findings", None); S.pop("decisions", None)
    save_template(S["raw"].columns, body.mapping, TEMPLATES)
    avail = clean_in.attrs["available"]
    logging.info("Pemetaan kolom dikonfirmasi: %d baris siap dianalisis", len(clean_in))
    return {"rows": len(clean_in), "available": avail,
            "hidden": [r for r in ROLES if r not in avail],
            "date_min": str(clean_in.date.min().date()), "date_max": str(clean_in.date.max().date())}
