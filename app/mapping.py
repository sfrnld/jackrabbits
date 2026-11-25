"""Guess which column plays which role, ask the user to confirm, remember it."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
import pandas as pd
from .ingest import parse_idr, parse_date_series

ROLES = ["date", "invoice", "region", "branch", "outlet_id", "outlet_name", "outlet_type",
         "salesman", "brand", "sku", "qty", "price", "gross", "discount", "net"]
REQUIRED = ["date", "outlet", "net"]   # 'outlet' = outlet_id or outlet_name; 'net' = net or gross

SYN = {
    "date": ["date", "tanggal", "tgl", "tgl faktur", "tanggal transaksi", "tanggal faktur", "tgl transaksi", "order date", "invoice date"],
    "invoice": ["invoice no", "invoice", "no invoice", "faktur", "no faktur", "nomor faktur", "invoice number", "no nota", "nota"],
    "region": ["region", "wilayah", "area", "provinsi", "regional"],
    "branch": ["branch", "cabang", "depo", "kota", "city"],
    "outlet_id": ["outlet id", "kode outlet", "kode toko", "id outlet", "id toko", "customer id", "kode pelanggan", "cust id", "customer code"],
    "outlet_name": ["outlet name", "nama outlet", "nama toko", "outlet", "toko", "customer", "pelanggan", "nama pelanggan", "customer name"],
    "outlet_type": ["outlet type", "tipe outlet", "jenis outlet", "tipe toko", "channel", "segment", "tipe", "type"],
    "salesman": ["salesman", "sales", "salesperson", "sales rep", "nama sales", "sales man", "tenaga penjual"],
    "brand": ["brand", "merek", "merk"],
    "sku": ["sku", "produk", "product", "nama produk", "item", "nama barang", "barang"],
    "qty": ["qty carton", "qty", "quantity", "jumlah", "kuantitas", "karton", "qty karton"],
    "price": ["price per carton", "price", "harga", "harga satuan", "harga per karton", "unit price"],
    "gross": ["gross sales", "gross", "bruto", "penjualan kotor", "nilai kotor"],
    "discount": ["discount", "diskon", "potongan", "disc"],
    "net": ["net sales", "net", "netto", "total penjualan", "nilai penjualan", "penjualan bersih", "omzet", "revenue", "sales", "total", "nilai", "amount", "jumlah rp"],
}
NUMERIC = {"qty", "price", "gross", "discount", "net"}
_STOP = {"idr", "rp", "rupiah"}

def _tokens(s: str) -> list[str]:
    return [t for t in re.sub(r"[^a-z0-9]+", " ", str(s).lower()).split() if t not in _STOP]

def _name_score(col: str, role: str) -> float:
    ct = _tokens(col)
    if not ct: return 0.0
    best = 0.0
    for phrase in SYN[role]:
        pt = _tokens(phrase)
        if pt == ct: return 1.0
        if set(pt) <= set(ct): best = max(best, 0.6 + 0.3 * len(pt) / len(ct))
    return best

def _content(col: pd.Series, role: str) -> float:
    s = col.dropna()
    if s.empty: return 0.0
    s = s.head(300)
    if role == "date": return float(parse_date_series(s).notna().mean())
    if role in NUMERIC: return float(s.map(parse_idr).notna().mean())
    return 0.0

def guess_mapping(df: pd.DataFrame) -> dict[str, dict]:
    cands = []
    for col in df.columns:
        for role in ROLES:
            ns = _name_score(col, role)
            if role == "date":
                pr = _content(df[col], role)
                score = ns * 0.6 + 0.4 * pr if ns else (pr * 0.5 if pr > 0.95 else 0)
                if ns and pr < 0.8: score *= 0.3
            elif role in NUMERIC:
                nr = _content(df[col], role)
                score = ns * 0.7 + 0.3 * nr if ns and nr >= 0.8 else 0
            else:
                score = ns
            if score >= 0.5: cands.append((score, col, role))
    out, used = {}, set()
    for score, col, role in sorted(cands, key=lambda x: -x[0]):
        if role in out or col in used: continue
        out[role] = {"column": col, "confidence": round(min(score, 1.0), 2)}; used.add(col)
    return out

def missing_required(m: dict) -> list[str]:
    miss = []
    if "date" not in m: miss.append("date")
    if "outlet_id" not in m and "outlet_name" not in m: miss.append("outlet")
    if "net" not in m and "gross" not in m: miss.append("net")
    return miss

class MappingError(ValueError):
    def __init__(self, missing): super().__init__(f"Missing required: {missing}"); self.missing = missing

def apply_mapping(df: pd.DataFrame, m: dict[str, str]) -> pd.DataFrame:
    """m: role -> source column. Returns the single canonical schema."""
    miss = missing_required(m)
    if miss: raise MappingError(miss)
    out = pd.DataFrame(index=df.index)
    out["src_row"] = df.index + 1
    for role, col in m.items():
        if role not in ROLES or col not in df.columns: continue
        s = df[col]
        if role == "date": out[role] = parse_date_series(s)
        elif role in NUMERIC: out[role] = s.map(parse_idr)
        else: out[role] = s.astype("string")
    if "outlet_id" not in out: out["outlet_id"] = out["outlet_name"]
    if "outlet_name" not in out: out["outlet_name"] = out["outlet_id"]
    if "net" not in out: out["net"] = out["gross"] - out.get("discount", 0)
    avail = [r for r in ROLES if r in out.columns and not out[r].isna().all()]
    out.attrs["available"] = avail
    return out

def _key(columns) -> str:
    norm = sorted(" ".join(_tokens(c)) for c in columns)
    return hashlib.sha1("|".join(norm).encode()).hexdigest()[:16]

def save_template(columns, mapping: dict[str, str], dir_: Path) -> None:
    dir_ = Path(dir_); dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / f"{_key(columns)}.json").write_text(json.dumps(mapping, ensure_ascii=False))

def load_template(columns, dir_: Path) -> dict[str, str] | None:
    f = Path(dir_) / f"{_key(columns)}.json"
    return json.loads(f.read_text()) if f.exists() else None
