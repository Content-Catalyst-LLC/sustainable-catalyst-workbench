#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/offline/wheelhouse}"
mkdir -p "$OUT"
python3 -m pip download --dest "$OUT" -r "$ROOT/offline/requirements.txt"
python3 - <<PY
from pathlib import Path
import hashlib
root=Path("$OUT")
lines=[]
for path in sorted(root.iterdir()):
    if path.is_file():
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
(root/"SHA256SUMS.txt").write_text("\\n".join(lines)+"\\n")
print(f"Wheelhouse created at {root}")
PY
