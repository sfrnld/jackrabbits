"""The real thing: boot the server as a subprocess exactly like the launcher does and talk HTTP to it."""
import os, subprocess, sys, time, urllib.request
from pathlib import Path
from app.main import find_free_port

ROOT = Path(__file__).resolve().parent.parent

def get(url):
    with urllib.request.urlopen(url, timeout=15) as r: return r.status, r.read().decode()

def test_app_boots_and_serves_everything(tmp_path):
    port = find_free_port(18000)
    env = {**os.environ, "SALES_STUDIO_PORT": str(port), "SALES_STUDIO_STATE": str(tmp_path), "SALES_STUDIO_ENV": str(tmp_path / ".env"),
           "BROWSER": "true", "TELEGRAM_BOT_TOKEN": ""}          # BROWSER=true: don't pop a real browser in tests
    p = subprocess.Popen([sys.executable, "-m", "app.main"], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        t0 = time.time()
        while time.time() - t0 < 30:
            try:
                if get(f"http://127.0.0.1:{port}/api/health")[0] == 200: break
            except OSError: time.sleep(0.3)
        else: raise AssertionError("server did not come up in 30s")
        assert time.time() - t0 < 15                                # criterion: welcome screen comes up fast
        for path in ("/", "/setup", "/studio/data", "/status"):     # SPA routes all serve the app
            code, body = get(f"http://127.0.0.1:{port}{path}"); assert code == 200 and "<div id=\"app\">" in body, path
        assert '"log"' in get(f"http://127.0.0.1:{port}/api/status")[1]
        assert "Sales Studio berjalan" in get(f"http://127.0.0.1:{port}/api/status")[1]
        assert all(i["status"] != "error" for i in __import__("json").loads(get(f"http://127.0.0.1:{port}/api/setup/check")[1])["items"])
    finally:
        p.terminate(); p.wait(timeout=10)
