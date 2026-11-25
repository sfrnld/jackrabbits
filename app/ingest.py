"""Read messy ERP exports (CSV/TSV/xlsx/xls/JSON/Parquet) into a raw string-ish DataFrame."""
from __future__ import annotations
import csv, io, re
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd

@dataclass
class Table:
    df: pd.DataFrame
    header_row: int = 0
    sheets: list[str] = field(default_factory=list)
    encoding: str = "utf-8"
    delimiter: str = ","
    fmt: str = "csv"

def _name(src, name):
    return (name or getattr(src, "name", None) or str(src)).lower()

def _bytes(src) -> bytes:
    if isinstance(src, (str, Path)):
        return Path(src).read_bytes()
    pos = src.tell() if hasattr(src, "tell") else None
    data = src.read()
    if pos is not None: src.seek(pos)
    return data

def _decode(raw: bytes) -> tuple[str, str]:
    for enc in ("utf-8-sig", "utf-16"):
        try:
            if enc == "utf-16" and not raw.startswith((b"\xff\xfe", b"\xfe\xff")): continue
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            pass
    return raw.decode("cp1252", errors="replace"), "cp1252"

def _detect_delim(lines: list[str]) -> str:
    best, score = ",", -1
    for d in (",", ";", "\t", "|"):
        counts = [len(next(csv.reader([l], delimiter=d))) for l in lines if l.strip()]
        multi = [c for c in counts if c > 1]
        if not multi: continue
        modal = max(set(multi), key=multi.count)
        s = multi.count(modal) * 100 + modal
        if s > score: best, score = d, s
    return best

def _read_csv(raw: bytes) -> Table:
    text, enc = _decode(raw)
    lines = text.splitlines()[:60]
    delim = _detect_delim(lines)
    counts = [len(next(csv.reader([l], delimiter=delim))) if l.strip() else 0 for l in lines]
    multi = [c for c in counts if c > 1]
    modal = max(set(multi), key=multi.count) if multi else 1
    header = next(i for i, c in enumerate(counts) if c == modal) if multi else 0
    df = pd.read_csv(io.StringIO(text), sep=delim, skiprows=header, dtype=str, engine="python")
    df.columns = [str(c).strip() for c in df.columns]
    return Table(df, header, [], enc, delim, "csv")

def _read_excel(src, sheet) -> Table:
    xl = pd.ExcelFile(src)
    sheets = xl.sheet_names
    raw = xl.parse(sheet if sheet is not None else sheets[0], header=None)
    raw = raw.dropna(how="all").reset_index(drop=False)
    head_idx = raw.drop(columns="index").head(30).notna().sum(axis=1)
    pos = int(head_idx.values.argmax())
    header_row = int(raw.loc[pos, "index"])
    cols = [str(c).strip() for c in raw.drop(columns="index").iloc[pos]]
    body = raw.drop(columns="index").iloc[pos + 1:].reset_index(drop=True)
    body.columns = cols
    return Table(body, header_row, sheets, fmt="xlsx")

def read_table(src, name: str | None = None, sheet: str | None = None) -> Table:
    n = _name(src, name)
    if n.endswith((".xlsx", ".xls", ".xlsm")):
        return _read_excel(src if not isinstance(src, (str, Path)) else str(src), sheet)
    if n.endswith(".parquet"):
        return Table(pd.read_parquet(src), fmt="parquet")
    if n.endswith(".json"):
        text, _ = _decode(_bytes(src))
        try:
            df = pd.read_json(io.StringIO(text))
        except ValueError:
            import json
            df = pd.json_normalize(json.loads(text))
        return Table(df, fmt="json")
    return _read_csv(_bytes(src))

def parse_idr(x) -> float:
    """'Rp 1.234.567,00' / '1,234,567.50' / '(528.000)' / 990000 -> float. Empty -> NaN."""
    if x is None or (isinstance(x, float) and pd.isna(x)): return float("nan")
    if isinstance(x, (int, float)): return float(x)
    s = str(x).strip()
    if not s: return float("nan")
    neg = s.startswith("(") and s.endswith(")") or s.startswith("-") or s.endswith("-")
    s = re.sub(r"(?i)rp\.?|idr|[\s()\-+]", "", s)
    if not s: return float("nan")
    dots, commas = s.count("."), s.count(",")
    if dots and commas:
        dec = "." if s.rfind(".") > s.rfind(",") else ","
        s = s.replace("," if dec == "." else ".", "").replace(dec, ".")
    elif dots or commas:
        sep = "." if dots else ","
        tail = s.rsplit(sep, 1)[1]
        if s.count(sep) > 1 or len(tail) == 3: s = s.replace(sep, "")      # thousands
        else: s = s.replace(sep, ".")                                       # decimal
    try: v = float(s)
    except ValueError: return float("nan")
    return -v if neg else v

_EXCEL_ORIGIN = pd.Timestamp("1899-12-30")

def parse_date_series(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s): return s
    num = pd.to_numeric(s, errors="coerce")
    if num.notna().mean() > 0.95 and num.dropna().between(20000, 80000).all():
        return _EXCEL_ORIGIN + pd.to_timedelta(num, unit="D")
    s = s.astype("string").str.strip()
    out = pd.to_datetime(s, format="ISO8601", errors="coerce")
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y"):
        m = out.isna() & s.notna()
        if not m.any(): break
        out[m] = pd.to_datetime(s[m], format=fmt, errors="coerce")
    m = out.isna() & s.notna()
    if m.any(): out[m] = pd.to_datetime(s[m], dayfirst=True, errors="coerce", format="mixed")
    return out
