#!/usr/bin/env bash
# Create a clean source archive and SHA-256 checksum from a working tree.
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARENT_DIR="$(dirname "$PROJECT_DIR")"
ARCHIVE="$PARENT_DIR/ubuntu-glove-rebuilt-0.2.0-alpha.zip"
CHECKSUM="$PARENT_DIR/ubuntu-glove-rebuilt-0.2.0-alpha.sha256"

command -v zip >/dev/null || { echo "Missing zip. Install it with: sudo apt install -y zip" >&2; exit 1; }
command -v sha256sum >/dev/null || { echo "Missing sha256sum." >&2; exit 1; }

cd "$PROJECT_DIR"
rm -f "$ARCHIVE" "$CHECKSUM"
find . -type d -name '__pycache__' -prune -exec rm -rf {} +
cd "$PARENT_DIR"
zip -qr "$ARCHIVE" "$(basename "$PROJECT_DIR")" \
  -x "$(basename "$PROJECT_DIR")/.git/*" \
     "$(basename "$PROJECT_DIR")/**/__pycache__/*" \
     "$(basename "$PROJECT_DIR")/**/*.pyc" \
     "$(basename "$PROJECT_DIR")/**/*.pyo" \
     "$(basename "$PROJECT_DIR")/.app-staging.*/*" \
     "$(basename "$PROJECT_DIR")/.app-previous/*"
(
  sha256sum "$(basename "$ARCHIVE")" > "$(basename "$CHECKSUM")"
)
printf 'Created:\n  %s\n  %s\n' "$ARCHIVE" "$CHECKSUM"
