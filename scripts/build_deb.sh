#!/usr/bin/env bash
# Build a local Ubuntu Glove .deb only after required release metadata is real.
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

for command in dpkg-buildpackage python3; do
  command -v "$command" >/dev/null || {
    echo "Missing required command: $command" >&2
    echo "On Ubuntu, install: sudo apt install -y build-essential debhelper dh-python python3-all" >&2
    exit 1
  }
done

if grep -R --line-number --fixed-strings 'REPLACE-BEFORE-DISTRIBUTION' debian; then
  echo "Refusing to build a distribution package with placeholder maintainer/source metadata." >&2
  echo "Set the real Maintainer and Homepage in debian/control and debian/changelog first." >&2
  exit 1
fi

python3 main.py --check-data
python3 -m unittest discover -s tests -v
DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -us -uc

echo "Build complete. Inspect the generated .deb one directory above: $(dirname "$PROJECT_DIR")"
