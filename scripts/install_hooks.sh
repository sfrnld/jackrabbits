#!/bin/bash
# Installs the pre-commit safety hook into this clone.
cd "$(dirname "$0")/.." || exit 1
cp scripts/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit && echo "Pre-commit hook installed."
