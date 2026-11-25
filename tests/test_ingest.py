import io, json
import pandas as pd
from app.ingest import read_table, parse_idr, parse_date_series
from app.mapping import guess_mapping, apply_mapping, save_template, load_template

def test_parse_idr_indonesian_and_plain():
    assert parse_idr("Rp 1.234.567,00") == 1234567.0
    assert parse_idr("1.234.567") == 1234567.0
    assert parse_idr("1,234,567.50") == 1234567.5
    assert parse_idr("-528.000") == -528000.0
    assert parse_idr("(528.000)") == -528000.0
    assert parse_idr(990000) == 990000.0
    assert pd.isna(parse_idr(""))

def test_dates_formats():
    iso = parse_date_series(pd.Series(["2026-09-01", "2026-10-31"]))
    dmy = parse_date_series(pd.Series(["01/09/2026", "31/10/2026"]))
    serial = parse_date_series(pd.Series([46266, 46326]))  # Excel serials
    assert list(iso.dt.strftime("%Y-%m-%d")) == ["2026-09-01", "2026-10-31"]
    assert list(dmy.dt.strftime("%Y-%m-%d")) == ["2026-09-01", "2026-10-31"]
    assert list(serial.dt.strftime("%Y-%m-%d")) == ["2026-09-01", "2026-10-31"]

def test_sample_csv_loads():
    t = read_table("data/sales.csv")
    assert len(t.df) == 1891 and t.df.shape[1] == 15

def test_delimiter_semicolon_and_tab():
    raw = "tgl;outlet;nilai\n2026-09-01;A;1.000\n"
    assert read_table(io.BytesIO(raw.encode()), name="a.csv").df.shape == (1, 3)
    raw = "tgl\toutlet\tnilai\n2026-09-01\tA\t1000\n"
    assert read_table(io.BytesIO(raw.encode()), name="a.tsv").df.shape == (1, 3)

def test_encoding_latin1_and_bom():
    raw = "tanggal,outlet,nilai\n2026-09-01,Toko Café,100\n".encode("latin-1")
    assert "Café" in read_table(io.BytesIO(raw), name="a.csv").df.outlet.iloc[0]
    raw = b"\xef\xbb\xbftanggal,outlet,nilai\n2026-09-01,A,100\n"
    assert list(read_table(io.BytesIO(raw), name="a.csv").df.columns)[0] == "tanggal"

def test_title_rows_above_header():
    raw = "LAPORAN PENJUALAN\nPT Dua Kelinci\n\ntanggal,outlet,nilai\n2026-09-01,A,100\n"
    t = read_table(io.BytesIO(raw.encode()), name="a.csv")
    assert list(t.df.columns) == ["tanggal", "outlet", "nilai"] and t.header_row == 3

def test_json_xlsx_parquet(tmp_path):
    df = pd.DataFrame({"tanggal": ["2026-09-01"], "outlet": ["A"], "nilai": [100]})
    df.to_json(tmp_path / "a.json", orient="records"); df.to_excel(tmp_path / "a.xlsx", index=False)
    df.to_parquet(tmp_path / "a.parquet")
    for n in ["a.json", "a.xlsx", "a.parquet"]:
        assert read_table(tmp_path / n).df.shape == (1, 3)

def test_xlsx_multi_sheet_lists_sheets(tmp_path):
    with pd.ExcelWriter(tmp_path / "m.xlsx") as w:
        pd.DataFrame({"a": [1]}).to_excel(w, sheet_name="S1", index=False); pd.DataFrame({"b": [2]}).to_excel(w, sheet_name="S2", index=False)
    t = read_table(tmp_path / "m.xlsx", sheet="S2")
    assert t.sheets == ["S1", "S2"] and list(t.df.columns) == ["b"]

def test_guess_mapping_sample():
    m = guess_mapping(read_table("data/sales.csv").df)
    roles = {k: v["column"] for k, v in m.items()}
    assert roles["date"] == "date" and roles["outlet_id"] == "outlet_id" and roles["net"] == "net_sales_idr"
    assert roles["region"] == "region" and roles["brand"] == "brand" and roles["salesman"] == "salesman"
    assert all(0 < v["confidence"] <= 1 for v in m.values())

def test_guess_mapping_indonesian_names():
    df = pd.DataFrame({"Tgl Faktur": ["01/09/2026"], "Wilayah": ["Jabar"], "Kode Toko": ["T1"], "Nama Toko": ["X"], "Total Penjualan": ["1.000"]})
    m = guess_mapping(df)
    assert m["date"]["column"] == "Tgl Faktur" and m["region"]["column"] == "Wilayah"
    assert m["outlet_id"]["column"] == "Kode Toko" and m["net"]["column"] == "Total Penjualan"

def test_apply_mapping_canonical_schema_and_missing_optional():
    df = read_table("data/sales.csv").df
    m = {k: v["column"] for k, v in guess_mapping(df).items()}
    out = apply_mapping(df, m)
    assert out.net.sum() == 1728036900 and out.date.dt.year.eq(2026).all()
    m2 = {k: v for k, v in m.items() if k != "brand"}
    out2 = apply_mapping(df, m2)
    assert "brand" not in out2.attrs["available"] and "region" in out2.attrs["available"]

def test_missing_required_is_reported():
    df = pd.DataFrame({"foo": [1]})
    m = guess_mapping(df)
    assert not all(r in m for r in ["date", "outlet_id", "net"])

def test_template_roundtrip(tmp_path):
    df = pd.DataFrame({"Tgl": ["x"], "Toko": ["y"]})
    save_template(df.columns, {"date": "Tgl", "outlet_id": "Toko"}, tmp_path)
    assert load_template(df.columns, tmp_path) == {"date": "Tgl", "outlet_id": "Toko"}
    assert load_template(["lain"], tmp_path) is None
