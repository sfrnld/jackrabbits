from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def test_built_frontend_is_fresh():
    dist = ROOT / "web" / "dist" / "index.html"
    assert dist.exists(), "run: cd web && npm run build"
    src = max(p.stat().st_mtime for p in (ROOT / "web" / "src").rglob("*") if p.is_file())
    assert dist.stat().st_mtime >= src, "web/dist is stale: rebuild before shipping"

def test_launchers_exist():
    assert (ROOT / "Mulai.command").stat().st_mode & 0o111
    assert (ROOT / "Mulai.bat").exists()
