#!/bin/bash
# Build the delivery zip. Rebuilds the frontend, runs the tests, and leaves out secrets and local state.
set -euo pipefail
cd "$(dirname "$0")/.."
( cd web && npm run build >/dev/null )
uv run pytest -q
OUT="dist-zip"; NAME="sales-studio"; rm -rf "$OUT" && mkdir -p "$OUT"
zip -qr "$OUT/$NAME.zip" . -x ".venv/*" "web/node_modules/*" "state/*" ".env" "*/__pycache__/*" "__pycache__/*" ".pytest_cache/*" "dist-zip/*" ".DS_Store" "*/.DS_Store" ".git/*"
echo "Zip siap: $OUT/$NAME.zip ($(du -h "$OUT/$NAME.zip" | cut -f1))"
unzip -l "$OUT/$NAME.zip" | grep -E "\.env$|state/|node_modules|\.venv" && { echo "ERROR: secrets or junk in zip"; exit 1; } || true
