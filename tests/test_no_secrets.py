"""Guards against publishing secrets: .gitignore covers them, and no tracked-looking file contains a bot token."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".git", ".venv", "node_modules", "state", "dist-zip", "__pycache__", ".pytest_cache"}
TOKEN = re.compile(r"\b[0-9]{8,10}:[A-Za-z0-9_-]{35}\b")

def test_gitignore_covers_secrets_and_local_state():
    g = (ROOT / ".gitignore").read_text().splitlines()
    for must in (".env", ".env.*", "!.env.example", "state/", "dist-zip/", "*.zip", "*.pem", "*.key", ".venv/", "web/node_modules/"):
        assert must in g, must

def test_env_example_has_no_real_token():
    assert (ROOT / ".env.example").read_text().strip().splitlines()[-1] == "TELEGRAM_BOT_TOKEN="

def test_no_bot_token_in_any_project_file():
    hits = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or SKIP & set(p.relative_to(ROOT).parts) or p.name == ".env" or p.stat().st_size > 2_000_000: continue
        try: txt = p.read_text(errors="ignore")
        except OSError: continue
        if TOKEN.search(txt): hits.append(str(p.relative_to(ROOT)))
    assert not hits, f"token-shaped string found in: {hits}"
