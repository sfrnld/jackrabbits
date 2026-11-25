"""Cheap guard: every api() call in the UI that hits a write-only route must use the method the server defines."""
import re
from pathlib import Path
from app.main import app

SRC = Path(__file__).resolve().parent.parent / "web" / "src"

def test_findings_calls_use_the_routes_methods():
    routes = {(path, m.upper()) for path, ops in app.openapi()["paths"].items() for m in ops}   # works however FastAPI nests routers
    store = (SRC / "lib" / "store.svelte.js").read_text()
    call = re.search(r"export async function decide\(.*?\n}\n", store, re.S).group(0)
    assert "'PUT'" in call and ("/api/findings/{fid}", "PUT") in routes
    assert ("/api/findings/{fid}", "DELETE") in routes and "'DELETE'" in re.search(r"export async function undoDecision.*?\n}\n", store, re.S).group(0)
