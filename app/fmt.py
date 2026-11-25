"""Indonesian number formatting for assistant messages and reports."""
def _n(x: float, nd: int = 1) -> str:
    s = f"{x:.{nd}f}".replace(".", ",")
    return s[:-2] if s.endswith(",0") else s

def rp(x: float) -> str:
    sign, a = ("−" if x < 0 else ""), abs(x)
    if a >= 1e9: t = f"{_n(a / 1e9)} miliar"
    elif a >= 1e6: t = f"{_n(a / 1e6)} juta"
    elif a >= 1e3: t = f"{_n(a / 1e3, 0)} ribu"
    else: t = f"{a:.0f}"
    return f"{sign}Rp {t}"

def rp_full(x: float) -> str:
    return ("−" if x < 0 else "") + "Rp " + f"{abs(x):,.0f}".replace(",", ".")

def pct(x: float) -> str:
    return f"{_n(abs(x))}%"

MONTHS_ID = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
def month_label(ym: str) -> str:
    y, m = ym.split("-"); return f"{MONTHS_ID[int(m) - 1]} {y}"
