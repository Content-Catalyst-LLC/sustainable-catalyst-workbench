#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/../sustainable-catalyst-workbench-plugin-v0.1.0.zip"
cd "$ROOT/wordpress-plugin"
rm -f "$OUT"
zip -qr "$OUT" sustainable-catalyst-workbench
printf 'Created %s\n' "$OUT"
