#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend"
if ! command -v python3.12 >/dev/null 2>&1; then
  echo "python3.12 not found. Install with: brew install python@3.12"
  exit 1
fi
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp -n .env.example .env 2>/dev/null || true
echo "Backend environment ready. Edit backend/.env if needed, then run scripts/run_backend.sh"
