"""Sales Studio server: serves the prebuilt web app and the JSON API."""
import logging, os, socket, sys, threading, webbrowser
from collections import deque
from pathlib import Path
import duckdb
from fastapi import FastAPI, Request
from . import settings
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data" / "sales.csv"
DIST = ROOT / "web" / "dist"
LOG: deque[str] = deque(maxlen=500)

import re
_SECRET = re.compile(r"bot\d+:[A-Za-z0-9_-]+")      # Telegram bot tokens appear in API URLs

class _Mem(logging.Handler):
    def emit(self, r): LOG.append(_SECRET.sub("bot***", self.format(r)))
logging.getLogger().addHandler(_Mem()); logging.getLogger().setLevel(logging.INFO)
for _n in ("httpx", "httpcore"): logging.getLogger(_n).setLevel(logging.WARNING)   # never log full request URLs

app = FastAPI(title="Sales Studio")
from . import data_api
data_api.TEMPLATES = ROOT / "state" / "templates"
from . import findings_api, analytics_api, actions_api, share_api
app.include_router(data_api.router)
app.include_router(findings_api.router)
app.include_router(analytics_api.router)
app.include_router(actions_api.router)
app.include_router(share_api.router)

def find_free_port(start: int = 8765) -> int:
    for p in range(start, start + 50):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); return s.getsockname()[1]

def _internet() -> tuple[int | None, str | None]:
    """Latency in ms to Telegram's API (TCP connect), or (None, reason)."""
    import time
    t = time.perf_counter()
    try:
        socket.create_connection(("api.telegram.org", 443), timeout=3).close()
        return round((time.perf_counter() - t) * 1000), None
    except socket.gaierror: return None, "nama server tidak ditemukan (DNS)"
    except TimeoutError: return None, "waktu habis"
    except OSError: return None, "tidak bisa terhubung"

def _id(x: float, nd: int = 1) -> str: return f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")
def _gb(b: float) -> str: return f"{_id(b / 2**30)} GB"
def _f(k, v, **kw): return {"k": k, "v": str(v), **kw}

@app.post("/api/reset")
def reset_everything():
    """Back to a first-run experience. Keeps ONLY the Telegram token (.env)."""
    import shutil
    from . import share, settings
    data_api.S.clear(); share.reset()
    sd = settings.state_dir()
    (sd / "share.json").unlink(missing_ok=True)
    shutil.rmtree(sd / "templates", ignore_errors=True)
    if data_api.TEMPLATES: shutil.rmtree(data_api.TEMPLATES, ignore_errors=True)
    LOG.clear(); logging.getLogger("sales_studio").info("Reset: semua data dan pengaturan dihapus (token Telegram dipertahankan)")
    return {"ok": True}

@app.get("/api/status")
def status(): return {"log": list(LOG)}

def install_id() -> str:
    """A random id stored in this install's state folder. The browser uses it to tell one install from another
    (they can share the same address, 127.0.0.1:8765, and therefore the same browser storage)."""
    import uuid
    f = settings.state_dir() / "install_id"
    try:
        if f.exists() and f.read_text().strip(): return f.read_text().strip()
        f.parent.mkdir(parents=True, exist_ok=True); i = uuid.uuid4().hex; f.write_text(i); return i
    except OSError: return "unknown"

@app.get("/api/health")
def health(): return {"ok": True, "app": "sales-studio", "pid": os.getpid(), "install_id": install_id()}

@app.get("/api/setup/check")
def check(request: Request):
    import platform, shutil, time
    import pandas
    from . import settings
    items = []
    # 1) data engine
    py = platform.python_version(); ok_py = tuple(int(x) for x in py.split(".")[:2]) >= (3, 11)
    try:
        t = time.perf_counter(); duckdb.sql("select 1").fetchall(); ms = round((time.perf_counter() - t) * 1000, 1); ok_q = True
    except Exception as e: ms, ok_q = None, False
    items.append(dict(id="engine", status="ok" if ok_py and ok_q else "error", facts=[
        _f("python", py, min="3.11"), _f("duckdb", duckdb.__version__), _f("pandas", pandas.__version__),
        _f("query_ms", f"{ms} ms" if ms is not None else "gagal")]))
    # 2) free disk space where the app lives
    try: u = shutil.disk_usage(ROOT); free = u.free; tot = u.total
    except OSError: free = tot = 0
    st = "error" if free < 0.2 * 2**30 else "warn" if free < 1 * 2**30 else "ok"
    items.append(dict(id="storage", status=st, facts=[_f("free", _gb(free), min="1 GB"), _f("total", _gb(tot)), _f("path", str(ROOT))]))
    # 3) can we save recipients, history and saved mappings?
    sd = settings.state_dir()
    try:
        sd.mkdir(parents=True, exist_ok=True); probe = sd / ".write_test"; probe.write_text("ok"); probe.unlink(); w = "ok"; why = "bisa menulis"
    except OSError as e: w, why = "error", e.strerror or "tidak bisa menulis"
    items.append(dict(id="writable", status=w, facts=[_f("path", str(sd)), _f("result", why)]))
    # 4) bundled sample data
    if SAMPLE.exists():
        try:
            with SAMPLE.open("rb") as fh: n = sum(1 for _ in fh) - 1
            cols = SAMPLE.open(encoding="utf-8-sig").readline().count(",") + 1
            items.append(dict(id="sample", status="ok", facts=[_f("path", SAMPLE.resolve()), _f("size", f"{_id(SAMPLE.stat().st_size / 1024, 0)} KB"), _f("rows", _id(n, 0)), _f("columns", cols)]))
        except OSError as e: items.append(dict(id="sample", status="warn", facts=[_f("path", SAMPLE.resolve()), _f("reason", e.strerror or "tidak bisa dibaca")]))
    else: items.append(dict(id="sample", status="warn", facts=[_f("path", SAMPLE.resolve()), _f("reason", "file tidak ditemukan (opsional: kamu tetap bisa mengunggah data sendiri)")]))
    # 5) the app itself
    items.append(dict(id="port", status="ok", facts=[_f("address", f"{request.url.hostname}:{request.url.port}"), _f("pid", os.getpid())]))
    # 6) internet (only needed to send Telegram reports)
    ms, why = _internet()
    st = "warn" if ms is None or ms > 1500 else "ok"
    items.append(dict(id="internet", status=st, facts=[_f("host", "api.telegram.org:443"),
        _f("latency", f"{ms} ms" if ms is not None else "-", max="1.500 ms"), *([_f("reason", why)] if why else [])]))
    return {"items": items}

if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")
    @app.get("/{path:path}")
    def spa(path: str):
        f = DIST / path
        return FileResponse(f if f.is_file() else DIST / "index.html")

def _pids_on_port(port: int) -> set[int]:
    import subprocess
    try:
        if os.name == "nt":
            out = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True, timeout=10).stdout
            return {int(l.split()[-1]) for l in out.splitlines() if f"127.0.0.1:{port} " in l and "LISTENING" in l}
        out = subprocess.run(["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"], capture_output=True, text=True, timeout=10).stdout
        return {int(x) for x in out.split()}
    except Exception: return set()

def stop_previous(start: int = 8765, span: int = 50) -> int:
    """Stop older Sales Studio servers (any port in our range) so a double-click always runs the newest build."""
    import httpx, signal
    n = 0
    for p in range(start, start + span):
        with socket.socket() as sk:
            if sk.connect_ex(("127.0.0.1", p)) != 0: continue
        try:
            r = httpx.get(f"http://127.0.0.1:{p}/api/status", timeout=1.5)
            if r.status_code != 200 or "log" not in r.json(): continue     # not ours: leave it alone
        except Exception: continue
        for pid in _pids_on_port(p) - {os.getpid()}:
            try: os.kill(pid, signal.SIGTERM); n += 1
            except OSError: pass
    if n:
        import time; time.sleep(1)
    return n

def run():
    if not os.environ.get("SALES_STUDIO_PORT"): stop_previous()      # an explicit port (tests, dev) never touches other instances
    import uvicorn
    port = int(os.environ.get("SALES_STUDIO_PORT") or find_free_port())
    url = f"http://127.0.0.1:{port}"
    logging.info("Sales Studio berjalan di %s", url)
    print("Membuka aplikasi di browser kamu…")
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

if __name__ == "__main__":
    run()
